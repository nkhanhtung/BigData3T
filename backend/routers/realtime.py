from fastapi import APIRouter, WebSocket
from realtime.realtime_trading import stream_matched_orders

router = APIRouter()

@router.websocket("/ws/matched-orders")
async def matched_orders_ws(websocket: WebSocket):
    await stream_matched_orders(websocket)
