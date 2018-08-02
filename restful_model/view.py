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
    LOGGER,
)
from .context import Context
# from .lru_cache import lru_cache

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
    def __init__(self, db: DataBase=None):
        self.db = db
        self.cache = {}

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
        if limit and not context.has_param:
            sql, sql_count = select_sql(
                self.__model__,
                where,
                filter_keys,
                keys,
                orders,
                limit,
                group,
                self.db.drivername()
            )
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
            sql = select_sql(
                self.__model__,
                where,
                filter_keys,
                keys,
                orders,
                limit,
                group,
                self.db.drivername()
            )
            async with self.db.engine.acquire() as conn:
                async with conn.execute(sql) as cursor:
                    if context.has_param:
                        data = model_to_dict(await cursor.first())
                    else:
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
        count, rowid = await self.db.execute_insert(sql)
        res = {
            'status': 201,
            'message': "Insert ok!",
            "meta": {
                "rowid": rowid if count == 1 else None,
                "count": count,
            },
        }
        return res

    async def delete(self, context: Context, filter_keys):
        """
        删除
        """
        form_data = context.form_data
        sql = delete_sql(self.__model__, form_data, filter_keys)
        count = await self.db.execute_dml(sql)
        return {
            'status': 200,
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
        data = form_data.get("data")
        sql = update_sql(self.__model__, form_data, filter_keys)
        count = await self.db.execute_dml(sql, data)
        return {
            'status': 201,
            'message': "Update ok!",
            "meta": {
                "count": count,
            },
        }

    async def patch(self, context: Context, filter_keys):
        """
        更新
        """
        return await self.put(context, filter_keys)
    # async def options(self, context, filter_keys):
        # return {}, {"Access-Control-Allow-Methods", ", ".join([m.upper() for m in self.__methods__])}

    async def dispatch_request(
        self,
        context: Context,
        method_filter=True,
        decorator_filter=True,
        key_filter=True,
    ):
        """
        分发请求
        """
        method = context.method
        if context.args and len(context.args) > 0:
            if method == "get":
                try:
                    for k in QUERY_ARGS:
                        if k in context.args:
                            context.form_data[k] = json.loads(context.args[k][0])
                except Exception:
                    pass
            if "method" in context.args:
                method = context.args["method"][0]
        if method_filter and self.__methods__ is not None and method not in self.__methods__:
            return {
                "status": 405,
                "message": "Method Not Allowed",
            }
        try:
            decorator_filters = self.generate_filter(method, decorator_filter)
            filter_keys = return_true
            if key_filter:
                if method in self.cache:
                    filter_keys = self.cache[method]
                else:
                    if self.__filter_keys__ is not None:
                        if isinstance(self.__filter_keys__, list):
                            filter_keys = get_filter_list(*self.__filter_keys__)
                        elif method in self.__filter_keys__:
                            filter_keys = get_filter_list(*self.__filter_keys__[method])
                    self.cache[method] = filter_keys

            async def next_handle():
                """
                中间件模式
                """
                handle, ok = next(decorator_filters)
                if ok:
                    return await handle(context, filter_keys)
                else:
                    return await handle(context, next_handle)
            return await next_handle()
        except Exception as e:
            LOGGER.error("view.BaseView.dispatch_request Error", exc_info=e)
            return {
                "status": 500,
                "message": "dispatch_request: " + str(e),
            }

    def generate_filter(self, method, decorator_filter):
        """
        把所有的方法都作为中间件处理

        :param method: 请求方法
        :param decorator_filter: 是否进行过滤
        :yield call: 
        """
        if decorator_filter:
            if hasattr(self, "auth_filter"):
                yield getattr(self, "auth_filter"), False
            filter_method_name = method + "_filter"
            if hasattr(self, filter_method_name):
                yield getattr(self, filter_method_name), False
        yield getattr(self, method), True

    async def raw_dispatch_request(self, context: Context):
        """
        跳过所有过滤器
        """
        return await self.dispatch_request(context, False, False, False)


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

        async def auth_filter(self, context: Context, next_filter):
            """
            过滤所有请求
            """
            if self.auth_model is None or self.verify_password is None:
                return await next_filter()
            sessions = context.sessions
            if sessions is not None:
                is_login = sessions.get(self.sessions_key, False)
                if is_login:
                    return await next_filter()
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
                            return await next_filter()
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

        async def auth_filter(self, context: Context, next_filter):
            """
            通过 Token 认证
            """
            if self.decode_token is None:
                return await next_filter()
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
                    return await next_filter()
            return UNAUTH
    return TokenAuthView
