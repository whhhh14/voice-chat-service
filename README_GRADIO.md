# Gradio 测试平台使用指南

## 概述

Gradio 测试平台提供了一个友好的 Web 界面，用于测试语音聊天服务的完整功能。相比简单的 HTML 测试页面，Gradio 平台支持：

- 🎤 **真实音频录制**：直接使用麦克风录制音频
- 📁 **音频文件上传**：支持多种音频格式（WAV, MP3, OGG 等）
- 🔄 **自动格式转换**：自动转换为服务所需的 16kHz 单声道格式
- 📊 **详细结果展示**：显示 ASR 识别、LLM 回复、TTS 音频等
- 🎯 **快速测试**：提供预定义的测试场景

## 快速开始

### 1. 安装依赖

```bash
# 安装 Gradio 相关依赖
pip install gradio librosa soundfile
```

或者重新安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

在一个终端中启动语音聊天服务：

```bash
python -m app.main
```

或使用启动脚本：

```bash
python start.py
```

### 3. 启动 Gradio 测试平台

在另一个终端中启动 Gradio 界面：

```bash
python gradio_app.py
```

### 4. 访问测试界面

打开浏览器访问：

```
http://localhost:7860
```

## 界面功能

### 输入区域

1. **音频输入**
   - **录音**：点击麦克风图标开始录音，再次点击停止
   - **上传**：点击上传按钮选择本地音频文件
   - 支持格式：WAV, MP3, OGG, FLAC, M4A 等

2. **上下文信息**（可选）
   - 输入 JSON 格式的上下文数据
   - 例如：`{"user_id": "test", "session_id": "123"}`
   - 留空则使用默认上下文

3. **操作按钮**
   - 🚀 **发送并处理**：发送音频到服务器并获取结果
   - 🗑️ **清空**：清除所有输入
   - 💚 **检查服务状态**：检查后端服务是否正常运行

### 输出区域

1. **处理状态**
   - 显示处理结果（成功/失败）
   - 技能 ID
   - 置信度
   - 是否为固定指令
   - 音频时长

2. **ASR 识别文本**
   - 显示语音识别的文本结果

3. **LLM 回复文本**
   - 显示智能回复的文本内容

4. **TTS 合成音频**
   - 播放 TTS 合成的语音（如果有）
   - 可以下载音频文件

## 测试场景

### 场景 1: 固定指令测试

录制或说出以下指令：

- "打开灯"
- "关闭灯"
- "打开空调"
- "关闭空调"
- "播放音乐"
- "停止播放"
- "今天天气"

**预期结果**：
- 快速响应（不经过 RAG 和 LLM）
- 返回预定义的回复文本
- 不返回 TTS 音频

### 场景 2: 知识问答测试

提出问题：

- "智能家居能做什么？"
- "如何设置空调温度？"
- "系统支持哪些场景模式？"
- "设备无法连接怎么办？"

**预期结果**：
- 经过 RAG 检索知识库
- LLM 生成回复
- 返回 TTS 合成的语音

### 场景 3: 闲聊测试

随意交谈：

- "你好"
- "今天天气怎么样"
- "你是谁"
- "给我讲个笑话"

**预期结果**：
- LLM 生成自然对话回复
- 返回 TTS 合成的语音

## 使用技巧

### 1. 录音技巧

- 🎯 **环境**：在安静的环境中录音
- 🗣️ **距离**：保持适当的麦克风距离（15-30cm）
- ⏱️ **时长**：说话清晰，避免过长或过短
- 🔊 **音量**：保持适中的音量，避免过响或过小

### 2. 文件上传

- 📁 **格式**：支持常见音频格式，推荐 WAV
- 📊 **质量**：清晰的录音质量会提高识别准确度
- ⚖️ **大小**：避免过大的文件（建议 < 10MB）

### 3. 调试技巧

1. **检查服务状态**
   - 点击"检查服务状态"按钮
   - 确保后端服务正常运行

2. **查看详细日志**
   - 终端中会显示详细的处理日志
   - 包括 VAD、ASR、LLM 等各步骤

