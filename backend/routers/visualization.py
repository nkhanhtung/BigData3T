from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.postsql.database import get_async_session  # sửa import cho đúng đường dẫn thực tế
from models.daily_stock_price import DailyStockPrice  # import model bạn định nghĩa
from models.stock import Stock
from models.p1_stock_price import P1StockPrice

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



@router.get("/ohlcv_1p/{stock_symbol}")
async def get_ohlc_data(stock_symbol: str, session: AsyncSession = Depends(get_async_session)):
    """
    Lấy dữ liệu OHLC của 1 cổ phiếu từ PostgreSQL để hiển thị biểu đồ nến.
    """
    try:
        stmt = (
            select(
                P1StockPrice.date,
                P1StockPrice.open_price.label("open_price"),
                P1StockPrice.high_price.label("high_price"),
                P1StockPrice.low_price.label("low_price"),
                P1StockPrice.close_price.label("close_price"),
                P1StockPrice.volumes.label("volumes"),
            )
            .where(P1StockPrice.stock_symbol == stock_symbol)
            .order_by(P1StockPrice.date)
        )

        result = await session.execute(stmt)
        rows = result.mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail=f"No OHLC data found for stock_id={stock_symbol}")

        return {"ohlc": [dict(row) for row in rows]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")



@router.get("/stocks/list")
async def get_stock_list(session: AsyncSession = Depends(get_async_session)):
    """
    Lấy toàn bộ danh sách mã và tên cổ phiếu từ database.
    """
    stmt = select(Stock.stock_symbol, Stock.stock_name).order_by(Stock.stock_name)
    result = await session.execute(stmt)
    rows = result.mappings().all()
    return {"stocks": [dict(row) for row in rows]}

@router.get("/info/{stock_symbol}")
async def get_stock_info(stock_symbol: str, session: AsyncSession = Depends(get_async_session)):
    stmt = select(Stock).where(Stock.stock_symbol == stock_symbol)
    result = await session.execute(stmt)
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {
        "stock_symbol": stock.stock_symbol,
        "stock_name": stock.stock_name,
        "major": stock.major,
        "market_name": stock.market_name
    }