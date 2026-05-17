import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

URL = "http://www.fundacaoculturaldecuritiba.com.br/agenda/"

def clean_text(element):
    if not element:
        return ""
    return element.get_text(" ", strip=True)

def scrape_events():
    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    response = session.get(
        URL,
        timeout=30,
        headers=headers,
        allow_redirects=True
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    for item in soup.select("article, .evento, .event, .card, .agenda-item"):
        title_element = item.select_one("h1, h2, h3, .titulo, .title")
        date_element = item.select_one(".data, .date, time")
        location_element = item.select_one(".local, .location, .venue")
        link_element = item.select_one("a")

        title = clean_text(title_element)

        if not title:
            continue

        link = ""
        if link_element and link_element.has_attr("href"):
            link = urljoin(URL, link_element["href"])

        events.append({
            "title": title,
            "dateText": clean_text(date_element),
            "location": clean_text(location_element),
            "url": link or URL,
            "source": URL
        })

    return events

def write_json(events, error=None):
    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "error": error,
        "events": events
    }

    output_path = Path("docs/agenda.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Arquivo gerado com {len(events)} eventos.")
    if error:
        print(f"Erro registrado no JSON: {error}")

def main():
    try:
        events = scrape_events()
        write_json(events)
    except Exception as error:
        write_json([], str(error))

if __name__ == "__main__":
    main()
