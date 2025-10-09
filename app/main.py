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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于WebSocket的语音聊天服务"
)

# 创建语音聊天服务实例
voice_service = VoiceChatService()


@app.get("/")
async def get_index():
    """返回测试页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>语音聊天服务测试</title>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                .status {
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                }
                .connected {
                    background-color: #d4edda;
                    color: #155724;
                }
                .disconnected {
                    background-color: #f8d7da;
                    color: #721c24;
                }
                .message {
                    padding: 10px;
                    margin: 5px 0;
                    background-color: #e7f3ff;
                    border-left: 4px solid #2196F3;
                }
                button {
                    padding: 10px 20px;
                    margin: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                button:hover {
                    background-color: #45a049;
                }
                button:disabled {
                    background-color: #cccccc;
                    cursor: not-allowed;
                }
                #messages {
                    max-height: 400px;
                    overflow-y: auto;
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <h1>语音聊天服务测试页面</h1>
            <div id="status" class="status disconnected">未连接</div>
            
            <div>
                <button id="connectBtn" onclick="connect()">连接</button>
                <button id="disconnectBtn" onclick="disconnect()" disabled>断开</button>
                <button id="sendTestBtn" onclick="sendTestAudio()" disabled>发送测试音频</button>
            </div>
            
            <h3>消息日志</h3>
            <div id="messages"></div>
            
            <script>
                let ws = null;
                
                function updateStatus(connected) {
                    const statusDiv = document.getElementById('status');
                    const connectBtn = document.getElementById('connectBtn');
                    const disconnectBtn = document.getElementById('disconnectBtn');
                    const sendTestBtn = document.getElementById('sendTestBtn');
                    
                    if (connected) {
                        statusDiv.textContent = '已连接';
                        statusDiv.className = 'status connected';
                        connectBtn.disabled = true;
                        disconnectBtn.disabled = false;
                        sendTestBtn.disabled = false;
                    } else {
                        statusDiv.textContent = '未连接';
                        statusDiv.className = 'status disconnected';
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                        sendTestBtn.disabled = true;
                    }
                }
                
                function addMessage(message, type = 'info') {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message';
                    messageDiv.innerHTML = `<strong>[${new Date().toLocaleTimeString()}]</strong> ${message}`;
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
                
                function connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws`;
                    
                    addMessage(`正在连接到 ${wsUrl}...`);
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function(event) {
                        addMessage('WebSocket连接已建立');
                        updateStatus(true);
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addMessage(`收到消息: ${JSON.stringify(data, null, 2)}`);
                    };
                    
                    ws.onerror = function(event) {
                        addMessage('WebSocket错误');
                        console.error('WebSocket error:', event);
                    };
                    
                    ws.onclose = function(event) {
                        addMessage('WebSocket连接已关闭');
                        updateStatus(false);
                    };
                }
                
                function disconnect() {
                    if (ws) {
                        ws.close();
                        ws = null;
                    }
                }
                
                function sendTestAudio() {
                    if (!ws) {
                        addMessage('未连接到服务器');
                        return;
                    }
                    
                    // 创建测试音频数据（1秒的静音）
                    const sampleRate = 16000;
                    const duration = 1; // 秒
                    const numSamples = sampleRate * duration;
                    const buffer = new Int16Array(numSamples);
                    
                    // 生成简单的正弦波（用于测试）
                    for (let i = 0; i < numSamples; i++) {
                        buffer[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 10000;
                    }
                    
                    // 转换为Base64
                    const bytes = new Uint8Array(buffer.buffer);
                    const base64 = btoa(String.fromCharCode.apply(null, bytes));
                    
                    // 发送音频消息
                    const message = {
                        type: 'audio',
                        data: base64,
                        context: {
                            test: true,
                            timestamp: Date.now()
                        },
                        is_end: true
                    };
                    
                    ws.send(JSON.stringify(message));
                    addMessage('已发送测试音频数据');
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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

