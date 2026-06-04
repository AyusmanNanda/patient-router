from pathlib import Path
import pandas as pd

from ml.generate_data import generate_dataset

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "data.csv"

def get_data_stats():
    df = pd.read_csv(DATA_FILE)
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "departments": df["department"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }
def generate_data(rows):
    df = generate_dataset()
    df.to_csv(DATA_FILE, index=False)
    return {
        "status": "success",
        "rows_generated": len(df)
    }