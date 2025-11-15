import asyncio
import pandas as pd
from sqlalchemy import Table, Column, Integer, String, Float, Date, MetaData, insert, select, Numeric
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import Table, Column, Integer, Numeric, Date, MetaData, PrimaryKeyConstraint
from datetime import datetime

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_X3MpLju8nzxi@ep-lingering-pond-a1q4x3j5-pooler.ap-southeast-1.aws.neon.tech:5432/neondb"

# Kết nối async engine
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Khởi tạo metadata
metadata = MetaData()

# Định nghĩa table trực tiếp (không dùng ORM)
daily_stock_table = Table(
    "daily_stocks_prices",
    metadata,
    Column("stock_id", Integer, nullable=False, primary_key=True),
    Column("date", Date, nullable=False),
    Column("open_price", Numeric(10,2), nullable=False),
    Column("close_price", Numeric(10,2), nullable=False),
    Column("high_price", Numeric(10,2), nullable=False),
    Column("low_price", Numeric(10,2), nullable=False),
    Column("volumes", Integer, nullable=False),
    PrimaryKeyConstraint("stock_id", "date") 
)

async def load_csv(file_path: str, stock_id: int):
    df = pd.read_csv(file_path)

    async with async_session() as session:
        async with session.begin():
            for _, row in df.iterrows():
                # Check duplicate (stock_id + date)
                row_date = datetime.strptime(row['date'], "%Y-%m-%d").date()
                stmt_check = select(daily_stock_table).where(
                    daily_stock_table.c.stock_id == stock_id,
                    daily_stock_table.c.date == row_date
                )
                result = await session.execute(stmt_check)
                existing = result.first()
                if existing:
                    continue

                stmt_insert = insert(daily_stock_table).values(
                    stock_id=stock_id,
                    date=row_date,
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    volumes=row['volume']
                )
                await session.execute(stmt_insert)

        await session.commit()
    print(f"✅ Loaded CSV {file_path} with stock_id={stock_id}")


async def load_multiple_csv(folder_path: str, file_list: list):
    stock_id = 2  # bắt đầu từ 2
    for f in file_list:
        file_path = f"{folder_path}/{f}"
        await load_csv(file_path, stock_id)
        stock_id += 1


if __name__ == "__main__":
    folder = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_daily/Banking"
    

    files = [
        "ACB.csv", "BID.csv", "CTG.csv", "HDB.csv", "MBB.csv", 
        "SHB.csv", "STB.csv", "TCB.csv", "VCB.csv", "VPB.csv"
    ]

    asyncio.run(load_multiple_csv(folder, files))
