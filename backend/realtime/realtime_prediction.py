import os
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Input
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import numpy as np
from models.daily_stock_price import DailyStockPrice
from models.monthly_stock_price import MonthlyStockPrice
from sqlalchemy import desc


class ModelManager:
    """Quản lý load/save model và scaler, cache trong bộ nhớ để reuse"""

    def __init__(self, model_dir: str = "predictors/models", scaler_dir: str = "predictors/scaler"):
        self.model_dir = model_dir
        self.scaler_dir = scaler_dir
        self.model_cache: Dict[str, tf.keras.Model] = {}
        self.scaler_cache: Dict[str, object] = {}

    def load_model(self, symbol: str) -> tf.keras.Model:
        """Load model h5 + rebuild Input nếu lỗi batch_shape"""
        if symbol in self.model_cache:
            return self.model_cache[symbol]

        model_path = os.path.join(self.model_dir, f"{symbol}_model.h5")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {symbol}")

        old_model = load_model(model_path, compile=False)

        try:
            # Rebuild input để tránh lỗi batch_shape
            x = Input(shape=(60, 1))
            new_model = tf.keras.models.Model(inputs=x, outputs=old_model(x))
            new_model.set_weights(old_model.get_weights())
            model = new_model
        except Exception:
            # fallback nếu rebuild không cần thiết
            model = old_model

        self.model_cache[symbol] = model
        return model

    def load_scaler(self, symbol: str):
        """Load scaler tương ứng với mã"""
        if symbol in self.scaler_cache:
            return self.scaler_cache[symbol]

        scaler_path = os.path.join(self.scaler_dir, f"{symbol}_scaler.pkl")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler not found: {symbol}")

        scaler = joblib.load(scaler_path)
        self.scaler_cache[symbol] = scaler
        return scaler



    async def fetch_last_n_days(self, stock_symbol: str, n: int, db: AsyncSession) -> np.ndarray:
        """Lấy n ngày dữ liệu close_price gần nhất"""
        query = (
            select(DailyStockPrice.close_price)
            .where(DailyStockPrice.stock_symbol == stock_symbol)
            .order_by(desc(DailyStockPrice.date))
            .limit(n)
        )
        result = await db.execute(query)
        rows: List[float] = result.scalars().all()
        if len(rows) < n:
            raise ValueError(f"Not enough data for {symbol}, need {n} rows")
        
        closes = np.array(rows[::-1], dtype=np.float32)
        return closes
    
    async def fetch_last_n_months(self, stock_symbol: str, n: int, db: AsyncSession) -> np.ndarray:
        """Lấy n ngày dữ liệu close_price gần nhất"""
        query = (
            select(MonthlyStockPrice.close_price)
            .where(MonthlyStockPrice.stock_symbol == stock_symbol)
            .order_by(desc(MonthlyStockPrice.date))
            .limit(n)
        )
        result = await db.execute(query)
        rows: List[float] = result.scalars().all()
        if len(rows) < n:
            raise ValueError(f"Not enough data for {symbol}, need {n} rows")
        
        closes = np.array(rows[::-1], dtype=np.float32)
        return closes


manager = ModelManager()