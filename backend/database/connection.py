"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from pathlib import Path
import logging

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 默认数据库路径
            db_path = Path(__file__).parent.parent / "data" / "app.db"
            db_path.parent.mkdir(exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        
        # SQLite 特殊配置
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                poolclass=StaticPool,
                pool_pre_ping=True,
                connect_args={
                    "check_same_thread": False,  # SQLite 多线程支持
                    "timeout": 20  # 超时设置
                },
                echo=False  # 设为 True 可以看到 SQL 语句
            )
        else:
            self.engine = create_engine(database_url, pool_pre_ping=True)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建表
        self.create_tables()
    
    def create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表（慎用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_sync_session(self) -> Session:
        """获取同步数据库会话（需要手动关闭）"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# 全局数据库管理器实例
_db_manager = None

def get_database_manager(database_url: str = None) -> DatabaseManager:
    """获取数据库管理器单例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager

def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话（用于依赖注入）"""
    db_manager = get_database_manager()
    yield from db_manager.get_session()

def init_database(database_url: str = None, force_recreate: bool = False) -> DatabaseManager:
    """初始化数据库"""
    global _db_manager
    
    if force_recreate and _db_manager:
        _db_manager.drop_tables()
        _db_manager = None
    
    _db_manager = get_database_manager(database_url)
    
    if not _db_manager.test_connection():
        raise Exception("Failed to initialize database connection")
    
    logger.info(f"Database initialized: {_db_manager.database_url}")
    return _db_manager