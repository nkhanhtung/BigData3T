from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.postsql.database import get_async_session  # sửa import cho đúng đường dẫn thực tế
from models.daily_stock_price import DailyStockPrice  # import model bạn định nghĩa


router = APIRouter()

@router.get("/ohlcv/{stock_symbol}")
async def get_ohlc_data(stock_symbol: str, session: AsyncSession = Depends(get_async_session)):
    """
    Lấy dữ liệu OHLC của 1 cổ phiếu từ PostgreSQL để hiển thị biểu đồ nến.
    """
    try:
        stmt = (
            select(
                DailyStockPrice.date,
                DailyStockPrice.open_price.label("open_price"),
                DailyStockPrice.high_price.label("high_price"),
                DailyStockPrice.low_price.label("low_price"),
                DailyStockPrice.close_price.label("close_price"),
                DailyStockPrice.volumes.label("volumes"),
            )
            .where(DailyStockPrice.stock_symbol == stock_symbol)
            .order_by(DailyStockPrice.date)
        )

        result = await session.execute(stmt)
        rows = result.mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail=f"No OHLC data found for stock_id={stock_symbol}")

        return {"ohlc": [dict(row) for row in rows]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
