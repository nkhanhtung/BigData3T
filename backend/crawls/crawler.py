import os, sys, json
from pathlib import Path
from datetime import date, datetime, timedelta
import time
import random

import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger # Import thêm IntervalTrigger
from pytz import timezone as tz_of

from utils import write_csv_upsert

# --- vnstock v3 ---
try:
    from vnstock import Quote
except Exception as e:
    Quote = None
    logger.error(f"Không import được vnstock. Hãy cài: pip install vnstock | Lỗi: {e}")

# --- Kafka (tùy chọn) ---
try:
    from kafka import KafkaProducer
except Exception:
    KafkaProducer = None

# --- Mongo (tùy chọn) ---
try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None


# =========================
#        CONFIG
# =========================
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

START_DATE = os.getenv("START_DATE", "2025-10-10")
TZ_NAME = os.getenv("TZ", "Asia/Bangkok")
RUN_DAILY_AT = os.getenv("RUN_DAILY_AT", "16:00")
RUN_INTRADAY_EVERY_MINUTES = int(os.getenv("RUN_INTRADAY_EVERY_MINUTES", "1")) # Tần suất cào theo phút

DATA_DIR = Path(os.getenv("DATA_DIR", "./datasets/datapush_new"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTRADAY_DATA_DIR = Path(os.getenv("INTRADAY_DATA_DIR", "./data_intraday")) # Thư mục riêng cho dữ liệu theo phút
INTRADAY_DATA_DIR.mkdir(parents=True, exist_ok=True)


# Kafka
KAFKA_HOST = os.getenv("KAFKA_HOST", "kafka")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "daily_prices")
KAFKA_INTRADAY_TOPIC = os.getenv("KAFKA_INTRADAY_TOPIC", "intraday_prices") # Topic riêng cho dữ liệu theo phút
PUBLISH_TO_KAFKA = os.getenv("PUBLISH_TO_KAFKA", "false").lower() == "true"

# Mongo
MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB = os.getenv("MONGO_DB", "stockdb")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "daily_prices")
MONGO_INTRADAY_COLLECTION = os.getenv("MONGO_INTRADAY_COLLECTION", "intraday_prices") # Collection riêng cho dữ liệu theo phút

logger.remove()
logger.add(sys.stdout, level="INFO")


# =========================
#     SECTOR MAPPING
# =========================
SECTOR_MAP = {
    "Banking": ["VCB","BID","CTG","TCB","MBB","VPB","STB","ACB","SHB","HDB"],
    "Securities": ["SSI","VND","HCM","VCI","SHS","FTS"],
    "RealEstate": ["VIC","VHM","VRE","NVL","PDR","KDH"],
    "PublicInvestment": ["HHV","CII","FCN","CTD","HBC"],
    "Transportation": ["VJC","HVN","GMD","VTP","VOS","VSC"]
}

# Tạo thư mục cho từng ngành
for sector in SECTOR_MAP.keys():
    (DATA_DIR / sector).mkdir(parents=True, exist_ok=True)
    (INTRADAY_DATA_DIR / sector).mkdir(parents=True, exist_ok=True) # Thư mục intraday

# Danh sách tất cả ticker cần crawl
TICKERS = [t for symbols in SECTOR_MAP.values() for t in symbols]


def get_sector_for(ticker: str) -> str:
    for sector, symbols in SECTOR_MAP.items():
        if ticker.upper() in symbols:
            return sector
    return None  # Không có ngành -> bỏ qua luôn


# =========================
#     EXTERNAL CLIENTS
# =========================
producer = None
if PUBLISH_TO_KAFKA and KafkaProducer is not None:
    try:
        producer = KafkaProducer(
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            retries=5,
        )
        logger.info(f"Kafka producer OK -> {KAFKA_HOST}:{KAFKA_PORT}, topic={KAFKA_TOPIC}, intraday_topic={KAFKA_INTRADAY_TOPIC}")
    except Exception as e:
        logger.warning(f"Kafka init failed: {e}")
        producer = None

mongo = None
if MONGO_URI and MongoClient is not None:
    try:
        mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo.server_info()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.warning(f"Mongo init failed: {e}")
        mongo = None


