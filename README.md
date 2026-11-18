# MiniProjects11-18

A collection of two small web and Python projects built for practical everyday use.

## Projects

| Project | Description | Technology |
| --- | --- | --- |
| [EasyFlight Website](EasyFlight%20Website) | A responsive flight-search interface with airport autocomplete | HTML, CSS, JavaScript |
| [ImpEmailToPhoneNumber](ImpEmailToPhoneNumber) | Finds likely action-required Gmail messages and sends weekly SMS summaries | Python, Gmail API, Twilio |

## EasyFlight Website

EasyFlight is a lightweight, browser-based flight-search page.

### Features

- One-way and round-trip searches
- Airport autocomplete covering more than 9,000 IATA-coded airports
- Search by airport code, city, airport name, or country
- Origin and destination swapping
- Traveler and cabin-class selection
- Suggested destinations
- Searches that open directly in Google Flights
- Responsive layouts and keyboard-accessible suggestions

### Run locally

No build step or package installation is required.

```sh
python3 -m http.server 8000 --directory "EasyFlight Website"
```

Open [http://localhost:8000](http://localhost:8000).

Airport data comes from a bundled snapshot based on OurAirports data. EasyFlight does not scrape Google Flights or provide its own live fare data.

See [EasyFlight Website/README.md](EasyFlight%20Website/README.md) for details.

## ImpEmailToPhoneNumber

ImpEmailToPhoneNumber scans recent Gmail messages for likely action-required emails and sends an optional weekly SMS summary through Twilio.

### Features

- Scans Gmail messages from the previous seven days
- Excludes Promotions, Social, and Forums categories
- Uses configurable action phrases to detect likely requests
- Supports a preview-only mode
- Sends no SMS unless `--send` is specified
- Sends at most one SMS per ISO week
- Uses Gmail read-only OAuth access

### Setup

Python 3.9 or newer is required.

```sh
cd ImpEmailToPhoneNumber
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

In Google Cloud:

1. Enable the Gmail API.
2. Configure the OAuth consent screen.
3. Create an OAuth client ID for a Desktop app.
4. Download the JSON file as `credentials.json` in the project folder.

Configure `.env` with the destination phone number and Twilio credentials:

```dotenv
GOOGLE_OAUTH_CLIENT_FILE=credentials.json
TO_PHONE_NUMBER=+15551234567
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=+15557654321
TIME_ZONE=America/Los_Angeles
```

Preview messages without sending an SMS:

```sh
.venv/bin/python main.py
```

Send the SMS manually:

```sh
.venv/bin/python main.py --send
```

Sending SMS messages may incur Twilio charges.

See [ImpEmailToPhoneNumber/README.md](ImpEmailToPhoneNumber/README.md) for setup, scheduling, tests, and privacy details.

## Repository Structure

```text
MiniProjects11-18/
├── EasyFlight Website/
│   ├── index.html
│   ├── airports.js
│   └── README.md
└── ImpEmailToPhoneNumber/
    ├── main.py
    ├── test_main.py
    ├── requirements.txt
    ├── .env.example
    └── README.md
```

## Security

Never commit `.env`, Gmail OAuth credentials, `token.json`, or `.state.json`. Keep all sensitive credentials private.
