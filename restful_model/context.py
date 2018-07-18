from typing import Dict, List, Union, Any, Optional


class Context(object):
    def __init__(self,
        method: str,
        url_path: str,
        headers: Dict[str, Union[str, List[str]]],
        form_data: Optional[Dict[str, Any]] = None,
        args: Optional[Dict[str, Any]] = None,
        sessions: Optional[Dict[str, Any]] = None
    ):
        self.method = method
        self.url_path = url_path
        self.form_data: Optional[Dict[str, Any]] = form_data
        self.headers: Optional[Dict[str, Any]] = headers
        self.args: Optional[Dict[str, Any]] = args
        self.sessions: Optional[Dict[str, Any]] = sessions
