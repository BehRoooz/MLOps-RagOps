import os

class Settings:
    APP_NAME: str = "RAGOPS API"
    APP_VERSION: str = "2.0.0"

    MEILI_URL: str = os.getenv("MEILI_URL", "")
    MEILI_KEY: str = os.getenv("MEILI_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "")
    PROXY_KEY: str = os.getenv("PROXY_KEY", "") 

    MEILI_INDEX: str = os.getenv("MEILI_INDEX", "documents")
    CHUNKS_INDEX: str = "chunks"
    EMBED_DIM: int = int(os.getenv("EMBED_DIM", "384"))

    # LLM and Embeddings settings for RAGAS evaluation
    LITELLM_MODEL: str = os.environ["LITELLM_MODEL"]  # Model name matching litellm config
    LITELLM_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"
    EMBEDDING_MODEL_NAME: str = os.environ["EMBEDDING_MODEL_NAME"]  # TEI embeddings via LiteLLM proxy
    TEI_EMBEDDINGS_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"  # Direct TEI endpoint
    
    # LLM and Embeddings settings for RAGAS evaluation
    LITELLM_MODEL: str = os.environ["LITELLM_MODEL"]
    LITELLM_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"
    EMBEDDING_MODEL_NAME: str = os.environ["EMBEDDING_MODEL_NAME"]
    TEI_EMBEDDINGS_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"
    

settings = Settings()
