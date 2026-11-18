import argparse
import base64
import json
import os
import re
from datetime import datetime
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_DIR = Path(__file__).resolve().parent
STATE_FILE = PROJECT_DIR / ".state.json"
MAX_MESSAGES = 100
MAX_SMS_LENGTH = 1400

ACTION_PHRASES = (
    "action is required",
    "action required",
    "action needed",
    "your response is required",
    "requires your approval",
    "awaiting your approval",
    "approval needed",
    "please respond",
    "please reply",
    "please confirm",
    "please complete",
    "please review",
    "please submit",
    "please sign",
    "respond by",
    "reply by",
    "confirm by",
    "submit by",
    "complete by",
    "due by",
    "payment due",
    "invoice due",
    "deadline",
    "verify your account",
    "verify your identity",
    "renew your",
    "we need you to",
    "you must",
    "to avoid interruption",
    "expires on",
)
ACTION_PATTERN = re.compile(
    "|".join(re.escape(phrase) for phrase in sorted(ACTION_PHRASES, key=len, reverse=True)),
    re.IGNORECASE,
)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _decode_body(payload):
    plain_parts = []
    html_parts = []

    def collect(part):
        body = part.get("body", {})
        data = body.get("data")
        mime_type = part.get("mimeType", "")
        if data:
            decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
            text = decoded.decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                plain_parts.append(text)
            elif mime_type == "text/html":
                html_parts.append(text)
        for child in part.get("parts", []):
            collect(child)

    collect(payload)
    if plain_parts:
        return "\n".join(plain_parts)
    if html_parts:
        extractor = _TextExtractor()
        extractor.feed("\n".join(html_parts))
        return " ".join(" ".join(extractor.parts).split())
    return ""


def is_action_required(subject, body):
    return bool(ACTION_PATTERN.search(f"{subject}\n{body}"))


def _header(message, name):
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _excerpt(body):
    match = ACTION_PATTERN.search(body)
    if match:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", body)
        for sentence in sentences:
            if match.group(0).lower() in sentence.lower():
                return " ".join(sentence.split())[:220]
    return " ".join(body.split())[:220]


def _gmail_messages(service):
    messages = []
    scanned = 0
    page_token = None
    while scanned < MAX_MESSAGES:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q="newer_than:7d -category:promotions -category:social -category:forums",
                maxResults=min(100, MAX_MESSAGES - scanned),
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("messages", []):
            scanned += 1
            message = (
                service.users()
                .messages()
                .get(userId="me", id=item["id"], format="full")
                .execute()
            )
            subject = _header(message, "Subject")
            body = _decode_body(message.get("payload", {}))
            if is_action_required(subject, body):
                messages.append(
                    {
                        "id": item["id"],
                        "from": parseaddr(_header(message, "From"))[1]
                        or _header(message, "From")
                        or "Unknown sender",
                        "subject": subject or "(no subject)",
                        "excerpt": _excerpt(body),
                    }
                )
            if scanned >= MAX_MESSAGES:
                break
        page_token = response.get("nextPageToken")
        if not page_token or scanned >= MAX_MESSAGES:
            break
    return messages


def _gmail_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    client_file = Path(
        os.environ.get("GOOGLE_OAUTH_CLIENT_FILE", str(PROJECT_DIR / "credentials.json"))
    )
    if not client_file.is_absolute():
        client_file = PROJECT_DIR / client_file
    if not client_file.is_file():
        raise FileNotFoundError(
            f"Gmail OAuth client file not found: {client_file}. "
            "Create a Desktop app OAuth client in Google Cloud and save it there."
        )

    token_file = PROJECT_DIR / "token.json"
    credentials = None
    if token_file.is_file():
        credentials = Credentials.from_authorized_user_file(
            str(token_file), ["https://www.googleapis.com/auth/gmail.readonly"]
        )
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_file), ["https://www.googleapis.com/auth/gmail.readonly"]
        )
        credentials = flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    token_file.chmod(0o600)
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _week_key(now):
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def _already_sent(week_key):
    if not STATE_FILE.is_file():
        return False
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return state.get("last_sent_week") == week_key


def _record_sent(week_key):
    temp_file = STATE_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps({"last_sent_week": week_key}) + "\n", encoding="utf-8"
    )
    temp_file.replace(STATE_FILE)


def _build_sms(messages, now):
    title = f"Weekly Gmail action check ({now:%b %-d}):"
    if not messages:
        return f"{title} no action-required emails found in the last 7 days."

    lines = [f"{title} {len(messages)} email(s) to review."]
    for index, message in enumerate(messages, start=1):
        item = (
            f"{index}. {message['from']}: {message['subject']}\n"
            f"{message['excerpt']}\n"
            f"https://mail.google.com/mail/u/0/#all/{message['id']}"
        )
        candidate = "\n\n".join(lines + [item])
        if len(candidate) > MAX_SMS_LENGTH:
            remaining = len(messages) - index + 1
            suffix = f"\n\n...and {remaining} more. Open Gmail to review."
            return "\n\n".join(lines)[: MAX_SMS_LENGTH - len(suffix)] + suffix
        lines.append(item)
    return "\n\n".join(lines)


def _send_sms(body):
    from twilio.rest import Client

    required = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "TO_PHONE_NUMBER")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise ValueError(f"Missing required SMS settings: {', '.join(missing)}")
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    return client.messages.create(
        body=body,
        from_=os.environ["TWILIO_FROM_NUMBER"],
        to=os.environ["TO_PHONE_NUMBER"],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Find likely action-required Gmail and send a weekly SMS."
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the SMS (without this flag, print a preview only).",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(PROJECT_DIR / ".env")
    timezone = ZoneInfo(os.environ.get("TIME_ZONE", "America/Los_Angeles"))
    now = datetime.now(timezone)
    week_key = _week_key(now)

    if args.send and _already_sent(week_key):
        print(f"An SMS has already been sent for {week_key}; skipping.")
        return 0

    messages = _gmail_messages(_gmail_service())
    sms = _build_sms(messages, now)
    if not args.send:
        print(f"Found {len(messages)} likely action-required email(s).")
        print("--- SMS preview (not sent) ---")
        print(sms)
        return 0

    sent = _send_sms(sms)
    _record_sent(week_key)
    print(f"Weekly SMS sent successfully (Twilio message SID: {sent.sid}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
