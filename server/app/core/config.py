from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Document Research Assistant"
    app_env: str = "local"
    debug: bool = True
    database_url: str = "sqlite:///./research_assistant.db"
    client_origin: str = "http://localhost:5173"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.2
    groq_timeout_seconds: float = 60.0
    vector_store_provider: str = "chroma"
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "research_documents"
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    retrieval_top_k: int = 6
    summary_top_k: int = 8
    report_top_k: int = 12
    vercel: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() == "release":
            return False
        return value

    @model_validator(mode="after")
    def apply_vercel_defaults(self) -> "Settings":
        if not self.vercel:
            return self

        if self.database_url == "sqlite:///./research_assistant.db":
            self.database_url = "sqlite:////tmp/research_assistant.db"
        if self.chroma_persist_dir == "./chroma_db":
            self.chroma_persist_dir = "/tmp/chroma_db"
        if self.upload_dir == "./uploads":
            self.upload_dir = "/tmp/uploads"
        if self.vector_store_provider == "chroma":
            self.vector_store_provider = "sqlite"
        if self.app_env == "local":
            self.app_env = "production"
        if self.debug is True:
            self.debug = False
        if self.embedding_provider == "sentence_transformers":
            self.embedding_provider = "hashing"
            self.embedding_model = "local-hashing-384"

        return self

    @property
    def client_origins(self) -> list[str]:
        return [origin.strip() for origin in self.client_origin.split(",") if origin.strip()]


settings = Settings()
