from typing import Dict, List, Union, Any, Optional


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
        self.form_data: Optional[Dict[str, Any]] = form_data or {}
        self.headers: Optional[Dict[str, Any]] = headers
        self.args: Optional[Dict[str, Any]] = args
        self.raw_args: Optional[Dict[str, Any]] = raw_args
        self.sessions: Optional[Dict[str, Any]] = sessions
