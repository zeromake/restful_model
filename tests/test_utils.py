from restful_model.utils import (
    get_filter_list,
    handle_param,
    handle_param_desc,
    handle_where_param,
    insert_sql,
    delete_sql,
    select_sql,
    update_sql,
)
import sqlalchemy as sa
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.ext.declarative import declarative_base
from aiosqlite3.sa.engine import compiler_dialect


dialect = compiler_dialect()

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
        doc="主键"
    ),
    sa.Column(
        'account',
        sa.String(16),
        nullable=False,
        doc="帐号"
    ),
    sa.Column(
        'role_name',
        sa.String(16),
        nullable=False,
        doc="昵称"
    ),
    sa.Column(
        'email',
        sa.String(256),
        nullable=False,
        doc="邮箱"
    ),
    sa.Column(
        'password',
        sa.String(128),
        nullable=False,
        doc="密码"
    ),
    sa.Column(
        "create_time",
        sa.BigInteger,
        nullable=False,
        doc="创建时间"
    )
)



Base = declarative_base()


class ClassUser(Base):
    __tablename__ = "user"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(64))
    account = sa.Column(sa.String(64))
    email = sa.Column(sa.String(64))
    role_name = sa.Column(sa.String(64))

def assert_param(p1, p2) -> bool:
    compile1 = p1.compile(dialect=dialect)
    compile2 = p2.compile(dialect=dialect)
    # print(compile1, compile1.params)
    # print(compile2, compile2.params)
    return str(compile1) == str(compile2) and compile1.params == compile2.params


def test_get_filter_list() -> None:
    """
    测试过滤功能
    """
    # 无过滤
    filter_list = get_filter_list()
    assert filter_list("tttt")
    # 黑名单过滤
    filter_list = get_filter_list({"key", "id"})
    assert not filter_list("key")
    assert not filter_list("id")
    assert filter_list("test")
    # 黑白名单过滤
    filter_list = get_filter_list(["key", "id"], ["test"])
    assert not filter_list("key")
    assert not filter_list("id")
    assert filter_list("test")
    assert not filter_list("test2")

def test_handle_param() -> None:
    """
    测试各种比较符的对应表达式
    """
    column = User.c.id
    assert assert_param(handle_param(column, {"opt": "$te", "val": 5}), column == 5)
    assert assert_param(handle_param(column, {"opt": "$ne", "val": 5}), column != 5)
    assert assert_param(handle_param(column, {"opt": "$lt", "val": 5}), column < 5)
    assert assert_param(handle_param(column, {"opt": "$lte", "val": 5}), column <= 5)
    assert assert_param(handle_param(column, {"opt": "$gt", "val": 5}), column > 5)
    assert assert_param(handle_param(column, {"opt": "$gte", "val": 5}), column >= 5)
    assert not assert_param(handle_param(column, {"opt": "$gte", "val": 4}), column >= 5)
    assert assert_param(handle_param(column, {"opt": "$like", "val": "hhhh"}), column.like("hhhh"))
    assert assert_param(handle_param(column, {"opt": "$in", "val": [1,2]}), column.in_([1,2]))
    assert assert_param(handle_param(column, {"opt": "$nin", "val": [1,2]}), ~column.in_([1,2]))
    assert handle_param(column, {"opt": "$raw", "val": "id = 4"}) == "id = 4"
    assert assert_param(handle_param(column, {"opt": "$bind", "val": "key"}), column == bindparam("key"))
    assert handle_param(column, {"opt": "$bind", "val": {"opt": "$bind"}}) is None
    assert assert_param(handle_param(column, {"opt": "$bind", "val": {"opt": "$ne", "val": "key"}}), column != bindparam("key"))
    assert assert_param(handle_param(column, {"opt": "$bind", "val": {"opt": "$in", "val": "key"}}), column.in_(bindparam("key", expanding=True)))


