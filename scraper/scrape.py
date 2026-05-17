import json
from datetime import datetime, timezone
from pathlib import Path

def main():
    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": 1,
        "error": None,
        "events": [
            {
                "title": "Evento de teste",
                "dateText": "Hoje",
                "location": "Curitiba",
                "url": "https://www.fundacaoculturaldecuritiba.com.br/agenda/",
                "source": "teste"
            }
        ]
    }

    output_path = Path("docs/agenda.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("agenda.json gerado com sucesso.")

if __name__ == "__main__":
    main()
