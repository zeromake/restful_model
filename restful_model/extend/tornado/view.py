import json
import tornado.web
from restful_model.view import BaseView
from restful_model.context import Context


async def tornado_dispatch_request(self: "ApiView", *path_args, **kwargs):
    """
    分发请求
    """
    request = self.request
    args = {}
    raw_args = {}
    for k, v in request.query_arguments.items():
        val = [vv.decode() for vv in v]
        args[k] = val
        raw_args[k] = val[0]
    method = request.method.lower()
    if method != "get" and request.body and request.body != b"":
        form_data = json.loads(request.body)
    else:
        form_data = {}
    context = Context(
        method,
        request.path,
        request.headers,
        kwargs,
        form_data,
        args,
        raw_args,
        self.session if hasattr(self, "session") else None,
    )
    resp = await self.view.dispatch_request(context)
    self.set_header("Content-Type", "application/json; charset=utf-8")
    if isinstance(resp, tuple):
        h = None
        status = 200
        res = None
        for i in resp:
            if res is None:
                res = i
            elif isinstance(i, int):
                status = i
            elif isinstance(i, dict):
                h = i
        if h:
            for k, v in h:
                self.set_header(k, v)
        self.set_status(status)
        self.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
        return
    self.set_status(resp["status"])
    self.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

class ApiView(BaseView):

    @classmethod
    def as_view(cls, *args, **kwargs):
        """
        生成请求响应类
        """
        obj = cls(*args, **kwargs)
        class ApiHandler(tornado.web.RequestHandler):
            get = tornado_dispatch_request
            post = tornado_dispatch_request
            delete = tornado_dispatch_request
            put = tornado_dispatch_request
            patch = tornado_dispatch_request
            options = tornado_dispatch_request
            view = obj
        return ApiHandler
