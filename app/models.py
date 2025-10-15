"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    AUDIO = "audio"
    TEXT = "text"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class SkillType(str, Enum):
    """技能类型"""
    COMMAND = "command"  # 固定指令
    QA = "qa"  # 问答
    CHAT = "chat"  # 闲聊


class AudioMessage(BaseModel):
    """音频消息"""
    type: MessageType = MessageType.AUDIO
    data: str = Field(..., description="Base64编码的PCM音频数据")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    is_end: bool = Field(default=False, description="是否为最后一帧")


class TextMessage(BaseModel):
    """文本消息"""
    type: MessageType = MessageType.TEXT
    text: str = Field(..., description="文本内容")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class ResultMessage(BaseModel):
    """结果消息"""
    type: MessageType = MessageType.RESULT
    skill_id: str = Field(..., description="技能ID")
    text: str = Field(..., description="回复文本")
    audio: Optional[str] = Field(default=None, description="Base64编码的音频数据")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class ErrorMessage(BaseModel):
    """错误消息"""
    type: MessageType = MessageType.ERROR
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")


class HeartbeatMessage(BaseModel):
    """心跳消息"""
    type: MessageType = MessageType.HEARTBEAT
    timestamp: float = Field(..., description="时间戳")


class IntentResult(BaseModel):
    """意图识别结果"""
    skill_id: str = Field(..., description="技能ID")
    skill_type: SkillType = Field(..., description="技能类型")
    confidence: float = Field(..., description="置信度")
    entities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="实体信息")
    is_fixed_command: bool = Field(..., description="是否为固定指令")


class RAGResult(BaseModel):
    """RAG检索结果"""
    documents: List[str] = Field(..., description="检索到的文档")
    scores: List[float] = Field(..., description="相关性分数")
    metadata: Optional[List[Dict[str, Any]]] = Field(default=None, description="文档元数据")


class LLMResponse(BaseModel):
    """LLM回复结果"""
    text: str = Field(..., description="生成的文本")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")


class TTSResult(BaseModel):
    """TTS合成结果"""
    audio: bytes = Field(..., description="音频数据")
    format: str = Field(default="pcm", description="音频格式")
    sample_rate: int = Field(..., description="采样率")


class EventType(int, Enum):
    """事件类型枚举"""
    DEFINED = 1  # 已定义事件
    UNDEFINED = 2  # 未定义事件


class Event(BaseModel):
    """事件模型"""
    event_time: str = Field(..., description="事件发生时间，格式：YYYY-MM-DD HH:MM:SS")
    event_type_id: int = Field(..., description="事件类型ID: 1-已定义事件, 2-未定义事件")
    event_name: str = Field(..., description="事件名称")
    event_desc: Optional[str] = Field(None, description="事件描述（由VL模型生成）")
    device_id: int = Field(..., description="记录事件的设备ID")
    device_name: str = Field(..., description="记录事件的设备位置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_time": "2025-10-13 10:10:01",
                "event_type_id": 1,
                "event_name": "快递送达",
                "event_desc": "一个穿红衣服的男子送达了快递",
                "device_id": 1,
                "device_name": "门口"
            }
        }


class EventSearchQuery(BaseModel):
    """事件搜索查询"""
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(default=5, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")

