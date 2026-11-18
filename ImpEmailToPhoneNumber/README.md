# ImpEmailToPhoneNumber

Scans recent Gmail for likely action-required messages and sends one concise SMS each week. The detector uses a list of common action phrases, so review the preview and tune `ACTION_PHRASES` in `main.py` to suit your inbox.

The app requests **read-only Gmail access**. It does not modify or label messages. It previews by default; an SMS is only sent when run with `--send`. Sending SMS may incur Twilio charges.

## Setup

1. Use Python 3.9 or newer and create a virtual environment:

   ```sh
   cd "/path/to/Prith's Projects/ImpEmailToPhoneNumber"
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. In Google Cloud, enable the Gmail API, configure the OAuth consent screen, create an OAuth client ID for a **Desktop app**, and download its JSON file as `credentials.json` into this project folder.
3. Copy `.env.example` to `.env`. Set your destination phone number, Twilio account SID, auth token, and Twilio sender number. Use international E.164 format (for example, `+15551234567`). Keep `.env`, `credentials.json`, and `token.json` private; they are excluded from Git.
4. Preview the first run. It opens Google's OAuth consent flow in a browser and saves the refresh token locally:

   ```sh
   .venv/bin/python main.py
   ```

5. To test delivery manually after reviewing the preview, run:

   ```sh
   .venv/bin/python main.py --send
   ```

   Successful sends are recorded locally so rerunning the command won't send a second SMS during the same ISO week. The scheduled job should run on the computer that holds the OAuth token and project files.

## Weekly schedule

The requested schedule is Monday at 9:00 AM in `America/Los_Angeles`. On macOS, add this line to your crontab with the actual absolute project path:

```cron
0 9 * * 1 cd "/absolute/path/to/Prith's Projects/ImpEmailToPhoneNumber" && .venv/bin/python main.py --send >> weekly.log 2>&1
```

Edit it with `crontab -e`. Cron uses the computer's local timezone; set macOS to Pacific time for the schedule above. The computer must be awake and connected to the internet when the job runs.

## Detection and limits

- Each run checks messages from the last seven days, excluding Gmail's Promotions, Social, and Forums categories.
- This is a phrase-based heuristic, not an AI classifier. It can miss relevant mail or flag irrelevant mail; check the dry-run preview before enabling the schedule.
- Up to 100 messages are checked per run. A long SMS is shortened to stay within the configured preview limit.
- `.state.json` prevents multiple sends in the same week on this machine. Keep it with the project to preserve that guard.
