# utils.py
import pandas as pd
from pathlib import Path

def write_csv_upsert(df: pd.DataFrame, filepath: str, index_cols: list):
    """
    Ghi DataFrame vào CSV, upsert theo index_cols.
    
    Nếu file CSV đã tồn tại:
      - Cập nhật các dòng trùng index_cols
      - Thêm mới các dòng chưa có
    Nếu file chưa tồn tại:
      - Tạo mới CSV

    Args:
        df (pd.DataFrame): DataFrame cần ghi
        filepath (str): đường dẫn file CSV
        index_cols (list): danh sách cột làm index để upsert
    """
    if df.empty:
        return

    file_path = Path(filepath)
    if file_path.exists():
        # Đọc file hiện tại
        existing = pd.read_csv(file_path, parse_dates=index_cols)
        # Ghép DataFrame mới với cũ, ưu tiên giá trị mới
        combined = pd.concat([existing, df])
        combined = combined.drop_duplicates(subset=index_cols, keep='last')
    else:
        combined = df.copy()

    # Ghi ra CSV
    combined.to_csv(file_path, index=False)
