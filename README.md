# Voice Chat Service / 智能语音聊天服务

> A real-time, end-to-end voice chat pipeline built with FastAPI & WebSocket.  
> 基于 FastAPI 和 WebSocket 的端到端实时语音对话后端服务。

---

## What It Does / 项目简介

This project implements a complete voice-assistant backend pipeline:

```
Client (PCM audio) → VAD → ASR → Intent Understanding → RAG → LLM → TTS → Client
```

It is designed for smart-home / IPC-device scenarios where the client sends raw PCM audio and expects:
- A recognized **skill ID** (e.g. `light_on`, `weather_query`)
- A **text reply**
- An optional **TTS audio** response

本项目面向智能家居 / IPC 摄像头场景，客户端通过 WebSocket 发送 PCM 音频，服务端返回技能 ID、回复文本和语音。

---

## Architecture / 架构

| Module | Technology | Description |
|--------|-----------|-------------|
| **VAD** | Silero VAD | Detects speech segments in audio stream |
| **ASR** | Whisper / any Whisper-compatible | Converts speech → text |
| **Intent** | LLM (OpenAI-compatible API) | Classifies intent + fixed command matching |
| **RAG** | Qdrant + Qwen3-Embedding | Event retrieval from vector database |
| **LLM** | Any OpenAI-compatible API | Generates natural language replies |
| **TTS** | Kokoro ONNX | Synthesizes speech from text |
| **API** | FastAPI + WebSocket | Handles real-time streaming communication |

---

## Features / 功能特性

- **WebSocket streaming**: Real-time bidirectional audio communication
- **Modular design**: Each stage is an independent, swappable module
- **Fixed command matching**: Instantly responds to predefined intents (no LLM needed)
- **RAG event system**: Stores and retrieves events using a vector database (Qdrant)
- **Gradio test UI**: Visual testing interface for the whole pipeline
- **Docker support**: One-command deployment with `docker-compose`

---

## Quick Start / 快速开始

### Prerequisites / 环境要求

- Python 3.10+
- An OpenAI-compatible LLM server (e.g. vLLM, Ollama, OpenAI)
- An OpenAI-compatible Embedding server
- Qdrant vector database (or use memory mode)
- Kokoro ONNX TTS model

### 1. Clone and install / 安装依赖

```bash
git clone https://github.com/YOUR_USERNAME/aibase-voice-chat.git
cd aibase-voice-chat

python3 -m venv venv
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure / 配置环境变量

```bash
cp env_example .env
# Edit .env and fill in your actual service addresses
```

Key variables in `.env`:

```bash
# Your LLM service (vLLM / Ollama / OpenAI etc.)
LLM_BASE_URL=http://YOUR_LLM_SERVER_IP:8093/v1
LLM_API_KEY=EMPTY

# Your Embedding service
EMBEDDING_API_BASE_URL=http://localhost:8002/v1

# Path to your downloaded Whisper model or use "base" for auto-download
ASR_MODEL=base

# Path to your Kokoro ONNX model file
TTS_MODEL_PATH=/path/to/kokoro-v0_19.fp16.onnx

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_USE_MEMORY=True  # set False for persistent mode
```

### 3. Run / 启动服务

```bash
python -m app.main
```

Service is available at `ws://localhost:8000/ws`

### 4. Test with Gradio UI / 用 Gradio 界面测试

```bash
python gradio_app.py
# Open http://localhost:7860 in your browser
```

### Docker (Recommended / 推荐)

```bash
cp env_example .env
docker-compose up -d
```

---

## API Overview / 接口概览

| Endpoint | Type | Description |
|----------|------|-------------|
| `ws://host/ws` | WebSocket | Main voice chat endpoint |
| `GET /health` | HTTP | Health check |
| `POST /api/events` | HTTP | Create event in RAG database |
| `POST /api/events/search` | HTTP | Search events |
| `GET /` | HTTP | Built-in HTML test page |

Full API docs: see [API.md](./API.md)

---

## Project Structure / 项目结构

```
aibase-voice-chat/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # All configuration (pydantic-settings)
│   ├── models.py                # Pydantic data models
│   ├── service.py               # Core pipeline orchestration
│   └── modules/
│       ├── audio_assembler.py   # Reassembles streaming audio chunks
│       ├── vad.py               # Voice Activity Detection
│       ├── asr.py               # Automatic Speech Recognition
│       ├── intent_understanding.py  # LLM-based intent classification
│       ├── rag.py               # RAG retrieval
│       ├── embedding.py         # Text vectorization
│       ├── llm_generator.py     # LLM reply generation
│       └── tts.py               # Text-to-Speech
├── conf/                        # System prompt templates
├── scripts/                     # Utility scripts (import events, test RAG)
├── env_example                  # Environment variable template
├── gradio_app.py                # Gradio test UI
├── docker-compose.yml           # Docker deployment
├── Dockerfile
├── requirements.txt
├── API.md                       # Detailed API documentation
└── README.md
```

---

## Tech Stack / 技术栈

`FastAPI` · `WebSocket` · `Pydantic` · `Silero VAD` · `Whisper` · `Qdrant` · `Kokoro TTS` · `Docker`

---

## License

MIT License — see [LICENSE](./LICENSE)
