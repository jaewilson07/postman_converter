from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


@dataclass
class Auth(ABC):
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        pass
