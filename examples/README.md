# 示例代码

这个目录包含了语音聊天服务的使用示例。

## 文件说明

- `client_example.py`: WebSocket 客户端示例，演示如何连接服务并发送音频
- `generate_test_audio.py`: 测试音频生成工具，用于生成各种测试用的 PCM 音频文件

## 使用方法

### 1. 生成测试音频

首先生成一些测试音频文件：

```bash
cd examples
python generate_test_audio.py
```

这将在 `test_audio/` 目录下生成多个测试音频文件：
- `silence_1s.pcm`: 1秒静音
- `sine_440hz_1s.pcm`: 440Hz 正弦波 1秒
- `sine_880hz_2s.pcm`: 880Hz 正弦波 2秒
- `beep_sequence.pcm`: 蜂鸣序列
- `frequency_sweep.pcm`: 扫频音频
- `short_beep.pcm`: 短蜂鸣
- `long_tone.pcm`: 长音调

### 2. 测试客户端

#### 测试发送音频文件

```bash
# 发送指定的音频文件
python client_example.py test_audio/sine_440hz_1s.pcm

# 或者使用相对路径
python client_example.py ../test_audio/sine_440hz_1s.pcm
```

#### 测试发送自动生成的音频

如果不指定音频文件，客户端会自动生成测试音频：

```bash
python client_example.py
```

#### 测试心跳功能

```bash
python client_example.py --heartbeat
```

### 3. 查看结果

客户端会打印接收到的响应，包括：
- 技能 ID
- 回复文本
- 元数据信息

如果服务返回了音频，会保存到 `response_audio.pcm` 文件。

## 音频格式

所有测试音频都使用以下格式：
- **编码**: PCM (未压缩)
- **采样率**: 16000 Hz
- **位深度**: 16-bit
- **声道**: 单声道
- **字节序**: 小端序

## 播放测试音频

### 使用 ffplay

```bash
# 播放 PCM 音频
ffplay -f s16le -ar 16000 -ac 1 test_audio/sine_440hz_1s.pcm
```

### 使用 SoX

```bash
# 播放 PCM 音频
play -r 16000 -e signed -b 16 -c 1 test_audio/sine_440hz_1s.pcm
```

### 转换为 WAV 格式

使用 ffmpeg 转换为 WAV 格式，方便播放：

```bash
ffmpeg -f s16le -ar 16000 -ac 1 -i test_audio/sine_440hz_1s.pcm test_audio/sine_440hz_1s.wav
```

## 自定义测试

你可以修改这些示例代码来进行自定义测试：

### 添加上下文信息

在 `client_example.py` 中修改 `context` 字段：

```python
"context": {
    "user_id": "your_user_id",
    "session_id": "your_session_id",
    "custom_field": "custom_value"
}
```

### 流式发送音频

修改客户端代码，分块发送音频：

```python
# 将音频分成多个块
chunk_size = 4096  # 每块 4KB
for i in range(0, len(audio_data), chunk_size):
    chunk = audio_data[i:i+chunk_size]
    is_end = (i + chunk_size >= len(audio_data))
    
    message = {
        "type": "audio",
        "data": base64.b64encode(chunk).decode('utf-8'),
        "context": {},
        "is_end": is_end
    }
    
    await websocket.send(json.dumps(message))
```

## 故障排查

### 连接失败

确保服务正在运行：

```bash
curl http://localhost:8000/health
```

### 音频处理失败

检查音频格式是否正确：

```bash
file test_audio/sine_440hz_1s.pcm
```

### 其他问题

查看服务端日志获取详细信息。

