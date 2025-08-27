from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field

from abc import ABC, abstractmethod


@dataclass
class PostmanBase(ABC):
    _raw: dict = field(repr=False)
    parent: Any = field(repr=False)

    @classmethod
    @abstractmethod
    def from_dict(cls, parent, data):
        raise NotImplementedError(
            f"{cls.__name__}.from_dict() must be implemented in subclasses."
        )

    def get_parents(self):

        def _get_parents(folder, accum: List[Any] = None):
            accum = accum or []

            if not folder.parent:
                return accum

            accum.append(folder.parent)

            _get_parents(folder.parent, accum)

            return accum

        accum = []
        accum = _get_parents(self, accum) or []
        accum.reverse()

        return accum

    @staticmethod
    def debug_cls(cls, data):
        print(f"{cls.__name__} data: {data}")

    def test_parity(self) -> bool:
        """Test if the dataclass instance matches the raw JSON object values."""
        from dataclasses import asdict

        if self._raw is None:
            raise ValueError("No raw_obj to compare against.")

        instance_dict = asdict(self)
        del instance_dict.parent
        instance_dict.pop("_raw", None)

        raw_obj_filtered = {k: v for k, v in self._raw.items() if k in instance_dict}

        return instance_dict == raw_obj_filtered


@dataclass
class PostmanAuth(PostmanBase):
    """Represents authentication information in a Postman collection or request.

    Attributes:
        type (str): The authentication type (e.g., 'basic', 'bearer', 'apikey', etc.)
        params (Optional[List[Dict[str, Any]]]): List of authentication parameters
    """

    type: str
    params: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(
        cls, parent, data: Dict[str, Any], debug_prn: bool = False
    ) -> "PostmanAuth":

        if debug_prn:
            cls.debug_cls(cls, data)

        auth_type = data.get("type")
        params = None
        if auth_type and auth_type in data:
            params = data[auth_type]
        return cls(parent=parent, _raw=data, type=auth_type, params=params)


@dataclass
class PostmanVariable(PostmanBase):
    """Represents a variable in a Postman collection or request/url.

    Attributes:
        key (str): The variable name
        value (str): The variable value
        type (Optional[str]): The variable type (e.g., 'string')
        description (Optional[str]): Description of the variable
    """

    key: str
    value: str
    type: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, parent, data: Dict[str, Any], debug_prn: bool = False):
        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            _raw=data,
            parent=parent,
            key=data["key"],
            value=data.get("value"),
            type=data.get("type"),
            description=data.get("description"),
        )


@dataclass
class PostmanRequest_Header(PostmanBase):
    """Represents an HTTP header in a request or response.

    Attributes:
        key (str): The name of the header (e.g., 'content-type', 'authorization')
        value (str): The value of the header
    """

    key: str
    value: str

    @classmethod
    def from_dict(cls, parent, data: Dict[str, str], debug_prn: bool = False):
        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent, _raw=data, key=data["key"].lower(), value=data["value"]
        )


@dataclass
class PostmanQueryParam(PostmanBase):
    """Represents a URL query parameter.

    Attributes:
        key (str): The parameter name
        value (str): The parameter value
        description (Optional[str]): Description of the parameter
        disabled (Optional[bool]): Whether the parameter is disabled
    """

    key: str
    value: str
    description: Optional[str] = None
    disabled: Optional[bool] = None

    @classmethod
    def from_dict(cls, parent, data: Dict[str, Any], debug_prn: bool = False):

        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent,
            _raw=data,
            key=data["key"],
            value=data["value"],
            description=data.get("description"),
            disabled=bool(data.get("disabled")),
        )