def test_handle_param_class() -> None:
    """
    使用 declarative_base 测试各种比较符的对应表达式
    """
    column = ClassUser.id
    assert assert_param(handle_param(column, {"opt": "$te", "val": 5}), column == 5)
    assert assert_param(handle_param(column, {"opt": "$ne", "val": 5}), column != 5)
    assert assert_param(handle_param(column, {"opt": "$lt", "val": 5}), column < 5)
    assert assert_param(handle_param(column, {"opt": "$lte", "val": 5}), column <= 5)
    assert assert_param(handle_param(column, {"opt": "$gt", "val": 5}), column > 5)
    assert assert_param(handle_param(column, {"opt": "$gte", "val": 5}), column >= 5)
    assert not assert_param(handle_param(column, {"opt": "$gte", "val": 4}), column >= 5)
    assert assert_param(handle_param(column, {"opt": "$like", "val": "hhhh"}), column.like("hhhh"))
    assert assert_param(handle_param(column, {"opt": "$in", "val": [1,2]}), column.in_([1,2]))
    assert assert_param(handle_param(column, {"opt": "$nin", "val": [1,2]}), ~column.in_([1,2]))
    assert handle_param(column, {"opt": "$raw", "val": "id = 4"}) == "id = 4"
    assert assert_param(handle_param(column, {"opt": "$bind", "val": "key"}), column == bindparam("key"))
    assert handle_param(column, {"opt": "$bind", "val": {"opt": "$bind"}}) is None
    assert assert_param(handle_param(column, {"opt": "$bind", "val": {"opt": "$ne", "val": "key"}}), column != bindparam("key"))
    assert assert_param(handle_param(column, {"opt": "$bind", "val": {"opt": "$in", "val": "key"}}), column.in_(bindparam("key", expanding=True)))

def test_handle_param_desc() -> None:
    """
    测试多个表达式
    """
    column = User.c.account
    assert assert_param(
        sa.and_(*handle_param_desc(
            column,
            [
                {"opt": "$te", "val": "test"},
                {"opt": "$ne", "val": "test1"}
            ],
        )),
        sa.and_(column == "test", column != "test1")
    )
    assert assert_param(
        handle_param_desc(
            column,
            {"opt": "$ne", "val": "test1"}
        ),
        column != "test1",
    )
    assert assert_param(
        handle_param_desc(
            column,
            "test1"
        ),
        column == "test1",
    )
    assert handle_param_desc(column, []) is None

def test_handle_param_desc_class() -> None:
    """
    测试多个表达式
    """
    column = ClassUser.name
    assert assert_param(
        sa.and_(*handle_param_desc(
            column,
            [
                {"opt": "$te", "val": "test"},
                {"opt": "$ne", "val": "test1"}
            ],
        )),
        sa.and_(column == "test", column != "test1")
    )
    assert assert_param(
        handle_param_desc(
            column,
            {"opt": "$ne", "val": "test1"}
        ),
        column != "test1",
    )
    assert assert_param(
        handle_param_desc(
            column,
            "test1"
        ),
        column == "test1",
    )
    assert handle_param_desc(column, []) is None

