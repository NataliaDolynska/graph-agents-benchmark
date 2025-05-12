from enum import Enum
from symtable import Function
from typing import Union, List, Generator, Optional, Callable
from pydantic import BaseModel


class Frameworks(str, Enum):
    LLAMA_INDEX = 'llamaindex'
    LANGCHAIN = 'langchain'
    CUSTOM = 'custom'


class Column(BaseModel):
    path: Union[str, List[str]]
    alias: str
    required: bool = True
    map_fn: Optional[Callable] = None
