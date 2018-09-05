import json
import asyncio
import sqlalchemy as sa

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

    def get_primary(self):
        """
        获取主键
        """
        for column in self.model.columns:
            if column.primary_key and isinstance(column.type, sa.Integer):
                return column

    @property
    def name(self):
        return self.model.name

    @property
    def model(self):
        return self.__model__

    def get_sql(self, context: Context):
        """
        分析请求生成sql
        """
        filter_keys = context.filter_keys
        form_data = context.form_data
        keys = form_data.get("keys")
        where = form_data.get("where")
        limit = form_data.get("limit")
        orders = form_data.get("order")
        group = form_data.get("group")
        return select_sql(
            self.model,
            where,
            filter_keys,
            keys,
            orders,
            None if context.has_param else limit,
            group,
            self.db.drivername()
        )

    async def get(self, context: Context):
        """
        GET 查询请求的统一调用
        """
        # filter_keys = context.filter_keys
        form_data = context.form_data
        limit = form_data.get("limit")
        sql_arr = self.get_sql(context)
        if isinstance(sql_arr, tuple):
            sql, sql_count = sql_arr
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
            sql = sql_arr
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

    def post_sql(self, context: Context):
        """
        分析请求生成sql
        """
        filter_keys = context.filter_keys
        form_data = context.form_data
        return insert_sql(self.model, form_data, filter_keys)

    async def post(self, context: Context):
        """
        插入
        """
        # filter_keys = context.filter_keyss
        sql = self.post_sql(context)
        count, rowid = await self.db.execute_insert(sql)
        res = {
            'status': 201,
            'message': "Insert ok!",
            "meta": {
                "count": count,
            },
        }
        if count == 1:
            res["meta"]["rowid"] = rowid
        return res

    def delete_sql(self, context: Context):
        """
        分析请求生成sql
        """
        # filter_keys = context.filter_keys
        form_data = context.form_data
        return delete_sql(self.model, form_data)

    async def delete(self, context: Context):
        """
        删除
        """
        # filter_keys = context.filter_keys
        sql = self.delete_sql(context)
        count = await self.db.execute_dml(sql)
        return {
            'status': 200,
            'message': "Delete ok!",
            "meta": {
                "count": count,
            },
        }

    async def put(self, context: Context):
        """
        更新
        """
        # filter_keys = context.filter_keys
        form_data = context.form_data
        data = form_data.get("data")
        sql = update_sql(self.model, form_data)
        count = await self.db.execute_dml(sql, data)
        return {
            'status': 201,
            'message': "Update ok!",
            "meta": {
                "count": count,
            },
        }

    async def dispatch_request(
        self,
        context: Context,
        method_filter=True,
        decorator_filter=True,
        key_filter=True,
        generate_sql=False,
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
                            context.form_data[k] = json.loads(
                                context.args[k][0]
                            )
                except Exception:
                    pass
            if "method" in context.args:
                method = context.args["method"][0]
        flag = method_filter and self.__methods__ is not None
        if flag and method not in self.__methods__:
            return {
                "status": 405,
                "message": "Method Not Allowed: %s" % method,
            }
        try:
            decorator_filters = self.generate_filter(
                method,
                decorator_filter,
                generate_sql,
            )
            filter_keys = return_true
            if key_filter:
                if method in self.cache:
                    filter_keys = self.cache[method]
                else:
                    if self.__filter_keys__ is not None:
                        if isinstance(self.__filter_keys__, list):
                            filter_keys = get_filter_list(
                                *self.__filter_keys__
                            )
                        elif method in self.__filter_keys__:
                            filter_keys = get_filter_list(
                                *self.__filter_keys__[method]
                            )
                    self.cache[method] = filter_keys

            async def next_handle():
                """
                中间件模式
                """
                handle, ok = next(decorator_filters)
                if handle is None:
                    return {
                        "status": 405,
                        "message": "Method Not Allowed: %s" % method,
                    }
                if ok:
                    res = handle(context)
                else:
                    res = handle(context, next_handle)
                if asyncio.iscoroutine(res):
                    return await res
                return res
            context.filter_keys = filter_keys
            return await next_handle()
        except Exception as e:
            LOGGER.error("view.BaseView.dispatch_request Error", exc_info=e)
            error = str(e)
            return {
                "status": 500,
                "message": "dispatch_request: " + error,
            }

    def generate_filter(self, method, decorator_filter, generate_sql=False):
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
        if generate_sql:
            method += "_sql"
        yield getattr(self, method, None), True

    async def raw_dispatch_request(self, context: Context):
        """
        跳过所有过滤器
        """
        return await self.dispatch_request(context, False, False, False)

    async def options(self, context: Context):
        return {}, 200

    patch = put
    # options = get
