# 语音聊天服务 (Voice Chat Service)

基于 FastAPI 和 WebSocket 的智能语音聊天服务，支持实时语音输入和文本/语音输出。

## 功能特性

- ✅ **WebSocket 实时通信**: 支持流式音频传输
- ✅ **模块化设计**: 各模块职责清晰，易于维护和扩展
- ✅ **完整的语音处理流程**: 
  - 音频组装 (Audio Assembler)
  - 语音活动检测 (VAD)
  - 语音识别 (ASR)
  - 意图理解 (Intent Understanding)
  - 检索增强生成 (RAG)
  - 大语言模型回复生成 (LLM)
  - 语音合成 (TTS)
- ✅ **固定指令支持**: 快速响应预定义指令
- ✅ **知识库检索**: 基于 RAG 的智能问答
- ✅ **Docker 支持**: 便捷的容器化部署

## 项目结构

```
aibase-voice-chat/
├── app/                          # 应用主目录
│   ├── __init__.py              # 应用包初始化
│   ├── config.py                # 配置管理
│   ├── models.py                # 数据模型定义
│   ├── service.py               # 核心服务逻辑
│   ├── main.py                  # FastAPI 主程序
│   └── modules/                 # 业务模块
│       ├── __init__.py
│       ├── audio_assembler.py   # 音频组装模块
│       ├── vad.py               # 语音活动检测
│       ├── asr.py               # 语音识别
│       ├── intent_understanding.py  # 意图理解
│       ├── rag.py               # RAG 检索
│       ├── llm_generator.py     # LLM 生成
│       └── tts.py               # 语音合成
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 镜像构建文件
├── docker-compose.yml           # Docker Compose 配置
├── env_example                  # 环境变量示例
├── start.py                     # 跨平台启动脚本
├── run.sh                       # Linux/Mac 启动脚本
├── API.md                       # API 文档
├── prd.md                       # 产品需求文档
└── README.md                    # 项目说明文档
```

## 系统架构

### 处理流程

```
IPC 客户端
    ↓ (WebSocket 流式上传 PCM 音频 + 上下文)
音频组装模块
    ↓
VAD 语音活动检测
    ↓
ASR 语音识别
    ↓
LLM 意图理解
    ├─ 命中固定指令 → 直接返回技能ID + 回复文本
    │
    └─ 未命中固定指令
        ↓
        RAG 检索
        ↓
        LLM 回复生成
        ↓
        TTS 语音合成
        ↓
        返回技能ID + 回复文本 + 语音
```

### 技术栈

- **Web 框架**: FastAPI
- **WebSocket**: websockets
- **数据验证**: Pydantic
- **音频处理**: NumPy
- **配置管理**: pydantic-settings

## 快速开始

### 方式一: 使用启动脚本（推荐）

#### Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

#### 跨平台（Python）:
```bash
python start.py
```

### 方式二: 手动启动

1. **创建虚拟环境**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

```bash
cp env_example .env
# 编辑 .env 文件，填入实际配置
```

4. **启动服务**

```bash
python -m app.main
```

### 方式三: 使用 Docker

1. **使用 Docker Compose（推荐）**

```bash
# 复制环境变量文件
cp env_example .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

2. **使用 Docker 命令**

```bash
# 构建镜像
docker build -t voice-chat-service .

# 运行容器
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name voice-chat-service \
  voice-chat-service

# 查看日志
docker logs -f voice-chat-service

# 停止容器
docker stop voice-chat-service
```

## 使用说明

### 访问服务

启动后，可以通过以下方式访问服务：

- **WebSocket 端点**: `ws://localhost:8000/ws`
- **HTML 测试页面**: `http://localhost:8000`
- **Gradio 测试平台**: `http://localhost:7860`（需单独启动）
- **健康检查**: `http://localhost:8000/health`

### 🎯 推荐：使用 Gradio 测试平台

我们提供了功能强大的 Gradio 测试界面，支持真实音频录制和文件上传：

