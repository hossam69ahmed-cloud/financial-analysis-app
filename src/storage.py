"""Saves / loads companies as JSON files in data/companies so work survives restarts."""
import json
from pathlib import Path

import pandas as pd

from .models import CompanyData
from .utils import slug

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "companies"


def save_company(c: CompanyData, folder: Path = DATA_DIR) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": c.name, "ticker": c.ticker, "currency": c.currency, "unit": c.unit, "sector": c.sector,
        "income": c.income.rename(columns=str).to_dict(),
        "balance": c.balance.rename(columns=str).to_dict(),
    }
    (folder / f"{slug(c.name)}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def load_all(folder: Path = DATA_DIR) -> dict[str, CompanyData]:
    out: dict[str, CompanyData] = {}
    for f in sorted(folder.glob("*.json")) if folder.exists() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            c = CompanyData(
                name=d["name"], income=pd.DataFrame(d["income"]), balance=pd.DataFrame(d["balance"]),
                ticker=d.get("ticker", ""), currency=d.get("currency", "EGP"),
                unit=d.get("unit", "Millions"), sector=d.get("sector", ""),
            )
            out[c.name] = c
        except Exception:
            continue  # skip corrupted files
    return out


def delete_company(name: str, folder: Path = DATA_DIR) -> None:
    (folder / f"{slug(name)}.json").unlink(missing_ok=True)
