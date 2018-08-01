import asyncio
import tornado.ioloop
import tornado.web
from example.tornado.app import make_app
import uvloop 
# from example.sanic.app import app
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

if __name__ == "__main__":
    # app.run(port=8000)
    app = loop.run_until_complete(make_app(loop))
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(1)
    tornado.ioloop.IOLoop.current().start()
