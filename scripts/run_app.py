import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import uvicorn


if __name__ == "__main__":
    uvicorn.run("tcc_sales.api:app", host="127.0.0.1", port=8000, reload=False, app_dir=str(ROOT / "src"))

