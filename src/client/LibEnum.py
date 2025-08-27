from enum import Enum


class LibEnum(Enum):

    @classmethod
    def get(cls, value):
        for member in cls:
            if member.name.lower() == value.lower():
                return member
        default = getattr(cls, "default", None)
        if default is not None:
            return default
        raise AttributeError(f"{cls.__name__} does not define a 'default' member")

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.name.lower() == value.lower():
                return member

        default = getattr(cls, "default", None)
        if default is not None:
            return default
        raise AttributeError(f"{cls.__name__} does not define a 'default' member")
