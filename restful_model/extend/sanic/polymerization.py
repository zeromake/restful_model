
from restful_model import BasePolymerization, Context
from sanic import response


class PolymerizationView(BasePolymerization):
    decorators = None

    async def sanic_dispatch_request(self, request, method, *args, **kwargs):
        session = request["session"] if "session" in request else None
        content = Context(
            method,
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
        return response.json(
            resp,
            headers={"Content-Type": "application/json;charset=utf-8"},
            status=resp["status"],
        )

    def as_view(self, method: str):
        """
        生成对应的操作view
        """
        async def view(request, *args, **kwargs):
            return await self.sanic_dispatch_request(
                request,
                method,
                *args,
                **kwargs
            )
        return view

    # @classmethod
    # def as_view(cls, *class_args, **class_kwargs):
    #     """
    #     创建一个对象
    #     """
    #     self = cls(*class_args, **class_kwargs)

    #     async def view(*args, **kwargs):
    #         return await self.sanic_dispatch_request(*args, **kwargs)

    #     if cls.decorators:
    #         view.__module__ = cls.__module__
    #         for decorator in cls.decorators:
    #             view = decorator(view)
    #     # view._view_class = cls
    #     view.view = self
    #     view.__doc__ = cls.__doc__
    #     view.__module__ = cls.__module__
    #     view.__name__ = cls.__name__
    #     return view
