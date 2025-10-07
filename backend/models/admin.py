from sqlalchemy import Column, Integer, Text, Numeric, DateTime, String
from databases.postsql.database import Base


class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_name = Column(Text, nullable=False)
    admin_email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True))

