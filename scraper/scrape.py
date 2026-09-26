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
    # Guia Curitiba — eventos públicos, parques, praças e lazer ao ar livre.
    # Imagens ficam desligadas por enquanto; imageUrl continua no contrato para ativação futura.
    {"title": "Prefeitura — Parques", "slug": "prefeitura-parques", "group": "prefeitura_eventos", "category": "Cidade", "categorySlug": "cidade", "public_space": True, "outdoor": True, "images_enabled": False, "url": "https://guia.curitiba.pr.gov.br/Evento/Listar/?categoriaid=27"},
    {"title": "Prefeitura — Esportes", "slug": "prefeitura-esportes", "group": "prefeitura_eventos", "category": "Esporte", "categorySlug": "esporte", "public_space": True, "outdoor": True, "images_enabled": False, "url": "https://guia.curitiba.pr.gov.br/Evento/Listar/?categoriaid=1"},
    {"title": "Prefeitura — Passeios e Tours", "slug": "prefeitura-passeios", "group": "prefeitura_eventos", "category": "Cidade", "categorySlug": "cidade", "public_space": True, "outdoor": True, "images_enabled": False, "url": "https://guia.curitiba.pr.gov.br/Evento/Listar/?categoriaid=30"},
    {"title": "Prefeitura — Feiras", "slug": "prefeitura-feiras", "group": "prefeitura_eventos", "category": "Cidade", "categorySlug": "cidade", "public_space": True, "outdoor": True, "images_enabled": False, "url": "https://guia.curitiba.pr.gov.br/Evento/Listar/?categoriaid=12"},

    # Universidades — eventos e programação pública dos campi de Curitiba
    {"title": "UTFPR Curitiba — Eventos", "slug": "utfpr-curitiba", "group": "universidade", "category": "Cidade", "categorySlug": "cidade", "organizer": "UTFPR", "images_enabled": False, "url": "https://www.utfpr.edu.br/campus/curitiba/agenda-eventos"},
    {"title": "UFPR — Agenda de Eventos", "slug": "ufpr-eventos", "group": "universidade", "category": "Cidade", "categorySlug": "cidade", "organizer": "UFPR", "images_enabled": False, "url": "https://ufpr.br/agenda-eventos/"},

    # Esporte — programação oficial dos clubes e eventos nos estádios
    {"title": "Coritiba — Couto Pereira", "slug": "coritiba", "group": "esporte", "category": "Esporte", "venue": "Couto Pereira", "sports_only": True, "url": "https://www.coritiba.com.br"},
    {"title": "Athletico — Ligga Arena", "slug": "athletico", "group": "esporte", "category": "Esporte", "venue": "Ligga Arena", "sports_only": True, "url": "https://www.athletico.com.br"},

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

def extract_date_time(text):
    if not text:
        return "", ""

    # Aceita datas comuns em sites brasileiros: DD/MM/YYYY, DD-MM-YYYY e ISO.
    match = re.search(r"\\b(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2,4})\\b", text)
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = "20" + year
        date = f"{year}-{int(month):02d}-{int(day):02d}"
        time_match = re.search(r"\\b([01]?\\d|2[0-3]):([0-5]\\d)\\b", text)
        return date, (time_match.group(0) if time_match else "")

    iso = re.search(r"\\b(20\\d{2})-(\\d{2})-(\\d{2})\\b", text)
    if iso:
        date = "-".join(iso.groups())
        time_match = re.search(r"\\b([01]?\\d|2[0-3]):([0-5]\\d)\\b", text)
        return date, (time_match.group(0) if time_match else "")

    return "", ""



