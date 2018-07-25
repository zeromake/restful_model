import base64
import json

from .database import DataBase
from .utils import (
    select_sql,
    model_to_dict,
    insert_sql,
    delete_sql,
    update_sql,
    get_filter_list,
    return_true,
)
from .context import Context

QUERY_ARGS = ("keys", "where", "limit", "order", "group")
UNAUTH = {
    "status": 401,
    "message": "Default Unauthorized",
}

class BaseView(object):
    """
    基本视图
    """
    __model__ = None
    __methods__ = None
    __filter_keys__ = None

    """
    通用请求响应处理器
    """
    def __init__(self, db: DataBase):
        self.db = db

    async def get(self, context: Context, filter_keys):
        """
        GET 查询请求的统一调用
        """
        form_data = context.form_data
        keys = form_data.get("keys")
        where = form_data.get("where")
        limit = form_data.get("limit")
        orders = form_data.get("order")
        group = form_data.get("group")
        sql_count = None
        if limit:
            sql, sql_count = select_sql(self.__model__, where, filter_keys, keys, orders, limit, group)
            async with self.db.engine.acquire() as conn:
                async with conn.execute(sql_count) as cursor:
                    total = (await cursor.first())._count
                async with conn.execute(sql) as cursor:
                    data = await cursor.fetchall()
                    data = [model_to_dict(row) for row in data]
                return {
                    'status': 200,
                    'message': "Query ok!",
                    'data': data,
                    "meta": {
                        "pagination": {
                            "total": total,
                            "count": len(data),
                            'skip': limit[0],
                            'limit': limit[1]
                        }
                    }
                }
        else:
            sql = select_sql(self.__model__, where, filter_keys, keys, orders, limit, group)
            async with self.db.engine.acquire() as conn:
                async with conn.execute(sql) as cursor:
                    data = await cursor.fetchall()
                    data = [model_to_dict(row) for row in data]
                    return {
                        'status': 200,
                        'message': "Query ok!",
                        'data': data
                    }

    async def post(self, context: Context, filter_keys):
        """
        插入
        """
        form_data = context.form_data
        sql = insert_sql(self.__model__, form_data, filter_keys)
        count = await self.db.execute_dml(sql)
        return {
            'status': 201,
            'message': "Insert ok!",
            "meta": {
                "count": count,
            },
        }

    async def delete(self, context: Context, filter_keys):
        """
        删除
        """
        form_data = context.form_data
        sql = delete_sql(self.__model__, form_data, filter_keys)
        count = await self.db.execute_dml(sql)
        return {
            'status': 204,
            'message': "Delete ok!",
            "meta": {
                "count": count,
            },
        }

    async def put(self, context: Context, filter_keys):
        """
        更新
        """
        form_data = context.form_data
        values = form_data.get("values")
        data = form_data.get("data")
        sql = update_sql(self.__model__, values, filter_keys)
        count = await self.db.execute_dml(sql, data)
        return {
            'status': 201,
            'message': "Insert ok!",
            "meta": {
                "count": count,
            },
        }

    async def patch(self, context: Context, filter_keys):
        """
        更新
        """
        return await self.put(context, filter_keys)

    async def dispatch_request(self, context: Context):
        """
        分发请求
        """
        method = context.method

        if method == "get":
            try:
                for k in QUERY_ARGS:
                    if k in context.args:
                        context.form_data[k] = json.loads(context.args[k][0])
            except Exception:
                pass
        if context.url_path.endswith("/query") or context.url_path.endswith("/query/"):
            if method == "post":
                method = "get"
            else:
                return {
                    "status": 405,
                    "message": "Method Not Allowed",
                }
        if self.__methods__ is not None and method not in self.__methods__:
            return {
                "status": 405,
                "message": "Method Not Allowed",
            }
        try:
            if hasattr(self, "auth_filter"):
                filter_method = getattr(self, "auth_filter")
                res = await filter_method(context)
                if res is not None:
                    return res
            filter_method_name = method + "_filter"
            if hasattr(self, filter_method_name):
                filter_method = getattr(self, filter_method_name)
                res = await filter_method(context)
                if res is not None:
                    return res
            filter_keys = return_true
            if self.__filter_keys__ is not None:
                if isinstance(self.__filter_keys__, list):
                    filter_keys = get_filter_list(*self.__filter_keys__)
                elif method in self.__filter_keys__:
                    filter_keys = get_filter_list(*self.__filter_keys__[method])
            handle = getattr(self, method, None)
            return await handle(context, filter_keys)
        except Exception as e:
            # raise e
            return {
                "status": 500,
                "message": "dispatch_request: " + str(e),
            }

def generate_basic_auth_view(
        view,
        auth_model,
        name_key="user_name",
        pwd_key="password",
        verify_password=None,
        sessions_key="is_login",
    ):
    class BasicAuthView(view):
        """
        BasicAuth 认证视图
        如果有 sessions 在一次会话中会自动挂载key 到 sessions 防止 api 请求每次查询数据库
        """
        auth_model = auth_model
        name_key = name_key
        pwd_key = pwd_key
        verify_password = verify_password
        sessions_key = sessions_key

        async def auth_filter(self, context: Context):
            """
            过滤所有请求
            """
            if self.auth_model is None or self.verify_password is None:
                return None
            sessions = context.sessions
            if sessions is not None:
                is_login = sessions.get(self.sessions_key, False)
                if is_login:
                    return None
            headers = context.headers
            auth = headers.get("Authorization")
            if auth is None:
                return UNAUTH
            auth_str = base64.decodestring(auth)
            name, pwd = auth_str.split(":")
            sql = self.auth_model.select().where(self.auth_model[self.name_key] == name)
            async with self.db.engine.acquire() as conn:
                async with conn.execute(sql) as cursor:
                    row = await cursor.first()
                    if row is None:
                        return UNAUTH
                    password = row[self.pwd_key]
                    if self.verify_password(pwd, password):
                        if sessions is not None:
                            sessions[self.sessions_key] = True
                            return None
            return UNAUTH
    return BasicAuthView

def generate_token_auth_view(
        view,
        decode_token=None,
        sessions_key="token",
    ):
    class TokenAuthView(view):
        """
        通用 Token 认证视图
        """
        decode_token = decode_token
        sessions_key = sessions_key

        async def auth_filter(self, context: Context):
            """
            通过 Token 认证
            """
            if self.decode_token is None:
                return None
            sessions = context.sessions
            if sessions is not None and self.sessions_key is not None:
                token = sessions.get(self.sessions_key, "")
            else:
                headers = context.headers
                token = headers.get("Authorization")
            if token is None:
                return UNAUTH
            payload = self.decode_token(token)
            if payload is not None:
                context.payload = payload
                if sessions is not None and self.sessions_key is not None:
                    sessions[self.sessions_key] = token
                    return None
            return UNAUTH
    return TokenAuthView
