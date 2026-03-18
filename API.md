# 语音聊天服务 API 文档

## 概述

这是一个基于 WebSocket 的语音聊天服务，支持实时语音输入和文本/语音输出。

## 服务信息

- **服务名称**: 语音聊天服务
- **版本**: 1.0.0
- **协议**: WebSocket
- **端口**: 8000（默认）

## 端点列表

### 1. WebSocket 连接端点

**端点**: `ws://localhost:8000/ws`

**描述**: 主要的 WebSocket 通信端点，用于实时语音交互。

### 2. HTTP 端点

#### 2.1 健康检查

**端点**: `GET /health`

**描述**: 检查服务健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "service": "语音聊天服务",
  "version": "1.0.0"
}
```

#### 2.2 测试页面

**端点**: `GET /`

**描述**: 返回一个 WebSocket 测试页面，可用于测试服务功能

## WebSocket 消息格式

### 消息类型

所有消息都是 JSON 格式，包含一个 `type` 字段标识消息类型：

- `audio`: 音频消息（客户端→服务器）
- `text`: 文本消息
- `result`: 结果消息（服务器→客户端）
- `error`: 错误消息（服务器→客户端）
- `heartbeat`: 心跳消息（双向）

### 1. 音频消息 (Audio Message)

**方向**: 客户端 → 服务器

**描述**: 发送 PCM 音频数据到服务器

**格式**:
```json
{
  "type": "audio",
  "data": "base64_encoded_pcm_audio_data",
  "context": {
    "user_id": "123",
    "session_id": "abc",
    "custom_field": "value"
  },
  "is_end": false
}
```

**字段说明**:
- `type` (string, 必需): 消息类型，固定为 "audio"
- `data` (string, 必需): Base64 编码的 PCM 音频数据
- `context` (object, 可选): 上下文信息，可包含任意键值对
- `is_end` (boolean, 必需): 是否为最后一帧音频。`true` 表示音频流结束，触发处理

**音频格式要求**:
- 编码格式: PCM
- 采样率: 16000 Hz
- 声道数: 1 (单声道)
- 位深度: 16-bit

**流式传输**:
可以分多次发送音频数据，每次发送一个音频块。服务器会自动组装这些音频块。只有当 `is_end` 为 `true` 时，服务器才会开始处理完整的音频。

**示例**:
```python
import base64
import json
import websocket

# 连接 WebSocket
ws = websocket.create_connection("ws://localhost:8000/ws")

# 读取音频文件
with open("audio.pcm", "rb") as f:
    audio_data = f.read()

# Base64 编码
audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# 发送音频消息
message = {
    "type": "audio",
    "data": audio_base64,
    "context": {
        "user_id": "user123",
        "session_id": "session456"
    },
    "is_end": True
}

