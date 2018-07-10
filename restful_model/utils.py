import sqlalchemy as sa
from sqlalchemy.sql import dml


def return_true(*args):
    return True

def get_filter_list(block_list=None, white_list=None):
    """
    生成过滤黑白名单
    """
    if block_list and isinstance(block_list, list):
        block_list = set(block_list)
    if white_list and isinstance(white_list, list):
            white_list = set(white_list)
    def filter_list(key: str) -> bool:
        """
        过滤黑白名单
        """
        status = True
        if block_list:
            status &= key not in block_list
        if white_list:
            status &= key in white_list
        return status
    return filter_list

def handle_param(column, data):
    """
    处理where条件
    """
    opt = data.get('opt', '$te')
    if 'val' in data:
        value = data['val']
        if opt == '$ne': # 不等于
            return column != value
        if opt == '$te': # 等于
            return column == value
        elif opt == '$lt': # 小于
            return column < value
        elif opt == '$lte': # 小于等于
            return column <= value
        elif opt == '$gt': # 大于
            return column > value
        elif opt == '$gte': # 大于等于
            return column >= value
        elif opt == '$like': # like
            return column.like(value)
        elif opt == '$in':
            return column.in_(value)
        elif opt == '$nin':
            return ~column.in_(value)
        elif opt == '$bind':
            # 占位符
            if isinstance(value, str):
                return column == bindparam(value)
            else:
                opt = value["opt"]
                if opt == '$bind':
                    return None
                if opt == "$in" or opt == "$nin":
                    value["val"] = bindparam(value["val"], expanding=True)
                else:
                    value["val"] = bindparam(value["val"])
                return handle_param(column, value)
        elif opt == '$raw':
            return value

def handle_param_desc(column, data):
    """
    处理参数类型
    """
    params = []
    if isinstance(data, list):
        if len(data) > 0:
            if isinstance(data[0], dict):
                for row in data:
                    param = handle_param(column, row)
                    if not param is None:
                        params.append(param)
            else:
                data.append(column.in_(data))
    elif isinstance(data, dict):
        param = handle_param(column, data)
        if not param is None:
            params.append(param)
    else:
        params.append(column==data)
    params_len = len(params)
    if params_len == 0:
        return
    elif params_len == 1:
        return params[0]
    elif params_len > 1:
        return params

def handle_param_primary(column_name, form_data, filter_list=return_true, is_or=False):
    """
    处理带主键的参数
    """
    data = []
    for key, val in form_data.items():
        if key in column_name and filter_list(key):
            column = column_name[key]
            params = handle_param_desc(column, val)
            if not params is None:
                if isinstance(params, list):
                    data.append(and_(params))
                else:
                    data.append(params)
        elif key == "$or" and isinstance(val, dict):
            params = handle_param_primary(column_name, val, filter_list, True)
            if not params is None:
                data.append(params)
        elif key == "$and" and isinstance(val, dict):
            params = handle_param_primary(column_name, val, filter_list, False)
            if not params is None:
                data.append(params)
    data_len = len(data)
    if data_len == 1:
        return data[0]
    elif data_len > 1:
        return sa.or_(*data) if is_or else sa.and_(*data)

def insert_sql(model: sa.Table, data, block_list=None, white_list=None) -> dml.Insert:
    """
    生成插入语句对象
    """
    filter_list = get_filter_list(block_list, white_list)
    if isinstance(data, list):
        data = [{ k: v for k, v in m if filter_list(k) } for m in data]
    else:
        data = { k: v for k, v in m if filter_list(data) }
    return model.insert().values(data)

def delete_sql(model: sa.Table, data, block_list=None, white_list=None) -> dml.Delete:
    """
    生成删除语句对象
    """
    filter_list = get_filter_list(block_list, white_list)
    where_data = handle_param_primary(model.columns, data, filter_list)
    return model.delete().where(where_data)

def update_sql(model: sa.Table, data, block_list=None, white_list=None) -> dml.Update:
    """
    生成更新语句对象
    """
    filter_list = get_filter_list(block_list, white_list)

