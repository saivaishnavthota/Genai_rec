import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://postgres:vaishnav@localhost:5432/postgres"
    postgres_user: str = "postgres"
    postgres_password: str = "vaishnav"
    postgres_db: str = "postgres"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # === Ollama LLM configuration ===
    use_ollama: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"  # Default model, can be overridden via env var
    llm_temperature: float = 0.3
    llm_max_tokens: int = 300         # per response
    llm_timeout_seconds: int = 300    # Increased timeout for detailed explanations (5 minutes)

    # (Optional) Local llama.cpp fallback (not required now, but kept if you want)
    model_path: Optional[str] = None
    llm_n_ctx: int = 2048
    llm_n_threads: int = 4
    llm_n_batch: int = 64
    llm_seed: int = 42
    chat_format: Optional[str] = None    # only for direct llama.cpp fallback
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "voyageuraryan@gmail.com"
    smtp_password: str = "lqlp aymq texs efrk"  # Gmail App Password
    email_from: str = "voyageuraryan@gmail.com"
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads"
    
    # Application Settings
    debug: bool = True
    environment: str = "development"
    secret_key: str = "your-super-secret-key-change-this-in-production"
    
    # Scoring Configuration
    match_score_weight: float = 0.5
    ats_score_weight: float = 0.5
    shortlist_threshold: int = 70
    requalify_threshold: int = 60
    
    # Resume Update Configuration
    max_resume_update_attempts: int = 3
    
    # Frontend URL for generating review links (can be overridden via FRONTEND_URL env var)
    frontend_url: str = "http://localhost:3000"
    
    # Google Calendar/Meet Configuration
    use_service_account: bool = False
    token_file: str = "token.json"
    service_account_file: str = "service_account.json"
    impersonate_user: Optional[str] = None
    meet_timezone: str = "Asia/Kolkata"
    meet_calendar_id: str = "primary"
    
    # AI Interview Module Configuration
    # MinIO/S3 Storage (set to empty string to disable for demo)
    minio_endpoint: str = ""
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    s3_bucket: str = "interview-blobs"
    s3_use_ssl: bool = False
    s3_region: str = "us-east-1"
    
    # Ollama Configuration (for RAG scoring)
    # Default: host.docker.internal for Docker (Windows/Mac), localhost for local dev
    # Override via OLLAMA_API_URL env var (set in docker-compose.yml)
    ollama_api_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    
    # Feature Flags
    enable_diarization: bool = False
    enable_ocr: bool = False
    
    # Policy & Rubric Versions
    policy_version: str = "1.0"
    rubric_version: str = "1.0"
    
    # Proctoring Configuration
    proctor_fps: int = 2  # Frames per second for proctoring
    clip_duration_min: float = 6.0  # Minimum clip duration in seconds
    clip_duration_max: float = 10.0  # Maximum clip duration in seconds
    
    # ASR Configuration
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu, cuda
    whisper_compute_type: str = "int8"  # int8, int8_float16, int16, float16, float32
    
    # RAG Configuration
    rag_top_k: int = 5
    rag_rerank_top_n: int = 3
    rag_hybrid_alpha: float = 0.5  # 0.0 = pure BM25, 1.0 = pure dense
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
        protected_namespaces = ('settings_',)  # Fix Pydantic warning for model_path

# Create settings instance
settings = Settings()

# Override email settings to ensure correct configuration
# This prevents environment variables from overriding the correct email config
settings.smtp_host = "smtp.gmail.com"
settings.smtp_port = 587
settings.smtp_username = "voyageuraryan@gmail.com"
settings.smtp_password = "lqlp aymq texs efrk"  # Gmail App Password
settings.email_from = "voyageuraryan@gmail.com"