ws.send(json.dumps(message))
```

### 2. 结果消息 (Result Message)

**方向**: 服务器 → 客户端

**描述**: 服务器返回处理结果

**格式**:
```json
{
  "type": "result",
  "skill_id": "light_on",
  "text": "好的，已为您打开灯",
  "audio": "base64_encoded_audio_or_null",
  "metadata": {
    "asr_text": "打开灯",
    "confidence": 0.95,
    "is_fixed_command": true
  }
}
```

**字段说明**:
- `type` (string): 消息类型，固定为 "result"
- `skill_id` (string): 技能 ID，标识触发的技能或意图
- `text` (string): 回复文本
- `audio` (string | null): Base64 编码的音频数据（TTS 合成的语音），可能为 null
- `metadata` (object): 元数据
  - `asr_text` (string): ASR 识别的文本
  - `confidence` (float): 置信度 (0-1)
  - `is_fixed_command` (boolean): 是否命中固定指令
  - `rag_documents` (int, 可选): RAG 检索到的文档数量
  - `finish_reason` (string, 可选): LLM 完成原因

**技能类型**:

#### 固定指令 (is_fixed_command=true)
当用户输入命中预定义的固定指令时，服务器直接返回结果，不调用 RAG 和 LLM。

**预定义的固定指令**:
- `light_on`: 打开灯
- `light_off`: 关闭灯
- `ac_on`: 打开空调
- `ac_off`: 关闭空调
- `music_play`: 播放音乐
- `music_stop`: 停止播放
- `weather_query`: 查询天气

**示例** (固定指令):
```json
{
  "type": "result",
  "skill_id": "light_on",
  "text": "好的，已为您打开灯",
  "audio": null,
  "metadata": {
    "asr_text": "打开灯",
    "confidence": 0.95,
    "is_fixed_command": true
  }
}
```

#### 问答/聊天 (is_fixed_command=false)
当未命中固定指令时，服务器会调用 RAG 检索相关信息，然后使用 LLM 生成回复，最后通过 TTS 合成语音。

**示例** (RAG + LLM + TTS):
```json
{
  "type": "result",
  "skill_id": "qa",
  "text": "根据相关信息，智能家居系统可以通过语音控制灯光、空调、窗帘等设备。您还有其他问题吗？",
  "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YQAAAAA=",
  "metadata": {
    "asr_text": "智能家居能做什么",
    "confidence": 0.85,
    "is_fixed_command": false,
    "rag_documents": 3,
    "finish_reason": "stop"
  }
}
```

### 3. 错误消息 (Error Message)

**方向**: 服务器 → 客户端

**描述**: 服务器返回错误信息

**格式**:
```json
{
  "type": "error",
  "code": 400,
  "message": "Invalid JSON format",
  "details": {
    "error": "Expecting value: line 1 column 1 (char 0)"
  }
}
```

**字段说明**:
- `type` (string): 消息类型，固定为 "error"
- `code` (int): 错误代码
- `message` (string): 错误消息
- `details` (object | null): 错误详情

**错误代码**:
- `204`: 未检测到有效语音或处理失败
- `400`: 请求格式错误
- `500`: 服务器内部错误

### 4. 心跳消息 (Heartbeat Message)

**方向**: 双向

**描述**: 保持连接活跃

**格式**:
```json
{
  "type": "heartbeat",
  "timestamp": 1704067200.123
}
```

**字段说明**:
- `type` (string): 消息类型，固定为 "heartbeat"
- `timestamp` (float): Unix 时间戳

## 处理流程

服务器接收到完整音频后（`is_end=true`），会按照以下流程处理：

```
1. 音频组装 (Audio Assembler)
   ↓
2. VAD 语音活动检测 (Voice Activity Detection)
   ↓
3. ASR 语音识别 (Automatic Speech Recognition)
   ↓
4. LLM 语义理解 (Intent Understanding)
   ↓
   ├─ 命中固定指令 → 返回预定义回复
   │
   └─ 未命中固定指令
      ↓
      5. RAG 检索 (Retrieval-Augmented Generation)
      ↓
      6. LLM 回复生成 (LLM Generator)
      ↓
      7. TTS 语音合成 (Text-to-Speech)
      ↓
      返回结果 (文本 + 语音)
```

## 使用示例

### Python 客户端示例

```python
import asyncio
import websockets
import json
import base64

async def voice_chat_client():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("已连接到服务器")
        
        # 读取音频文件
        with open("test_audio.pcm", "rb") as f:
            audio_data = f.read()
        
        # 发送音频消息
        message = {
            "type": "audio",
            "data": base64.b64encode(audio_data).decode('utf-8'),
            "context": {
                "user_id": "test_user",
                "session_id": "test_session"
            },
            "is_end": True
        }
        
        await websocket.send(json.dumps(message))
        print("音频已发送")
        
        # 接收响应
        response = await websocket.recv()
        result = json.loads(response)
        
        print(f"收到响应: {result['type']}")
        print(f"文本: {result.get('text')}")
        print(f"技能ID: {result.get('skill_id')}")
        
        # 如果有音频，保存到文件
        if result.get('audio'):
            audio_bytes = base64.b64decode(result['audio'])
            with open("response_audio.pcm", "wb") as f:
                f.write(audio_bytes)
            print("音频已保存")

# 运行客户端
asyncio.run(voice_chat_client())
```

### JavaScript 客户端示例

```javascript
// 创建 WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('已连接到服务器');
    
    // 发送测试音频
    sendTestAudio();
};

ws.onmessage = function(event) {
    const result = JSON.parse(event.data);
    console.log('收到响应:', result);
    
    if (result.type === 'result') {
        console.log('文本:', result.text);
        console.log('技能ID:', result.skill_id);
        
        // 如果有音频，可以播放
        if (result.audio) {
            playAudio(result.audio);
        }
    } else if (result.type === 'error') {
        console.error('错误:', result.message);
    }
};

ws.onerror = function(error) {
    console.error('WebSocket 错误:', error);
};

