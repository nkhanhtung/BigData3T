import os
from pathlib import Path
from datetime import date, datetime
import pandas as pd
from loguru import logger

from utils import write_csv_upsert
from crawler import (
    fetch_historical,
    TICKERS,
    DATA_DIR,
    get_sector_for,
    publish_row,
    START_DATE
)

logger.remove()
logger.add(lambda msg: print(msg, end=''), level="INFO")


def backfill_all():
    today = date.today().isoformat()
    for tk in TICKERS:
        sector = get_sector_for(tk)
        if not sector:
            continue

        target_path = DATA_DIR / sector / f"{tk}.csv"
        logger.info(f"[Backfill Daily] {sector}/{tk} {START_DATE} -> {today}")
        df = fetch_historical(tk, START_DATE, today)
        write_csv_upsert(df, str(target_path), index_cols=["ticker", "date"])
        for _, r in df.iterrows():
            publish_row(r, data_type="daily")


def incremental_update_daily():
    logger.info("[Incremental Daily] Checking updates...")
    for tk in TICKERS:
        sector = get_sector_for(tk)
        if not sector:
            continue

        f = DATA_DIR / sector / f"{tk}.csv"

        if f.exists() and f.stat().st_size > 0:
            base = pd.read_csv(f, parse_dates=["date"])
            last_date = base["date"].max().date() if not base.empty else datetime.fromisoformat(START_DATE).date()
        else:
            last_date = datetime.fromisoformat(START_DATE).date()

        start_next = (last_date + pd.Timedelta(days=1)).date()
        today = date.today()

        if start_next <= today:
            df = fetch_historical(tk, start_next.isoformat(), today.isoformat())
            if not df.empty:
                write_csv_upsert(df, str(f), index_cols=["ticker", "date"])
                for _, r in df.iterrows():
                    publish_row(r, data_type="daily")
                logger.info(f"{sector}/{tk}: +{len(df)} daily rows")
            else:
                logger.info(f"{sector}/{tk}: No new daily data found from {start_next} to {today}")
        else:
            logger.info(f"{sector}/{tk}: Daily data up-to-date")


if __name__ == "__main__":
    # Nếu chưa có CSV, backfill toàn bộ
    missing_daily = [
        tk for tk in TICKERS if not (DATA_DIR / get_sector_for(tk) / f"{tk}.csv").exists()
    ]
    if missing_daily:
        logger.info(f"Các mã chưa có dữ liệu daily: {missing_daily}. Bắt đầu full backfill daily.")
        backfill_all()
    else:
        logger.info("Đã có CSV daily -> chạy incremental cập nhật mới nhất.")
        incremental_update_daily()
