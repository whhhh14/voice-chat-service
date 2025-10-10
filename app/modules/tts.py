"""
TTS (Text-to-Speech) 语音合成模块
负责将文本转换为语音
"""
import numpy as np
from typing import Optional
from app.models import TTSResult
import tempfile
import os
import numpy as np
import io
import librosa
import soundfile as sf

import torch
from melo.api import TTS as MeloTTS


import loguru

logger = loguru.logger


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
            logger.info(f"开始语音合成: {text}")
            speaker_key = "EN-Newest"
            speaker_id = 0

            # 使用临时目录生成音频文件
            tmp_dir = os.path.join(os.path.dirname(__file__), '../..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix='tts_', suffix='.wav', dir=tmp_dir, delete=False) as src_file:
                src_path = src_file.name
            logger.info(f"完整音频文件路径: {src_path}")

            self.model.tts_to_file(text, speaker_id, src_path, speed=speed)

            # 读取合成的 WAV 文件
            with open(src_path, "rb") as f:
                wav_bytes = f.read()
            
            # 使用 soundfile 和 librosa 加载 WAV (到 float32, 自动采样率)
            audio_np, original_sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
            if len(audio_np.shape) > 1:
                audio_np = np.mean(audio_np, axis=1)  # 转单声道
            
            # 重采样到16K
            if original_sr != 16000:
                audio_np = librosa.resample(audio_np, orig_sr=original_sr, target_sr=16000)
            
            # 转为 16bit PCM
            audio_int16 = (audio_np * 32767.0).astype(np.int16).tobytes()
            audio_bytes = audio_int16
            
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
    # CUDA_VISIBLE_DEVICES=5 python -m app.modules.tts
    tts = TTS(language="EN_NEWEST")
    tts.synthesize("Hello, world!")