@dataclass
class PostmanUrl(PostmanBase):
    """Represents a complete URL with all its components.

    Attributes:
        raw (str): The complete URL as a string
        protocol (str): The protocol (e.g., 'http', 'https')
        host (List[str]): The host components (e.g., ['api', 'example', 'com'])
        path (List[str]): The path components
        query (Optional[List[PostmanQueryParam]]): List of query parameters, if any
        variable (Optional[List[PostmanVariable]]): List of variables in the URL, if any
    """

    raw: str
    protocol: str
    host: List[str]
    path: List[str]
    query: Optional[List[PostmanQueryParam]] = None
    variable: Optional[List[PostmanVariable]] = None

    @classmethod
    def from_dict(
        cls, parent, data: Dict[str, Any], debug_prn: bool = False
    ) -> "PostmanUrl":
        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent,
            _raw=data,
            raw=data.get("raw", ""),
            protocol=data.get("protocol", "https"),
            host=data.get("host", ["localhost"]),
            path=data.get("path", []),
            query=(
                [PostmanQueryParam.from_dict(parent, q) for q in data.get("query", [])]
                if "query" in data
                else None
            ),
            variable=(
                [PostmanVariable.from_dict(parent, v) for v in data.get("variable", [])]
                if "variable" in data
                else None
            ),
        )


@dataclass
class PostmanFormDataParam(PostmanBase):
    """Represents a form-data parameter in a request body."""

    key: str
    value: Optional[str] = None
    type: Optional[str] = None
    src: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None

    @classmethod
    def from_dict(
        cls, parent, data: Dict[str, Any], debug_prn: bool = False
    ) -> "PostmanFormDataParam":
        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent,
            _raw=data,
            key=data["key"],
            value=data.get("value"),
            type=data.get("type"),
            src=data.get("src"),
            description=data.get("description"),
            disabled=data.get("disabled"),
        )


@dataclass
class PostmanUrlEncodedParam(PostmanBase):
    """Represents a urlencoded parameter in a request body."""

    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None

    @classmethod
    def from_dict(
        cls, parent, data: Dict[str, Any], debug_prn: bool = False
    ) -> "PostmanUrlEncodedParam":
        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent,
            _raw=data,
            key=data["key"],
            value=data.get("value"),
            description=data.get("description"),
            disabled=data.get("disabled"),
        )


@dataclass
class PostmanRequest_Body(PostmanBase):
    """Represents the body of an HTTP request.

    Attributes:
        mode (str): The mode of the body (e.g., 'raw', 'formdata', 'urlencoded', 'file', 'graphql')
        raw (Optional[str]): The actual content of the body (for 'raw' mode)
        formdata (Optional[List[PostmanFormDataParam]]): List of form-data parameters
        urlencoded (Optional[List[PostmanUrlEncodedParam]]): List of urlencoded parameters
        file (Optional[Dict[str, Any]]): File upload details
        graphql (Optional[Dict[str, Any]]): GraphQL body details
    """

    mode: str
    raw: Optional[str] = None
    formdata: Optional[List[PostmanFormDataParam]] = None
    urlencoded: Optional[List[PostmanUrlEncodedParam]] = None
    file: Optional[Dict[str, Any]] = None
    graphql: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(
        cls, parent, data: Optional[Dict[str, Any]], debug_prn: bool = False
    ) -> Optional["PostmanRequest_Body"]:

        if debug_prn:
            cls.debug_cls(cls, data)

        """Create a PostmanRequest_Body from body data supporting all modes."""
        if not data:
            return None

        mode = data["mode"]
        kwargs = {"mode": mode}

        if mode == "raw":
            kwargs["raw"] = data.get("raw")

        elif mode == "formdata":
            kwargs["formdata"] = [
                PostmanFormDataParam.from_dict(parent, fd)
                for fd in data.get("formdata", [])
            ]
        elif mode == "urlencoded":
            kwargs["urlencoded"] = [
                PostmanUrlEncodedParam.from_dict(parent, ue)
                for ue in data.get("urlencoded", [])
            ]
        elif mode == "file":
            kwargs["file"] = data.get("file")
        elif mode == "graphql":
            kwargs["graphql"] = data.get("graphql")

        return cls(parent=parent, _raw=data, **kwargs)


