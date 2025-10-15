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
import librosa
import soundfile as sf

import torch
from kokoro import KPipeline, KModel

import loguru

logger = loguru.logger


class TTS:
    """语音合成器"""
    
    def __init__(
        self,
        language: str = "a",  # 'a' => American English
        model_path: str = None,
        voice_name: str = "af_heart"
    ):
        """
        初始化TTS
        
        Args:
            language: TTS语言代码 ('a' => American English, 'z' => Mandarin Chinese, etc.)
            model_path: Kokoro模型路径
            voice_name: 声音名称
        """
        self.language = language
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = model_path
        self.voice_name = voice_name
        self.sample_rate = 16000  # 最终输出采样率
        
        # 初始化Kokoro模型
        self.kmodel = KModel(
            repo_id='hexgrad/Kokoro-82M',
            config=f"{model_path}/config.json",
            model=f"{model_path}/kokoro-v1_0.pth",
        ).to(device).eval()

        self.pipeline = KPipeline(
            repo_id='hexgrad/Kokoro-82M', 
            lang_code=language, 
            model=self.kmodel,
            device=device
        )
        
        # 加载voice tensor
        voice_path = f'{model_path}/voices/{voice_name}.pt'
        self.voice_tensor = torch.load(voice_path, weights_only=True)
        
        logger.info(f"初始化Kokoro TTS: language={language}, model_path={model_path}, voice={voice_name}")
    
    def synthesize(self, text: str, speed: float = 1.0) -> Optional[TTSResult]:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            speed: 语速 (默认1.0)
            
        Returns:
            TTS合成结果
        """
        try:
            logger.info(f"开始语音合成: {text}")
            
            # 使用Kokoro生成音频
            generator = self.pipeline(
                text, 
                voice=self.voice_tensor,
                speed=speed, 
                split_pattern=r'\n+'
            )
            
            # 获取生成的音频
            gs, ps, audio = next(generator)
            logger.info(f"生成文本: {gs}")
            logger.info(f"音素: {ps}")
            
            # Kokoro输出的是float32 numpy数组，采样率24000Hz
            audio_np = audio.detach().cpu().numpy().astype(np.float32)
            original_sr = 24000
            # 使用临时目录生成音频文件
            tmp_dir = os.path.join(os.path.dirname(__file__), '../..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix='tts_', suffix='.wav', dir=tmp_dir, delete=False) as src_file:
                src_path = src_file.name
            logger.info(f"完整音频文件路径: {src_path}")

            # 保存当前音频为 wav 文件
            sf.write(src_path, audio_np, original_sr)
            
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
            logger.exception("语音合成失败")
            return None
    
    async def synthesize_async(self, text: str, speed: float = 1.0) -> Optional[TTSResult]:
        """
        异步合成语音
        
        Args:
            text: 要合成的文本
            speed: 语速 (默认1.0)
            
        Returns:
            TTS合成结果
        """
        return self.synthesize(text, speed)


if __name__ == "__main__":
    # CUDA_VISIBLE_DEVICES=5 python -m app.modules.tts
    # 'a' => American English, 'z' => Mandarin Chinese
    import time

    tts = TTS(language="a", voice_name="af_heart", model_path="/data/work/MaxZeng/work/models/Kokoro-82M")
    # warmup
    tts.synthesize("Open the door")

    t1 = time.time()
    result = tts.synthesize("Hello, world!")
    t2 = time.time()
    print(f"合成时间: {t2 - t1} 秒")
    if result:
        print(f"合成成功: {len(result.audio)} 字节, 采样率: {result.sample_rate}Hz")
