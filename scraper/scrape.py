import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

SOURCES = [
    # Categorias culturais principais
    {"title": "Artes Visuais", "slug": "artes-visuais", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/artes-visuais/"},
    {"title": "Cinema", "slug": "cinema", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/cinema/"},
    {"title": "Dança", "slug": "danca", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/danca/"},
    {"title": "Literatura", "slug": "literatura", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/literatura/"},
    {"title": "Música", "slug": "musica", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/musica/"},
    {"title": "Patrimônio Cultural", "slug": "patrimonio-cultural", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/patrimonio-cultural/"},
    {"title": "Teatro e Circo", "slug": "teatro-e-circo", "group": "categoria", "url": "http://www.fundacaoculturaldecuritiba.com.br/teatro-e-circo/"},

    # Conteúdo principal
    {"title": "Agenda", "slug": "agenda", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/agenda/"},
    {"title": "Notícias", "slug": "noticias", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/noticias/"},
    {"title": "Cursos e Oficinas", "slug": "cursos", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/cursos/"},
    {"title": "Grandes Eventos", "slug": "grandes-eventos", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/grandes-eventos/"},
    {"title": "Espaços Culturais", "slug": "espacos-culturais", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/espacos-culturais/"},
    {"title": "Faça, Curta e Confira Cultura em Curitiba", "slug": "faca-curta-confira", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/faca-curta-e-confira-cultura/"},
    {"title": "Núcleos Regionais", "slug": "nucleos-regionais", "group": "conteudo", "url": "http://www.fundacaoculturaldecuritiba.com.br/nucleos-regionais/"},

    # Notícias e informações da Prefeitura de Curitiba
    {"title": "Notícias da Prefeitura", "slug": "noticias-prefeitura", "group": "noticias_prefeitura", "url": "https://www.curitiba.pr.gov.br/"},
    {"title": "Prefeitura de Curitiba", "slug": "prefeitura-curitiba", "group": "informacoes_prefeitura", "url": "https://www.curitiba.pr.gov.br/"},

    # Notícias culturais independentes
    {"title": "Curitibacult", "slug": "curitibacult", "group": "noticias_culturais", "url": "https://curitibacult.com.br/"},

    # Institucional
    {"title": "Institucional", "slug": "institucional", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/historia/inicio/"},
    {"title": "Galeria", "slug": "galeria", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/galeria/"},
    {"title": "Lei de Incentivo", "slug": "lei-de-incentivo", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/leideincentivo/avisos/"},
    {"title": "Editais FCC", "slug": "editais", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/editais/"},
    {"title": "Apoie a Cultura", "slug": "apoie-a-cultura", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/apoie-a-cultura/"},
    {"title": "Transparência", "slug": "transparencia", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/institucional/transparencia/"},
    {"title": "Contato", "slug": "contato", "group": "institucional", "url": "http://www.fundacaoculturaldecuritiba.com.br/contato/"},
]

def clean_text(element):
    if not element:
        return ""
    return element.get_text(" ", strip=True)

def fetch_html(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
    )
    response.raise_for_status()
    return response.text

def extract_items(source):
    try:
        html = fetch_html(source["url"])
        soup = BeautifulSoup(html, "html.parser")

        items = []
        candidates = soup.select("article, .post, .noticia, .evento, .item, .card, li")

        for candidate in candidates:
            title_element = candidate.select_one("h1, h2, h3, h4, a")
            link_element = candidate.select_one("a")
            summary_element = candidate.select_one("p, .resumo, .summary, .descricao")
            image_element = candidate.select_one("img")

            title = clean_text(title_element)
            summary = clean_text(summary_element)

            if not title or len(title) < 4:
                continue

            url = source["url"]
            if link_element and link_element.has_attr("href"):
                url = urljoin(source["url"], link_element["href"])

            image_url = ""
            if image_element and image_element.has_attr("src"):
                image_url = urljoin(source["url"], image_element["src"])

            items.append({
                "title": title,
                "summary": summary,
                "category": source["title"],
                "categorySlug": source["slug"],
                "group": source["group"],
                "url": url,
                "imageUrl": image_url,
                "sourceUrl": source["url"]
            })

        return items

    except Exception as error:
        print(f"Erro em {source['title']}: {error}")
        return []

def main():
    all_items = []

    for source in SOURCES:
        print(f"Coletando: {source['title']}")
        all_items.extend(extract_items(source))

    unique_items = []
    seen = set()

    for item in all_items:
        key = item["title"] + item["url"]
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(unique_items),
        "sources": SOURCES,
        "items": unique_items,
        "events": unique_items
    }

    output_path = Path("docs/agenda.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"agenda.json gerado com {len(unique_items)} itens.")

if __name__ == "__main__":
    main()
