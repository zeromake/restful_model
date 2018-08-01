import tornado.ioloop
import tornado.web
import tornado.routing
from restful_model.extend.tornado import ApiView
from restful_model import DataBase
import sqlalchemy as sa
import asyncio

import logging
from datetime import datetime, timezone, timedelta

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


logging.basicConfig(level=logging.DEBUG)

UTC8 = timezone(timedelta(hours=8))

def to_timestamp(obj: datetime) -> int:
    """
    秒值
    """
    return int(obj.timestamp())

def get_offset_timestamp(zone=None, **kwargs) -> int:
    """
    获取偏移时间戳

    :param zone: 时区
    :param **kwargs: 时间偏移参数
    :returns: timestamp 该时区的秒
    """
    if zone is None:
        return to_timestamp(datetime.now(timezone.utc) + timedelta(**kwargs))
    return to_timestamp(datetime.now(zone).replace(tzinfo=timezone.utc) + timedelta(**kwargs))


class MainHandler(ApiView):
    __model__ = User

    __methods__ = {"post", "get", "put"}
    __filter_keys__ = {
        "post": ({"id",},),
        "get": ({"password",},),
        "put": ({"id",},),
    }
    async def post_filter(self, context, next_handle):
        now = get_offset_timestamp()
        if isinstance(context.form_data, dict):
            context.form_data["create_time"] = now
        else:
            for d in context.form_data:
                d["create_time"] = now
        return await next_handle()

async def make_app(loop):
    db = DataBase("sqlite:///db.db", loop)
    db.engine = await db.create_engine()
    userView = MainHandler.as_view(db)
    router = tornado.web.Application([
        ("/user", userView)
    ])
    return router

if __name__ == "__main__":
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(1)
    tornado.ioloop.IOLoop.current().start()
