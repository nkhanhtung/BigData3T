from fastapi import APIRouter, WebSocket
from realtime.realtime_trading import stream_matched_orders, stream_price_alerts, stream_volume_alerts, stream_indicator_alerts, stream_candlestick_ohlc
from models.p1_stock_price import P1StockPrice
from databases.postsql.database import get_async_session_cm
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import select
import logging
import asyncio


router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/matched-orders")
async def websocket_matched_orders(websocket: WebSocket):
    await stream_matched_orders(websocket)


@router.websocket("/ws/price-alerts")
async def websocket_price_alerts(websocket: WebSocket):
    await stream_price_alerts(websocket)


@router.websocket("/ws/volume-alerts")
async def matched_volume_alerts(websocket: WebSocket):
    await stream_volume_alerts(websocket)


@router.websocket("/ws/indicator-alerts")
async def matched_indicator_alerts(websocket: WebSocket):
    await stream_indicator_alerts(websocket)
    

@router.websocket("/ws/candlestick-ohlc")
async def matched_candlestick_ohlc(websocket: WebSocket):
    await stream_candlestick_ohlc(websocket)


@router.websocket("/ws/realtime-ohlc/{stock_symbol}")
async def websocket_realtime_ohlc(websocket: WebSocket, stock_symbol: str):
    await websocket.accept()
    try:
        async with get_async_session_cm() as session:  # <- Dùng context manager
            query = select(
            P1StockPrice.stock_symbol,
            P1StockPrice.date,
            P1StockPrice.open_price,
            P1StockPrice.close_price,
            P1StockPrice.high_price,
            P1StockPrice.low_price,
            P1StockPrice.volumes
        ).where(P1StockPrice.stock_symbol == stock_symbol).order_by(P1StockPrice.date.asc())

            result = await session.execute(query)

            rows = result.all()

            for row in rows:
                ohlc = {
                    "stock_symbol": row.stock_symbol,
                    "date": row.date.isoformat(),
                    "open_price": float(row.open_price),
                    "close_price": float(row.close_price),
                    "high_price": float(row.high_price),
                    "low_price": float(row.low_price),
                    "volumes": row.volumes
                }
                await websocket.send_json(ohlc)
                await asyncio.sleep(1)  # gửi từng dòng cách 3 giây
    except Exception as e:
        print(f"Error in websocket_realtime_ohlc: {e}")