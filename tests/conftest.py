import pytest
import gc
import asyncio
from restful_model import DataBase
from urllib.parse import unquote_plus


@pytest.fixture(scope='session')
def event_loop():
    loop_obj = asyncio.new_event_loop()
    yield loop_obj
    gc.collect()
    loop_obj.close()


@pytest.fixture(scope='session')
def loop(event_loop):
    """
    生成loop
    """
    return event_loop


@pytest.fixture(scope="session")
def db_name():
    # pg
    # return "test_pg"
    # mysql
    # return "test_pymysql"
    # sqlite
    return ":memory:"


@pytest.fixture(scope="session")
def data_bese(db_name):
    # pg
    # return "postgresql://aiopg:mypass@127.0.0.1:5432/%s" % db_name
    # mysql
    # return "mysql://aiomysql:mypass@127.0.0.1:3306/%s" % db_name
    # mariadb
    # return "mysql://aiomysql:mypass@127.0.0.1:3307/%s" % db_name
    # sqlite
    db_name = unquote_plus(db_name)
    return "sqlite:///%s" % db_name


@pytest.fixture
def db(loop, data_bese):
    db = DataBase(data_bese, loop)
    db.engine = loop.run_until_complete(db.create_engine(echo=True))
    yield db
    db.engine.close()
    db.engine = None
