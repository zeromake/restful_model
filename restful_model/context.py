import json
from typing import Dict, List, Union, Any, Optional

NAMES = ("form_data", "args")

class Context(object):
    def __init__(self,
        method: str,
        url_path: str,
        headers: Dict[str, Union[str, List[str]]],
        url_param: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        args: Optional[Dict[str, Any]] = None,
        raw_args: Optional[Dict[str, Any]] = None,
        sessions: Optional[Dict[str, Any]] = None
    ):
        self.method = method
        self.url_path = url_path
        self.form_data: Optional[Dict[str, Any]] = (form_data or {})
        self.has_param = False
        if url_param and len(url_param) > 0:
            if method != "delete":
                where = self.form_data.get("where", {})
                where.update(url_param)
                self.form_data["where"] = where
            else:
                self.form_data.update(url_param)
            self.has_param = True
        self.header: Optional[Dict[str, Any]] = headers
        self.args: Optional[Dict[str, Any]] = args
        self.raw_args: Optional[Dict[str, Any]] = raw_args
        self.sessions: Optional[Dict[str, Any]] = sessions

    # def __str__(self):
        # return str(hash("%s, %s" % (str(self.form_data), str(self.args))))

    def __repr__(self):
        return "<Context %s>" % hash("%s, %s" % (repr(self.form_data), repr(self.args)))
