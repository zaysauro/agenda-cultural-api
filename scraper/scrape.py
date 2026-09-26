# Force refresh: run the agenda scraper on the current sources.
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
    # Guia Curitiba — fonte geral. A categoria é extraída do próprio card do evento.
    {"title": "Prefeitura — Guia de Eventos", "slug": "prefeitura-guia", "group": "prefeitura_guia", "images_enabled": False, "url": "https://guia.curitiba.pr.gov.br/Evento/Listar/"},

    # DiskIngressos — catálogo de eventos e sessões vendidos pela plataforma.\n    # O scraper percorre a vitrine, paginações e páginas individuais para capturar\n    # os eventos publicados, incluindo título, data, horário, local, cidade, categoria e URL de ingresso.\n    {"title": "DiskIngressos — Eventos", "slug": "diskingressos", "group": "diskingressos", "images_enabled": False, "url": "https://www.diskingressos.com.br/"},\n\n    # Cinemas — filmes em cartaz e programação local.
    {"title": "Cine Passeio — Programação", "slug": "cine-passeio", "group": "cinema", "category": "Cinema", "categorySlug": "cinema", "venue": "Cine Passeio", "cinema": True, "images_enabled": False, "url": "https://www.cinepasseio.org/programacao"},
    {"title": "Shopping Estação — Cinema", "slug": "shopping-estacao-cinema", "group": "cinema", "category": "Cinema", "categorySlug": "cinema", "venue": "Shopping Estação", "cinema": True, "images_enabled": False, "url": "https://shoppingestacao.com.br/cinema/"},
    {"title": "UCI Estação", "slug": "uci-estacao", "group": "cinema", "category": "Cinema", "categorySlug": "cinema", "venue": "UCI Estação", "cinema": True, "images_enabled": False, "url": "https://www.ucicinemas.com.br/Filmes/FiltroCinema/0%2C15%2C1"},
    {"title": "Cine Lido Curitiba", "slug": "cine-lido-curitiba", "group": "cinema", "category": "Cinema", "categorySlug": "cinema", "venue": "Cine Lido", "cinema": True, "images_enabled": False, "url": "https://www.cinelidocuritiba.com.br"},

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
    match = re.search(r"\b(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)?\s*\(?([0-3]?\d)[/-]([01]?\d)\)?\b", text, re.I)
    if not match:
        return ""
    day, month = map(int, match.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return ""
    return f"{datetime.now().year:04d}-{month:02d}-{day:02d}"



def portuguese_month_number(value):
    months = {
        "jan": 1, "janeiro": 1, "fev": 2, "fevereiro": 2,
        "mar": 3, "março": 3, "marco": 3, "abr": 4, "abril": 4,
        "mai": 5, "maio": 5, "jun": 6, "junho": 6,
        "jul": 7, "julho": 7, "ago": 8, "agosto": 8,
        "set": 9, "setembro": 9, "out": 10, "outubro": 10,
        "nov": 11, "novembro": 11, "dez": 12, "dezembro": 12
    }
    return months.get(norm_text(value))


def norm_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def extract_portuguese_dates(text):
    """Extrai todas as datas DD/Mon e horários de uma programação."""
    if not text:
        return []

    current_year = datetime.now().year
    results = []
    pattern = re.compile(
        r"\b([0-3]?\d)[/.-]([A-Za-zÀ-ÿ]+)\b[^0-9]{0,45}"
        r"\b([01]?\d|2[0-3])h(?:([0-5]\d))?\b",
        re.I
    )

    for match in pattern.finditer(text):
        day = int(match.group(1))
        month = portuguese_month_number(match.group(2)[:3])
        if not month or not (1 <= day <= 31):
            continue
        hour = int(match.group(3))
        minute = int(match.group(4) or 0)
        results.append((
            f"{current_year:04d}-{month:02d}-{day:02d}",
            f"{hour:02d}:{minute:02d}"
        ))

    # Formato numérico usado pelo Cine Passeio: 26/09 (SÁB) - 13h30
    numeric = re.compile(
        r"\b([0-3]?\d)/([01]?\d)\b[^0-9]{0,45}"
        r"\b([01]?\d|2[0-3])h(?:([0-5]\d))?\b",
        re.I
    )
    for match in numeric.finditer(text):
        day, month = int(match.group(1)), int(match.group(2))
        if not (1 <= day <= 31 and 1 <= month <= 12):
            continue
        results.append((
            f"{current_year:04d}-{month:02d}-{day:02d}",
            f"{int(match.group(3)):02d}:{int(match.group(4) or 0):02d}"
        ))

    return list(dict.fromkeys(results))


def guide_category(text):
    lowered = norm_text(text)
    categories = (
        ("cinema", ("cinema", "filme", "filmes", "cine")),
        ("teatro", ("teatro", "espetaculo", "espetaculos", "peca teatral", "circo")),
        ("musica", ("musica", "show", "concerto", "festival", "banda")),
        ("esporte", ("esporte", "esportes", "futebol", "corrida", "copa", "campeonato", "bmx")),
        ("exposicao", ("exposicao", "exposicoes", "mostra", "galeria")),
        ("danca", ("danca", "ballet", "balé")),
    )
    for slug, words in categories:
        if any(word in lowered for word in words):
            return slug
    return "cidade"


def guide_category_label(slug):
    return {
        "cinema": "Cinema",
        "musica": "Música",
        "teatro": "Teatro",
        "esporte": "Esporte",
        "exposicao": "Exposição",
        "danca": "Dança",
        "cidade": "Cidade",
    }.get(slug, "Cidade")


def extract_guia_events(source):
    """Extrai eventos do Guia Curitiba e preserva a categoria exibida em cada card."""
    items = []
    seen = set()

    urls = [source["url"]]
    for page in range(2, 7):
        urls.append(f"{source['url']}?pagina={page}")

    for page_url in urls:
        try:
            soup = BeautifulSoup(fetch_html(page_url), "html.parser")
        except Exception as error:
            print(f"Erro no Guia Curitiba ({page_url}): {error}")
            continue

        candidates = soup.select(
            "article, .evento, .event, .card, .item, "
            "[class*='evento'], [class*='event'], [class*='card'], li"
        )

        for candidate in candidates:
            text = clean_text(candidate)
            if len(text) < 25:
                continue

            link = candidate.select_one("a[href]")
            title_element = candidate.select_one("h1, h2, h3, h4, h5, .titulo, .title")
            title = clean_text(title_element) or (clean_text(link) if link else "")
            if not title or len(title) < 4:
                continue

            lowered = norm_text(title)
            if lowered in {"ver mais", "aplicar filtros", "limpar filtro", "filtre por categoria"}:
                continue

            url = urljoin(page_url, link.get("href", "")) if link else page_url
            key = (norm_text(title), url)
            if key in seen:
                continue

            dates = extract_portuguese_dates(text)
            if not dates:
                date, time = extract_date_time(text)
                dates = [(date, time)] if date else []

            category_slug = guide_category(text)
            public = any(word in norm_text(text) for word in (
                "parque", "praça", "praca", "bosque", "rua da cidadania", "regional"
            ))

            free = any(word in norm_text(text) for word in (
                "gratuito", "gratuita", "gratis", "entrada franca", "acesso livre"
            ))

            # Cada sessão/data vira um item próprio. Isso permite o filtro
            # de calendário e evita esconder um evento que ocorre em vários dias.
            if dates:
                for event_date, event_time in dates:
                    items.append({
                        "title": title,
                        "summary": text[:500],
                        "category": guide_category_label(category_slug),
                        "categorySlug": category_slug,
                        "startDate": event_date,
                        "startTime": event_time,
                        "venue": "",
                        "group": source["group"],
                        "url": url,
                        "imageUrl": "",
                        "sourceUrl": source["url"],
                        "publicSpace": public,
                        "outdoor": public,
                        "free": free,
                        "organizer": "Prefeitura de Curitiba"
                    })
            else:
                items.append({
                    "title": title,
                    "summary": text[:500],
                    "category": guide_category_label(category_slug),
                    "categorySlug": category_slug,
                    "startDate": "",
                    "startTime": "",
                    "venue": "",
                    "group": source["group"],
                    "url": url,
                    "imageUrl": "",
                    "sourceUrl": source["url"],
                    "publicSpace": public,
                    "outdoor": public,
                    "free": free,
                    "organizer": "Prefeitura de Curitiba"
                })

            seen.add(key)

    return items


def extract_cinema_events(source):
    """Extrai filmes de cinemas com estruturas HTML diferentes."""
    try:
        soup = BeautifulSoup(fetch_html(source["url"]), "html.parser")
    except Exception as error:
        print(f"Erro em {source['title']}: {error}")
        return []

    items = []
    seen = set()

    # Primeiro tentamos blocos semânticos. Depois usamos headings/links como
    # fallback, pois cada cinema possui um HTML completamente diferente.
    candidates = soup.select(
        "article, .filme, .filme-card, .movie, .movie-card, "
        "[class*='filme'], [class*='movie'], [class*='cinema'], li"
    )

    for candidate in candidates:
        text = clean_text(candidate)
        if len(text) < 12:
            continue

        title_element = candidate.select_one("h1, h2, h3, h4, h5")
        link = candidate.select_one("a[href]")
        title = clean_text(title_element) or (clean_text(link) if link else "")
        if not title or len(title) < 3:
            continue

        if norm_text(title) in {
            "filmes em cartaz", "programacao", "cinema", "mais detalhes",
            "comprar ingressos", "ver mais"
        }:
            continue

        # O card precisa parecer realmente um filme, não um bloco de navegação.
        movie_signal = any(token in norm_text(text) for token in (
            "min", "filme", "filmes", "movie", "cinema", "access time", "comprar ingresso"
        ))
        if not movie_signal and source["slug"] != "uci-estacao":
            continue

        url = urljoin(source["url"], link.get("href", "")) if link else source["url"]
        key = (norm_text(title), source["slug"])
        if key in seen:
            continue

        dates = extract_portuguese_dates(text)
        if not dates:
            date, time = extract_date_time(text)
            dates = [(date, time)] if date else []

        # Para "filmes em cartaz" sem sessão na página, mantemos a data vazia:
        # eles continuam aparecendo em Todos/Cinema sem inventar uma data.
        if not dates:
            dates = [("", "")]

        for event_date, event_time in dates:
            items.append({
                "title": title,
                "summary": text[:700],
                "category": "Cinema",
                "categorySlug": "cinema",
                "startDate": event_date,
                "startTime": event_time,
                "venue": source.get("venue", "Cinema"),
                "group": source["group"],
                "url": url,
                "imageUrl": "",
                "sourceUrl": source["url"],
                "publicSpace": False,
                "outdoor": False,
                "free": False,
                "organizer": source.get("venue", "")
            })

        seen.add(key)

    # Fallback específico para páginas como o UCI, onde o título é um H1 e
    # os cards não possuem uma classe de filme confiável.
    if not items:
        for heading in soup.select("h1, h2, h3, h4"):
            title = clean_text(heading)
            if len(title) < 3 or norm_text(title) in {"programacao", "resultado de pesquisa"}:
                continue
            if any(x in norm_text(title) for x in ("cinema:", "veja mais", "comprar ingressos")):
                continue
            text = clean_text(heading.parent or heading)
            if len(text) < len(title) + 5:
                continue
            key = norm_text(title)
            if key in seen:
                continue
            items.append({
                "title": title,
                "summary": text[:700],
                "category": "Cinema",
                "categorySlug": "cinema",
                "startDate": "",
                "startTime": "",
                "venue": source.get("venue", "Cinema"),
                "group": source["group"],
                "url": source["url"],
                "imageUrl": "",
                "sourceUrl": source["url"],
                "publicSpace": False,
                "outdoor": False,
                "free": False,
                "organizer": source.get("venue", "")
            })
            seen.add(key)

    return items


def disk_category(text):
    lowered = norm_text(text)
    categories = (
        ("cinema", ("cinema", "filme", "filmes", "cine")),
        ("teatro", ("teatro", "teatral", "espetaculo", "espetáculos", "peca", "peça", "musical", "circo")),
        ("musica", ("musica", "música", "show", "concerto", "festival", "banda", "sertanejo", "rock", "pagode", "samba")),
        ("danca", ("danca", "dança", "ballet", "balé")),
        ("esporte", ("esporte", "esportes", "futebol", "jogo", "partida", "campeonato", "copa", "corrida")),
        ("exposicao", ("exposicao", "exposição", "mostra", "galeria")),
    )
    for slug, words in categories:
        if any(word in lowered for word in words):
            return slug
    return "cidade"


def extract_diskingressos_events(source):
    """
    Percorre a vitrine do DiskIngressos e as páginas individuais /evento/ e /grupo/.
    A página inicial expõe eventos em blocos e cada evento possui uma página de detalhe
    com data, horário, local e descrição. O crawler segue links internos do domínio
    e também descobre novas páginas através da paginação.
    """
    base_url = source["url"]
    domain = "www.diskingressos.com.br"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; CuritibaEmFoco/1.0; +https://zaysauro.github.io/agenda-cultural-api/)",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    })

    def get_soup(url):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as error:
            print(f"Erro no DiskIngressos ({url}): {error}")
            return None

    def internal_url(href, current_url):
        if not href:
            return ""
        absolute = urljoin(current_url, href).split("#")[0]
        if absolute.startswith("https://diskingressos.com.br/"):
            absolute = absolute.replace("https://diskingressos.com.br/", "https://www.diskingressos.com.br/")
        if absolute.startswith("http://diskingressos.com.br/"):
            absolute = absolute.replace("http://diskingressos.com.br/", "https://www.diskingressos.com.br/")
        if not absolute.startswith(f"https://{domain}/"):
            return ""
        return absolute

    def is_event_url(url):
        return bool(re.search(r"/(?:evento|event|grupo)/", url, re.I))

    def parse_detail(url, soup):
        text = clean_text(soup)
        if len(text) < 20:
            return None

        title_element = soup.select_one("h1, .event-title, [class*='event-title']")
        title = clean_text(title_element) if title_element else ""

        if not title:
            # Nas páginas do DiskIngressos o título aparece antes da data.
            headings = [clean_text(node) for node in soup.select("h1, h2, h3") if clean_text(node)]
            for heading in headings:
                candidate = heading.strip()
                if len(candidate) >= 4 and norm_text(candidate) not in {
                    "informacoes do evento", "informações do evento",
                    "confira os valores e setores", "clique e faça a sua escolha",
                }:
                    title = candidate
                    break

        if not title:
            return None

        # Remove textos de compra/navegação para deixar a classificação mais precisa.
        date, time = extract_date_time(text)
        portuguese_dates = extract_portuguese_dates(text)
        if portuguese_dates:
            date, time = portuguese_dates[0]

        if not date:
            # Formatos como 05.dez.2026 (sábado).
            match = re.search(
                r"\b([0-3]?\d)\.([A-Za-zÀ-ÿ]{3,})\.(20\d{2})\b",
                text,
                re.I,
            )
            if match:
                day = int(match.group(1))
                month = portuguese_month_number(match.group(2)[:3])
                year = int(match.group(3))
                if month:
                    date = f"{year:04d}-{month:02d}-{day:02d}"

        # Horários do DiskIngressos aparecem como "Abertura: 19h 00min" e "Evento: 20h 00min".
        if not time:
            match = re.search(
                r"(?:Evento|Início|Inicio)\s*:\s*([01]?\d|2[0-3])h\s*(\d{2})min",
                text,
                re.I,
            )
            if match:
                time = f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

        venue = ""
        address = ""
        city = ""
        state = ""

        # O bloco de serviço normalmente vem imediatamente após a data.
        service = soup.select_one(
            ".event-info, .event-detail, .evento-info, [class*='event-info'], "
            "[class*='event-detail'], [class*='local']"
        )
        service_text = clean_text(service) if service else text

        location_patterns = [
            r"(?:Local|Local do evento)\s*:\s*([^\n]+)",
            r"(?:Evento)\s*:\s*([^\n]+)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, service_text, re.I)
            if match:
                value = match.group(1).strip()
                if len(value) < 180 and not re.search(r"\d{1,2}h", value):
                    venue = value
                    break

        # Estrutura observada nas páginas públicas: "Teatro Positivo/Curitiba"
        # seguido de endereço. Também funciona para "Ópera de Arame/Curitiba".
        if not venue:
            match = re.search(
                r"([^\n]{2,100})/([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .'-]{2,40})\s+"
                r"(?:Rua|Av\.|Avenida|Praça|Rodovia|Alameda|R\.)",
                text,
                re.I,
            )
            if match:
                venue = match.group(1).strip()
                city = match.group(2).strip()

        # Endereço brasileiro + cidade/UF.
        address_match = re.search(
            r"((?:Rua|R\.|Avenida|Av\.|Praça|Pça\.|Alameda|Rodovia|Estrada)\s+"
            r"[^\n]{3,180}?\s+\d{1,6}[^\n]{0,100}?\b"
            r"(?:Curitiba|Colombo|Pinhais|São José dos Pinhais|Campo Largo|"
            r"Campo Magro|Maringá|Londrina|Cascavel|Ponta Grossa|"
            r"São Paulo|Porto Alegre|Pelotas|Sorocaba|Cajamar)\s*/?\s*"
            r"([A-Z]{2})\b",
            text,
            re.I,
        )
        if address_match:
            address = re.sub(r"\s+", " ", address_match.group(1)).strip()
            state = address_match.group(2).upper()

        if not city:
            city_match = re.search(
                r"/([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .'-]{2,40})\s+(?:PR|SC|SP|RS|MG|RJ|BA|PE|CE|GO|DF)\b",
                text,
                re.I,
            )
            if city_match:
                city = city_match.group(1).strip()

        if not state:
            state_match = re.search(
                r"\b([A-Z]{2})\b(?=\s*(?:\n|$))",
                text,
            )
            if state_match:
                state = state_match.group(1)

        category_slug = disk_category(f"{title} {text}")
        free = any(word in norm_text(text) for word in (
            "gratuito", "gratuita", "gratis", "entrada franca", "acesso livre"
        ))

        # A imagem oficial pode estar em og:image ou JSON-LD na página de detalhe.
        image_url = page_preview_image(soup, url)

        return {
            "title": title,
            "summary": text[:900],
            "description": text[:900],
            "category": guide_category_label(category_slug),
            "categorySlug": category_slug,
            "startDate": date,
            "startTime": time,
            "venue": venue,
            "address": address,
            "city": city,
            "state": state,
            "group": source["group"],
            "url": url,
            "imageUrl": image_url,
            "sourceUrl": source["url"],
            "publicSpace": False,
            "outdoor": False,
            "free": free,
            "organizer": "DiskIngressos",
        }

    # A home atual lista dezenas de eventos. Além dela, seguimos paginações
    # e links internos de evento/grupo encontrados em cada página.
    queue = [base_url]
    visited_pages = set()
    event_urls = set()

    # Limite alto o suficiente para o catálogo, mas impede loops infinitos.
    max_listing_pages = 60
    max_event_pages = 1200

    while queue and len(visited_pages) < max_listing_pages:
        page_url = queue.pop(0)
        if page_url in visited_pages or is_event_url(page_url):
            continue
        visited_pages.add(page_url)

        soup = get_soup(page_url)
        if not soup:
            continue

        for link in soup.select("a[href]"):
            url = internal_url(link.get("href"), page_url)
            if not url:
                continue
            if is_event_url(url):
                event_urls.add(url)
            elif len(queue) < max_listing_pages and (
                "pagina" in norm_text(url)
                or "page" in norm_text(url)
                or "/event" in norm_text(url)
                or "/busca" in norm_text(url)
                or "/pesquisa" in norm_text(url)
            ):
                if url not in visited_pages:
                    queue.append(url)

        # Alguns layouts usam paginação numérica sem links semânticos.
        for anchor in soup.select("a[href]"):
            label = norm_text(clean_text(anchor))
            if label.isdigit() and 1 <= int(label) <= 60:
                url = internal_url(anchor.get("href"), page_url)
                if url and url not in visited_pages:
                    queue.append(url)

    # Se a home já entregou muitos eventos, ainda percorremos as páginas
    # de catálogo descobertas. Ordenação garante resultado determinístico.
    for url in sorted(event_urls)[:max_event_pages]:
        soup = get_soup(url)
        if not soup:
            continue
        item = parse_detail(url, soup)
        if item:
            yield item


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

def scrape_ingresso_cinema():
    """Coleta filmes em cartaz, cinemas e sessões de hoje do Ingresso.com."""
    base_url = "https://api-content.ingresso.com/v0"
    partnership = "ingresso.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    def api_get(path, params=None):
        response = requests.get(
            f"{base_url}{path}",
            params=params or {},
            timeout=20,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    # Resolve Curitiba pelo próprio catálogo do Ingresso.com para não depender
    # de um ID que possa mudar.
    city_id = "178"
    try:
        state = api_get("/states/PR")
        for city in state.get("cities", []) if isinstance(state, dict) else []:
            if norm_text(city.get("name")) == "curitiba":
                city_id = str(city.get("id") or city_id)
                break
    except Exception as error:
        print(f"Aviso: não foi possível resolver Curitiba no Ingresso.com: {error}")

    today = datetime.now().strftime("%Y-%m-%d")
    filmes = []
    cinemas = []
    sessoes = []

    # O endpoint antigo /movies/now-playing/{city} não está mais disponível.
    # A API atual documenta templates/nowplaying e events.
    try:
        payload = api_get(f"/templates/nowplaying/{city_id}/partnership/{partnership}")
        if isinstance(payload, dict):
            payload = payload.get("items") or payload.get("events") or []
        for f in payload if isinstance(payload, list) else []:
            images = f.get("images") or []
            poster = (images[0] or {}).get("url") if images else ""
            filmes.append({
                "id_ingresso": f.get("id"),
                "titulo": f.get("title") or "",
                "titulo_original": f.get("originalTitle") or "",
                "sinopse": f.get("synopsis") or "",
                "duracao": f.get("duration") or "",
                "classificacao": f.get("contentRating") or "",
                "generos": [g if isinstance(g, str) else g.get("name", "") for g in (f.get("genres") or [])],
                "poster": poster,
                "url": f.get("siteURL") or "",
            })
    except Exception as error:
        print(f"Erro nos filmes do Ingresso.com: {error}")

    try:
        payload = api_get(f"/theaters/city/{city_id}/partnership/{partnership}")
        if isinstance(payload, dict):
            payload = payload.get("items") or payload.get("theaters") or []
        for theater in payload if isinstance(payload, list) else []:
            cinemas.append({
                "nome": theater.get("name") or "",
                "id": theater.get("id"),
                "endereco": theater.get("address") or "",
                "bairro": theater.get("neighborhood") or "",
                "cidade": theater.get("cityName") or "Curitiba",
                "url": theater.get("siteURL") or "",
            })
    except Exception as error:
        print(f"Erro nos cinemas do Ingresso.com: {error}")

    # A API atual entrega as sessões por cinema sem precisar de /date/{YYYY-MM-DD}.
    for cinema in cinemas:
        cinema_id = cinema.get("id")
        if not cinema_id:
            continue
        try:
            payload = api_get(
                f"/sessions/city/{city_id}/theater/{cinema_id}/partnership/{partnership}",
                {"date": today},
            )
            if not isinstance(payload, list):
                payload = payload.get("items") or payload.get("movies") or []

            for day in payload if isinstance(payload, list) else []:
                movies = day.get("movies") or []
                # Algumas respostas podem vir diretamente como um filme.
                if not movies and day.get("title"):
                    movies = [day]

                for filme in movies:
                    titulo = filme.get("title") or ""
                    poster = next((f.get("poster") for f in filmes if f.get("titulo") == titulo), None)
                    if not poster:
                        images = filme.get("images") or []
                        poster = (images[0] or {}).get("url") if images else ""

                    for room in filme.get("rooms") or []:
                        room_name = room.get("name") or room.get("fullName") or ""
                        room_type = room.get("type") or []
                        if isinstance(room_type, list):
                            room_type = ", ".join(str(x) for x in room_type if x)
                        for sessao in room.get("sessions") or []:
                            date_info = sessao.get("date") or sessao.get("realDate") or {}
                            local_date = date_info.get("localDate") if isinstance(date_info, dict) else ""
                            is_today = bool(date_info.get("isToday")) if isinstance(date_info, dict) else False
                            if local_date:
                                session_date = str(local_date)[:10]
                            else:
                                session_date = today if is_today else ""

                            if session_date != today and not is_today:
                                continue

                            session_time = sessao.get("time") or (
                                date_info.get("hour", "") if isinstance(date_info, dict) else ""
                            )
                            types = sessao.get("types") or sessao.get("type") or []
                            if isinstance(types, list):
                                type_names = []
                                for item in types:
                                    if isinstance(item, dict):
                                        name = item.get("name") or item.get("alias")
                                    else:
                                        name = str(item)
                                    if name:
                                        type_names.append(name)
                                session_type = ", ".join(dict.fromkeys(type_names))
                            else:
                                session_type = str(types or "")

                            buy_link = sessao.get("siteURL") or filme.get("siteURLByTheater") or filme.get("siteURL") or ""
                            sessoes.append({
                                "filme": titulo,
                                "filme_id": filme.get("id"),
                                "poster": poster,
                                "cinema_id": cinema_id,
                                "cinema": cinema.get("nome") or "",
                                "endereco": cinema.get("endereco") or "",
                                "bairro": cinema.get("bairro") or "",
                                "horario": session_time,
                                "data": session_date,
                                "sala": room_name,
                                "tipo": session_type or room_type,
                                "idioma": "",
                                "url_compra": buy_link,
                            })
        except Exception as error:
            print(f"Erro nas sessões de {cinema.get('nome')}: {error}")

    # Mantém somente filmes que realmente possuem sessão hoje quando possível.
    session_titles = {s["filme"] for s in sessoes if s.get("filme")}
    if session_titles:
        filmes = [f for f in filmes if f.get("titulo") in session_titles]

    return {
        "source": "ingresso.com",
        "cidade": "Curitiba",
        "cidade_id": city_id,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "data_sessoes": today,
        "filmes_em_cartaz": filmes,
        "cinemas": cinemas,
        "sessoes_hoje": sessoes,
    }

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
        elif source.get("group") == "prefeitura_guia":
            all_items.extend(extract_guia_events(source))
        elif source.get("group") == "universidade":
            all_items.extend(extract_university_events(source))
        elif source.get("group") == "diskingressos":
            all_items.extend(extract_diskingressos_events(source))
        elif source.get("group") == "cinema":
            continue
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
