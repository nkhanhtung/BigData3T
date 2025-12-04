# import asyncio
# import pandas as pd
# from sqlalchemy import (
#     Table, Column, String, Numeric, Integer, Date,
#     MetaData, insert, select, PrimaryKeyConstraint
# )
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# from datetime import datetime
# from sqlalchemy import DateTime

# DATABASE_URL = (
#     "postgresql+asyncpg://neondb_owner:npg_X3MpLju8nzxi"
#     "@ep-lingering-pond-a1q4x3j5-pooler.ap-southeast-1.aws.neon.tech:5432/neondb"
# )

# # Create async engine
# engine = create_async_engine(DATABASE_URL, echo=True,connect_args={"prepared_statement_cache_size": 0})
# async_session = async_sessionmaker(engine, expire_on_commit=False)

# # Metadata
# metadata = MetaData()

# # ================================
# # DEFINE TABLE - NO stock_id
# # ================================
# daily_stock_table = Table(
#     "p_stocks_prices",
#     metadata,
#     Column("stock_symbol", String(3), nullable=False),
#     Column("date", DateTime, nullable=False),
#     Column("open_price", Numeric(10, 2), nullable=False),
#     Column("close_price", Numeric(10, 2), nullable=False),
#     Column("high_price", Numeric(10, 2), nullable=False),
#     Column("low_price", Numeric(10, 2), nullable=False),
#     Column("volumes", Integer, nullable=False),

#     PrimaryKeyConstraint("stock_symbol", "date")
# )


# # ================================
# # LOAD ONE CSV
# # ================================
# async def load_csv(file_path: str, stock_symbol: str):
#     df = pd.read_csv(file_path)

#     async with async_session() as session:
#         async with session.begin():
#             for _, row in df.iterrows():

#                 row_date = datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S")

#                 # Check duplicate
#                 stmt_check = select(daily_stock_table).where(
#                     daily_stock_table.c.stock_symbol == stock_symbol,
#                     daily_stock_table.c.date == row_date
#                 )
#                 result = await session.execute(stmt_check)
#                 if result.first():
#                     continue

#                 # Insert row
#                 stmt_insert = insert(daily_stock_table).values(
#                     stock_symbol=stock_symbol[:3],
#                     date=row_date,
#                     open_price=row["open"],
#                     high_price=row["high"],
#                     low_price=row["low"],
#                     close_price=row["close"],
#                     volumes=row["volume"]
#                 )
#                 await session.execute(stmt_insert)

#         await session.commit()

#     print(f"✅ Loaded CSV {file_path} (symbol={stock_symbol})")


# # ================================
# # LOAD MULTIPLE CSVs
# # ================================
# async def load_multiple_csv(folder_path: str, file_list: list):
#     for f in file_list:
#         stock_symbol = f.replace(".csv", "").upper()
#         file_path = f"{folder_path}/{f}"
#         await load_csv(file_path, stock_symbol)
    

# # ================================
# # MAIN
# # ================================
# if __name__ == "__main__":
#     folder = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/datasets/Banking"

#     files = [
#         "ACB.csv","BID.csv"
#     ]

#     asyncio.run(load_multiple_csv(folder, files))


import asyncio
import pandas as pd
from decimal import Decimal
from sqlalchemy import (
    Table, Column, String, Numeric, Integer, MetaData,
    PrimaryKeyConstraint, DateTime
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert

# ================================
# DATABASE CONFIG
# ================================
DATABASE_URL = (
    "postgresql+asyncpg://neondb_owner:npg_X3MpLju8nzxi"
    "@ep-lingering-pond-a1q4x3j5-pooler.ap-southeast-1.aws.neon.tech:5432/neondb"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"prepared_statement_cache_size": 0}
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# ================================
# DEFINE TABLE
# ================================
metadata = MetaData()

daily_stock_table = Table(
    "p_stocks_prices",
    metadata,
    Column("stock_symbol", String(3), nullable=False),
    Column("date", DateTime, nullable=False),
    Column("open_price", Numeric(10, 2), nullable=False),
    Column("close_price", Numeric(10, 2), nullable=False),
    Column("high_price", Numeric(10, 2), nullable=False),
    Column("low_price", Numeric(10, 2), nullable=False),
    Column("volumes", Integer, nullable=False),
    PrimaryKeyConstraint("stock_symbol", "date")
)

# ================================
# LOAD ONE CSV
# ================================
async def load_csv(file_path: str, stock_symbol: str):
    df = pd.read_csv(file_path)

    async with async_session() as session:
        async with session.begin():
            for _, row in df.iterrows():
                row_date = datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S")

                # INSERT or UPDATE nếu đã tồn tại
                stmt_insert = pg_insert(daily_stock_table).values(
                    stock_symbol=stock_symbol[:3],
                    date=row_date,
                    open_price=Decimal(row["open"]),
                    high_price=Decimal(row["high"]),
                    low_price=Decimal(row["low"]),
                    close_price=Decimal(row["close"]),
                    volumes=int(row["volume"])
                ).on_conflict_do_update(
                    index_elements=['stock_symbol','date'],
                    set_={
                        "open_price": Decimal(row["open"]),
                        "high_price": Decimal(row["high"]),
                        "low_price": Decimal(row["low"]),
                        "close_price": Decimal(row["close"]),
                        "volumes": int(row["volume"])
                    }
                )

                await session.execute(stmt_insert)

        await session.commit()
    print(f"✅ Loaded CSV {file_path} (symbol={stock_symbol})")

# ================================
# LOAD MULTIPLE CSVs
# ================================
async def load_multiple_csv(folder_path: str, file_list: list):
    for f in file_list:
        stock_symbol = f.replace(".csv", "").upper()
        file_path = f"{folder_path}/{f}"
        await load_csv(file_path, stock_symbol)

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    folder = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T"
    files = ["ACB.csv"]
    asyncio.run(load_multiple_csv(folder, files))