def test_handle_param_primary() -> None:
    """
    测试具体的where转换效果
    """
    columns = User.c
    filter_list = get_filter_list({"password"})
    assert assert_param(
        handle_where_param(
            columns,
            {
                "id": 1,
                "account": {"opt": "$ne", "val": "test"},
                "email": [
                    {
                        "opt": "$te",
                        "val": "test1@test.com",
                    },
                    {
                        "opt": "$te",
                        "val": "test2@test.com",
                    },
                ],
                "password": "12345678",
            },
            filter_list,
        ),
        sa.and_(
            columns.id == 1,
            columns.account != "test",
            columns.email == "test1@test.com",
            columns.email == "test2@test.com",
        )
    )
    assert handle_where_param(columns, {"password": "12345678"}, filter_list) is None
    assert assert_param(
        handle_where_param(columns, {"account": "12345678"}, filter_list),
        columns.account == "12345678",
    )
    assert assert_param(
        handle_where_param(
            columns,
            {
                "$or": {
                    "id": 1,
                    "account": {"opt": "$ne", "val": "test"},
                    "email": [
                        {
                            "opt": "$te",
                            "val": "test1@test.com",
                        },
                        {
                            "opt": "$te",
                            "val": "test2@test.com",
                        },
                    ],
                    "password": "12345678",
                },
            },
            filter_list,
        ),
        sa.or_(
            columns.id == 1,
            columns.account != "test",
            sa.and_(
                columns.email == "test1@test.com",
                columns.email == "test2@test.com",
            )
        )
    )
    assert assert_param(
        handle_where_param(
            columns,
            {
                "$or": {
                    "id": 1,
                    "account": {"opt": "$ne", "val": "test"},
                    "$and": {
                        "email": {
                            "opt": "$te",
                            "val": "test2@test.com",
                        },
                        "role_name": "gggg"
                    },
                    "password": "12345678",
                },
            },
            filter_list,
        ),
        sa.or_(
            columns.id == 1,
            columns.account != "test",
            sa.and_(
                columns.email == "test2@test.com",
                columns.role_name == "gggg",
            )
        )
    )

def test_handle_param_primary_class() -> None:
    """
    测试具体的where转换效果
    """
    columns = ClassUser.__table__.c
    filter_list = get_filter_list({"password"})
    assert assert_param(
        handle_where_param(
            columns,
            {
                "id": 1,
                "account": {"opt": "$ne", "val": "test"},
                "email": [
                    {
                        "opt": "$te",
                        "val": "test1@test.com",
                    },
                    {
                        "opt": "$te",
                        "val": "test2@test.com",
                    },
                ],
                "password": "12345678",
            },
            filter_list,
        ),
        sa.and_(
            columns.id == 1,
            columns.account != "test",
            columns.email == "test1@test.com",
            columns.email == "test2@test.com",
        )
    )
    assert handle_where_param(columns, {"password": "12345678"}, filter_list) is None
    assert assert_param(
        handle_where_param(columns, {"account": "12345678"}, filter_list),
        columns.account == "12345678",
    )
    assert assert_param(
        handle_where_param(
            columns,
            {
                "$or": {
                    "id": 1,
                    "account": {"opt": "$ne", "val": "test"},
                    "email": [
                        {
                            "opt": "$te",
                            "val": "test1@test.com",
                        },
                        {
                            "opt": "$te",
                            "val": "test2@test.com",
                        },
                    ],
                    "password": "12345678",
                },
            },
            filter_list,
        ),
        sa.or_(
            columns.id == 1,
            columns.account != "test",
            sa.and_(
                columns.email == "test1@test.com",
                columns.email == "test2@test.com",
            )
        )
    )
    assert assert_param(
        handle_where_param(
            columns,
            {
                "$or": {
                    "id": 1,
                    "account": {"opt": "$ne", "val": "test"},
                    "$and": {
                        "email": {
                            "opt": "$te",
                            "val": "test2@test.com",
                        },
                        "role_name": "gggg"
                    },
                    "password": "12345678",
                },
            },
            filter_list,
        ),
        sa.or_(
            columns.id == 1,
            columns.account != "test",
            sa.and_(
                columns.email == "test2@test.com",
                columns.role_name == "gggg",
            )
        )
    )


def test_insert_sql() -> None:
    filter_list = get_filter_list({"id"})
    assert assert_param(
        insert_sql(
            User,
            {"id": 1, "account": "test"},
            filter_list,
        ),
        User.insert().values({"account": "test"})
    )
    assert not assert_param(
        insert_sql(
            User,
            {"id": 1, "account": "tes"},
            filter_list,
        ),
        User.insert().values({"account": "test"})
    )
    data = [
        {"account": "test"},
        {"account": "test1"},
    ]
    assert assert_param(
        insert_sql(
            User,
            data,
            filter_list,
        ),
        User.insert().values(data)
    )