# =========================
#     DATA FUNCTIONS
# =========================
def fetch_historical(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Lấy OHLCV daily bằng vnstock v3."""
    if Quote is None:
        raise RuntimeError("vnstock chưa sẵn sàng. Hãy cài: pip install vnstock")

    def _try(source_name: str) -> pd.DataFrame:
        try:
            q = Quote(symbol=symbol, source=source_name)
            df = q.history(start=start, end=end)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.warning(f"vnstock daily fetch failed for {symbol} from {source_name}: {e}")
            return pd.DataFrame()

    df = _try("VCI")
    if df.empty:
        df = _try("TCBS")

    if df.empty:
        return pd.DataFrame(columns=["ticker","date","open","high","low","close","volume"])

    if "time" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"time": "date"})

    out = pd.DataFrame({
        "ticker": symbol,
        "date": pd.to_datetime(df.get("date")).dt.date,
        "open": pd.to_numeric(df.get("open"), errors="coerce"),
        "high": pd.to_numeric(df.get("high"), errors="coerce"),
        "low":  pd.to_numeric(df.get("low"),  errors="coerce"),
        "close": pd.to_numeric(df.get("close"), errors="coerce"),
        "volume": pd.to_numeric(df.get("volume"), errors="coerce").fillna(0).astype("Int64"),
    }).dropna(subset=["date"])

    return out

def mock_fetch_intraday(symbol: str) -> pd.DataFrame:
    """
    Mô phỏng lấy dữ liệu OHLCV theo phút.
    Bạn CẦN THAY THẾ hàm này bằng một API hoặc thư viện thực tế (ví dụ: Alpha Vantage, Finnhub, v.v.)
    mà hỗ trợ dữ liệu intraday.

    Một API ví dụ (cần key): https://www.alphavantage.co/documentation/#intraday
    """
    now = datetime.now()
    # Giả định lấy dữ liệu của phút hiện tại
    timestamp = now.replace(second=0, microsecond=0)

    # Giá giả định (cần thay bằng giá thực tế)
    last_close = random.uniform(10.0, 100.0) # Có thể lấy từ giá close cuối cùng của ngày nếu có
    open_p = last_close + random.uniform(-0.5, 0.5)
    high_p = open_p + random.uniform(0.1, 0.8)
    low_p = open_p - random.uniform(0.1, 0.8)
    close_p = open_p + random.uniform(-0.5, 0.5)
    volume_p = random.randint(100, 5000)

    data = [{
        "ticker": symbol,
        "datetime": timestamp,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "volume": volume_p,
    }]
    df = pd.DataFrame(data)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def publish_row(row: pd.Series, data_type: str = "daily"):
    """
    Gửi 1 bản ghi lên Kafka và upsert Mongo (nếu bật).
    data_type: "daily" hoặc "intraday"
    """
    if data_type == "daily":
        payload = {
            "ticker": row["ticker"],
            "date": str(row["date"]),
            "open": None if pd.isna(row["open"]) else float(row["open"]),
            "high": None if pd.isna(row["high"]) else float(row["high"]),
            "low":  None if pd.isna(row["low"])  else float(row["low"]),
            "close": None if pd.isna(row["close"]) else float(row["close"]),
            "volume": int(row["volume"]) if not pd.isna(row["volume"]) else 0,
        }
        kafka_topic = KAFKA_TOPIC
        mongo_collection = MONGO_COLLECTION
        # Dùng 'date' làm key cho dữ liệu hàng ngày
        mongo_filter = {"ticker": payload["ticker"], "date": payload["date"]}
    else: # intraday
        payload = {
            "ticker": row["ticker"],
            "datetime": str(row["datetime"]), # Lưu datetime đầy đủ
            "open": None if pd.isna(row["open"]) else float(row["open"]),
            "high": None if pd.isna(row["high"]) else float(row["high"]),
            "low":  None if pd.isna(row["low"])  else float(row["low"]),
            "close": None if pd.isna(row["close"]) else float(row["close"]),
            "volume": int(row["volume"]) if not pd.isna(row["volume"]) else 0,
        }
        kafka_topic = KAFKA_INTRADAY_TOPIC
        mongo_collection = MONGO_INTRADAY_COLLECTION
        # Dùng 'datetime' làm key cho dữ liệu theo phút
        mongo_filter = {"ticker": payload["ticker"], "datetime": payload["datetime"]}


    if producer is not None:
        try:
            producer.send(kafka_topic, payload)
        except Exception as e:
            logger.warning(f"Kafka send failed to {kafka_topic}: {e}")

    if mongo is not None:
        try:
            mongo[MONGO_DB][mongo_collection].update_one(
                mongo_filter,
                {"$set": payload},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Mongo upsert failed to {mongo_collection}: {e}")


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

        start_next = (last_date + timedelta(days=1)).isoformat()
        today = date.today().isoformat()

        if start_next <= today:
            df = fetch_historical(tk, start_next, today)
            if not df.empty:
                write_csv_upsert(df, str(f), index_cols=["ticker", "date"])
                for _, r in df.iterrows():
                    publish_row(r, data_type="daily")
                logger.info(f"{sector}/{tk}: +{len(df)} daily rows")
            else:
                logger.info(f"{sector}/{tk}: No new daily data found from {start_next} to {today}")
        else:
            logger.info(f"{sector}/{tk}: Daily data up-to-date")

def incremental_update_intraday():
    # Kiểm tra xem có đang trong giờ giao dịch không (ví dụ: 9h-15h)
    now = datetime.now(tz_of(TZ_NAME))
    # Bạn cần điều chỉnh giờ giao dịch thực tế của thị trường bạn quan tâm
    if not (9 <= now.hour < 15 and now.weekday() < 5): # Mon-Fri, 9:00 - 14:59
        logger.info(f"[Incremental Intraday] Not within trading hours or weekend ({now.strftime('%H:%M %A')}). Skipping.")
        return

    logger.info("[Incremental Intraday] Checking updates for minute data...")
    for tk in TICKERS:
        sector = get_sector_for(tk)
        if not sector:
            continue

        f = INTRADAY_DATA_DIR / sector / f"{tk}_intraday.csv" # Tên file riêng

        # Lấy dữ liệu của phút hiện tại
        df = mock_fetch_intraday(tk) # Dùng hàm mock_fetch_intraday

        if not df.empty:
            # Dùng 'datetime' làm cột index chính để upsert
            write_csv_upsert(df, str(f), index_cols=["ticker", "datetime"])
            for _, r in df.iterrows():
                publish_row(r, data_type="intraday")
            logger.info(f"{sector}/{tk}: +{len(df)} intraday rows (at {df['datetime'].iloc[0]})")
        # else: Không cần log nếu không có dữ liệu, vì mock_fetch_intraday luôn trả về 1 dòng


# =========================
#          MAIN
# =========================
def main():
    # --- Backfill Daily Data (nếu cần) ---
    missing_daily = [tk for tk in TICKERS if not (DATA_DIR / get_sector_for(tk) / f"{tk}.csv").exists()]
    if missing_daily:
        logger.info(f"Các mã chưa có dữ liệu daily: {missing_daily}. Bắt đầu full backfill daily.")
        backfill_all()
    else:
        logger.info("Đã có CSV daily -> bỏ qua full backfill daily.")

    sched = BlockingScheduler(timezone=tz_of(TZ_NAME))

    # --- Schedule Daily Update ---
    hour, minute = map(int, RUN_DAILY_AT.split(":"))
    sched.add_job(
        incremental_update_daily,
        CronTrigger(day_of_week="mon-fri", hour=hour, minute=minute, timezone=tz_of(TZ_NAME)),
        id='daily_update',
        name='Daily Stock Price Update'
    )
    logger.info(f"Scheduler Daily tại {RUN_DAILY_AT} ({TZ_NAME}) [Mon–Fri]. Chạy incremental daily 1 lần ngay bây giờ.")
    incremental_update_daily()

    # --- Schedule Intraday Update ---
    # Chạy mỗi RUN_INTRADAY_EVERY_MINUTES phút, từ 9:00 đến 14:59 (giờ thị trường giả định)
    # Lưu ý: Cần điều chỉnh start_date và end_date cho IntervalTrigger nếu muốn nó bắt đầu/kết thúc cụ thể
    sched.add_job(
        incremental_update_intraday,
        IntervalTrigger(minutes=RUN_INTRADAY_EVERY_MINUTES, timezone=tz_of(TZ_NAME)),
        id='intraday_update',
        name='Intraday Stock Price Update'
    )
    logger.info(f"Scheduler Intraday chạy mỗi {RUN_INTRADAY_EVERY_MINUTES} phút. Chạy incremental intraday 1 lần ngay bây giờ.")
    incremental_update_intraday()


    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")


if __name__ == "__main__":
    main()