@dataclass
class PostmanResponse(PostmanBase):
    """Represents an HTTP response in a Postman collection.

    Note: This is currently a placeholder class as the example collection
    had empty responses. In a real implementation, you would want to add
    fields like status code, headers, body, etc.
    """

    status: Optional[int] = None
    code: Optional[str] = None
    header: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None

    @classmethod
    def from_dict(cls, parent, data: Dict[str, Any], debug_prn: bool = False):

        if debug_prn:
            cls.debug_cls(cls, data)

        return cls(
            parent=parent,
            _raw=data,
            status=data.get("status"),
            code=data.get("code"),
            header=data.get("header"),
            body=data.get("body"),
        )


@dataclass
class PostmanRequest(PostmanBase):
    """Represents a single request in a Postman collection.

    A request typically represents a single API endpoint with its request
    and response details.

    Attributes:
        name (str): The name of the request
        method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT')
        header (List[PostmanRequest_Header]): List of HTTP headers
        url (PostmanUrl): The request URL
        body (Optional[PostmanRequest_Body]): The request body, if any
        response (List[PostmanResponse]): List of example responses
        raw_obj (Optional[Dict[str, Any]]): The raw JSON object for parity testing
    """

    name: str
    method: str
    headers: List[PostmanRequest_Header]
    url: PostmanUrl
    description: str = None
    body: Optional[PostmanRequest_Body] = None
    responses: List[PostmanResponse] = field(repr=False, default=list)

    def extract_method(self):
        method = self._raw.get("method")
        if method:
            self.method = method

        return self.method

    @classmethod
    def from_dict(cls, parent, data: Dict[str, Any], debug_prn: bool = False):

        if debug_prn:
            cls.debug_cls(cls, data)

        request_data = data.get("request", {})

        return cls(
            parent=parent,
            _raw={**data},
            name=data.get("name"),
            method=request_data.get("method"),
            description=request_data.get("description"),
            headers=[
                PostmanRequest_Header.from_dict(parent, h)
                for h in request_data.get("header", [])
            ],
            url=PostmanUrl.from_dict(
                parent,
                request_data.get(
                    "url",
                    {},
                ),
            ),
            body=PostmanRequest_Body.from_dict(parent, request_data.get("body")),
            responses=[
                PostmanResponse.from_dict(parent, r) for r in data.get("response", [])
            ],
        )

    # Remove duplicate from_dict for PostmanResponse


@dataclass
class PostmanFolder(PostmanBase):
    name: Optional[str] = None
    items: List[Union["PostmanFolder", PostmanRequest]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, parent, data: Dict[str, Any], debug_prn: bool = False):
        folder = cls(parent=parent, _raw=data, name=data.get("name"))

        folder.items = create_items_and_requests(
            data=data, parent=folder, debug_prn=debug_prn
        )

        return folder

    def get_folder_requests(self):

        def _get_requests(ele, res):
            if isinstance(ele, PostmanRequest):
                res.append(ele)
                return res

            if isinstance(ele, list):
                for item in ele:
                    _get_requests(item, res)

            else:
                for item in ele.items:
                    _get_requests(item, res)

            return res

        res = []
        return _get_requests(self.items, res=res)

    def get_subfolders(self):

        def _get_folders(ele, res):

            if isinstance(ele, PostmanRequest):
                return res

            if isinstance(ele, PostmanFolder):
                res.append(ele)
                return res

            if isinstance(ele, list):
                for item in ele:
                    _get_folders(item, res)

            else:
                for item in ele.items:
                    _get_folders(item, res)

            return res

        res = []
        return _get_folders(self.items, res=res)

    def list_all_headers(self) -> Dict[str, List[str]]:
        """List all unique headers and their values from this collection.

        Returns:
            Dict[str, List[str]]: Dictionary where keys are header names and values are lists of unique values
        """
        headers_dict = {}

        res = self.get_folder_requests()

        for request in res:
            for header in request.headers:
                if header.key not in headers_dict:
                    headers_dict[header.key] = set()
                headers_dict[header.key].add(header.value)

        # Convert sets to lists for better serialization
        return {key: list(values) for key, values in headers_dict.items()}

    def list_all_params(self) -> Dict[str, List[str]]:
        """List all unique query parameters and their values from this collection.

        Returns:
            Dict[str, List[str]]: Dictionary where keys are parameter names and values are lists of unique values
        """
        params_dict = {}

        res = self.get_folder_requests()

        for request in res:
            if request.url.query:
                for param in request.url.query:
                    if param.key not in params_dict:
                        params_dict[param.key] = set()
                    params_dict[param.key].add(param.value)

        # Convert sets to lists for better serialization
        return {key: list(values) for key, values in params_dict.items()}


