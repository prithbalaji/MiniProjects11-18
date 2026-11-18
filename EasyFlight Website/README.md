# EasyFlight

EasyFlight is a lightweight flight-search page with a simple search form and a searchable directory of airport codes. It sends searches to Google Flights for current prices and booking options.

## Features

- Round-trip and one-way searches
- Airport autocomplete covering 9,053 IATA-coded airports
- Search airports by code, city, or airport name
- Keyboard-accessible airport suggestions
- Traveler and cabin selections
- Responsive layout for desktop and mobile

## Run locally

No build step or package installation is required. Keep `index.html` and `airports.js` together in the `EasyFlight Website` folder, then open `index.html` in a browser.

Alternatively, run a local static server from the project root:

```sh
python3 -m http.server 8000 --directory "EasyFlight Website"
```

Then visit <http://localhost:8000>.

## Project files

- `EasyFlight Website/index.html` — page markup, styles, and search behavior
- `EasyFlight Website/airports.js` — bundled airport-code directory

## Airport data

The airport directory is a local snapshot of [OurAirports data](https://ourairports.com/data/). The data is public domain. Update `airports.js` from the source periodically to refresh the airport catalog.

## Flight results

EasyFlight does not scrape Google Flights or provide its own live fares. Searches open Google Flights, where current prices and booking options are shown. EasyFlight is not affiliated with Google.
