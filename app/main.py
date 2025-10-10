"""
FastAPI WebSocket 服务主程序
"""
import logging
import json
import base64
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.config import settings
from app.models import (
    AudioMessage, MessageType, ResultMessage, 
    ErrorMessage, HeartbeatMessage
)
from app.modules.audio_assembler import AudioAssembler
from app.service import VoiceChatService
import time
import os
import tempfile
import wave

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
import loguru
logger = loguru.logger
logger.add("logs/app.log", rotation="10 MB", retention="7 days", enqueue=True, encoding="utf-8")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于WebSocket的语音聊天服务"
)

# 创建语音聊天服务实例
voice_service = VoiceChatService()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点
    处理与IPC的WebSocket连接
    """
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"新的WebSocket连接: {client_id}")
    
    # 为每个连接创建音频组装器
    audio_assembler = AudioAssembler(
        sample_rate=settings.audio_sample_rate,
        channels=settings.audio_channels
    )
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                logger.info(f"收到消息类型: {message_type}")
                
                if message_type == MessageType.AUDIO:
                    # 处理音频消息
                    await handle_audio_message(
                        websocket,
                        message,
                        audio_assembler
                    )
                
                elif message_type == MessageType.HEARTBEAT:
                    # 处理心跳消息
                    await handle_heartbeat(websocket, message)
                
                else:
                    logger.warning(f"未知消息类型: {message_type}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                error_msg = ErrorMessage(
                    code=400,
                    message="Invalid JSON format",
                    details={"error": str(e)}
                )
                await websocket.send_text(error_msg.model_dump_json())
                
            except Exception as e:
                logger.error(f"处理消息时发生错误: {e}", exc_info=True)
                error_msg = ErrorMessage(
                    code=500,
                    message="Internal server error",
                    details={"error": str(e)}
                )
                await websocket.send_text(error_msg.model_dump_json())
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {client_id}")
    
    except Exception as e:
        logger.error(f"WebSocket错误: {e}", exc_info=True)
    
    finally:
        logger.info(f"清理连接资源: {client_id}")


async def handle_audio_message(
    websocket: WebSocket,
    message: Dict[str, Any],
    audio_assembler: AudioAssembler
):
    """
    处理音频消息
    
    Args:
        websocket: WebSocket连接
        message: 音频消息
        audio_assembler: 音频组装器
    """
    try:
        audio_msg = AudioMessage(**message)
        
        # 添加音频块到组装器
        audio_assembler.add_chunk(
            audio_msg.data,
            audio_msg.context
        )
        
        # 如果是最后一帧，开始处理
        if audio_msg.is_end:
            logger.info("收到最后一帧音频，开始处理")
            
            # 获取完整音频
            complete_audio = audio_assembler.get_audio()
            context = audio_assembler.get_context()
            
            # 保存到项目tmp目录下，格式为wav
            tmp_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_file = tempfile.NamedTemporaryFile(prefix='asr_', suffix='.wav', dir=tmp_dir, delete=False)
            with wave.open(tmp_file.name, 'wb') as wf:
                wf.setnchannels(audio_assembler.channels)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(audio_assembler.sample_rate)
                wf.writeframes(complete_audio)
            logger.info(f"完整音频已保存到 {tmp_file.name}")
            
            
            # 处理音频
            result = await voice_service.process_audio(
                complete_audio,
                context
            )
            
            # 发送结果
            if result:
                await websocket.send_text(result.model_dump_json())
                logger.info("结果已发送")
            else:
                # 未检测到有效语音或处理失败
                error_msg = ErrorMessage(
                    code=204,
                    message="No valid speech detected or processing failed"
                )
                await websocket.send_text(error_msg.model_dump_json())
            
            # 重置组装器
            audio_assembler.reset()
        
    except Exception as e:
        logger.error(f"处理音频消息失败: {e}", exc_info=True)
        raise


async def handle_heartbeat(websocket: WebSocket, message: Dict[str, Any]):
    """
    处理心跳消息
    
    Args:
        websocket: WebSocket连接
        message: 心跳消息
    """
    try:
        # 回复心跳
        heartbeat = HeartbeatMessage(timestamp=time.time())
        await websocket.send_text(heartbeat.model_dump_json())
        logger.debug("心跳响应已发送")
    except Exception as e:
        logger.error(f"处理心跳失败: {e}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"监听地址: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

