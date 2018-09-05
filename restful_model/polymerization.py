from typing import Dict
from .context import Context
from .view import BaseView
from .utils import LOGGER, inject_value


async def execute_request(self, method: str, form_data):
    """
    集中处理
    """
    all_count = 0
    async with self.db.engine.acquire() as conn:
        async with conn.begin() as t:
            for item in form_data:
                view_name = item["name"]
                if view_name not in self.views:
                    continue
                view: BaseView = self.views[view_name]
                data = item["data"]
                ctx = Context(method, form_data=data)
                sql = await view.dispatch_request(
                    ctx,
                    generate_sql=True,
                )
                if isinstance(sql, (dict, tuple)):
                    await t.rollback()
                    return sql
                count = await self.db.execute_dml(
                    sql,
                    conn=conn,
                )
                all_count += count
    return {
        'status': 200,
        'message': "polymerization %s ok!" % method,
        "meta": {
            "count": all_count,
        }
    }


class BasePolymerization(object):
    """
    聚合
    """
    def __init__(self, db):
        self.db = db
        self.views: Dict[str, BaseView] = {}

    def add_view(self, view: BaseView):
        """
        添加
        """
        self.views[view.name] = view

    async def dispatch_request(self, context):
        """
        分发请求
        """
        request_method_name = context.method + "_request"
        if hasattr(self, request_method_name):
            try:
                return await getattr(self, request_method_name)(context)
            except Exception as e:
                LOGGER.error(
                    "view.BaseView.dispatch_request Error",
                    exc_info=e
                )
                error = str(e)
                return {
                    "status": 500,
                    "message": "polymerization dispatch_request: " + error,
                }
        return {"status": 405, "message": "Method Not Allowed!"}

    async def post_request(self, context):
        """
        多表创建或连接表创建
        """
        form_data = context.form_data
        cache = {}
        all_count = 0
        async with self.db.engine.acquire() as conn:
            async with conn.begin() as t:
                # 也许需要进行两次循环一次做依赖处理循环并根据依赖关系排序
                # 第二次直接开启事务并缓存之前插入的数据
                for item in form_data:
                    view_name = item["name"]
                    if view_name not in self.views:
                        continue
                    view: BaseView = self.views[view_name]
                    data = item["data"]
                    if isinstance(data, list):
                        for i in data:
                            for k, v in i.items():
                                if isinstance(v, str) and v[0] == "$":
                                    i[k] = inject_value(v, cache)
                    else:
                        for k, v in data.items():
                            if isinstance(v, str) and v[0] == "$":
                                data[k] = inject_value(v, cache)
                    ctx = Context("post", form_data=data)
                    sql = await view.dispatch_request(
                        ctx,
                        generate_sql=True,
                    )
                    if isinstance(sql, (dict, tuple)):
                        await t.rollback()
                        return sql
                    count, rowid = await self.db.execute_insert(
                        sql,
                        conn,
                    )
                    has_rowid = count == 1 and rowid > 0
                    all_count += count
                    primary_key = view.get_primary()
                    if has_rowid and primary_key is not None:
                        if isinstance(data, list):
                            data[0][primary_key.name] = rowid
                        else:
                            data[primary_key.name] = rowid
                    cache[view.name] = data
        return {
            "status": 201,
            "message": "Inserts Ok!",
            "meta": {"count": all_count}
        }

    async def delete_request(self, context):
        """
        删除
        """
        form_data = context.form_data
        return await execute_request(self, "delete", form_data)

    async def put_request(self, context):
        """
        修改
        """
        form_data = context.form_data
        return await execute_request(self, "put", form_data)

    async def patch_request(self, context):
        form_data = context.form_data
        return await execute_request(self, "patch", form_data)
