restful_model
=============

restful_model is an `sqlalchemy`_ auto generate REATful API

Example
-------

sanic
^^^^^^

app.py

.. code-block:: python
    import sqlalchemy as sa
    from sanic import Sanic
    from sanic.constants import HTTP_METHODS
    from restful_model import DataBase
    from restful_model.extend.sanic import ApiView

    metadata = sa.MetaData()
    User = sa.Table(
        'user',
        metadata,
        sa.Column(
            'id',
            sa.Integer,
            autoincrement=True,
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'account',
            sa.String(16),
            nullable=False,
        ),
        sqlite_autoincrement=True,
    )
    class UserView(ApiView):
        __model__ = User
    
    app = Sanic(__name__)
    db = DataBase("sqlite:///db.db")
    app.db = db

    @app.listener('before_server_start')
    async def setup_db(app, loop):
        if app.db.loop is None:
            app.db.loop = loop
            app.db.engine = await app.db.create_engine(echo=True)
            if not await app.db.exists_table(User.name):
                await app.db.create_table(User)

    userView = UserView.as_view(app.db)
    app.add_route(userView, "/user", HTTP_METHODS)
    app.add_route(userView, "/user/<id:int>", HTTP_METHODS)

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)

curl test

.. code-block:: bash
    $ # create
    $ curl -X POST http://127.0.0.1:8000/user \
    -H 'content-type: application/json' \
    -d '{ "account": "test1" }'
    > {"status":201,"message":"Insert ok!","meta":{"count":1}}
    $ # select
    $ curl -X GET http://127.0.0.1:8000/user
    > {"status":200,"message":"Query ok!","data":[{"id":1,"account":"test1"}]}
    $ # update
    $ curl -X PUT http://127.0.0.1:8000/user \
    -H 'content-type: application/json' \
    -d '{"where": {"id": 1}, "values": {"account": "test2"}}'
    > {"status":201,"message":"Update ok!","meta":{"count":1}}
    $ curl -X GET http://127.0.0.1:8000/user
    > {"status":200,"message":"Query ok!","data":[{"id":1,"account":"test2"}]}
    $ # delete
    $ curl -X DELETE http://127.0.0.1:8000/user \
    -H 'content-type: application/json' \
    -d '{"id": 1}'
    > {"status":200,"message":"Delete ok!","meta":{"count":1}}
    $ curl -X GET http://127.0.0.1:8000/user
    > {"status":200,"message":"Query ok!","data":[]}
Links
-----

.. _sqlalchemy: https://github.com/zzzeek/sqlalchemy
