import asyncio
import pytest
from urllib.parse import quote_plus as urlquote, unquote_plus
from restful_model.database import DataBase
import logging

import sqlalchemy as sa

logging.basicConfig(level=logging.DEBUG)

metadata = sa.MetaData()
User = sa.Table(
    'user',
    metadata,
    sa.Column(
        'id',
        sa.Integer,
        autoincrement=True,
        primary_key=True,
        nullable=False,
        doc="主键"
    ),
    sa.Column(
        'account',
        sa.String(16),
        nullable=False,
        doc="帐号"
    ),
    sa.Column(
        'role_name',
        sa.String(16),
        nullable=False,
        doc="昵称"
    ),
    sa.Column(
        'email',
        sa.String(256),
        nullable=False,
        doc="邮箱"
    ),
    sa.Column(
        'password',
        sa.String(128),
        nullable=False,
        doc="密码"
    ),
    sa.Column(
        "create_time",
        sa.BigInteger,
        nullable=False,
        doc="创建时间"
    ),
    sqlite_autoincrement=True,
)

@pytest.mark.asyncio
async def test_create_engine() -> None:
    db = urlquote(":memory:")
    data = DataBase("sqlite:///%s" % db, asyncio.get_event_loop())
    assert data._url.database == ":memory:"
    assert not data._url.username
    assert not data._url.host
    assert not data._url.port
    assert not data._url.password
    data.engine = await data.create_engine(echo=True)
    assert data.engine is not None
    await data.create_table(User)
    assert await data.exists_table("user")
