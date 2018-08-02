import asyncio
import sys

def run_tornado():
    import tornado.ioloop
    import tornado.web
    from example.tornado.app import make_app
    loop = tornado.ioloop.IOLoop.current()
    app = loop.run_sync(make_app)
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(1)
    loop.start()

def run_sanic():
    from example.sanic.app import app
    app.run(port=8000)


# import multiprocessing
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# loop = asyncio.get_event_loop()

if __name__ == "__main__":
    arg = sys.argv[1]
    if arg == "s":
        run_sanic()
    elif arg == "t":
        run_tornado()
    # app.run(port=8000)
    # workers = multiprocessing.cpu_count() * 2
