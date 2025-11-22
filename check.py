#docker-compose run --rm backend-app /bin/bash
# docker-compose run --rm spark-volume-alert /bin/bash

import os
import pandas as pd

BASE_DIR = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_daily"
OUTPUT_DIR = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_monthly"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_file(filepath: str):
    df = pd.read_csv(filepath)

    # Chuyển date thành datetime
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Tính trung bình close theo tháng/năm
    monthly = (
        df.groupby(["year", "month"])["close"]
        .mean()
        .reset_index()
    )

    # Lấy tên mã từ tên file
    symbol = os.path.basename(filepath).replace(".csv", "")
    monthly["symbol"] = symbol

    return monthly


for sector in os.listdir(BASE_DIR):
    sector_path = os.path.join(BASE_DIR, sector)

    if not os.path.isdir(sector_path):
        continue

    for file in os.listdir(sector_path):
        if file.endswith(".csv"):
            filepath = os.path.join(sector_path, file)
            print("Processing:", filepath)

            monthly_df = process_file(filepath)

            # Xuất CSV mới
            output_file = os.path.join(OUTPUT_DIR, f"{monthly_df['symbol'].iloc[0]}_monthly.csv")
            monthly_df.to_csv(output_file, index=False)

print("DONE — đã tạo tất cả file monthly CSV!")