def extract_month_day(text):
    """Extrai datas em formatos como 'domingo (05)' quando possível."""
    if not text:
        return ""
    match = re.search(r"\\b(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)?\\s*\\(?([0-3]?\\d)[/-]([01]?\\d)\\)?\\b", text, re.I)
    if not match:
        return ""
    day, month = map(int, match.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return ""
    return f"{datetime.now().year:04d}-{month:02d}-{day:02d}"


def classify_public_event(text, source):
    lowered = clean_text(text).casefold()
    public_space_keywords = (
        "parque", "praça", "praca", "bosque", "jardim", "regional",
        "calçadão", "calcadao", "largo", "quadra pública", "quadra publica",
        "pista", "ciclovia"
    )
    free_keywords = (
        "gratuito", "gratuita", "grátis", "gratis", "entrada franca",
        "sem custo", "livre", "de graça", "gratuitamente"
    )
    outdoor = any(k in lowered for k in public_space_keywords) or source.get("outdoor", False)
    public_space = outdoor or source.get("public_space", False)
    free = any(k in lowered for k in free_keywords)

    return {
        "publicSpace": bool(public_space),
        "outdoor": bool(outdoor),
        "free": bool(free),
        "organizer": "Prefeitura de Curitiba"
    }


def extract_prefeitura_events(source):
    """Coleta eventos do Guia Curitiba, priorizando espaços públicos."""
    urls = [source["url"]]
    for page in range(2, 6):
        separator = "&" if "?" in source["url"] else "?"
        urls.append(f"{source['url']}{separator}pagina={page}")

    items = []
    seen_urls = set()

    for page_url in urls:
        try:
            html = fetch_html(page_url)
            soup = BeautifulSoup(html, "html.parser")
        except Exception as error:
            print(f"Erro no Guia Curitiba ({page_url}): {error}")
            continue

        candidates = soup.select(
            "article, .evento, .event, .card, .item, "
            "[class*='evento'], [class*='event'], [class*='card']"
        )

        for candidate in candidates:
            title_element = candidate.select_one(
                "h1, h2, h3, h4, h5, .titulo, .title, [class*='titulo'], [class*='title']"
            )
            link_element = candidate.select_one("a[href]")
            title = clean_text(title_element) or (clean_text(link_element) if link_element else "")

            if not title or len(title) < 4:
                continue

            url = page_url
            if link_element:
                url = urljoin(page_url, link_element.get("href", ""))

            if not url or url in seen_urls:
                continue

            text = clean_text(candidate)
            if len(text) < 12:
                continue

            noise = ("filtre por categoria", "limpar filtro", "compartilhe com seus amigos")
            if any(n in text.casefold() for n in noise) and len(text) < 250:
                continue

            event_date, event_time = extract_date_time(text)
            if not event_date:
                event_date = extract_month_day(text)

            classification = classify_public_event(text, source)

            image_url = ""
            if source.get("images_enabled", False):
                image_url = candidate_image(candidate, page_url)

            items.append({
                "title": title,
                "summary": text[:500],
                "category": source.get("category", "Cidade"),
                "categorySlug": source.get("categorySlug", "cidade"),
                "startDate": event_date,
                "startTime": event_time,
                "venue": source.get("venue", ""),
                "group": source["group"],
                "url": url,
                "imageUrl": image_url,
                "sourceUrl": source["url"],
                **classification
            })
            seen_urls.add(url)

    return items

def extract_university_events(source):
    """Coleta agendas oficiais das universidades, sem baixar imagens."""
    items = []
    seen = set()
    base_url = source["url"]

    # UTFPR possui uma área própria de agenda; UFPR usa uma listagem paginada.
    urls = [base_url]
    if "ufpr.br" in base_url:
        urls.extend(urljoin(base_url, f"page/{page}/") for page in range(2, 7))

    for page_url in urls:
        try:
            html = fetch_html(page_url)
            soup = BeautifulSoup(html, "html.parser")
        except Exception as error:
            print(f"Erro em {source['title']} ({page_url}): {error}")
            continue

        candidates = soup.select(
            "article, .item, .card, .event, [class*='event'], "
            "[class*='evento'], [class*='agenda'], li"
        )

        for candidate in candidates:
            link = candidate.select_one("a[href]")
            title_element = candidate.select_one(
                "h1, h2, h3, h4, h5, .title, .titulo, "
                "[class*='title'], [class*='titulo']"
            )
            title = clean_text(title_element) or (clean_text(link) if link else "")

            if not title or len(title) < 5:
                continue

            url = urljoin(page_url, link.get("href", "")) if link else page_url
            if url in seen:
                continue

            text = clean_text(candidate)
            if len(text) < 20:
                continue

            # Não transformar menus, rodapés e blocos institucionais em eventos.
            noise = (
                "universidade federal do paraná",
                "universidade tecnológica federal do paraná",
                "sistema de bibliotecas",
                "eventos e formaturas",
                "superintendência de comunicação"
            )
            if title.casefold() in noise:
                continue

            event_date, event_time = extract_date_time(text)
            if not event_date:
                event_date = extract_month_day(text)

            lower = text.casefold()
            free = any(word in lower for word in (
                "gratuito", "gratuita", "grátis", "gratis", "entrada franca",
                "aberto ao público", "aberta ao público", "acesso livre"
            ))

            # Só UTFPR/UFPR em Curitiba entram no recorte local.
            is_curitiba = (
                "curitiba" in lower
                or "sede centro" in lower
                or "sede neoville" in lower
                or "centro politécnico" in lower
                or "centro politecnico" in lower
                or "reitoria" in lower
            )
            if "utfpr.edu.br" in base_url and not is_curitiba:
                continue

            items.append({
                "title": title,
                "summary": text[:500],
                "category": source.get("category", "Cidade"),
                "categorySlug": source.get("categorySlug", "cidade"),
                "startDate": event_date,
                "startTime": event_time,
                "venue": "",
                "group": source["group"],
                "url": url,
                "imageUrl": "",
                "sourceUrl": source["url"],
                "publicSpace": False,
                "outdoor": False,
                "free": free,
                "organizer": source.get("organizer", "")
            })
            seen.add(url)

    return items

def is_sports_candidate(candidate):
    text = clean_text(candidate)
    lowered = text.casefold()
    keywords = (
        "couto pereira", "ligga arena", "estádio", "estadio", "jogo", "partida",
        "rodada", "campeonato", "copa", "ingresso", "matchday", "próximo jogo",
        "proximo jogo", "athletico", "coritiba"
    )
    return any(keyword in lowered for keyword in keywords)

def extract_items(source):
    try:
        html = fetch_html(source["url"])
        soup = BeautifulSoup(html, "html.parser")
        source_preview = page_preview_image(soup, source["url"])

        items = []
        candidates = soup.select("article, .post, .noticia, .evento, .item, .card, li")

        for candidate in candidates:
            if source.get("sports_only") and not is_sports_candidate(candidate):
                continue

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
            event_date, event_time = extract_date_time(clean_text(candidate))

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
                "category": source.get("category", source["title"]),
                "categorySlug": source.get("categorySlug", source.get("slug", "")),
                "startDate": event_date,
                "startTime": event_time,
                "venue": source.get("venue", ""),
                "group": source["group"],
                "url": url,
                "imageUrl": image_url,
                "sourceUrl": source["url"],
                "publicSpace": bool(source.get("public_space", False)),
                "outdoor": bool(source.get("outdoor", False)),
                "free": False,
                "organizer": source.get("organizer", "")
            })

        return items

    except Exception as error:
        print(f"Erro em {source['title']}: {error}")
        return []

def main():
    all_items = []

    for source in SOURCES:
        print(f"Coletando: {source['title']}")
        if source.get("group") == "prefeitura_eventos":
            all_items.extend(extract_prefeitura_events(source))
        elif source.get("group") == "universidade":
            all_items.extend(extract_university_events(source))
        else:
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