3. **测试音频质量**
   - 上传音频后，可以先试听
   - 确保音频清晰可听

## 高级功能

### 自定义上下文

可以在上下文中传递额外信息：

```json
{
  "user_id": "user_123",
  "session_id": "session_456",
  "location": "living_room",
  "history": ["previous", "commands"],
  "preferences": {
    "language": "zh",
    "speed": 1.0
  }
}
```

### 批量测试

1. 准备多个测试音频文件
2. 依次上传并测试
3. 记录结果用于分析

### 与浏览器测试页面对比

| 特性 | Gradio 平台 | HTML 测试页面 |
|-----|------------|--------------|
| 音频录制 | ✅ 真实麦克风录音 | ✅ 生成测试音频 |
| 文件上传 | ✅ 支持多种格式 | ❌ 不支持 |
| 格式转换 | ✅ 自动转换 | ❌ 需手动 |
| 结果展示 | ✅ 详细分类 | ✅ JSON 格式 |
| 音频播放 | ✅ 内置播放器 | ❌ 需手动保存 |
| 界面美观 | ✅ 现代化 UI | ⚠️ 基础 HTML |

## 故障排查

### 问题 1: 无法连接到服务

**症状**：点击"发送并处理"后显示连接错误

**解决方案**：
1. 确认后端服务已启动：`python -m app.main`
2. 检查服务端口：默认 8000
3. 点击"检查服务状态"按钮验证

### 问题 2: 录音没有声音

**症状**：录音完成但播放无声

**解决方案**：
1. 检查浏览器麦克风权限
2. 检查系统麦克风设置
3. 尝试使用其他浏览器（推荐 Chrome）

### 问题 3: 音频格式不支持

**症状**：上传音频后处理失败

**解决方案**：
1. 确认音频文件完整且未损坏
2. 尝试转换为 WAV 格式
3. 检查文件大小是否过大

### 问题 4: Gradio 启动失败

**症状**：运行 gradio_app.py 报错

**解决方案**：
```bash
# 重新安装 Gradio 依赖
pip install --upgrade gradio librosa soundfile
```

## 生产环境部署

### 使用 Gradio 提供的共享链接

```python
demo.launch(
    share=True,  # 启用公共链接
    server_name="0.0.0.0",
    server_port=7860,
)
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name gradio.example.com;
    
    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用 Docker 部署

创建 `Dockerfile.gradio`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gradio_app.py .
COPY app/ ./app/

EXPOSE 7860

CMD ["python", "gradio_app.py"]
```

构建并运行：

```bash
docker build -f Dockerfile.gradio -t voice-chat-gradio .
docker run -d -p 7860:7860 --name gradio voice-chat-gradio
```

## 性能优化

### 1. 音频预处理

- 在客户端进行音频压缩
- 减少网络传输时间

### 2. 缓存策略

- 缓存常用的 ASR/TTS 结果
- 减少重复处理

### 3. 并发处理

- 使用异步处理提高吞吐量
- 支持多用户同时使用

## 扩展功能

### 添加更多测试功能

可以在 `gradio_app.py` 中添加：

1. **历史记录**：保存测试历史
2. **性能监控**：显示处理时间
3. **对比测试**：对比不同模型效果
4. **批量测试**：批量处理多个音频

### 集成到 CI/CD

使用 Gradio 的 API 模式进行自动化测试：

```python
from gradio_client import Client

client = Client("http://localhost:7860/")
result = client.predict("audio.wav", api_name="/predict")
```

## 总结

Gradio 测试平台提供了一个强大且友好的测试环境，让你能够：

- ✅ 使用真实音频进行测试
- ✅ 快速验证服务功能
- ✅ 调试和优化服务
- ✅ 演示给其他人

建议在开发和测试阶段都使用 Gradio 平台，它将大大提高你的工作效率！

---

**相关文档**：
- [README.md](./README.md) - 项目总体说明
- [API.md](./API.md) - API 详细文档
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始指南

