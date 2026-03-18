"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    app_name: str = "语音聊天服务"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # VAD配置
    vad_threshold: float = 0.5
    vad_min_speech_duration: float = 0.3  # 最小语音持续时间（秒）
    vad_max_speech_duration: float = 30.0  # 最大语音持续时间（秒）
    vad_min_silence_duration: float = 0.5  # 最小静音持续时间（秒）
    
    # 音频配置
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_sample_width: int = 2  # 16-bit PCM
    
    # ASR配置
    asr_model: str = "base"
    asr_language: str = "zh"
    
    # LLM配置
    llm_api_key: str = "EMPTY"
    llm_base_url: str = "http://YOUR_LLM_SERVER_IP:8093/v1"
    
    # 意图理解配置
    intent_system_prompt_path: str = "conf/system_prompt_intent.txt"
    
    # 回复生成配置
    generator_system_prompt_path: str = "conf/system_prompt_generator.txt"
    
    # RAG配置
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.2  # 降低阈值以匹配 Qwen3-Embedding 的特性
    rag_embedding_model: str = "Qwen3-Embedding-0.6B"
    
    # Embedding配置
    # 通过HTTP API调用远程Embedding服务
    embedding_api_base_url: str = "http://localhost:8002/v1"  # Qwen3-Embedding-0.6B
    embedding_api_key: str = "EMPTY"
    embedding_dim: int = 1024  # Qwen3-Embedding-0.6B 向量维度
    
    # Qdrant配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "events"
    qdrant_use_memory: bool = False  # True使用内存模式，False使用持久化模式（Docker部署）
    
    # TTS配置 (Kokoro TTS)
    # 语言代码: 'a' => American English, 'b' => British English, 'z' => Mandarin Chinese
    tts_language: str = "a"
    tts_model_path: str
    tts_voice_name: str = "af_heart"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

