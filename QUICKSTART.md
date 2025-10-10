# 快速开始指南

这是一个 5 分钟快速开始指南，帮助你快速运行和测试语音聊天服务。

## 步骤 1: 安装和启动服务

### 方法 A: 使用启动脚本（推荐）

```bash
# 跨平台启动脚本
python start.py
```

这个脚本会自动：
- 创建虚拟环境
- 安装依赖
- 创建配置文件
- 启动服务

### 方法 B: 使用 Docker（推荐用于生产）

```bash
# 复制配置文件
cp env_example .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方法 C: 手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建配置文件
cp env_example .env

# 4. 启动服务
python -m app.main
```

## 步骤 2: 验证服务运行

打开浏览器访问：

- 健康检查: http://localhost:8000/health

如果看到健康检查返回 `{"status":"healthy",...}`，说明服务正常运行。

## 步骤 3: 测试服务

### ⭐ 方式 A: Gradio 测试平台（强烈推荐）

**最真实、最强大的测试方式！**

1. **启动 Gradio**（在新终端）：
   ```bash
   python gradio_app.py
   ```

2. **访问界面**：
   ```
   http://localhost:7860
   ```

3. **录制或上传音频**：
   - 点击麦克风图标录制音频
   - 或点击上传按钮上传音频文件（支持 WAV, MP3 等）

4. **发送并查看结果**：
   - 点击"🚀 发送并处理"按钮
   - 查看 ASR 识别文本
   - 查看 LLM 回复文本
   - 试听 TTS 合成音频

**优势**：
- ✅ 真实麦克风录音
- ✅ 支持多种音频格式
- ✅ 自动格式转换
- ✅ 详细结果展示
- ✅ 音频播放功能
- ✅ 美观现代的界面

详细使用说明：[README_GRADIO.md](./README_GRADIO.md)

### 方式 B: HTML 测试页面

1. 访问 http://localhost:8000
2. 点击"连接"按钮
3. 点击"发送测试音频"按钮
4. 查看返回的结果

### 方式 C: Python 客户端

```bash
# 1. 生成测试音频
python examples/generate_test_audio.py

# 2. 运行客户端测试
python examples/client_example.py

# 3. 或者发送指定的音频文件
python examples/client_example.py examples/test_audio/sine_440hz_1s.pcm
```

### 方式 D: 使用 Python 代码

创建一个测试脚本 `test.py`：

```python
import asyncio
import websockets
import json
import base64
import numpy as np

async def test():
    # 连接到服务
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # 生成测试音频（1秒正弦波）
        sample_rate = 16000
        t = np.linspace(0, 1, sample_rate)
        audio = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        # 发送消息
        message = {
            "type": "audio",
            "data": base64.b64encode(audio.tobytes()).decode(),
            "context": {"user_id": "test"},
            "is_end": True
        }
        await ws.send(json.dumps(message))
        
        # 接收响应
        response = json.loads(await ws.recv())
        print(f"技能ID: {response['skill_id']}")
        print(f"回复: {response['text']}")

asyncio.run(test())
```

运行：
```bash
python test.py
```

## 预期结果

你应该会看到类似以下的响应：

```json
{
  "type": "result",
  "skill_id": "chat",
  "text": "智能回复文本...",
  "audio": "base64_encoded_audio_data",
  "metadata": {
    "asr_text": "识别的文本",
    "confidence": 0.85,
    "is_fixed_command": false,
    "rag_documents": 3,
    "finish_reason": "stop"
  }
}
```

## 测试固定指令

服务预定义了一些固定指令，可以快速响应。

### 使用 Gradio 测试（推荐）

1. 打开 Gradio 界面
2. 录制以下音频：
   - "打开灯"
   - "关闭灯"
   - "打开空调"
   - "关闭空调"
   - "播放音乐"
   - "停止播放"
   - "今天天气"

### 预定义的固定指令

| 指令 | 技能ID | 说明 |
|-----|--------|------|
| 打开灯 | light_on | 打开灯光 |
| 关闭灯 | light_off | 关闭灯光 |
| 打开空调 | ac_on | 打开空调 |
| 关闭空调 | ac_off | 关闭空调 |
| 播放音乐 | music_play | 播放音乐 |
| 停止播放 | music_stop | 停止播放 |
| 今天天气 | weather_query | 查询天气 |

## 常见问题

### Q: 服务无法启动？

**A**: 检查端口是否被占用：
```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

如果被占用，可以修改 `.env` 文件中的 `PORT` 配置。

### Q: 客户端连接失败？

**A**: 
1. 确认服务正在运行
2. 检查防火墙设置
3. 查看服务日志

### Q: Gradio 界面无法打开？

**A**:
1. 确认已安装 Gradio：`pip install gradio librosa soundfile`
2. 检查端口 7860 是否被占用
3. 查看终端错误信息

### Q: 录音没有声音？

**A**:
1. 检查浏览器麦克风权限
2. 检查系统麦克风设置
3. 尝试使用其他浏览器（推荐 Chrome）

### Q: 音频没有返回？

**A**: 这是正常的。固定指令模式下不返回音频，只返回文本。只有在 RAG + LLM 模式下才会返回 TTS 合成的音频。

### Q: 返回的是模拟数据？

**A**: 是的，默认配置使用模拟的 ASR/TTS/LLM 服务。要使用真实服务，需要：
1. 在 `.env` 文件中配置相应的 API 密钥
2. 修改对应模块的代码，接入真实服务
3. 安装相关依赖（如 transformers、torch、melo 等）

## 下一步

1. **接入真实服务**: 
   - 参考 `README.md` 中的"扩展开发"章节
   - 接入真实的 ASR、TTS、LLM 服务

2. **自定义固定指令**:
   - 编辑 `app/modules/intent_understanding.py`
   - 添加自己的指令

3. **添加知识库**:
   - 编辑 `app/modules/rag.py`
   - 接入向量数据库

4. **部署到生产环境**:
   - 使用 Docker 部署
   - 配置 Nginx 反向代理
   - 添加 HTTPS 支持

## 推荐工作流程

### 开发测试阶段

1. **启动后端服务**：
   ```bash
   python -m app.main
   ```

2. **启动 Gradio 测试平台**：
   ```bash
   python gradio_app.py
   ```

3. **使用 Gradio 进行测试**：
   - 录制真实音频测试
   - 查看详细结果
   - 调试各个模块

### 生产部署阶段

1. **使用 Docker 部署**：
   ```bash
   docker-compose up -d
   ```

2. **配置域名和 HTTPS**

3. **监控服务状态**

## 获取帮助

- 查看完整文档: [README.md](./README.md)
- 查看 API 文档: [API.md](./API.md)
- Gradio 使用说明: [README_GRADIO.md](./README_GRADIO.md)
- 查看示例代码: [examples/](./examples/)
- 提交 Issue: 在项目仓库提交问题

---

享受你的语音聊天服务！🎉

**特别推荐**：使用 Gradio 测试平台获得最佳测试体验！
