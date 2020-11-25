from sqlalchemy import Column, String, create_engine,TEXT,Integer,TIMESTAMP,text,desc,or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 创建对象的基类:
Base = declarative_base()

# 定义User对象:
class Configure(Base):
    # 表的名字:
    __tablename__ = 'configure'
    # 表的结构:
    id = Column(Integer, primary_key=True)
    lanmuId = Column(String(50))
    lanmuName = Column(String(50))
    detailUrl=Column(String(255))
    java=Column(TEXT)
    cron=Column(String(50))
    machines = Column(Integer)
    userName=Column(String(50))
    updateTime=Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
    abandon=Column(Integer)

class username(Base):
    # 表的名字:
    __tablename__ = 'username'
    # 表的结构:
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    pwd = Column(String(255))

# 初始化数据库连接:
engine = create_engine('mysql+pymysql://root:Ysjzx221@39.98.35.147:3306/test?connect_timeout=30')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)