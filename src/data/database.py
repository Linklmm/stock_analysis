"""
数据库管理模块
Database Management Module

提供 MySQL 数据库连接、表模型和数据操作功能。
Provides MySQL database connection, table models, and data operations.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, Date, DateTime, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

import pandas as pd

from config.settings import DATABASE_CONFIG
from src.core.utils import logger

# 创建基类 / Create base class
Base = declarative_base()


# ==================== 数据表模型 / Table Models ====================

class StockDaily(Base):
    """
    股票日线行情表
    Stock Daily Market Data Table
    """
    __tablename__ = "stock_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码 TS代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    pre_close = Column(Float, comment="昨收价")
    change = Column(Float, comment="涨跌额")
    pct_chg = Column(Float, comment="涨跌幅(%)")
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_stock_daily_code_date", "ts_code", "trade_date", unique=True),
    )

    def __repr__(self):
        return f"<StockDaily({self.ts_code}, {self.trade_date}, {self.close})>"


class IndexDaily(Base):
    """
    指数日线行情表
    Index Daily Market Data Table
    """
    __tablename__ = "index_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="指数代码 TS代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    pre_close = Column(Float, comment="昨收价")
    change = Column(Float, comment="涨跌额")
    pct_chg = Column(Float, comment="涨跌幅(%)")
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_index_daily_code_date", "ts_code", "trade_date", unique=True),
    )

    def __repr__(self):
        return f"<IndexDaily({self.ts_code}, {self.trade_date}, {self.close})>"


class StockBasic(Base):
    """
    股票基本信息表
    Stock Basic Information Table
    """
    __tablename__ = "stock_basic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, unique=True, comment="TS代码")
    symbol = Column(String(10), comment="股票代码")
    name = Column(String(50), comment="股票名称")
    area = Column(String(20), comment="地域")
    industry = Column(String(50), comment="所属行业")
    market = Column(String(20), comment="市场类型")
    list_date = Column(Date, comment="上市日期")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<StockBasic({self.ts_code}, {self.name})>"


class TradeCalendar(Base):
    """
    交易日历表
    Trade Calendar Table
    """
    __tablename__ = "trade_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(10), nullable=False, comment="交易所 SSE/SZSE")
    cal_date = Column(Date, nullable=False, comment="日期")
    is_open = Column(Integer, nullable=False, comment="是否交易 0休市 1交易")
    pretrade_date = Column(Date, comment="上一交易日")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_trade_calendar_date", "exchange", "cal_date", unique=True),
    )

    def __repr__(self):
        return f"<TradeCalendar({self.exchange}, {self.cal_date}, is_open={self.is_open})>"


class Watchlist(Base):
    """
    自选股表
    Watchlist Table
    """
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码 TS代码")
    name = Column(String(50), comment="股票名称")
    group_name = Column(String(50), default="默认", comment="分组名称")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    remark = Column(String(200), comment="备注")
    created_at = Column(DateTime, default=datetime.now, comment="添加时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (
        Index("idx_watchlist_code", "ts_code", unique=True),
    )

    def __repr__(self):
        return f"<Watchlist({self.ts_code}, {self.name})>"


# ==================== 数据库管理类 / Database Manager Class ====================

class DatabaseManager:
    """
    数据库管理器
    Database Manager

    负责数据库连接、会话管理和数据操作。
    Responsible for database connection, session management, and data operations.
    """

    def __init__(self):
        """初始化数据库连接 / Initialize database connection"""
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        """获取数据库引擎 / Get database engine"""
        if self._engine is None:
            self._engine = create_engine(
                DATABASE_CONFIG.connection_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )
        return self._engine

    @property
    def session_factory(self):
        """获取会话工厂 / Get session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def get_session(self) -> Session:
        """获取数据库会话 / Get database session"""
        return self.session_factory()

    def create_tables(self):
        """创建所有数据表 / Create all tables"""
        Base.metadata.create_all(self.engine)
        logger.info("数据库表创建成功")

    def create_database(self):
        """
        创建数据库（如果不存在）
        Create database if not exists
        """
        # 连接到 MySQL 服务器（不指定数据库）
        url = f"mysql+pymysql://{DATABASE_CONFIG.user}:{DATABASE_CONFIG.password}@{DATABASE_CONFIG.host}:{DATABASE_CONFIG.port}?charset=utf8mb4"
        engine = create_engine(url)

        with engine.connect() as conn:
            # 创建数据库
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()

        engine.dispose()
        logger.info(f"数据库 {DATABASE_CONFIG.database} 已就绪")

    # ==================== 股票数据操作 / Stock Data Operations ====================

    def save_stock_daily(self, df: pd.DataFrame) -> int:
        """
        保存股票日线数据（支持增量更新，避免重复）
        Save stock daily data (supports incremental update, avoids duplicates)

        Args:
            df: 股票日线数据 DataFrame

        Returns:
            保存的记录数
        """
        if df.empty:
            return 0

        session = self.get_session()
        try:
            saved_count = 0
            for _, row in df.iterrows():
                # 使用 merge 实现 upsert（插入或更新）
                # 先检查是否存在
                existing = session.query(StockDaily).filter(
                    StockDaily.ts_code == row.get("ts_code"),
                    StockDaily.trade_date == pd.to_datetime(row.get("trade_date")).date()
                ).first()

                if existing:
                    # 更新现有记录
                    existing.open = row.get("open")
                    existing.high = row.get("high")
                    existing.low = row.get("low")
                    existing.close = row.get("close")
                    existing.pre_close = row.get("pre_close")
                    existing.change = row.get("change")
                    existing.pct_chg = row.get("pct_chg")
                    existing.vol = row.get("vol", row.get("volume"))
                    existing.amount = row.get("amount")
                else:
                    # 插入新记录
                    record = StockDaily(
                        ts_code=row.get("ts_code"),
                        trade_date=pd.to_datetime(row.get("trade_date")).date(),
                        open=row.get("open"),
                        high=row.get("high"),
                        low=row.get("low"),
                        close=row.get("close"),
                        pre_close=row.get("pre_close"),
                        change=row.get("change"),
                        pct_chg=row.get("pct_chg"),
                        vol=row.get("vol", row.get("volume")),
                        amount=row.get("amount")
                    )
                    session.add(record)
                    saved_count += 1

            session.commit()
            logger.info(f"保存股票日线数据: 新增 {saved_count} 条，更新 {len(df) - saved_count} 条")
            return len(df)
        except Exception as e:
            session.rollback()
            logger.error(f"保存股票日线数据失败: {e}")
            raise
        finally:
            session.close()

    def get_stock_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        查询股票日线数据
        Query stock daily data

        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            股票日线数据 DataFrame
        """
        session = self.get_session()
        try:
            query = session.query(StockDaily).filter(StockDaily.ts_code == ts_code)

            if start_date:
                query = query.filter(StockDaily.trade_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
            if end_date:
                query = query.filter(StockDaily.trade_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

            query = query.order_by(StockDaily.trade_date)

            results = query.all()

            if not results:
                return None

            data = []
            for r in results:
                data.append({
                    "ts_code": r.ts_code,
                    "trade_date": r.trade_date,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "pre_close": r.pre_close,
                    "change": r.change,
                    "pct_chg": r.pct_chg,
                    "vol": r.vol,
                    "amount": r.amount
                })

            df = pd.DataFrame(data)
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df = df.set_index("trade_date")
            return df
        finally:
            session.close()

    # ==================== 指数数据操作 / Index Data Operations ====================

    def save_index_daily(self, df: pd.DataFrame) -> int:
        """
        保存指数日线数据（支持增量更新，避免重复）
        Save index daily data (supports incremental update, avoids duplicates)

        Args:
            df: 指数日线数据 DataFrame

        Returns:
            保存的记录数
        """
        if df.empty:
            return 0

        session = self.get_session()
        try:
            saved_count = 0
            for _, row in df.iterrows():
                # 检查是否存在
                existing = session.query(IndexDaily).filter(
                    IndexDaily.ts_code == row.get("ts_code"),
                    IndexDaily.trade_date == pd.to_datetime(row.get("trade_date")).date()
                ).first()

                if existing:
                    # 更新现有记录
                    existing.open = row.get("open")
                    existing.high = row.get("high")
                    existing.low = row.get("low")
                    existing.close = row.get("close")
                    existing.pre_close = row.get("pre_close")
                    existing.change = row.get("change")
                    existing.pct_chg = row.get("pct_chg")
                    existing.vol = row.get("vol")
                    existing.amount = row.get("amount")
                else:
                    # 插入新记录
                    record = IndexDaily(
                        ts_code=row.get("ts_code"),
                        trade_date=pd.to_datetime(row.get("trade_date")).date(),
                        open=row.get("open"),
                        high=row.get("high"),
                        low=row.get("low"),
                        close=row.get("close"),
                        pre_close=row.get("pre_close"),
                        change=row.get("change"),
                        pct_chg=row.get("pct_chg"),
                        vol=row.get("vol"),
                        amount=row.get("amount")
                    )
                    session.add(record)
                    saved_count += 1

            session.commit()
            logger.info(f"保存指数日线数据: 新增 {saved_count} 条，更新 {len(df) - saved_count} 条")
            return len(df)
        except Exception as e:
            session.rollback()
            logger.error(f"保存指数日线数据失败: {e}")
            raise
        finally:
            session.close()

    def get_index_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        查询指数日线数据
        Query index daily data

        Args:
            ts_code: 指数代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            指数日线数据 DataFrame
        """
        session = self.get_session()
        try:
            query = session.query(IndexDaily).filter(IndexDaily.ts_code == ts_code)

            if start_date:
                query = query.filter(IndexDaily.trade_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
            if end_date:
                query = query.filter(IndexDaily.trade_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

            query = query.order_by(IndexDaily.trade_date)

            results = query.all()

            if not results:
                return None

            data = []
            for r in results:
                data.append({
                    "ts_code": r.ts_code,
                    "trade_date": r.trade_date,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "pre_close": r.pre_close,
                    "change": r.change,
                    "pct_chg": r.pct_chg,
                    "vol": r.vol,
                    "amount": r.amount
                })

            df = pd.DataFrame(data)
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df = df.set_index("trade_date")
            return df
        finally:
            session.close()

    def get_latest_index_data(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的指数数据
        Get latest index data

        Args:
            ts_code: 指数代码

        Returns:
            最新指数数据字典
        """
        session = self.get_session()
        try:
            result = session.query(IndexDaily).filter(
                IndexDaily.ts_code == ts_code
            ).order_by(IndexDaily.trade_date.desc()).first()

            if result:
                return {
                    "ts_code": result.ts_code,
                    "trade_date": result.trade_date,
                    "close": result.close,
                    "pct_chg": result.pct_chg
                }
            return None
        finally:
            session.close()

    # ==================== 交易日历操作 / Trade Calendar Operations ====================

    def save_trade_calendar(self, df: pd.DataFrame) -> int:
        """
        保存交易日历数据
        Save trade calendar data

        Args:
            df: 交易日历数据 DataFrame

        Returns:
            保存的记录数
        """
        if df.empty:
            return 0

        session = self.get_session()
        try:
            records = []
            for _, row in df.iterrows():
                record = TradeCalendar(
                    exchange=row.get("exchange"),
                    cal_date=pd.to_datetime(row.get("cal_date")).date(),
                    is_open=row.get("is_open"),
                    pretrade_date=pd.to_datetime(row.get("pretrade_date")).date() if row.get("pretrade_date") else None
                )
                records.append(record)

            session.bulk_save_objects(records)
            session.commit()
            logger.info(f"保存交易日历数据 {len(records)} 条")
            return len(records)
        except Exception as e:
            session.rollback()
            logger.error(f"保存交易日历数据失败: {e}")
            raise
        finally:
            session.close()

    def is_trading_day(self, check_date: date = None, exchange: str = "SSE") -> bool:
        """
        判断是否为交易日
        Check if a date is a trading day

        Args:
            check_date: 检查日期，默认今天
            exchange: 交易所 SSE/SZSE

        Returns:
            是否为交易日
        """
        if check_date is None:
            check_date = date.today()

        session = self.get_session()
        try:
            result = session.query(TradeCalendar).filter(
                TradeCalendar.exchange == exchange,
                TradeCalendar.cal_date == check_date
            ).first()

            if result:
                return result.is_open == 1

            # 如果数据库中没有数据，默认周一到周五为交易日
            return check_date.weekday() < 5
        finally:
            session.close()

    def get_trading_days(
        self,
        start_date: str,
        end_date: str,
        exchange: str = "SSE"
    ) -> List[date]:
        """
        获取交易日列表
        Get list of trading days

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            exchange: 交易所

        Returns:
            交易日列表
        """
        session = self.get_session()
        try:
            results = session.query(TradeCalendar).filter(
                TradeCalendar.exchange == exchange,
                TradeCalendar.cal_date >= datetime.strptime(start_date, "%Y-%m-%d").date(),
                TradeCalendar.cal_date <= datetime.strptime(end_date, "%Y-%m-%d").date(),
                TradeCalendar.is_open == 1
            ).order_by(TradeCalendar.cal_date).all()

            return [r.cal_date for r in results]
        finally:
            session.close()

    # ==================== 股票基本信息操作 / Stock Basic Operations ====================

    def save_stock_basic(self, df: pd.DataFrame) -> int:
        """
        保存股票基本信息
        Save stock basic information

        Args:
            df: 股票基本信息 DataFrame

        Returns:
            保存的记录数
        """
        if df.empty:
            return 0

        session = self.get_session()
        try:
            records = []
            for _, row in df.iterrows():
                record = StockBasic(
                    ts_code=row.get("ts_code"),
                    symbol=row.get("symbol"),
                    name=row.get("name"),
                    area=row.get("area"),
                    industry=row.get("industry"),
                    market=row.get("market"),
                    list_date=pd.to_datetime(row.get("list_date")).date() if row.get("list_date") else None
                )
                records.append(record)

            # 使用 merge 避免重复
            for record in records:
                session.merge(record)

            session.commit()
            logger.info(f"保存股票基本信息 {len(records)} 条")
            return len(records)
        except Exception as e:
            session.rollback()
            logger.error(f"保存股票基本信息失败: {e}")
            raise
        finally:
            session.close()

    def get_stock_basic(self, ts_code: str = None) -> Optional[pd.DataFrame]:
        """
        查询股票基本信息
        Query stock basic information

        Args:
            ts_code: 股票代码，为空则查询所有

        Returns:
            股票基本信息 DataFrame
        """
        session = self.get_session()
        try:
            query = session.query(StockBasic)

            if ts_code:
                query = query.filter(StockBasic.ts_code == ts_code)

            results = query.all()

            if not results:
                return None

            data = []
            for r in results:
                data.append({
                    "ts_code": r.ts_code,
                    "symbol": r.symbol,
                    "name": r.name,
                    "area": r.area,
                    "industry": r.industry,
                    "market": r.market,
                    "list_date": r.list_date
                })

            return pd.DataFrame(data)
        finally:
            session.close()

    # ==================== 自选股操作 / Watchlist Operations ====================

    def add_to_watchlist(
        self,
        ts_code: str,
        name: str = None,
        group_name: str = "默认",
        remark: str = None
    ) -> bool:
        """
        添加股票到自选股
        Add stock to watchlist

        Args:
            ts_code: 股票代码
            name: 股票名称
            group_name: 分组名称
            remark: 备注

        Returns:
            是否添加成功
        """
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(Watchlist).filter(
                Watchlist.ts_code == ts_code
            ).first()

            if existing:
                logger.warning(f"股票 {ts_code} 已在自选股中")
                return False

            # 获取当前最大排序号
            max_order = session.query(Watchlist).filter(
                Watchlist.group_name == group_name
            ).count()

            # 添加新记录
            record = Watchlist(
                ts_code=ts_code,
                name=name or ts_code,
                group_name=group_name,
                sort_order=max_order,
                remark=remark
            )
            session.add(record)
            session.commit()
            logger.info(f"添加自选股: {ts_code} {name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"添加自选股失败: {e}")
            return False
        finally:
            session.close()

    def remove_from_watchlist(self, ts_code: str) -> bool:
        """
        从自选股中移除股票
        Remove stock from watchlist

        Args:
            ts_code: 股票代码

        Returns:
            是否移除成功
        """
        session = self.get_session()
        try:
            record = session.query(Watchlist).filter(
                Watchlist.ts_code == ts_code
            ).first()

            if record:
                session.delete(record)
                session.commit()
                logger.info(f"移除自选股: {ts_code}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"移除自选股失败: {e}")
            return False
        finally:
            session.close()

    def update_watchlist_name(self, ts_code: str, name: str) -> bool:
        """
        更新自选股名称
        Update watchlist stock name

        Args:
            ts_code: 股票代码
            name: 新的股票名称

        Returns:
            是否更新成功
        """
        session = self.get_session()
        try:
            record = session.query(Watchlist).filter(
                Watchlist.ts_code == ts_code
            ).first()

            if record:
                record.name = name
                session.commit()
                logger.info(f"更新自选股名称: {ts_code} -> {name}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新自选股名称失败: {e}")
            return False
        finally:
            session.close()

    def get_watchlist(self, group_name: str = None) -> List[Dict[str, Any]]:
        """
        获取自选股列表
        Get watchlist

        Args:
            group_name: 分组名称，为空则获取所有

        Returns:
            自选股列表
        """
        session = self.get_session()
        try:
            query = session.query(Watchlist)

            if group_name:
                query = query.filter(Watchlist.group_name == group_name)

            query = query.order_by(Watchlist.sort_order)
            results = query.all()

            return [
                {
                    "ts_code": r.ts_code,
                    "name": r.name,
                    "group_name": r.group_name,
                    "sort_order": r.sort_order,
                    "remark": r.remark,
                    "created_at": r.created_at
                }
                for r in results
            ]
        finally:
            session.close()

    def is_in_watchlist(self, ts_code: str) -> bool:
        """
        检查股票是否在自选股中
        Check if stock is in watchlist

        Args:
            ts_code: 股票代码

        Returns:
            是否在自选股中
        """
        session = self.get_session()
        try:
            count = session.query(Watchlist).filter(
                Watchlist.ts_code == ts_code
            ).count()
            return count > 0
        finally:
            session.close()

    def get_watchlist_groups(self) -> List[str]:
        """
        获取自选股分组列表
        Get watchlist groups

        Returns:
            分组名称列表
        """
        session = self.get_session()
        try:
            results = session.query(Watchlist.group_name).distinct().all()
            return [r[0] for r in results]
        finally:
            session.close()

    def update_watchlist_remark(self, ts_code: str, remark: str) -> bool:
        """
        更新自选股备注
        Update watchlist remark

        Args:
            ts_code: 股票代码
            remark: 备注内容

        Returns:
            是否更新成功
        """
        session = self.get_session()
        try:
            record = session.query(Watchlist).filter(
                Watchlist.ts_code == ts_code
            ).first()

            if record:
                record.remark = remark
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新自选股备注失败: {e}")
            return False
        finally:
            session.close()


# 全局数据库管理器实例 / Global database manager instance
db_manager = DatabaseManager()