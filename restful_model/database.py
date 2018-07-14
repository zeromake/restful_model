import asyncio
import sqlalchemy as sa
from sqlalchemy.sql.ddl import CreateTable, DropTable
from typing import List, Optional, cast
from urllib.parse import unquote_plus

DRIVER_NAME = (
    "sqlite",
    "mysql",
    "postgresql"
)


class DataBase(object):
    """
    orm 统一数据库切换器，支持 sqlite, mysql, pg
    """
    def __init__(self, database: str, loop=None) -> None:
        self._url = sa.engine.url.make_url(database)
        if "%" in self._url.database:
            self._url.database = unquote_plus(self._url.database)
        self._driver: Optional[str] = None
        self._load_driver()
        self._loop = loop or asyncio.get_event_loop()
        # self._tables = tables
        self.engine = None

    def _load_driver(self) -> None:
        """
        加载driver
        """
        for name in DRIVER_NAME:
            if self._url.drivername.startswith(name):
                self._driver = name
                break
    
    async def create_engine(self, *args, **kwargs) -> None:
        """
        创建engine
        """
        if self.engine is not None:
            return
        loop = self._loop
        if self._driver == "sqlite":
            from aiosqlite3.sa import create_engine
            # init = os.path.exists(self._url.database)
            engine = await create_engine(
                self._url.database,
                loop=loop,
                *args,
                **kwargs,
            )
        elif self._driver == "mysql":
            from aiomysql.sa import create_engine
            engine = await create_engine(
                user=self._url.username,
                db=self._url.database,
                host=self._url.host,
                password=self._url.password,
                port=self._url.port,
                loop=loop
                *args,
                **kwargs,
            )
        elif self._driver == "postgresql":
            from aiopg.sa import create_engine
            engine = await create_engine(
                user=self._url.username,
                database=self._url.database,
                host=self._url.host,
                port=self._url.port,
                password=self._url.password,
                loop=loop,
                *args,
                **kwargs,
            )
        self.engine = engine
    
    def create_table_sql(self, table: 'sa.Table') -> CreateTable:
        """
        生成创建表的 sql
        """
        return CreateTable(table)

    async def create_table(self, table: 'sa.Table', conn=None) -> None:
        """
        创建一个表
        """
        if conn is None:
            async with self.engine.acquire() as conn:
                await conn.execute(self.create_table_sql(table))
        else:
            await conn.execute(self.create_table_sql(table))

    async def create_tables(self, tables: List['sa.Table']) -> None:
        """
        创建多个表
        """
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                try:
                    for table in tables:
                        return await conn.execute(self.create_table_sql(table))
                except Exception as e:
                    await transaction.close()
                    raise e
    
    def drop_table_sql(self, table: 'sa.Table') -> DropTable:
        """
        生成删除表的sql语句
        """
        return DropTable(table)

    async def drop_table(self, table: 'sa.Table', conn=None) -> None:
        """
        删除表
        """
        if conn is None:
            async with engine.acquire() as conn:
                return await conn.execute(self.drop_table_sql(table))
        else:
            await conn.execute(self.drop_table_sql(table))


    async def drop_tables(self, tables: List['sa.Table']) -> None:
        """
        删除多个表
        """
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                try:
                    for table in tables:
                        await conn.execute(self.drop_table_sql(table))
                except Exception as e:
                    await transaction.close()
                    raise e

    async def exists_table(self, table_name: str, conn=None) -> bool:
        """
        手动使用各个数据库的专有 sql 查询 table 是否存在
        """
        sql = None
        if self._driver == "sqlite":
            sql = "SELECT name FROM sqlite_master where type='table' and name='%s'" % table_name
        elif self._driver == "mysql":
            sql = "SELECT TABLE_NAME FROM information_schema.TABLES "\
            "WHERE TABLE_NAME ='%s' AND TABLE_SCHEMA = '%s'" % (table_name, self._url.database)
        elif self._driver == "postgresql":
            sql = "SELECT relname FROM pg_class WHERE relname = '%s'" % table_name
        if conn is None:
            async with self.engine.acquire() as conn:
                result = await conn.execute(sql)
                first = await result.first()
        else:
            result = await conn.execute(sql)
            first = await result.first()
        return first != None

    async def get_last_id(self, key="id", conn=None, cursor=None):
        """
        获取最后的id, pg需要传入cursor
        """
        sql = None
        if self._driver == "sqlite":
            sql = "SELECT last_insert_rowid() as id"
        elif self._driver == "mysql":
            sql = "SELECT LAST_INSERT_ID() as id"
        elif self._driver == "postgresql":
            if cursor is not None:
                result = await cursor.first()
                if not result is None:
                    return result[0]
        if sql:
            if conn is None:
                async with self.engine.acquire() as conn:
                    cursor = await conn.execute(sql)
                    return getattr((await cursor.first()), key)
            else:
                cursor = await conn.execute(sql)
                return getattr((await cursor.first()), key)