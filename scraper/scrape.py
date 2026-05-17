import json
from datetime import datetime, timezone
from pathlib import Path

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

def main():
    write_json(
        [],
        "Teste OK: GitHub Actions funcionando. O scraping real será configurado depois."
    )
    print("agenda.json gerado com sucesso.")

if __name__ == "__main__":
    main()
