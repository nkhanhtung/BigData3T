from fastapi import APIRouter, HTTPException, Depends, status
from schemas.prediction import PredictionRequest, PredictionResponse
import numpy as np
import joblib
from realtime.realtime_prediction import manager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from databases.postsql.database import get_async_session, get_async_session_cm
import numpy as np
from fastapi import WebSocket
from databases.postsql.database import AsyncSessionLocal
import asyncio
import random
import numpy as np
import asyncio
from datetime import datetime, timedelta
import numpy as np
import random

router = APIRouter()

# async def rolling_closes(symbol: str, db: AsyncSession, window: int = 60, interval: int = 3):
#     """Yield rolling windows of closes trong 180 giá trị đã có"""
#     closes_all = await manager.fetch_last_n_minutes(symbol, 105, db)  # lấy 180 giá trị cố định
#     for start in range(len(closes_all) - window + 1):
#         window_data = closes_all[start:start+window]
#         yield window_data
#         await asyncio.sleep(interval)  # delay 5s giữa mỗi window

# async def rolling_predictions(symbol: str, db: AsyncSession, model, scaler, window: int = 60):
#     async for window_data in rolling_closes(symbol, db, window):
#         # Chuẩn hóa và reshape input
#         X_scaled = scaler.transform(window_data.reshape(-1,1)).reshape(1, window, 1)
#         pred_scaled = model.predict(X_scaled, verbose=0)[0][0]
#         pred_real = scaler.inverse_transform([[pred_scaled]])[0][0] + random.uniform(1,1.5)
#         yield float(pred_real)
async def rolling_windows(symbol: str, db: AsyncSession, window: int = 60):
    # fetch_last_n_minutes bây giờ trả về (closes, timestamps)
    closes_all, timestamps_all = await manager.fetch_last_n_minutes(symbol, 105, db)
    closes_all = [float(x) for x in closes_all]   # convert to python float

    for start in range(len(closes_all) - window):
        window_data = closes_all[start:start+window]
        window_timestamps = timestamps_all[start:start+window]  # tương ứng với window
        # yield tuple (window_data, window_timestamps)
        yield list(zip(window_data, window_timestamps))
        await asyncio.sleep(3)


async def rolling_predictions(symbol: str, db: AsyncSession, model, scaler, window: int = 60):
    check = False
    async for window_data_with_ts in rolling_windows(symbol, db, window):
        # window_data_with_ts: list of tuples (close_price, timestamp)
        window_data = [x for x, _ in window_data_with_ts]
        window_timestamps = [ts for _, ts in window_data_with_ts]

        # === Gửi 60 giá trị historical với date ===
        historical_with_date = [
            {"date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"), "close_price": float(x)}
            for x, ts in zip(window_data, window_timestamps)
        ]
        yield {"historical": historical_with_date}

        # Gửi độ dài window
        yield {'len': len(window_data)}

        # Gửi giá thực tế cuối cùng (real) nếu check=True
        if check:
            yield {'real': {"date": window_timestamps[-1], "close_price": float(window_data[-1])}}
        check = True

        # === Scale input + predict ===
        X_scaled = scaler.transform(np.array(window_data).reshape(-1,1)).reshape(1, window, 1)
        pred_scaled = float(model.predict(X_scaled, verbose=0)[0][0])
        pred_real = float(scaler.inverse_transform([[pred_scaled]])[0][0])

        # random nhỏ để demo
        pred_real += float(random.uniform(1,1.2))

        # === Gửi prediction ===
        yield {"prediction": pred_real}


@router.websocket("/ws/realtime/predict/{symbol}")
async def ws_realtime(websocket: WebSocket):
    await websocket.accept()
    symbol = websocket.path_params["symbol"].upper()
    try:
        model = manager.load_model(symbol)
        scaler = manager.load_scaler(symbol)

        async with get_async_session_cm() as db:
            async for packet in rolling_predictions(symbol, db, model, scaler):
                await websocket.send_json(packet)

    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()



@router.get("/short-term/{symbol}", response_model=PredictionResponse)
async def predict_daily(symbol: str, db: AsyncSession = Depends(get_async_session)):
    symbol = symbol.upper()
    try:
        model = manager.load_model(symbol)
        scaler = manager.load_scaler(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Lấy 60 ngày gần nhất
    try:
        closes = await manager.fetch_last_n_days(symbol, 60, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    predictions = []
    current_input = closes.reshape(-1, 1)

    # Dự đoán rolling 30 ngày
    for _ in range(15):
        scaled = scaler.transform(current_input)
        X = scaled.reshape(1, 60, 1)
        pred_scaled = model.predict(X, verbose=0)[0][0]
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0] + random.uniform(1,1.5)
        predictions.append(float(pred_real))
        current_input = np.append(current_input[1:], [[pred_real]], axis=0)

    return PredictionResponse(
        symbol=symbol,
        predictions=predictions,
        device="cpu"
    )


@router.get("/medium-term/{symbol}", response_model=PredictionResponse)
async def predict_monthly(symbol: str, db: AsyncSession = Depends(get_async_session)):
    symbol = symbol.upper()
    try:
        model = manager.load_model(symbol)
        scaler = manager.load_scaler(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Lấy 60 ngày gần nhất
    try:
        closes = await manager.fetch_last_n_months(symbol, 60, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    predictions = []
    current_input = closes.reshape(-1, 1)

    # Dự đoán rolling 30 ngày
    for _ in range(5):
        scaled = scaler.transform(current_input)
        X = scaled.reshape(1, 60, 1)
        pred_scaled = model.predict(X, verbose=0)[0][0]
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0] + random.uniform(1,1.5)
        predictions.append(float(pred_real))
        current_input  = np.append(current_input[1:], [[pred_real]], axis=0)

    return PredictionResponse(
        symbol=symbol,
        predictions=predictions,
        device="cpu"
    )


@router.get("/long-term/{symbol}", response_model=PredictionResponse)
async def predict_yearly(symbol: str, db: AsyncSession = Depends(get_async_session)):
    symbol = symbol.upper()
    try:
        model = manager.load_model(symbol)
        scaler = manager.load_scaler(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Lấy 60 ngày gần nhất
    try:
        closes = await manager.fetch_last_n_months(symbol, 60, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    predictions = []
    current_input = closes.reshape(-1, 1)

    # Dự đoán rolling 30 ngày
    for _ in range(12):
        scaled = scaler.transform(current_input)
        X = scaled.reshape(1, 60, 1)
        pred_scaled = model.predict(X, verbose=0)[0][0]
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0] + random.uniform(1,1.5)
        predictions.append(float(pred_real))
        current_input = np.append(current_input[1:], [[pred_real]], axis=0)

    return PredictionResponse(
        symbol=symbol,
        predictions=predictions,
        device="cpu"
    )
