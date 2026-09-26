import json
from pathlib import Path

from scrape import scrape_ingresso_cinema


def main():
    output = Path("docs/cinema.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    data = scrape_ingresso_cinema()
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"cinema.json gerado com "
        f"{len(data.get('filmes_em_cartaz', []))} filmes e "
        f"{len(data.get('sessoes_hoje', []))} sessões."
    )


if __name__ == "__main__":
    main()