```bash
# 1. 启动后端服务（在一个终端）
python -m app.main

# 2. 启动 Gradio 测试平台（在另一个终端）
python gradio_app.py

# 3. 访问 Gradio 界面
浏览器打开: http://localhost:7860
```

**Gradio 平台功能：**
- 🎤 麦克风录音测试
- 📁 音频文件上传（支持 WAV, MP3 等多种格式）
- 🔄 自动格式转换（转为 16kHz 单声道）
- 📊 详细结果展示（ASR、LLM、TTS）
- 🎯 快速测试场景

详细使用说明请查看：[README_GRADIO.md](./README_GRADIO.md)

### API 文档

详细的 API 文档请查看 [API.md](./API.md)

### 快速测试

#### 方式 1: Gradio 测试平台（推荐）

1. 启动 Gradio：`python gradio_app.py`
2. 打开浏览器访问 `http://localhost:7860`
3. 点击麦克风图标录制音频或上传音频文件
4. 点击"发送并处理"按钮
5. 查看 ASR 识别、LLM 回复和 TTS 音频

#### 方式 2: HTML 测试页面

1. 打开浏览器访问 `http://localhost:8000`
2. 点击"连接"按钮建立 WebSocket 连接
3. 点击"发送测试音频"按钮发送测试数据
4. 查看返回的结果

### Python 客户端示例

```python
import asyncio
import websockets
import json
import base64

async def test_voice_chat():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # 读取音频文件
        with open("test.pcm", "rb") as f:
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
        
        # 接收响应
        response = await websocket.recv()
        result = json.loads(response)
        
        print(f"技能ID: {result['skill_id']}")
        print(f"回复文本: {result['text']}")
        
        # 保存返回的音频
        if result.get('audio'):
            audio_bytes = base64.b64decode(result['audio'])
            with open("response.pcm", "wb") as f:
                f.write(audio_bytes)

asyncio.run(test_voice_chat())
```

## 配置说明

环境变量配置（`.env` 文件）：

```bash
# 服务配置
HOST=0.0.0.0              # 监听地址
PORT=8000                 # 监听端口

# VAD 配置
VAD_THRESHOLD=0.5         # VAD 阈值
VAD_MIN_SPEECH_DURATION=0.3   # 最小语音时长（秒）
VAD_MAX_SPEECH_DURATION=30.0  # 最大语音时长（秒）

# 音频配置
AUDIO_SAMPLE_RATE=16000   # 采样率
AUDIO_CHANNELS=1          # 声道数

# ASR 配置
ASR_MODEL=base            # ASR 模型
ASR_LANGUAGE=zh           # 语言

# LLM 配置
LLM_API_KEY=EMPTY         # LLM API 密钥
LLM_BASE_URL=http://192.168.111.3:8093/v1  # LLM 服务地址

# 意图理解配置
INTENT_SYSTEM_PROMPT_PATH=conf/system_prompt_intent.txt  # 意图理解提示词路径

# 回复生成配置
GENERATOR_SYSTEM_PROMPT_PATH=conf/system_prompt_generator.txt  # 回复生成提示词路径

# RAG 配置
RAG_TOP_K=3               # 返回文档数量
RAG_SIMILARITY_THRESHOLD=0.7  # 相似度阈值

# TTS 配置
TTS_VOICE=zh-CN           # TTS 语音
TTS_SPEED=1.0             # 语速
```

## 固定指令

系统预定义了以下固定指令，可快速响应：

| 指令 | 技能ID | 说明 |
|-----|--------|------|
| 打开灯 | light_on | 打开灯光 |
| 关闭灯 | light_off | 关闭灯光 |
| 打开空调 | ac_on | 打开空调 |
| 关闭空调 | ac_off | 关闭空调 |
| 播放音乐 | music_play | 播放音乐 |
| 停止播放 | music_stop | 停止播放 |
| 今天天气 | weather_query | 查询天气 |

可在 `app/modules/intent_understanding.py` 中添加更多固定指令。

## 扩展开发

### 接入真实的 ASR 服务

编辑 `app/modules/asr.py`：

