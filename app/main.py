"""
FastAPI WebSocket 服务主程序
"""
import json
import base64
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from app.config import settings
from app.models import (
    AudioMessage, MessageType, ResultMessage, 
    ErrorMessage, HeartbeatMessage, Event, EventSearchQuery
)
from app.modules.audio_assembler import AudioAssembler
from app.service import VoiceChatService
import time
import os
import tempfile
import wave

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


def _load_events_from_json(json_file: str = "data/test_events.json") -> List[Event]:
    """
    从JSON文件加载测试事件数据
    
    Args:
        json_file: JSON文件路径（相对于项目根目录）
        
    Returns:
        事件列表
    """
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        json_path = project_root / json_file
        
        if not json_path.exists():
            logger.warning(f"测试数据文件不存在: {json_path}")
            return []
        
        # 读取JSON文件
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换为Event对象
        events = []
        for event_data in data.get('events', []):
            events.append(Event(**event_data))
        
        logger.info(f"从 {json_file} 加载了 {len(events)} 个事件")
        return events
        
    except Exception as e:
        logger.error(f"加载测试数据失败: {e}")
        return []


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("=" * 60)
    logger.info("检查向量数据库状态...")
    
    try:
        # 检查数据库是否为空
        collection_info = voice_service.rag.get_collection_info()
        count = collection_info.get("points_count", 0)
        
        if count == 0:
            logger.info("数据库为空，从JSON文件加载测试数据...")
            
            # 从JSON文件加载事件
            events = _load_events_from_json()
            
            if events:
                # 导入到向量数据库
                success_count = voice_service.rag.add_events_batch(events)
                logger.info(f"✓ 已自动导入 {len(success_count)} 个测试事件")
                
                # 统计事件类型
                event_types = {}
                for event in events:
                    event_name = event.event_name
                    event_types[event_name] = event_types.get(event_name, 0) + 1
                
                for event_name, count in event_types.items():
                    logger.info(f"  - {event_name}: {count}个")
            else:
                logger.warning("未能加载测试数据，请检查 data/test_events.json 文件")
        else:
            logger.info(f"数据库已有 {count} 个事件，跳过自动导入")
    except Exception as e:
        logger.warning(f"初始化测试数据失败: {e}")
        logger.info("服务将继续运行，但RAG功能可能不可用")
    
    logger.info("=" * 60)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.post("/api/events")
async def create_event(event: Event):
    """
    创建单个事件
    
    Args:
        event: 事件对象
        
    Returns:
        事件ID
    """
    try:
        event_id = voice_service.rag.add_event(event)
        return {
            "success": True,
            "event_id": event_id,
            "message": "事件创建成功"
        }
    except Exception as e:
        logger.error(f"创建事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/batch")
async def create_events_batch(events: list[Event]):
    """
    批量创建事件
    
    Args:
        events: 事件列表
        
    Returns:
        事件ID列表
    """
    try:
        event_ids = voice_service.rag.add_events_batch(events)
        return {
            "success": True,
            "event_ids": event_ids,
            "count": len(event_ids),
            "message": f"成功创建 {len(event_ids)} 个事件"
        }
    except Exception as e:
        logger.error(f"批量创建事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/search")
async def search_events(query: EventSearchQuery):
    """
    搜索事件
    
    Args:
        query: 搜索查询
        
    Returns:
        搜索结果
    """
    try:
        result = voice_service.rag.retrieve(
            query=query.query,
            context=None,
            filters=query.filters,
            top_k=query.top_k
        )
        return {
            "success": True,
            "query": query.query,
            "results": [
                {
                    "document": doc,
                    "score": score,
                    "metadata": metadata
                }
                for doc, score, metadata in zip(result.documents, result.scores, result.metadata)
            ],
            "count": len(result.documents)
        }
    except Exception as e:
        logger.error(f"搜索事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/collection/info")
async def get_collection_info():
    """
    获取事件集合信息
    
    Returns:
        集合信息
    """
    try:
        info = voice_service.rag.get_collection_info()
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        logger.error(f"获取集合信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        reload=False,
        log_level="info",
        workers=1
    )
