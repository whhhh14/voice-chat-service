"""
ASR (Automatic Speech Recognition) 语音识别模块
负责将语音转换为文本
"""
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

import loguru

logger = loguru.logger


class ASR:
    """语音识别器"""
    
    def __init__(self, model_path: str, language: str = "en"):
        """
        初始化ASR
        
        Args:
            model: 模型名称
            language: 语言代码
        """
        self.model_path = model_path
        self.language = language
        logger.info(f"初始化ASR: model={model_path}, language={language}")
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # 加载模型和处理器
        self.processor = WhisperProcessor.from_pretrained(model_path)
        self.model = WhisperForConditionalGeneration.from_pretrained(
            model_path,
            dtype=torch_dtype,
            use_safetensors=True,
            attn_implementation="sdpa"  # 内存优化的注意力机制
        )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        
    def recognize(self, audio_data):
        """
        识别语音

        Args:
            audio_data: 可以是float32数组（如librosa.load输出），或原始PCM字节流

        Returns:
            ASR识别结果
        """
        import numpy as np

        try:
            logger.info("开始语音识别")

            # 如果audio_data是bytes，则将其转为numpy float32
            if isinstance(audio_data, bytes):
                # 假设输入是16-bit PCM little-endian, 单通道
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif isinstance(audio_data, np.ndarray):
                audio_np = audio_data.astype(np.float32)
            else:
                raise ValueError("audio_data必须是bytes或numpy数组")

            # Whisper 要求输入为 16kHz、单通道、float32(-1~1)
            # 为避免 dtype 错误，确保 input_features 的 dtype 与模型权重一致
            input_features = self.processor(
                audio_np,
                sampling_rate=16000,
                return_tensors="pt"
            ).input_features

            # 自动匹配 input_features 到模型预期 dtype
            input_features = input_features.to(self.device, dtype=self.model.dtype)

            # 生成文本
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                language=self.language, task="transcribe"
            )

            with torch.no_grad():
                predicted_ids = self.model.generate(
                    input_features,
                    forced_decoder_ids=forced_decoder_ids
                )[0]

            # 解码生成的文本
            transcription = self.processor.decode(predicted_ids, skip_special_tokens=True)

            # 使用Whisper处理器的标准化方法
            normalized_transcription = self.processor.tokenizer._normalize(transcription)
            return normalized_transcription

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return None
    
    async def recognize_async(self, audio_data: str):
        """
        异步识别语音
        
        Args:
            audio_data: PCM音频数据
            
        Returns:
            ASR识别结果
        """
        # 实际应用中，这里可以调用异步的ASR服务
        return self.recognize(audio_data)


if __name__ == "__main__":
    # CUDA_VISIBLE_DEVICES=5 python -m app.modules.asr

    import librosa
    asr = ASR(model_path="/data/work/MaxZeng/work/models/whisper-large-v3", language="en")
    audio_data, sr = librosa.load("tmp/tmprwzsjcuv.wav", sr=16000)
    result = asr.recognize(audio_data)
    print(f"result: {result}")
