import pytest
import asyncio

from datetime import datetime

from .model import User
from restful_model.view import BaseView
from restful_model.context import Context
from restful_model.database import DataBase
from restful_model.utils import return_true
from urllib.parse import quote_plus as urlquote

class ApiView(BaseView):
    __model__ = User

@pytest.mark.asyncio
async def test_view_query():
    """
    测试view的查询
    """
    db_name = urlquote(":memory:")
    db = DataBase("sqlite:///%s" % db_name, asyncio.get_event_loop())
    db.engine = await db.create_engine(echo=True)
    api = ApiView(db)
    await db.create_table(User)
    query_context = Context("get", "/user", {})
    assert {"status": 200, "message": "Query ok!", "data": []} == await api.get(query_context, return_true)
    user1 = {
        "account": "test1",
        "email": "test1@test.com",
        "role_name": "昵称1",
        "password": "123456",
        "create_time": int(datetime.now().timestamp()),
    }
    create_context = Context("post", "", {}, form_data=user1)
    assert {
        "status": 201,
        "message": "Insert ok!",
        "meta": {"count": 1, "rowid": 1}
    } == await api.post(create_context, return_true)
    # context = Context("get", "/user", {})
    user1["id"] = 1
    assert {"status": 200, "message": "Query ok!", "data": [user1]} == await api.get(query_context, return_true)
