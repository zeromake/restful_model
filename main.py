import asyncio
import tornado.ioloop
import tornado.web
from example.tornado.app import make_app
# from example.sanic.app import app

loop = asyncio.get_event_loop()

if __name__ == "__main__":
    # app.run(port=8000)
    app = loop.run_until_complete(make_app(loop))
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(1)
    tornado.ioloop.IOLoop.current().start()
