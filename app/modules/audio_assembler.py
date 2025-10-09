"""
音频组装模块
负责接收流式音频数据并组装成完整音频
"""
import base64
import logging
from typing import Optional, Dict, Any
from io import BytesIO

logger = logging.getLogger(__name__)


class AudioAssembler:
    """音频组装器"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        初始化音频组装器
        
        Args:
            sample_rate: 采样率
            channels: 声道数
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_buffer = BytesIO()
        self.context: Dict[str, Any] = {}
        self.total_frames = 0
        
    def add_chunk(self, audio_data: str, context: Optional[Dict[str, Any]] = None) -> int:
        """
        添加音频块
        
        Args:
            audio_data: Base64编码的音频数据
            context: 上下文信息
            
        Returns:
            当前缓冲区的总字节数
        """
        try:
            # 解码Base64音频数据
            audio_bytes = base64.b64decode(audio_data)
            
            # 写入缓冲区
            self.audio_buffer.write(audio_bytes)
            self.total_frames += len(audio_bytes)
            
            # 更新上下文
            if context:
                self.context.update(context)
            
            logger.debug(f"添加音频块: {len(audio_bytes)} 字节, 总计: {self.total_frames} 字节")
            
            return self.total_frames
            
        except Exception as e:
            logger.error(f"添加音频块失败: {e}")
            raise
    
    def get_audio(self) -> bytes:
        """
        获取组装后的完整音频
        
        Returns:
            音频字节数据
        """
        self.audio_buffer.seek(0)
        audio_data = self.audio_buffer.read()
        logger.info(f"获取完整音频: {len(audio_data)} 字节")
        return audio_data
    
    def get_context(self) -> Dict[str, Any]:
        """
        获取上下文信息
        
        Returns:
            上下文字典
        """
        return self.context.copy()
    
    def reset(self):
        """重置组装器"""
        self.audio_buffer = BytesIO()
        self.context = {}
        self.total_frames = 0
        logger.debug("音频组装器已重置")
    
    def get_duration(self) -> float:
        """
        获取音频时长（秒）
        
        Returns:
            音频时长
        """
        # 假设16-bit PCM音频
        bytes_per_sample = 2
        total_samples = self.total_frames // (bytes_per_sample * self.channels)
        duration = total_samples / self.sample_rate
        return duration

