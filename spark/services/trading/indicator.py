
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

# ================= SMA =================
def sma(df: DataFrame, price_col: str = "matched_price", period: int = 10, alias: str = None) -> DataFrame:
    """
    Simple Moving Average
    """
    alias = alias or f"SMA_{period}"
    w = Window.partitionBy("stock_symbol").orderBy("trade_timestamp").rowsBetween(-period + 1, 0)
    return df.withColumn(alias, F.avg(price_col).over(w))

# ================= EMA (approximation) =================
def ema(df: DataFrame, price_col: str = "matched_price", period: int = 10, alias: str = None) -> DataFrame:
    """
    Exponential Moving Average (approximate in Spark)
    """
    alias = alias or f"EMA_{period}"
    # Simple iterative EMA approximation using UDF or placeholder
    # For exact EMA, compute in foreachBatch using Pandas or PySpark iterative method
    return df.withColumn(alias, F.lit(None).cast("double"))

# ================= VWAP =================
def vwap(df: DataFrame, price_col: str = "matched_price", qty_col: str = "matched_quantity", alias: str = "VWAP") -> DataFrame:
    """
    Volume Weighted Average Price
    """
    w = Window.partitionBy("stock_symbol").orderBy("trade_timestamp").rowsBetween(Window.unboundedPreceding, 0)
    vwap_col = F.sum(F.col(price_col) * F.col(qty_col)).over(w) / F.sum(F.col(qty_col)).over(w)
    return df.withColumn(alias, vwap_col)

# ================= RSI =================
def rsi(df: DataFrame, price_col: str = "matched_price", period: int = 14, alias: str = "RSI") -> DataFrame:
    """
    Relative Strength Index (approximate in Spark)
    """
    w = Window.partitionBy("stock_symbol").orderBy("trade_timestamp").rowsBetween(-period, 0)
    diff = F.col(price_col) - F.lag(price_col).over(Window.partitionBy("stock_symbol").orderBy("trade_timestamp"))
    gain = F.when(diff > 0, diff).otherwise(0)
    loss = F.when(diff < 0, -diff).otherwise(0)
    avg_gain = F.avg(gain).over(w)
    avg_loss = F.avg(loss).over(w)
    rs = avg_gain / F.when(avg_loss == 0, F.lit(1e-9)).otherwise(avg_loss)
    rsi_col = 100 - (100 / (1 + rs))
    return df.withColumn(alias, rsi_col)

# ================= MACD =================
def macd(df: DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> DataFrame:
    """
    MACD Line, Signal, Histogram
    """
    df = ema(df, period=fast, alias=f"EMA_{fast}")
    df = ema(df, period=slow, alias=f"EMA_{slow}")
    df = df.withColumn("MACD_line", F.col(f"EMA_{fast}") - F.col(f"EMA_{slow}"))
    df = ema(df, price_col="MACD_line", period=signal, alias="MACD_signal")
    df = df.withColumn("MACD_hist", F.col("MACD_line") - F.col("MACD_signal"))
    return df

# ================= Bollinger Bands =================
def bollinger_bands(df: DataFrame, period: int = 20, k: int = 2) -> DataFrame:
    """
    Bollinger Bands
    """
    df = sma(df, period=period, alias=f"SMA_{period}")
    w = Window.partitionBy("stock_symbol").orderBy("trade_timestamp").rowsBetween(-period+1, 0)
    stddev_col = F.stddev(F.col("matched_price")).over(w)
    df = df.withColumn("BB_upper", F.col(f"SMA_{period}") + k * stddev_col)
    df = df.withColumn("BB_lower", F.col(f"SMA_{period}") - k * stddev_col)
    return df

def generate_trading_signal(df: DataFrame) -> DataFrame:
    """
    Thêm cột 'signal' dựa trên các indicator:
    BUY / SELL / HOLD
    """
    # SMA crossover: nếu matched_price > SMA_10 → BUY, < SMA_10 → SELL
    df = df.withColumn(
        "signal_sma",
        F.when(F.col("matched_price") > F.col("SMA_10"), "BUY")
         .when(F.col("matched_price") < F.col("SMA_10"), "SELL")
         .otherwise("HOLD")
    )
    
    # RSI: <30 BUY, >70 SELL
    df = df.withColumn(
        "signal_rsi",
        F.when(F.col("RSI") < 30, "BUY")
         .when(F.col("RSI") > 70, "SELL")
         .otherwise("HOLD")
    )
    
    # MACD: MACD_line cắt MACD_signal
    df = df.withColumn(
        "signal_macd",
        F.when(F.col("MACD_line") > F.col("MACD_signal"), "BUY")
         .when(F.col("MACD_line") < F.col("MACD_signal"), "SELL")
         .otherwise("HOLD")
    )
    
    # Bollinger Bands
    df = df.withColumn(
        "signal_bb",
        F.when(F.col("matched_price") < F.col("BB_lower"), "BUY")
         .when(F.col("matched_price") > F.col("BB_upper"), "SELL")
         .otherwise("HOLD")
    )
    
    # Tổng hợp tín hiệu (simple voting)
    df = df.withColumn(
        "signal",
        F.when(
            (F.col("signal_sma") == "BUY") | (F.col("signal_rsi") == "BUY") |
            (F.col("signal_macd") == "BUY") | (F.col("signal_bb") == "BUY"), "BUY"
        ).when(
            (F.col("signal_sma") == "SELL") | (F.col("signal_rsi") == "SELL") |
            (F.col("signal_macd") == "SELL") | (F.col("signal_bb") == "SELL"), "SELL"
        ).otherwise("HOLD")
    )
    
    return df