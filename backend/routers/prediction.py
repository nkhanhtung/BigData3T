
from fastapi import APIRouter, HTTPException, Depends, status
from schemas.prediction import PredictionRequest, PredictionResponse
import numpy as np
import joblib
from realtime.realtime_prediction import manager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from databases.postsql.database import get_async_session 
import numpy as np

router = APIRouter()


@router.get("/realtime/{symbol}", response_model=PredictionResponse)
async def predict_realtime(symbol: str, db: AsyncSession = Depends(get_async_session)):
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
    for _ in range(5):
        scaled = scaler.transform(current_input)
        X = scaled.reshape(1, 60, 1)
        pred_scaled = model.predict(X, verbose=0)[0][0]
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0]
        predictions.append(float(pred_real))
        current_input = np.append(current_input[1:], [[pred_real]], axis=0)

    return PredictionResponse(
        symbol=symbol,
        predictions=predictions,
        device="cpu"
    )


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
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0]
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
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0]
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
        pred_real = scaler.inverse_transform([[pred_scaled]])[0][0]
        predictions.append(float(pred_real))
        current_input = np.append(current_input[1:], [[pred_real]], axis=0)

    return PredictionResponse(
        symbol=symbol,
        predictions=predictions,
        device="cpu"
    )