ws.onclose = function() {
    console.log('连接已关闭');
};

function sendTestAudio() {
    // 创建测试音频数据
    const sampleRate = 16000;
    const duration = 1;
    const numSamples = sampleRate * duration;
    const buffer = new Int16Array(numSamples);
    
    // 生成简单的正弦波
    for (let i = 0; i < numSamples; i++) {
        buffer[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 10000;
    }
    
    // 转换为 Base64
    const bytes = new Uint8Array(buffer.buffer);
    const base64 = btoa(String.fromCharCode.apply(null, bytes));
    
    // 发送音频消息
    const message = {
        type: 'audio',
        data: base64,
        context: {
            user_id: 'js_user',
            session_id: 'js_session'
        },
        is_end: true
    };
    
    ws.send(JSON.stringify(message));
    console.log('音频已发送');
}

function playAudio(base64Audio) {
    // 解码 Base64 音频并播放
    const audioData = atob(base64Audio);
    // ... 播放逻辑
}
```

## 配置

服务可以通过环境变量或 `.env` 文件进行配置。参考 `.env.example` 文件：

```bash
# 服务配置
HOST=0.0.0.0
PORT=8000

# VAD 配置
VAD_THRESHOLD=0.5
VAD_MIN_SPEECH_DURATION=0.3

# ASR 配置
ASR_MODEL=base
ASR_LANGUAGE=zh

# LLM 配置
LLM_API_KEY=EMPTY
LLM_BASE_URL=http://YOUR_LLM_SERVER_IP:8093/v1

# 意图理解配置
INTENT_SYSTEM_PROMPT_PATH=conf/system_prompt_intent.txt

# 回复生成配置
GENERATOR_SYSTEM_PROMPT_PATH=conf/system_prompt_generator.txt

# RAG 配置
RAG_TOP_K=3
RAG_SIMILARITY_THRESHOLD=0.7

# TTS 配置
TTS_VOICE=zh-CN
TTS_SPEED=1.0
```

## 部署

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

3. 启动服务：
```bash
python -m app.main
```

4. 访问测试页面：
打开浏览器访问 `http://localhost:8000`

### Docker 部署

```bash
# 构建镜像
docker build -t voice-chat-service .

# 运行容器
docker run -d -p 8000:8000 --env-file .env voice-chat-service
```

## 注意事项

1. **音频格式**: 确保上传的音频符合格式要求（16kHz, 16-bit, 单声道 PCM）
2. **Base64 编码**: 所有音频数据都需要 Base64 编码传输
3. **流式传输**: 可以分块发送音频，但必须在最后一块设置 `is_end=true`
4. **连接保持**: 使用心跳消息保持连接活跃
5. **错误处理**: 客户端应该处理各种错误消息类型
6. **超时**: 建议实现客户端超时重连机制

## 模块说明

服务采用模块化设计，各模块职责清晰：

- **AudioAssembler**: 音频组装模块，负责流式音频的组装
- **VAD**: 语音活动检测模块，识别音频中的语音片段
- **ASR**: 语音识别模块，将语音转为文本
- **IntentUnderstanding**: 意图理解模块，识别用户意图
- **RAG**: 检索增强生成模块，从知识库检索相关信息
- **LLMGenerator**: LLM 生成模块，生成回复文本
- **TTS**: 语音合成模块，将文本转为语音

每个模块都可以独立配置和替换，方便后续维护和升级。

## 扩展开发

### 添加新的固定指令

在 `app/modules/intent_understanding.py` 中的 `fixed_commands` 字典添加新指令：

```python
self.fixed_commands = {
    "你的指令": {
        "skill_id": "your_skill_id",
        "skill_type": SkillType.COMMAND,
        "response": "你的回复"
    },
    # ... 其他指令
}
```

### 接入真实的 ASR/TTS/LLM 服务

各模块都预留了接口，可以方便地接入真实服务：

- ASR: 修改 `app/modules/asr.py` 中的 `recognize` 方法
- TTS: 修改 `app/modules/tts.py` 中的 `synthesize` 方法
- LLM: 修改 `app/modules/llm_generator.py` 中的 `generate` 方法

### 接入向量数据库

修改 `app/modules/rag.py` 中的 `retrieve` 方法，接入 Qdrant、Milvus 等向量数据库。

## 技术支持

如有问题，请联系开发团队或查看项目文档。

