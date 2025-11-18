from fastapi import APIRouter, WebSocket
from realtime.realtime_trading import stream_matched_orders, stream_price_alerts, stream_volume_alerts

router = APIRouter()

@router.websocket("/ws/matched-orders")
async def websocket_matched_orders(websocket: WebSocket):
    await stream_matched_orders(websocket)


@router.websocket("/ws/price-alerts")
async def websocket_price_alerts(websocket: WebSocket):
    await stream_price_alerts(websocket)


@router.websocket("/ws/volume-alerts")
async def matched_volume_alerts(websocket: WebSocket):
    await stream_volume_alerts(websocket)