from ._1_models import PostmanRequest, PostmanUrl, PostmanFolder
import src.Converter_Params as pmcp

import src.utils.convert as pmcv
import src.utils.files as pmfi
from typing import Any, Tuple
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin

import ast
import re


def replace_postman_variables(
    text: str,
    variable_name: str,
    provider_class_attribute: str,
    provider_class_name="auth",
) -> str:

    def repl(match):
        var_name = match.group(1)
        if var_name == variable_name:
            # Use the provided attribute name directly
            if provider_class_name:
                return f"{{{provider_class_name}.{provider_class_attribute}}}"
            else:
                return f"{{{provider_class_attribute}}}"
        # Otherwise, keep the original variable unchanged
        return match.group(0)

    return re.sub(r"\{\{(\w+)\}\}", repl, text)


def generate_params_from_request(
    prq: PostmanRequest,
    signature_params: Optional[List[str]] = None,
    excluded_params: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Build query parameters dictionary from this PostmanRequest.

    Returns:
        Dict[str, str]: Dictionary of query parameters
    """

    pru = prq.url

    # Store the parameters configuration
    signature_params = signature_params or []
    excluded_params = excluded_params or []

    if not pru.query:
        return []

    params = [
        pmcp.PostmanParamConverter.from_param(
            param, is_signature=param.key.lower() in signature_params
        )
        for param in (pru.query or [])
        if param.key.lower() not in excluded_params and not param.disabled
    ]

    return params


def generate_url_from_request(prq: PostmanRequest) -> str:
    """Build the complete URL from this PostmanRequest.

    Returns:
        str: The complete URL
    """
    purl: PostmanUrl = prq.url

    base_url = f"{purl.protocol}://{'.'.join(purl.host)}"
    path = "/".join(purl.path)
    generated_url = str(urljoin(base_url, path))

    return generated_url


def generate_headers_from_request(
    request: PostmanRequest,
    required_headers: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Build headers dictionary from this PostmanRequest, optionally filtered by required headers.

    Args:
        required_headers (Optional[List[str]]): List of header keys to include. If None, all headers are included.

    Returns:
        Dict[str, str]: Dictionary of headers
    """

    headers = {h.key.lower(): h.value for h in request.headers}
    if required_headers:
        headers = {
            key: value
            for key, value in headers.items()
            if key.lower() in [req_header.lower() for req_header in required_headers]
        }
    return headers


def generate_function_name_from_request(
    prq: PostmanRequest, drop_n_from_path_head: int = 0, prefix=""
) -> str:
    """
    Generate a function name as METHOD_endpoint from a PostmanRequest.
    """
    method = prq.method.lower()
    endpoint = "endpoint"

    if prq.url and hasattr(prq.url, "path"):
        path_parts = prq.url.path[(drop_n_from_path_head - 1) :]

        endpoint = pmcv.convert_str_keep_alphanumeric(
            "_".join(path_parts),
            allowed_characters=r"[^0-9a-zA-Z_\s]+",
            replacement_character="_",
        )

    return f"{prefix}{endpoint}_{method}"


@dataclass
class PostmanRequestConverter:

    request: PostmanRequest = field(repr=False)
    function_name: Optional[str] = None
    description: str = None
    headers: Dict[str, str] = field(default_factory=dict)
    params: List[pmcp.PostmanParamConverter] = field(default_factory=list)

    url: str = None

    code: str = ""

    @classmethod
    def from_postman_request(
        cls, request: PostmanRequest, config: Dict[str, Any]
    ) -> "PostmanRequestConverter":
        """Create a PostmanRequestConverter from a PostmanRequest and generate function code."""

        # Use dataclass inheritance to initialize from PostmanRequest

        converter = cls(request=request)

        converter.generate_request_code(config=config)

        return converter

    def generate_function_name(
        self, drop_n_from_path_head: int = 0, prefix: str = "", **kwargs
    ) -> str:
        """Generate a function name as method_endpoint, not including params."""
        self.function_name = generate_function_name_from_request(
            self.request, drop_n_from_path_head, prefix
        )
        return self.function_name

    def generate_headers(self, **kwargs) -> Dict[str, str]:
        """Generate headers for the request."""
        self.headers = generate_headers_from_request(self.request)
        return self.headers

    def generate_params(
        self,
        signature_params: Optional[List[str]] = None,
        excluded_params: Optional[List[str]] = None,
        **kwargs,
    ) -> Tuple[List[pmcp.PostmanParamConverter], Dict[str, str]]:
        """Generate query parameters for the request."""

        signature_params = signature_params or []
        excluded_params = excluded_params or []

        self.params = generate_params_from_request(
            self.request,
            signature_params=signature_params,
            excluded_params=excluded_params,
        )

        if not self.params:
            return [], {}

        self._params_signature = [p for p in self.params if p.key in signature_params]

        res = "{"

        res += ",".join(
            [
                ", ".join(
                    f'"{p.key}": {p._generate_value_str()}'
                    for p in self.params
                    if p.key not in excluded_params and p.key not in signature_params
                ),
                ", ".join(
                    f'"{p.key}": {p.name}'
                    for p in self.params
                    if p.key not in excluded_params and p.key in signature_params
                ),
            ]
        )

        res += "}"

        self._params_body = res

        return self._params_signature, self._params_body

    def generate_url(self, base_url_variable: str = None, **kwargs) -> str:
        """Generate the URL for the request."""

        self.url = generate_url_from_request(self.request)

        if base_url_variable:
            self.url = replace_postman_variables(
                generate_url_from_request(self.request),
                variable_name=base_url_variable,
                provider_class_attribute=pmcv.to_snake_case(base_url_variable),
                provider_class_name="auth",
            )

        return self.url

    def generate_description(self, **kwargs):
        if not self.request.description:
            self.description = (
                f"Function to {self.request.method} {self.request.url.path}."
            )

        else:
            self.description = self.request.description

        self.description = self.description.replace("\n", " ")

        return self.description

    def _append_code(self, code_ls: List[str], indent: int = 0) -> str:
        indent = " " * (indent * 4)

        self.code += "\n".join(
            f"{indent}{line}" if line.strip() else line for line in code_ls
        )

        return self.code

    def generate_request_code(
        self,
        config=None,
        is_add_imports: bool = True,
    ) -> str:
        """Build the request code for the function."""

        self.code = ""

        params_signature, params_body = self.generate_params(**config)

        if config:
            self.generate_function_name(**config)
            self.generate_headers(**config)
            self.generate_description(**config)
            self.generate_url(**config)

        if is_add_imports:

            self._append_code(
                code_ls=[
                    "# Auto-generated by PostmanConverter. Do not edit manually.\n",
                    f"# {' > '.join([parent.name for parent in self.request.get_parents() if isinstance(parent, PostmanFolder)] +[self.request.name])}\n",
                    "from src.client.Auth import Auth\n"
                    "from src.client.get_data import gd_requests\n"
                    "from typing import Dict\n\n",
                ],
                indent=0,
            )

            self._append_code(
                [
                    f"def {self.function_name}(\n",
                ],
                indent=0,
            )

        self._append_code(
            [
                "auth : Auth, # class that handles generating auth headers",
                *[param.generate_signature_part() for param in params_signature],
                "\n",
            ],
            indent=1,
        )

        self._append_code(
            [
                "):\n",
            ],
            indent=0,
        )

        if self.description:
            self._append_code(
                [
                    '"""',
                    *pmcv.convert_str_to_str_list(
                        self.description, is_return_list=True
                    ),
                    '"""\n',
                ],
                1,
            )

        self._append_code([f"url = '{self.url}'\n"], indent=1)

        self.headers = {"content-type": "application/json"}

        if self.headers:
            self._append_code([f"headers = {self.headers}\n"], indent=1)

        self._append_code([f"method = '{self.request.method.lower()}'\n"], indent=1)

        self._append_code([f"params = {params_body}\n"], indent=1)

        self._append_code(
            [
                "res = gd_requests(auth = auth , method = method, url = url, headers = headers, params = params)\n\n"
            ],
            indent=1,
        )

        self._append_code(
            [
                "if not res.ok:",
                "    raise ValueError(f'Error {res.status_code}: {res.text}')",
                "else:",
                "    return res",
            ],
            indent=1,
        )

        return self.code

    def validate_code(self) -> bool:
        try:
            ast.parse(self.code)
            return True
        except SyntaxError as e:
            print(f"Invalid Python code: {e}")
            raise e from e

    # required_headers: Optional[List[str]] = field(default_factory=list)
    # default_params: Optional[List[str]] = field(default_factory=list)
    # ignored_params: Optional[List[str]] = field(default_factory=list)

    # # Derived fields for conversion logic
    # generated_url: Optional[str] = None
    # generated_headers: Optional[Dict[str, str]] = None
    # generated_params: Optional[Dict[str, str]] = None

    # def __post_init__(self):
    #     self.generate_function_name()
    #     self.generated_headers = self.generate_headers()
    #     self.generated_url = self.generate_url()
    #     self.generated_params = self.generate_params()

    def export_code(
        self,
        file_path: str = None,
        export_base_folder: str = "./EXPORT",
        config: dict = None,
        prefix: str = "",  # only applies if no file_path specified
        replace_folder: bool = False,
        is_add_imports: bool = True,
        # include_test_code: bool = True,
        debug_prn: bool = False,
    ) -> str:

        code = self.generate_request_code(config=config, is_add_imports=is_add_imports)

        if not file_path:
            file_path = f"{prefix}{self.function_name}.py"

        if export_base_folder:
            file_path = os.path.join(export_base_folder, file_path)

        if debug_prn:
            print(f"Exporting to {file_path}")

        pmfi.upsert_file(file_path, content=code, replace_folder=replace_folder)

        # Add test code if requested
        # if include_test_code:
        #     test_code = self.build_test_code()
        #     complete_code = request_code + "\n\n" + test_code
        # else:
        #     complete_code = request_code

    # def build_request_code(self) -> str:
    #     """Build the request code for a function.

    #     Args:
    #         default_params (Optional[List[str]]): List of parameters to expose as function arguments

    #     Returns:
    #         str: The request code as a string
    #     """
    #     # Parse the URL to extract the path part
    #     parsed_url = urlparse(self.url)
    #     path = parsed_url.path
    #     if parsed_url.query:
    #         path += f"?{parsed_url.query}"

    #     # Build function signature with default parameters
    #     signature = f"def {self.function_name}( auth: Dict[str, str], "
    #     param_args = []

    #     if self.default_params and self.params:
    #         for param in self.default_params:
    #             if param in self.params:
    #                 param_args.append(f"{param}: str = '{self.params[param]}', ")

    #     # Add auth parameter after any default parameters
    #     signature += (
    #         ", ".join(param_args) + "debug_api: bool = False ) -> requests.Response:"
    #     )

    #     code = [
    #         signature,
    #         f'    """Make a {self.Request.method} request to {self.url}',
    #         "    ",
    #     ]

    #     # Add parameter documentation
    #     if self.default_params and self.params:
    #         code.append("    Args:")
    #         for param in self.default_params:
    #             if param in self.params:
    #                 code.append(
    #                     f"        {param} (str, optional): Value for the {param} parameter"
    #                 )
    #         code.append("        auth (Dict[str, str]): Authentication information")
    #         code.append(
    #             "        debug_api (bool, optional): Enable debug output for API calls"
    #         )

    #     code.extend(
    #         [
    #             "    ",
    #             "    Returns:",
    #             "        requests.Response: The response from the API",
    #             '    """',
    #             f'    base_url = auth.get("base_url") if auth else ""',
    #             f'    url = f"{{base_url}}{path}"',
    #             f"    headers = {{**{self.headers}, **auth.get('headers', {{}})}}",
    #         ]
    #     )

    #     # Handle parameters, including any custom default parameters
    #     if self.default_params and self.params:
    #         # Start with original params dictionary
    #         code.append(f"    params = {self.params}")

    #         # Update with provided parameter values
    #         for param in self.default_params:
    #             if param in self.params:
    #                 code.append(f"    if {param} is not None:")
    #                 code.append(f"        params['{param}'] = {param}")
    #     else:
    #         code.append(f"    params = {self.params}")

    #     if self.body:
    #         # Normalize JSON values in body to Python syntax
    #         body_value = utils.normalize_json_to_python(self.body.raw)
    #         code.extend(
    #             [
    #                 f"    data = {body_value}",
    #                 f"    response = gd_requests(method='{self.method.lower()}', url=url, headers=headers, params=params, body=data, debug_api=debug_api)",
    #             ]
    #         )
    #     else:
    #         code.append(
    #             f"    response = gd_requests(method='{self.method.lower()}', url=url, headers=headers, params=params, debug_api=debug_api)"
    #         )

    #     code.append("    return response")
    #     return "\n".join(code)

    # def build_test_code(
    #     self,
    #     func_name: Optional[str] = None,
    #     default_params: Optional[List[str]] = None,
    # ) -> str:
    #     """Build the test code for a function.

    #     Args:
    #         func_name (Optional[str]): Name of the function to test.
    #             If None, uses the converter's function_name.
    #         default_params (Optional[List[str]]): List of parameters
    #             exposed as function arguments.

    #     Returns:
    #         str: The test code as a string
    #     """
    #     # Use provided function name or fall back to the converter's function name
    #     func_name = func_name or self.function_name

    #     # Use provided default params or fall back to the converter's default params
    #     params_to_use = default_params or self.default_params

    #     param_args = []
    #     if params_to_use:
    #         # Add default values for all parameters in test function
    #         param_args = [f"{param}= {self.parms or 'None'}" for param in params_to_use]

    #     return "\n".join(
    #         [
    #             "",
    #             f"def test_{func_name}({', '.join(param_args + ['auth: Dict[str, str] = None, debug_api: bool = False'])}):",
    #             f'    """Test the {func_name} function."""',
    #             f"    auth = {{'base_url': '', 'headers': {{}}}} if auth is None else auth",
    #             f"    response = {func_name}(auth = auth, debug_api = debug_api, {', '.join(param_args)})",
    #             '    assert response.status_code == 200, f"Expected status code 200, got {{response.status_code}}"',
    #             "    return response",
    #         ]
    #     )


# @dataclass
# class PostmanCollectionConverter:
#     """Class to handle conversions for entire Postman Collections."""

#     export_folder: str
#     collection: PostmanCollection
#     converters: List[PostmanRequestConverter] = field(default_factory=list)

#     customize: Dict[str, Dict] = field(default_factory=dict)
#     required_headers: List[str] = field(default_factory=list)

#     @classmethod
#     def from_postman_collection(
#         cls,
#         postman_path: str,
#         export_folder: str,
#         customize: Optional[Dict[str, Dict]] = None,
#         required_headers: Optional[List[str]] = None,
#         is_replace: bool = False,
#         is_include_test_code: bool = True,
#     ) -> "PostmanCollectionConverter":
#         """Load a PostmanCollection from a file.

#         Args:
#             postman_path (str): Path to the Postman collection file
#             export_folder (str): Folder to export the generated files to
#             customize (Optional[Dict[str, Dict]]): Customization options for functions
#             required_headers (Optional[List[str]]): List of header keys to include

#         Returns:
#             PostmanCollectionConverter: Converter instance for the collection
#         """
#         collection = PostmanCollection.from_file(postman_path)

#         collection_converter = cls(
#             collection=collection,
#             export_folder=export_folder,
#             customize=customize or {},
#             required_headers=required_headers or [],
#         )

#         if is_replace:
#             utils.upsert_folder(export_folder, is_replace=True)

#         collection_converter.generate_conversion_files(
#             is_replace=False,
#             is_include_test_code=is_include_test_code,
#         )
#         return collection_converter

#     def get_customize(self, function_name):
#         """Get the customization options for a specific function."""
#         return self.customize.get(function_name, {})

#     def generate_conversion_files(
#         self, is_replace: bool = False, is_include_test_code: bool = True
#     ) -> List[PostmanRequestConverter]:
#         """Generate implementation files for each request in the collection.

#         Args:
#             is_replace (bool): Whether to replace existing files. Defaults to True.
#             is_include_test_code (bool): Whether to include test code. Defaults to True

#         Returns:
#             List[PostmanRequestConverter]: List of converters used to generate the files
#         """

#         for request in self.collection.requests:
#             # Generate the function name that would be used
#             function_name = PostmanRequestConverter._generate_function_name(
#                 request.name, request.method
#             )

#             # Get any customizations for this function
#             customize = self.get_customize(function_name)

#             # Use function-specific required_headers if provided, or class-wide required_headers otherwise
#             req_headers = customize.get("required_headers", self.required_headers)

#             # Convert request to a PostmanRequestConverter
#             converter = PostmanRequestConverter.from_postman_request(
#                 request=request,
#                 export_folder=self.export_folder,
#                 is_include_test_code=is_include_test_code,
#                 is_replace=is_replace,
#                 required_headers=req_headers,
#                 **{k: v for k, v in customize.items() if k != "required_headers"},
#             )

#             self.converters.append(converter)

#         return self.converters