def test_delete_sql() -> None:
    """
    测试删除sql
    """
    assert assert_param(delete_sql(User, {"id": 1}), User.delete().where(User.c.id==1))
    assert not assert_param(delete_sql(User, {"id": 2}), User.delete().where(User.c.id==1))

def test_select_sql() -> None:
    """
    测试查询
    """
    filter_list = get_filter_list(block_list={"password"})
    sql = select_sql(User, {
        "id": 1,
    }, filter_list)
    assert assert_param(
        sql,
        sa.sql.select([c for c in User.c if c.name != "password"]).where(User.c.id==1)
    )

    sql = select_sql(User, {
        "id": 1,
    })
    assert assert_param(
        sql,
        User.select().where(User.c.id==1)
    )
    sql = select_sql(User, {
        "id": 1,
    }, orders={"-account"})
    assert assert_param(
        sql,
        User.select().where(User.c.id==1).order_by(sa.desc(User.c.account))
    )
    sql = select_sql(User, {
        "id": 1,
    }, orders={"id"})
    assert assert_param(
        sql,
        User.select().where(User.c.id==1).order_by( User.c.id)
    )
    sql, sql_count = select_sql(User, {
        "id": 1,
    }, limit=(0, 50,))
    assert assert_param(
        sql,
        User.select().where(User.c.id==1).offset(0).limit(50)
    )
    assert assert_param(
        sql_count,
        sa.sql.select([sa.func.count(User.c.id).label("_count")]).where(User.c.id==1),
    )
    # max
    filter_list = get_filter_list(white_list={"id", "account", "create_time"})
    sql = select_sql(User, {
        "id": 1,
    }, filter_list, orders={"id"}, keys=[{"column": "id", "func": "max"}, "account"], group=["id", "account"])
    assert assert_param(
        sql,
        sa.sql
            .select(
                [sa.func.max(User.c.id), User.c.account]
            )
            .where(User.c.id==1)
            .order_by(User.c.id)
            .group_by(User.c.id, User.c.account)
    )
    sql = select_sql(User, {
        "id": 1,
    }, keys=[{ "column": "create_time", "func": "from_unixtime", "args": [r"%Y-%m-%d %H:%i:%s"]}, "id", "account"])
    assert assert_param(
        sql,
        sa.sql.select(
                [
                    sa.func.from_unixtime(User.c.create_time, r"%Y-%m-%d %H:%i:%s"),
                    User.c.id,
                    User.c.account,
                ]
            )
            .where(User.c.id==1)
    )


    sql = select_sql(User, {
        "id": 1,
    }, keys=[{"column": "create_time", "func": "max", "label": "max_time"}, "id", "account"])
    assert assert_param(
        sql,
        sa.sql
            .select(
                [
                    sa.func.max(User.c.create_time).label("max_time"),
                    User.c.id,
                    User.c.account,
                ]
            )
            .where(User.c.id==1)
    )

    sql = select_sql(User, {
        "id": 1,
    }, keys=["id", "account", "create_time"])
    assert assert_param(
        sql,
        sa.sql
            .select(
                [
                    User.c.id,
                    User.c.account,
                    User.c.create_time
                ]
            )
            .where(User.c.id==1)
    )

def test_update_sql():
    """
    测试更新语句
    """
    sql = update_sql(User, {
        "where": {
            "id": 1,
        },
        "values": {
            "account": "change"
        }
    })
    assert assert_param(
        sql,
        User.update().where(User.c.id == 1).values({"account": "change"})
    )

    sql = update_sql(User, {
        "values": {
            "account": "change"
        }
    })
    assert assert_param(
        sql,
        User.update().values({"account": "change"})
    )

    sql = update_sql(User, {
        "values": {
            "account": "$bind.account1"
        }
    })
    assert assert_param(
        sql,
        User.update().values({"account": bindparam("account1")})
    )

    sql = update_sql(User, [{
        "values": {
            "account": "$bind.account1"
        }
    }])
    assert assert_param(
        sql[0],
        User.update().values({"account": bindparam("account1")})
    )

