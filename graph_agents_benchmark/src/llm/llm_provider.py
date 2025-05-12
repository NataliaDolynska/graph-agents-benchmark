import os
from typing import Tuple

from google.auth.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from graph_agents_benchmark.src.models import Frameworks


class ModelsProvider:

    @staticmethod
    def provide(framework: Frameworks, llm_model: str):
        match framework:
            case Frameworks.LANGCHAIN:
                return ModelsProvider.__get_langchain(llm_model)
            case Frameworks.LLAMA_INDEX:
                return ModelsProvider.__get_llama_index(llm_model)
            case Frameworks.CUSTOM:
                return ModelsProvider.__get_custom(llm_model)

    @staticmethod
    def __get_llama_index(model, **kwargs):
        from llama_index.core.settings import Settings

        if "vertex/" in model:
            from llama_index.llms.vertex import Vertex
            from llama_index.embeddings.vertex import VertexTextEmbedding
            import vertexai
            from google.oauth2 import service_account

            service_account = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
            if service_account:
                credentials = ServiceAccountCredentials.from_service_account_file(service_account)
            else:
                credentials = Credentials()
                
            model = model.replace("vertex/", "")
            llm = Vertex(model, "dev-ai-demo", "us-central1")
            embed_model = VertexTextEmbedding(
                project="dev-ai-demo", location="us-central1", credentials=credentials
            )
            vertexai.init(
                project="dev-ai-demo",
                location="us-central1",
                api_transport="grpc",
                # credentials=credentials,
            )

            Settings.llm = llm
            Settings.embed_model = embed_model
            return llm, embed_model

        elif "ollama/" in model:
            from llama_index.llms.ollama import Ollama
            from llama_index.embeddings.ollama import OllamaEmbedding

            model = model.replace("ollama/", "")
            llm = Ollama(model=model, request_timeout=60.0, **kwargs)
            embed_model = OllamaEmbedding(model_name=model, **kwargs)
            Settings.llm = llm
            Settings.embed_model = embed_model
            return llm, embed_model

        else:
            raise NotImplementedError()

    @staticmethod
    def __get_langchain(model):
        print(f"Model: {model}")
        if "vertex/" in model:
            from langchain_google_vertexai import VertexAI
            from langchain_google_vertexai import VertexAIEmbeddings
            import vertexai

            service_account = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
            if service_account:
                credentials = ServiceAccountCredentials.from_service_account_file(service_account)
            else:
                credentials = Credentials()

            model = model.replace("vertex/", "")
            print(f"NEW MODEL NAME : {model}")
            vertexai.init(
                project="dev-ai-demo",
                location="us-central1",
                api_transport="grpc",
                credentials=credentials,
            )
            llm = VertexAI(model_name=model)
            embed_model = VertexAIEmbeddings("text-embedding-005")
            return llm, embed_model

    @staticmethod
    def __get_custom(model):
        pass
