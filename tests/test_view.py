import pytest
import copy

from datetime import datetime

from .model import User
from restful_model import BaseView, Context
from restful_model.utils import return_true


class ApiView(BaseView):
    __model__ = User


async def insert_user(api: "ApiView"):
    user1 = {
        "account": "test1",
        "email": "test1@test.com",
        "role_name": "昵称1",
        "password": "123456",
        "create_time": int(datetime.now().timestamp()),
    }
    create_context = Context("post", "", {}, form_data=user1)
    create_context.filter_keys = return_true
    assert {
        "status": 201,
        "message": "Insert ok!",
        "meta": {"count": 1, "rowid": 1}
    } == await api.post(create_context)
    # context = Context("get", "/user", {})
    user1["id"] = 1
    query_context = Context("get", "/user", {})
    query_context.filter_keys = return_true
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1]
    } == await api.get(query_context)
    del user1["id"]
    return user1


@pytest.mark.asyncio
async def test_options(db):
    """
    测试options
    """
    api = ApiView(db)
    assert ({}, 200) == await api.options(None)


@pytest.mark.asyncio
async def test_view_query(db):
    """
    测试view的查询
    """
    # db = await build_db()
    api = ApiView(db)
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    query_context = Context("get", "/user", {})
    query_context.filter_keys = return_true
    assert repr(query_context).startswith("<Context ")
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": []
    } == await api.get(query_context)
    user1 = {
        "account": "test1",
        "email": "test1@test.com",
        "role_name": "昵称1",
        "password": "123456",
        "create_time": int(datetime.now().timestamp()),
    }
    create_context = Context("post", "", {}, form_data=user1)
    create_context.filter_keys = return_true
    assert {
        "status": 201,
        "message": "Insert ok!",
        "meta": {"count": 1, "rowid": 1}
    } == await api.post(create_context)
    # context = Context("get", "/user", {})
    user1["id"] = 1
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1]
    } == await api.get(query_context)
    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_create(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    user1 = await insert_user(api)
    user2 = copy.copy(user1)
    user3 = copy.copy(user1)
    user2["account"] = "test2"
    user3["account"] = "test3"
    create_context2 = Context("post", "", {}, form_data=[user2, user3])
    count = 2
    create_context2.filter_keys = return_true
    # elif db.drivername() == "postgresql":
    #     count = 0
    assert {
        "status": 201,
        "message": "Insert ok!",
        "meta": {"count": count}
    } == await api.post(create_context2)
    user1["id"] = 1
    user2["id"] = 2
    user3["id"] = 3
    query_context = Context("get", "/user", {})
    query_context.filter_keys = return_true
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1, user2, user3]
    } == await api.get(query_context)

    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_delete(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    await insert_user(api)
    query_context = Context("get", "/user", {})
    query_context.filter_keys = return_true
    delete_context = Context(
        "delete",
        "",
        {},
        form_data={"id": 1},
        url_param={"id": 1}
    )
    delete_context.filter_keys = return_true
    assert {
        "status": 200,
        "message": "Delete ok!",
        "meta": {"count": 1}
    } == await api.delete(delete_context)
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": []
    } == await api.get(query_context)
    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_update(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    user1 = await insert_user(api)
    user2 = copy.copy(user1)
    user2["account"] = "test2"
    put_context = Context(
        "put",
        "",
        {},
        form_data={
            "where": {"id": 1},
            "values": {"account": "test2"},
        },
    )
    put_context.filter_keys = return_true
    assert {
        "status": 201,
        "message": "Update ok!",
        "meta": {"count": 1}
    } == await api.put(put_context)
    user2["id"] = 1
    query_context = Context("get", "/user", {})
    query_context.filter_keys = return_true
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user2]
    } == await api.get(query_context)
    count = 0
    if db.drivername() in ("sqlite", "postgresql"):
        count = 1
    assert {
        "status": 201,
        "message": "Update ok!",
        "meta": {"count": count}
    } == await api.patch(put_context)
    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_name(db):
    api = ApiView(db)
    assert api.name == User.name


@pytest.mark.asyncio
async def test_generate_sql(db):
    api = ApiView(db)
    query_context = Context("get", "/user", {})
    await api.dispatch_request(query_context, generate_sql=True)


@pytest.mark.asyncio
async def test_view_query2(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    user1 = await insert_user(api)
    query_context1 = Context("get", "/user", {}, url_param={"id": 1})
    user1["id"] = 1
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": user1
    } == await api.dispatch_request(query_context1, return_true)
    query_context2 = Context("get", "/user", {}, form_data={"limit": [0, 10]})
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
        "meta": {
            "pagination": {
                "total": 1,
                "count": 1,
                'skip': 0,
                'limit': 10
            }
        }
    } == await api.dispatch_request(
        query_context2,
        return_true
    )
    query_context3 = Context(
        "get",
        "/user",
        {},
        args={"limit": ["[0, 10]"], "order": ["00000"]}
    )
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
        "meta": {
            "pagination": {
                "total": 1,
                "count": 1,
                'skip': 0,
                'limit': 10
            }
        }
    } == await api.dispatch_request(query_context3, return_true)

    query_context3 = Context("post", "/user", {}, args={"method": ["get"]})
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
    } == await api.dispatch_request(query_context3, return_true)
    await db.drop_table(User)


UNAUTH = {"status": 401, "message": "UNAUTH"}


@pytest.mark.asyncio
async def test_view_auth_filter(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)

    async def auth_filter(context: "Context", next_handle):
        return UNAUTH
    api.auth_filter = auth_filter
    query_context = Context("get", "/user", {})
    assert UNAUTH == await api.dispatch_request(
        query_context,
        decorator_filter=True
    )
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [],
    } == await api.dispatch_request(
        query_context,
        decorator_filter=False
    )
    del api.auth_filter
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [],
    } == await api.dispatch_request(
        query_context,
        decorator_filter=True
    )
    api.get_filter = auth_filter
    assert UNAUTH == await api.dispatch_request(
        query_context,
        decorator_filter=True
    )
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [],
    } == await api.dispatch_request(
        query_context,
        decorator_filter=False
    )

    self_error = TypeError("self error")

    async def try_error(context, next_handle):
        raise self_error

    api.auth_filter = try_error
    # with pytest.raises(self_error):
    assert {
        "status": 500,
        "message": "dispatch_request: self error",
    } == await api.dispatch_request(query_context, decorator_filter=True)
    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_method_filter(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    api.__methods__ = {"post"}
    query_context = Context("get", "/user", {})
    assert {
        "status": 405,
        "message": "Method Not Allowed: get",
    } == await api.dispatch_request(query_context, method_filter=True)
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [],
    } == await api.raw_dispatch_request(query_context)
    del api.__methods__
    context = Context("gett", "/user", {})
    assert {
        "status": 405,
        "message": "Method Not Allowed: gett",
    } == await api.dispatch_request(context)
    await db.drop_table(User)


@pytest.mark.asyncio
async def test_view_keys_filter(db):
    # db = await build_db()
    if await db.exists_table("user"):
        await db.drop_table(User)
    await db.create_table(User)
    api = ApiView(db)
    user1 = await insert_user(api)

    api.__filter_keys__ = ["id"]

    query_context = Context("get", "/user", {})

    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
    } == await api.dispatch_request(query_context)
    user1["id"] = 1
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
    } == await api.dispatch_request(query_context, key_filter=False)
    api.__filter_keys__ = {"get": ["id"]}
    api.cache = {}
    del user1["id"]
    assert {
        "status": 200,
        "message": "Query ok!",
        "data": [user1],
    } == await api.dispatch_request(query_context)
    await db.drop_table(User)
