import json
import tornado.web
from restful_model.view import BaseView
from restful_model.context import Context

class ApiView(tornado.web.RequestHandler, BaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self, db):
        self.db = db
        self.cache = {}

    async def tornado_dispatch_request(self):
        """
        分发请求
        """
        request = self.request
        args = {k: [vv.decode() for vv in v] for k, v in request.query_arguments.items()}
        context = Context(
            request.method.lower(),
            request.path,
            request.headers,
            None,
            json.loads(request.body),
            args,
            None,
            self.session if hasattr(self, "session") else None,
        )
        resp = await self.dispatch_request(context)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
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
            self.write(json.dumps(res).encode())
            return
        self.set_status(resp["status"])
        self.write(json.dumps(resp).encode())

    get = tornado_dispatch_request
    post = tornado_dispatch_request
    put = tornado_dispatch_request
    patch = tornado_dispatch_request
    delete = tornado_dispatch_request
    options = tornado_dispatch_request
