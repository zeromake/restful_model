
class BasePolymerization(object):
    """
    聚合
    """
    def __init__(self, db):
        self.db = db
        self.views = {}

    def add_view(self, view):
        """
        添加
        """
        self.views[view.name] = view

    async def dispatch_request(self, context):
        """
        分发请求
        """