```python
# 示例：接入 Whisper
import whisper

class ASR:
    def __init__(self, model: str = "base", language: str = "zh"):
        self.model = whisper.load_model(model)
        self.language = language
    
    def recognize(self, audio_data: bytes, sample_rate: int = 16000):
        import numpy as np
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        result = self.model.transcribe(audio_array, language=self.language)
        return ASRResult(text=result["text"], confidence=0.95, language=self.language)
```

### 接入真实的 TTS 服务

编辑 `app/modules/tts.py`：

```python
# 示例：接入 Edge TTS
import edge_tts

class TTS:
    async def synthesize_async(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return TTSResult(audio=audio_data, format="mp3", sample_rate=24000)
```

### 接入真实的 LLM 服务

编辑 `app/modules/llm_generator.py`：

```python
# 示例：接入 OpenAI
from openai import OpenAI

class LLMGenerator:
    def __init__(self, model: str, api_key: str, temperature: float, max_tokens: int):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(self, query: str, context: List[str], history: List[Dict]):
        prompt = self._build_prompt(query, context, history)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            finish_reason=response.choices[0].finish_reason
        )
```

### 接入向量数据库

编辑 `app/modules/rag.py`：

```python
# 示例：接入 Qdrant
from qdrant_client import QdrantClient

class RAG:
    def __init__(self, top_k: int, similarity_threshold: float):
        self.client = QdrantClient("localhost", port=6333)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(self, query: str, context: Dict):
        # 将查询转换为向量
        query_vector = self.embed(query)
        
        # 在向量数据库中搜索
        results = self.client.search(
            collection_name="knowledge_base",
            query_vector=query_vector,
            limit=self.top_k
        )
        
        documents = [r.payload["text"] for r in results]
        scores = [r.score for r in results]
        
        return RAGResult(documents=documents, scores=scores)
```

## 音频格式要求

- **编码格式**: PCM (未压缩)
- **采样率**: 16000 Hz
- **位深度**: 16-bit
- **声道数**: 1 (单声道)
- **字节序**: 小端序 (Little-endian)

## 故障排查

### 服务无法启动

1. 检查端口是否被占用：
```bash
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows
```

2. 检查 Python 版本（需要 3.9+）：
```bash
python --version
```

3. 检查依赖是否正确安装：
```bash
pip list
```

### WebSocket 连接失败

1. 检查防火墙设置
2. 确认服务正常运行
3. 查看服务日志：
```bash
docker-compose logs -f  # Docker
# 或查看 logs/ 目录下的日志文件
```

### 音频处理失败

1. 确认音频格式符合要求
2. 检查音频数据是否正确 Base64 编码
3. 查看服务日志获取详细错误信息

## 性能优化建议

1. **使用异步操作**: 所有 I/O 操作都使用异步方式
2. **连接池**: 为外部服务（LLM、数据库等）使用连接池
3. **缓存**: 对频繁访问的数据使用缓存
4. **负载均衡**: 多实例部署 + Nginx 负载均衡
5. **GPU 加速**: ASR 和 TTS 模型可使用 GPU 加速

## 依赖说明

主要依赖包：

- `fastapi`: Web 框架
- `uvicorn`: ASGI 服务器
- `websockets`: WebSocket 支持
- `pydantic`: 数据验证
- `numpy`: 音频数据处理
- `gradio`: 测试界面（可选）
- `librosa`: 音频处理（用于 Gradio）

可选依赖（生产环境建议安装）：

- `transformers`: Whisper ASR 模型
- `torch`: 深度学习框架
- `melo`: MeloTTS 语音合成
- `openai`: OpenAI API
- `qdrant-client`: Qdrant 向量数据库

## 开发计划

- [ ] 支持多语言（英语、日语等）
- [ ] 实现会话管理
- [ ] 添加用户认证
- [ ] 支持更多音频格式
- [ ] 添加监控和日志分析
- [ ] 性能优化和压力测试
- [ ] 添加单元测试和集成测试

## 许可证

本项目采用 MIT 许可证。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue 或联系开发团队。

---

**版本**: 1.0.0  
**最后更新**: 2025-01
