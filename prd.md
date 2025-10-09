
# 需求描述
1. 使用websocket实现一个服务，该服务是一个语音聊天服务，请使用FastAPI实现
2. 该服务接收上游IPC的调用，然后返回结果
3. 各个模块需要方便维护
4. 具体模块调用的流程参考模块流程
5. 请输出最终的api调用文档

# 模块流程

```
sequenceDiagram
  IPC->>+音频组装: WebSocket流式上传 PCM音频 + 上下文
  音频组装->>+VAD: 组装的完整音频 + 上下文

  VAD->>+ASR: 说话音频
  ASR->>+LLM语义理解: 转译文本

  alt 命中固定指令
    LLM语义理解-->>-IPC: 技能ID + 回复文本
  else 未命中固定指令
    LLM语义理解->>+RAG: 检索条件
    RAG->>+LLM回复生成: 检索上下文
    LLM回复生成->>+TTS: 回复文本
    TTS-->>-IPC: WebSocket传输 技能ID + 回复文本 + 语音
  end
```
