import logging
import asyncio
import pytest
import sqlalchemy as sa
from sqlalchemy.sql.expression import bindparam
from urllib.parse import quote_plus as urlquote, unquote_plus
from datetime import datetime, timezone, timedelta
from restful_model import DataBase
from restful_model.utils import model_to_dict
from .model import User

logging.basicConfig(level=logging.DEBUG)

def to_timestamp(obj: datetime) -> int:
    """
    毫秒值
    """
    return int(obj.timestamp())

def get_offset_timestamp(**kwargs) -> int:
    """
    获取偏移时间戳
    """
    return to_timestamp(datetime.now(timezone.utc) + timedelta(**kwargs))

@pytest.mark.asyncio
async def test_create_engine(data_bese, db_name) -> None:
    # db = urlquote(":memory:")
    data = DataBase(data_bese, asyncio.get_event_loop())
    assert data._url.database == db_name
    if data.drivername() == "sqlite":
        assert not data._url.username
        assert not data._url.host
        assert not data._url.port
        assert not data._url.password
    else:
        assert data._url.username is not None
        assert data._url.host is not None
        assert data._url.port is not None
        assert data._url.password is not None
    data.engine = await data.create_engine(echo=True)
    assert data.engine is not None
    if await data.exists_table("user"):
        await data.drop_table(User)
    await data.create_table(User)
    assert await data.exists_table("user")
    await data.drop_table(User)
    assert not await data.exists_table("user")
    await data.create_tables([User])
    assert await data.exists_table("user")
    await data.drop_tables([User])
    assert not await data.exists_table("user")

    async with data.engine.acquire() as conn:
        async with conn.begin():
            await data.create_table(User, conn)
            assert await data.exists_table("user", conn)
            await data.drop_table(User, conn)
            assert not await data.exists_table("user", conn)


@pytest.mark.asyncio
async def test_execute_sql(data_bese) -> None:
    # db = urlquote(":memory:")
    data = DataBase(data_bese, asyncio.get_event_loop())
    # data = DataBase("mysql+pymysql://aiomysql:mypass@127.0.0.1:3306/test_pymysql", asyncio.get_event_loop())
    data.engine = await data.create_engine(echo=True)
    if await data.exists_table("user"):
        await data.drop_table(User)
    await data.create_table(User)
    user1 = {
        "account": "test1",
        "role_name": "test1",
        "email": "test1@test.com",
        "password": "12345678",
        "create_time": get_offset_timestamp(),
    }
    sql = User.insert().values(user1)
    assert 1 == await data.execute_dml(sql)
    user2 = {
        "account": "test2",
        "role_name": "test2",
        "email": "test2@test.com",
        "password": "12345678",
        "create_time": get_offset_timestamp(),
    }
    sql2 = User.insert().values(user2)
    assert 2 == await data.execute_dml([sql, sql2])
    sql = User.select().where(User.c.id == 1)
    async with data.engine.acquire() as conn:
        async with conn.begin():
            async with conn.execute(sql) as cursor:
                user1["id"] = 1
                assert user1 == model_to_dict(await cursor.first())
            sql = User.select().where(User.c.id == 2)
            async with conn.execute(sql) as cursor:
                user1["id"] = 2
                assert user1 == model_to_dict(await cursor.first())
            
            sql = User.select().where(User.c.id == 3)
            async with conn.execute(sql) as cursor:
                user2["id"] = 3
                assert user2 == model_to_dict(await cursor.first())
            sql1 = User.update().where(User.c.id == bindparam("id")).values({
                "account": bindparam("account"),
            })
            async with conn.execute(sql1, {"id": 1, "account": "gggg"}) as cursor:
                assert 1 == cursor.rowcount
            sql = User.select().where(User.c.id == 1)
            async with conn.execute(sql) as cursor:
                user1["id"] = 1
                user1["account"] = "gggg"
                assert user1 == model_to_dict(await cursor.first())
            if data.drivername == "sqlite":
                async with conn.execute(sql1, [{"id": 1, "account": "test5"}, {"id": 2, "account": "test6"}] ) as cursor:
                    assert 2 == cursor.rowcount
                sql = User.select().where(User.c.id < 3)
                async with conn.execute(sql) as cursor:
                    user1["id"] = 1
                    user1["account"] = "test5"
                    assert user1 == model_to_dict(await cursor.fetchone())
                    user1["id"] = 2
                    user1["account"] = "test6"
                    assert user1 == model_to_dict(await cursor.fetchone())
    await data.drop_table(User)
