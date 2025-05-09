from enum import Enum


class Frameworks(str, Enum):
    LLAMA_INDEX = 'llamaindex'
    LANGCHAIN = 'langchain'
    CUSTOM = 'custom'