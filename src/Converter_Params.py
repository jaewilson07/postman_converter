from dataclasses import dataclass
from src.client.LibEnum import LibEnum
import src.utils.convert as pmcv
from src._1_models import PostmanRequest, PostmanUrlEncodedParam


class QueryValueType(LibEnum):
    LONG = "<long>"
    INTEGER = "<integer>"
    BOOLEAN = "<boolean>"
    STRING = "<string>"
    NUMBER = "<number>"
    ARRAY = "<array>"
    OBJECT = "<object>"
    DEFAULT = "<default>"

    @property
    def python_type(self):
        mapping = {
            QueryValueType.LONG: "int",
            QueryValueType.INTEGER: "int",
            QueryValueType.STRING: "str",
            QueryValueType.NUMBER: "float",
            QueryValueType.BOOLEAN: "bool",
            QueryValueType.ARRAY: "list",
            QueryValueType.OBJECT: "dict",
            QueryValueType.DEFAULT: "Any",
        }
        return mapping.get(self)


def map_query_type_to_enum(type_str: str) -> QueryValueType:
    for member in QueryValueType:
        if member.value == type_str:
            return member

    return QueryValueType.DEFAULT  # Default


@dataclass
class PostmanParamConverter:
    param: PostmanUrlEncodedParam

    key: str
    name: str
    value: str = None
    description: str = ""
    python_type: str = "Any"
    is_signature: bool = False

    @classmethod
    def from_param(cls, param, is_signature: bool = False):

        cp = cls(
            param=param,
            key=param.key,
            name=pmcv.to_snake_case(param.key),
            description=param.description,
            python_type=map_query_type_to_enum(param.value).python_type,
            value=param.value if not param.value.startswith("<") else None,
            is_signature=is_signature,
        )
        return cp

    def _generate_value_str(self, is_signature: bool = False):

        if self.python_type == "str" and self.value is not None:
            return f"'{self.value}'"

        return self.value if not is_signature else self.name

    def generate_signature_part(self):
        # For function signature

        value_str = self._generate_value_str()

        return f"{self.name}: {self.python_type} = {value_str},  # {self.description}"

    # def hardcoded_declaration(self):

    #     return f"{self.name} = {self._generate_value_str()}  # {self.description}"
