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

import onnxruntime
from onnxruntime import InferenceSession
from kokoro_onnx import Kokoro

import loguru

logger = loguru.logger


class TTS:
    """语音合成器 (ONNX版本)"""
    
    def __init__(
        self,
        language: str = "en-us",  # 'en-us' => American English
        model_path: str = None,
        voice_name: str = "af_heart"
    ):
        """
        初始化TTS
        
        Args:
            language: TTS语言代码 ('en-us' => American English)
            model_path: Kokoro ONNX模型路径 (如: kokoro-v1.0.onnx)
            voice_name: 声音名称 (如: af_sarah, af_heart, etc.)
        """
        self.language = language
        self.model_path = model_path
        self.voices_path = os.path.join(os.path.dirname(self.model_path), "voices-v1.0.bin")
        self.voice_name = voice_name
        self.sample_rate = 16000  # 最终输出采样率
        
        # 创建ONNX Runtime Session
        providers = onnxruntime.get_available_providers()
        logger.info(f"可用的ONNX Runtime提供者: {providers}")
        
        # 配置Session选项
        sess_options = onnxruntime.SessionOptions()
        cpu_count = os.cpu_count() if os.cpu_count() < 16 else 16
        logger.info(f"设置线程数为CPU核心数: {cpu_count}")
        sess_options.intra_op_num_threads = cpu_count
        
        # 创建推理Session
        self.session = InferenceSession(
            model_path, providers=providers, sess_options=sess_options
        )
        
        # 初始化Kokoro ONNX模型
        self.kokoro = Kokoro.from_session(self.session, self.voices_path)
        
        logger.info(f"初始化Kokoro ONNX TTS: language={language}, model_path={model_path}, voice={voice_name}")
    
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
            
            # 使用Kokoro ONNX生成音频
            samples, sample_rate = self.kokoro.create(
                text,
                voice=self.voice_name,
                speed=speed,
                lang=self.language
            )
            
            logger.info(f"原始采样率: {sample_rate}Hz")
            
            # samples是float32 numpy数组
            audio_np = samples.astype(np.float32)
            
            # 使用临时目录生成音频文件
            tmp_dir = os.path.join(os.path.dirname(__file__), '../..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix='tts_', suffix='.wav', dir=tmp_dir, delete=False) as src_file:
                src_path = src_file.name
            logger.info(f"完整音频文件路径: {src_path}")

            # 保存当前音频为 wav 文件
            sf.write(src_path, audio_np, sample_rate)
            
            # 重采样到16K
            if sample_rate != self.sample_rate:
                audio_np = librosa.resample(audio_np, orig_sr=sample_rate, target_sr=self.sample_rate)
                logger.info(f"重采样到 {self.sample_rate}Hz")
            
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
    # python -m app.modules.tts
    # 'en-us' => American English
    import time
    import sys

    # 使用示例:
    # python -m app.modules.tts /path/to/kokoro-v1.0.onnx
    
    if len(sys.argv) < 2:
        print("用法: python -m app.modules.tts <model_path>")
        print("示例: python -m app.modules.tts kokoro-v1.0.onnx")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    tts = TTS(
        language="en-us", 
        voice_name="af_sarah", 
        model_path=model_path
    )
    
    # warmup
    tts.synthesize("Open the door")

    t1 = time.time()
    result = tts.synthesize("Hello, world!")
    t2 = time.time()
    print(f"合成时间: {t2 - t1} 秒")
    if result:
        print(f"合成成功: {len(result.audio)} 字节, 采样率: {result.sample_rate}Hz")
