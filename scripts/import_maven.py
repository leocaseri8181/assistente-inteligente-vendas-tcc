import argparse
import json
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcc_sales.dataset import DataValidationError
from tcc_sales.importer import connect, import_folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida e importa os CSVs Maven para SQLite.")
    parser.add_argument("--source", type=Path, default=ROOT / "data/raw/maven")
    parser.add_argument("--database", type=Path, default=ROOT / "data/tcc.sqlite3")
    parser.add_argument("--tenant", default="demo")
    args = parser.parse_args()
    try:
        with closing(connect(args.database)) as connection:
            result = import_folder(connection, args.source, args.tenant)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except DataValidationError as error:
        print(json.dumps({"status": "invalid", "errors": error.errors}, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
