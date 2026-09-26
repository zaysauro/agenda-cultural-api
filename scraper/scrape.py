import json
import re
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

def is_valid_image_url(value):
    if not value:
        return False
    value = value.strip()
    if value.startswith("data:image/"):
        return False
    if value.lower().startswith(("javascript:", "about:")):
        return False
    return bool(re.match(r"^(https?:)?//|^/", value, re.I))

def image_from_element(image_element, base_url):
    if not image_element:
        return ""

    # Prioriza os atributos de lazy loading, que normalmente apontam para a
    # imagem original, e deixa src como último recurso porque ele pode ser
    # apenas um placeholder de baixa resolução.
    for attr in (
        "data-original",
        "data-full",
        "data-image",
        "data-lazy-src",
        "data-src",
        "data-url",
        "data-thumbnail",
        "data-thumb",
        "src",
    ):
        value = image_element.get(attr)
        if is_valid_image_url(value):
            return urljoin(base_url, value)

    # <picture> pode guardar a imagem original em <source>.
    for source in image_element.find_all("source"):
        srcset = source.get("srcset") or source.get("data-srcset")
        if srcset:
            candidates = []
            for entry in srcset.split(","):
                url = entry.strip().split(" ")[0]
                if is_valid_image_url(url):
                    candidates.append(url)
            if candidates:
                return urljoin(base_url, candidates[-1])

    # Tenta o maior endereço disponível no srcset.
    srcset = image_element.get("srcset") or image_element.get("data-srcset")
    if srcset:
        candidates = []
        for entry in srcset.split(","):
            url = entry.strip().split(" ")[0]
            if is_valid_image_url(url):
                candidates.append(url)
        if candidates:
            return urljoin(base_url, candidates[-1])

    # Alguns cards usam background-image em vez de <img>.
    style = image_element.get("style", "")
    match = re.search(r"background-image\s*:\s*url\((?:'|\")?([^'\")]+)", style, re.I)
    if match and is_valid_image_url(match.group(1)):
        return urljoin(base_url, match.group(1))

    return ""

def jsonld_images(soup, base_url):
    images = []

    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        stack = data if isinstance(data, list) else [data]
        while stack:
            node = stack.pop()

            if isinstance(node, list):
                stack.extend(node)
                continue

            if not isinstance(node, dict):
                continue

            image = node.get("image")
            if isinstance(image, str) and is_valid_image_url(image):
                images.append(urljoin(base_url, image))
            elif isinstance(image, list):
                for value in image:
                    if isinstance(value, str) and is_valid_image_url(value):
                        images.append(urljoin(base_url, value))
                    elif isinstance(value, dict):
                        url = value.get("url") or value.get("contentUrl")
                        if isinstance(url, str) and is_valid_image_url(url):
                            images.append(urljoin(base_url, url))
            elif isinstance(image, dict):
                url = image.get("url") or image.get("contentUrl")
                if isinstance(url, str) and is_valid_image_url(url):
                    images.append(urljoin(base_url, url))

            for value in node.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)

    return list(dict.fromkeys(images))

def page_preview_image(soup, base_url):
    # Fallback para a imagem Open Graph da própria página.
    for selector in (
        'meta[property="og:image"]',
        'meta[property="og:image:url"]',
        'meta[name="twitter:image"]',
    ):
        meta = soup.select_one(selector)
        if meta and is_valid_image_url(meta.get("content")):
            return urljoin(base_url, meta["content"])

    # JSON-LD costuma conter a arte original do evento/filme, quando o site
    # publica Schema.org.
    images = jsonld_images(soup, base_url)
    if images:
        return images[0]

    return ""

def candidate_image(candidate, base_url):
    # Procura primeiro dentro do próprio card.
    image = candidate.select_one("img")
    image_url = image_from_element(image, base_url)
    if image_url:
        return image_url

    # Também cobre <picture>, <source> e elementos com background-image.
    visual = candidate.select_one("picture, source, [style*='background-image']")
    image_url = image_from_element(visual, base_url)
    if image_url:
        return image_url

    # Alguns sites colocam a imagem dentro de um link separado do bloco de
    # texto; procura uma segunda camada antes de desistir.
    link_with_image = candidate.select_one("a img")
    return image_from_element(link_with_image, base_url)

def extract_items(source):
    try:
        html = fetch_html(source["url"])
        soup = BeautifulSoup(html, "html.parser")
        source_preview = page_preview_image(soup, source["url"])

        items = []
        candidates = soup.select("article, .post, .noticia, .evento, .item, .card, li")

        for candidate in candidates:
            title_element = candidate.select_one("h1, h2, h3, h4, a")
            link_element = candidate.select_one("a")
            summary_element = candidate.select_one("p, .resumo, .summary, .descricao")

            title = clean_text(title_element)
            summary = clean_text(summary_element)

            if not title or len(title) < 4:
                continue

            url = source["url"]
            if link_element and link_element.has_attr("href"):
                url = urljoin(source["url"], link_element["href"])

            image_url = candidate_image(candidate, source["url"])

            # Se o card não expõe a imagem, tenta a página individual do evento.
            # Muitos sites deixam a arte oficial apenas em og:image/JSON-LD da página
            # de detalhe, e não no HTML da listagem.
            if not image_url and url != source["url"]:
                try:
                    detail_html = fetch_html(url)
                    detail_soup = BeautifulSoup(detail_html, "html.parser")
                    image_url = page_preview_image(detail_soup, url)
                except Exception:
                    pass

            # Último fallback: imagem original declarada pela própria página-fonte.
            if not image_url:
                image_url = source_preview

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
