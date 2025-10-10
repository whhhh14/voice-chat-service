"""
TTS (Text-to-Speech) 语音合成模块
负责将文本转换为语音
"""
import logging
import numpy as np
from typing import Optional
from app.models import TTSResult
import tempfile
import os

import torch
from melo.api import TTS as MeloTTS


logger = logging.getLogger(__name__)


class TTS:
    """语音合成器"""
    
    def __init__(
        self,
        language: str = "EN_NEWEST",
    ):
        """
        初始化TTS
        
        Args:
            language: TTS语言
        """
        self.language = language
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = MeloTTS(language=language, device=device)
        self.sample_rate = 16000
        
        logger.info(f"初始化TTS: language={language}")
    
    def synthesize(self, text: str, speed: float = 0.8) -> Optional[TTSResult]:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            
        Returns:
            TTS合成结果
        """
        try:
            logger.info(f"开始语音合成: {text[:50]}...")
            speaker_key = "EN-Newest"
            speaker_id = 0

            # 使用临时目录生成音频文件
            with tempfile.TemporaryDirectory() as tmpdir:
                src_path = os.path.join(tmpdir, "tts.wav")
                self.model.tts_to_file(text, speaker_id, src_path, speed=speed)
                with open(src_path, "rb") as f:
                    audio_bytes = f.read()
            
            logger.info(f"合成完成: {len(audio_bytes)} 字节")
            
            return TTSResult(
                audio=audio_bytes,
                format="pcm",
                sample_rate=self.sample_rate
            )
            
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return None
    
    async def synthesize_async(self, text: str, speed: float = 0.8) -> Optional[TTSResult]:
        """
        异步合成语音
        
        Args:
            text: 要合成的文本
            
        Returns:
            TTS合成结果
        """
        return self.synthesize(text, speed)


if __name__ == "__main__":
    # CUDA_VISIBLE_DEVICES=1 python -m app.modules.tts
    tts = TTS(language="EN_NEWEST")
    tts.synthesize("Hello, world!")
