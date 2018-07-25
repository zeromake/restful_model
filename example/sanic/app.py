from sanic import Sanic
from sanic.constants import HTTP_METHODS
from restful_model import DataBase
from restful_model.extend.sanic.view import ApiView
from .model import User
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.DEBUG)

def to_timestamp(obj: datetime) -> int:
    """
    毫秒值
    """
    return int(obj.timestamp())

def get_offset_timestamp(**kwargs) -> int:
    """
    获取偏移时间戳
    """
    return to_timestamp(datetime.now(timezone.utc) + timedelta(**kwargs))

class UserView(ApiView):
    __model__ = User
    __methods__ = {"post", "get", "put"}
    __filter_keys__ = {
        "post": ({"id",},),
        "get": ({"password",},),
        "put": ({"id", "create_time"},),
    }
    async def post_filter(self, context):
        now = get_offset_timestamp()
        if isinstance(context.form_data, dict):
            context.form_data["create_time"] = now
        else:
            for d in context.form_data:
                d["create_time"] = now


app = Sanic()

db = DataBase("sqlite:///db.db")
app.db = db

@app.listener('before_server_start')
async def setup_db(app, loop):
    if app.db.loop is None:
        app.db.loop = loop
        app.db.engine = await app.db.create_engine(echo=True)
        if not await app.db.exists_table(User.name):
            await app.db.create_table(User)

view = UserView.as_view(app.db)
app.add_route(view, "/user", HTTP_METHODS)
app.add_route(view, "/user/query", {"POST",})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
