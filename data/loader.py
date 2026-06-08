"""
data/loader.py
Loads and merges all 5 sheets from the MOEI HR dataset (xlsx).
Returns a dict of DataFrames keyed by sheet name.
"""

import openpyxl
import pandas as pd
from datetime import date, datetime
from pathlib import Path

AS_OF_DATE = date(2026, 6, 1)
DATA_DIR = Path(__file__).parent.parent / "resources" / "MOEI_HR_Employee_Dataset.xlsx"


def _parse_date(val):
    """Return date or None from various Excel date formats."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(str(val), "%d-%m-%Y").date()
        except Exception:
            return None


def load_employees(xlsx_path=DATA_DIR):
    df = pd.read_excel(xlsx_path, sheet_name="Employees")
    df["date_of_birth"] = df["date_of_birth"].apply(_parse_date)
    df["hire_date"] = df["hire_date"].apply(_parse_date)
    df["last_promotion_date"] = df["last_promotion_date"].apply(_parse_date)
    return df


def load_performance(xlsx_path=DATA_DIR):
    df = pd.read_excel(xlsx_path, sheet_name="Performance")
    df["record_id"] = df["record_id"].astype(str)
    return df


def load_training(xlsx_path=DATA_DIR):
    df = pd.read_excel(xlsx_path, sheet_name="Training")
    df["completion_date"] = df["completion_date"].apply(_parse_date)
    return df


def load_leave(xlsx_path=DATA_DIR):
    df = pd.read_excel(xlsx_path, sheet_name="Leave")
    return df


def load_movement(xlsx_path=DATA_DIR):
    df = pd.read_excel(xlsx_path, sheet_name="Movement")
    df["effective_date"] = df["effective_date"].apply(_parse_date)
    return df


def load_all(xlsx_path=DATA_DIR):
    return {
        "employees": load_employees(xlsx_path),
        "performance": load_performance(xlsx_path),
        "training": load_training(xlsx_path),
        "leave": load_leave(xlsx_path),
        "movement": load_movement(xlsx_path),
    }