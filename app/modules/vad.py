"""
VAD (Voice Activity Detection) 语音活动检测模块
负责从音频中检测并分离出说话片段
"""
import logging
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class VAD:
    """语音活动检测器"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration: float = 0.3,
        max_speech_duration: float = 30.0,
        min_silence_duration: float = 0.5
    ):
        """
        初始化VAD
        
        Args:
            sample_rate: 采样率
            threshold: 能量阈值
            min_speech_duration: 最小语音持续时间（秒）
            max_speech_duration: 最大语音持续时间（秒）
            min_silence_duration: 最小静音持续时间（秒）
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_samples = int(min_speech_duration * sample_rate)
        self.max_speech_samples = int(max_speech_duration * sample_rate)
        self.min_silence_samples = int(min_silence_duration * sample_rate)
        
    def detect_speech(self, audio_data: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        检测音频中的语音活动
        
        Args:
            audio_data: PCM音频数据
            
        Returns:
            (是否检测到语音, 语音片段数据)
        """
        try:
            # 将字节数据转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 如果音频太短，直接返回
            if len(audio_array) < self.min_speech_samples:
                logger.debug("音频太短，未检测到语音")
                return False, None
            
            # 如果音频太长，截断
            if len(audio_array) > self.max_speech_samples:
                logger.warning(f"音频超过最大长度，截断到 {self.max_speech_samples} 采样点")
                audio_array = audio_array[:self.max_speech_samples]
            
            # 计算能量（简化的VAD方法）
            # 归一化
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 计算短时能量
            frame_length = int(0.025 * self.sample_rate)  # 25ms帧
            hop_length = int(0.010 * self.sample_rate)    # 10ms跳跃
            
            energy = []
            for i in range(0, len(audio_float) - frame_length, hop_length):
                frame = audio_float[i:i + frame_length]
                frame_energy = np.sum(frame ** 2) / frame_length
                energy.append(frame_energy)
            
            energy = np.array(energy)
            
            # 简单的能量阈值检测
            # 计算能量的统计信息
            mean_energy = np.mean(energy)
            std_energy = np.std(energy)
            adaptive_threshold = mean_energy + self.threshold * std_energy
            
            # 检测语音帧
            speech_frames = energy > adaptive_threshold
            
            # 统计语音帧数量
            speech_ratio = np.sum(speech_frames) / len(speech_frames) if len(speech_frames) > 0 else 0
            
            # 如果语音帧比例超过30%，认为检测到语音
            has_speech = speech_ratio > 0.3
            
            if has_speech:
                logger.info(f"检测到语音活动: {speech_ratio:.2%} 语音帧")
                # 返回原始音频数据
                return True, audio_data
            else:
                logger.debug(f"未检测到足够的语音活动: {speech_ratio:.2%} 语音帧")
                return False, None
                
        except Exception as e:
            logger.error(f"VAD检测失败: {e}")
            # 出错时，假设有语音，返回原始数据
            return True, audio_data
    
    def extract_speech_segments(self, audio_data: bytes) -> list:
        """
        从音频中提取多个语音片段
        
        Args:
            audio_data: PCM音频数据
            
        Returns:
            语音片段列表
        """
        try:
            has_speech, speech_data = self.detect_speech(audio_data)
            if has_speech and speech_data:
                return [speech_data]
            return []
        except Exception as e:
            logger.error(f"提取语音片段失败: {e}")
            return []

