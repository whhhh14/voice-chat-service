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
    llm_base_url: str = "http://192.168.111.3:8093/v1"
    
    # 意图理解配置
    intent_system_prompt_path: str = "conf/system_prompt_intent.txt"
    
    # 回复生成配置
    generator_system_prompt_path: str = "conf/system_prompt_generator.txt"
    
    # RAG配置
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.7
    
    # TTS配置
    tts_language: str = "EN_NEWEST"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

