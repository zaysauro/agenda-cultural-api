import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "http://www.fundacaoculturaldecuritiba.com.br"

CATEGORIES = [
    "cinema",
    "musica",
    "teatro-e-circo",
    "artes-visuais",
    "danca",
    "literatura"
]

DAYS_AHEAD = 3

def clean_text(element):
    if not element:
        return ""
    return element.get_text(" ", strip=True)

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def extract_events(html, url, category, date_text):
    soup = BeautifulSoup(html, "html.parser")
    events = []

    items = soup.select("article, .evento, .event, .card, .item, li")

    for item in items:
        title_element = item.select_one("h1, h2, h3, h4, a")
        link_element = item.select_one("a")

        title = clean_text(title_element)

        if not title or len(title) < 4:
            continue

        link = url
        if link_element and link_element.has_attr("href"):
            link = urljoin(BASE_URL, link_element["href"])

        events.append({
            "title": title,
            "dateText": date_text,
            "category": category,
            "location": "",
            "url": link,
            "source": url
        })

    return events

def scrape_events():
    all_events = []
    today = datetime.now().date()

    for category in CATEGORIES:
        for offset in range(DAYS_AHEAD):
            date = today + timedelta(days=offset)
            date_string = date.isoformat()

            url = f"{BASE_URL}/agenda/{category}/{date_string}?o=1"

            try:
                print(f"Buscando: {url}")
                html = fetch_html(url)
                events = extract_events(html, url, category, date_string)
                all_events.extend(events)
            except Exception as error:
                print(f"Erro em {url}: {error}")

    unique_events = []
    seen = set()

    for event in all_events:
        key = event["title"] + event["dateText"] + event["url"]
        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    return unique_events

def main():
    events = scrape_events()

    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "events": events
    }

    output_path = Path("docs/agenda.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"agenda.json gerado com {len(events)} eventos.")

if __name__ == "__main__":
    main()
