import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

URLS = [
    "http://www.fundacaoculturaldecuritiba.com.br/agenda/",
    "https://www.fundacaoculturaldecuritiba.com.br/agenda/",
    "https://www.fundacaoculturaldecuritiba.com.br/agenda/todas/"
]

def clean_text(element):
    if not element:
        return ""
    return element.get_text(" ", strip=True)

def fetch_page():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    last_error = None

    for url in URLS:
        for attempt in range(3):
            try:
                print(f"Tentando acessar: {url} tentativa {attempt + 1}")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                if len(response.text) < 500:
                    raise Exception("Página retornou conteúdo muito pequeno.")

                return url, response.text

            except Exception as error:
                last_error = error
                print(f"Falhou: {error}")
                time.sleep(5)

    raise Exception(f"Não foi possível acessar nenhuma URL. Último erro: {last_error}")

def scrape_events():
    source_url, html = fetch_page()
    soup = BeautifulSoup(html, "html.parser")

    events = []

    possible_items = soup.select(
        "article, .evento, .event, .card, .agenda-item, .item, li"
    )

    for item in possible_items:
        title_element = item.select_one("h1, h2, h3, h4, .titulo, .title, a")
        date_element = item.select_one(".data, .date, time")
        location_element = item.select_one(".local, .location, .venue")
        link_element = item.select_one("a")

        title = clean_text(title_element)

        if not title or len(title) < 4:
            continue

        link = source_url
        if link_element and link_element.has_attr("href"):
            link = urljoin(source_url, link_element["href"])

        events.append({
            "title": title,
            "dateText": clean_text(date_element),
            "location": clean_text(location_element),
            "url": link,
            "source": source_url
        })

    unique_events = []
    seen = set()

    for event in events:
        key = event["title"] + event["url"]
        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    return unique_events

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
        print(f"Erro registrado: {error}")

def main():
    try:
        events = scrape_events()
        write_json(events)
    except Exception as error:
        write_json([], str(error))
        print(f"Erro final: {error}")

if __name__ == "__main__":
    main()
