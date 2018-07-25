from restful_model.view import BaseView
from restful_model.context import Context
from sanic import response

class ApiView(BaseView):
    decorators = None
    async def sanic_dispatch_request(self, request, *args, **kwargs):
        session = request["session"] if "session" in request else None
        content = Context(
            request.method.lower(),
            request.path,
            request.headers,
            kwargs,
            request.json,
            request.args,
            request.raw_args,
            session,
        )
        resp = await self.dispatch_request(content)
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
            return response.json(res, headers=h, status=status)
        return response.json(resp, headers={"Content-Type": "application/json;charset=utf-8"}, status=resp["status"])

    @classmethod
    def as_view(cls, *class_args, **class_kwargs):
        self = cls(*class_args, **class_kwargs)
        async def view(*args, **kwargs):
            return await self.sanic_dispatch_request(*args, **kwargs)
        if cls.decorators:
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)
        view._view_class = cls
        view.self = self
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.__name__ = cls.__name__
        return view
