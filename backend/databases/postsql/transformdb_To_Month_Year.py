import os
import pandas as pd
import calendar
from pathlib import Path

BASE_DIR = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_daily"
OUTPUT_DIR = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_monthly"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_file(filepath: str):
    df = pd.read_csv(filepath)

    # Parse date
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Lấy symbol từ tên file
    symbol = os.path.basename(filepath).replace(".csv", "")
    df["ticker"] = symbol.upper()

    # ---- Tính tổng và số ngày thực tế có dữ liệu ----
    monthly = df.groupby(["ticker","year","month"]).agg(
        open_sum=("open","sum"),
        high_sum=("high","sum"),
        low_sum=("low","sum"),
        close_sum=("close","sum"),
        volume_sum=("volume","sum"),
        days_count=("date","count")
    ).reset_index()

    # ---- Tính số ngày thực của tháng ----
    monthly["days_in_month"] = monthly.apply(lambda x: calendar.monthrange(int(x["year"]), int(x["month"]))[1], axis=1)

    # ---- Chia tổng cho số ngày thực để ra trung bình ----
    monthly["open"] = (monthly["open_sum"] / monthly["days_in_month"]).round(2)
    monthly["high"] = (monthly["high_sum"] / monthly["days_in_month"]).round(2)
    monthly["low"] = (monthly["low_sum"] / monthly["days_in_month"]).round(2)
    monthly["close"] = (monthly["close_sum"] / monthly["days_in_month"]).round(2)
    monthly["volume"] = (monthly["volume_sum"] / monthly["days_in_month"]).round(2)

    # ---- Tạo cột date = ngày đầu tháng ----
    monthly["date"] = pd.to_datetime(monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01")

    # ---- Chọn cột cuối cùng ----
    monthly = monthly[["ticker","date","open","high","low","close","volume"]]

    return monthly

# -------------------------
# DUYỆT TOÀN BỘ FOLDER
# -------------------------
for sector in os.listdir(BASE_DIR):
    sector_path = os.path.join(BASE_DIR, sector)
    if not os.path.isdir(sector_path):
        continue

    # Tạo folder output tương ứng
    output_sector_path = os.path.join(OUTPUT_DIR, sector)
    os.makedirs(output_sector_path, exist_ok=True)

    for file in os.listdir(sector_path):
        if file.endswith(".csv"):
            filepath = os.path.join(sector_path, file)
            print("Processing:", filepath)
            monthly_df = process_file(filepath)

            # Xuất file vào đúng folder ngành
            symbol = monthly_df["ticker"].iloc[0]
            output_file = os.path.join(output_sector_path, f"{symbol}.csv")
            monthly_df.to_csv(output_file, index=False)

print("DONE — đã tạo tất cả file monthly, volume theo số ngày thực, làm tròn 2 chữ số!")