def create_items_and_requests(data, parent, debug_prn: bool = False):
    if not data.get("item"):
        return None

    items = []

    for obj in data["item"]:

        if obj.get("request"):
            items.append(
                PostmanRequest.from_dict(parent=parent, data=obj, debug_prn=debug_prn)
            )

        else:
            items.append(
                PostmanFolder.from_dict(parent=parent, data=obj, debug_prn=debug_prn)
            )

    return items


@dataclass
class PostmanCollectionInfo(PostmanBase):
    """Contains metadata about the Postman collection.

    Attributes:
        _postman_id (str): Unique identifier for the collection
        name (str): Name of the collection
        schema (str): The schema version used by the collection
        _exporter_id (str): ID of the exporter that created the collection
        _collection_link (str): Link to the collection in Postman
    """

    id: str
    name: str
    schema: str
    _exporter_id: str
    _collection_link: str

    @classmethod
    def from_dict(
        cls, parent, data: Dict[str, str], debug_prn: bool = False
    ) -> "PostmanCollectionInfo":
        if debug_prn:
            print(data)
        return cls(
            parent=parent,
            _raw=data,
            id=data["_postman_id"],
            name=data["name"],
            schema=data["schema"],
            _exporter_id=data["_exporter_id"],
            _collection_link=data["_collection_link"],
        )


@dataclass
class PostmanCollection(PostmanFolder):
    """Represents a complete Postman collection.

    This is the root class that contains all the information about
    a Postman collection, including its metadata and all the API
    requests it contains.

    Attributes:
        info (PostmanCollectionInfo): Collection metadata
        requests (List[PostmanRequest]): List of requests in the collection
        variables (Optional[List[PostmanVariable]]): List of collection-level variables
    """

    info: PostmanCollectionInfo = field(default=None)

    variables: Optional[List[PostmanVariable]] = field(default_factory=list)
    auth: Optional[PostmanAuth] = field(default=None)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], debug_prn: bool = False
    ) -> "PostmanCollection":

        collection = cls(
            parent=None,
            _raw=data,
            name=data.get("info", {}).get("name", "Unnamed Collection"),
        )

        if data.get("info"):
            collection.info = PostmanCollectionInfo.from_dict(
                parent=collection, data=data["info"], debug_prn=debug_prn
            )

        collection.items = create_items_and_requests(
            data=data, parent=collection, debug_prn=debug_prn
        )

        if data.get("variable"):
            collection.variables = [
                PostmanVariable.from_dict(
                    parent=collection, data=v, debug_prn=debug_prn
                )
                for v in data["variable"]
            ]

        if data.get("auth"):
            collection.auth = (
                PostmanAuth.from_dict(
                    parent=collection, data=data["auth"], debug_prn=debug_prn
                )
                if "auth" in data
                else None
            )

        return collection

    @classmethod
    def from_file(cls, file_path: str, debug_prn: bool = False) -> "PostmanCollection":
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data, debug_prn=debug_prn)
