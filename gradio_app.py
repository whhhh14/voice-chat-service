#!/usr/bin/env python3
"""
Gradio 测试应用
提供友好的 Web 界面用于测试语音聊天服务
"""
import gradio as gr
import asyncio
import websockets
import json
import base64
import numpy as np
import librosa
import io
import wave
from typing import Optional, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceChatClient:
    """语音聊天客户端"""

    def __init__(self, ws_url: str = "ws://192.168.111.9:8900/ws"):
        self.ws_url = ws_url

    async def send_audio(self, audio_data: bytes, context: dict = None) -> Optional[dict]:
        """
        发送音频到服务器

        Args:
            audio_data: PCM 音频数据
            context: 上下文信息

        Returns:
            服务器响应
        """
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Base64 编码
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                # 构建消息
                message = {
                    "type": "audio",
                    "data": audio_base64,
                    "context": context or {},
                    "is_end": True
                }

                # 发送消息
                await websocket.send(json.dumps(message))
                logger.info("音频已发送")

                # 接收响应
                response = await websocket.recv()
                result = json.loads(response)
                logger.info(f"收到响应: {result.get('type')}")

                return result

        except Exception as e:
            logger.error(f"发送音频失败: {e}")
            return {"type": "error", "message": str(e)}


def process_audio_file(audio_file) -> Tuple[np.ndarray, int]:
    """
    处理音频文件，转换为 16kHz 单声道 PCM

    Args:
        audio_file: 音频文件路径或元组 (sample_rate, audio_data)

    Returns:
        (audio_array, sample_rate)
    """
    try:
        if audio_file is None:
            return None, None

        # Gradio 录音返回 (sample_rate, audio_data)
        if isinstance(audio_file, tuple):
            sample_rate, audio_data = audio_file
            # 转换为 float32 并归一化
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            else:
                audio_float = audio_data.astype(np.float32)
        else:
            # 从文件加载
            audio_float, sample_rate = librosa.load(audio_file, sr=None)

        # 确保单声道
        if len(audio_float.shape) > 1:
            audio_float = np.mean(audio_float, axis=1)

        # 重采样到 16kHz
        if sample_rate != 16000:
            audio_float = librosa.resample(audio_float, orig_sr=sample_rate, target_sr=16000)
            sample_rate = 16000

        logger.info(f"音频处理完成: {len(audio_float)} 采样点, {sample_rate} Hz")
        return audio_float, sample_rate

    except Exception as e:
        logger.error(f"音频处理失败: {e}")
        return None, None


def audio_array_to_pcm_bytes(audio_float: np.ndarray) -> bytes:
    """
    将音频数组转换为 PCM 字节数据

    Args:
        audio_float: 浮点音频数组 (-1.0 到 1.0)

    Returns:
        PCM 字节数据
    """
    # 转换为 int16
    audio_int16 = (audio_float * 32767).astype(np.int16)
    return audio_int16.tobytes()


def pcm_bytes_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    将 PCM 字节转换为 WAV 字节（用于播放）

    Args:
        pcm_data: PCM 字节数据
        sample_rate: 采样率

    Returns:
        WAV 字节数据
    """
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

    return wav_io.getvalue()


async def process_voice_chat(audio_input, context_str: str) -> Tuple[str, str, Optional[str]]:
    """
    处理语音聊天

    Args:
        audio_input: 音频输入
        context_str: 上下文 JSON 字符串

    Returns:
        (状态信息, 识别文本, 回复文本, 回复音频路径)
    """
    try:
        # 处理音频
        audio_float, sample_rate = process_audio_file(audio_input)
        if audio_float is None:
            return "❌ 音频处理失败", "", "", None

        # 转换为 PCM 字节
        pcm_data = audio_array_to_pcm_bytes(audio_float)

        # 解析上下文
        try:
            context = json.loads(context_str) if context_str.strip() else {}
        except json.JSONDecodeError:
            context = {"note": context_str}

        # 添加时间戳
        context["timestamp"] = datetime.now().isoformat()

        # 发送到服务器
        client = VoiceChatClient()
        result = await client.send_audio(pcm_data, context)

        if result is None:
            return "❌ 服务器无响应", "", "", None

        # 解析结果
        if result.get("type") == "error":
            error_msg = result.get("message", "未知错误")
            return f"❌ 错误: {error_msg}", "", "", None

        if result.get("type") == "result":
            skill_id = result.get("skill_id", "unknown")
            reply_text = result.get("text", "")
            metadata = result.get("metadata", {})
            asr_text = metadata.get("asr_text", "")
            confidence = metadata.get("confidence", 0)
            is_fixed_command = metadata.get("is_fixed_command", False)

            # 构建状态信息
            status = f"""✅ 处理成功

**技能 ID**: {skill_id}
**置信度**: {confidence:.2%}
**固定指令**: {'是' if is_fixed_command else '否'}
**音频时长**: {len(audio_float) / sample_rate:.2f} 秒
"""

            # 处理返回的音频
            audio_output = None
            if result.get("audio"):
                try:
                    audio_bytes = base64.b64decode(result["audio"])
                    # 保存为临时 WAV 文件
                    import tempfile
                    import os

                    # 使用项目内的 tmp 目录（在当前工作目录下）
                    tmp_dir = os.path.join(os.getcwd(), 'tmp', 'tts_output')
                    os.makedirs(tmp_dir, exist_ok=True)
                    with tempfile.NamedTemporaryFile(prefix='tts_gradio_', suffix='.wav', dir=tmp_dir, delete=False) as f:
                        f.write(pcm_bytes_to_wav_bytes(audio_bytes))
                        audio_output = f.name
                    logger.info(f"音频已保存到: {audio_output}")
                except Exception as e:
                    logger.error(f"音频解码失败: {e}")

            return status, asr_text, reply_text, audio_output

        return "❌ 未知响应类型", "", "", None

    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return f"❌ 异常: {str(e)}", "", "", None


def sync_process_voice_chat(audio_input, context_str: str):
    """同步包装器"""
    return asyncio.run(process_voice_chat(audio_input, context_str))


def check_service_health() -> str:
    """检查服务健康状态"""
    try:
        import requests
        response = requests.get("http://192.168.111.9:8900/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"""✅ 服务正常运行

**服务名称**: {data.get('service', 'Unknown')}
**版本**: {data.get('version', 'Unknown')}
**状态**: {data.get('status', 'Unknown')}
"""
        else:
            return f"⚠️ 服务返回异常状态码: {response.status_code}"
    except Exception as e:
        return f"❌ 无法连接到服务: {str(e)}\n\n请确保服务已启动：python -m app.main"


# 创建 Gradio 界面
def create_interface():
    """创建 Gradio 界面"""

    with gr.Blocks(title="语音聊天服务测试", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎙️ 语音聊天服务测试平台

        使用此界面测试语音聊天服务的完整功能。你可以：
        - 🎤 录制音频进行测试
        - 📁 上传音频文件进行测试
        - 📝 查看 ASR 识别结果
        - 💬 获取 LLM 回复
        - 🔊 试听 TTS 合成的语音
        """)

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📥 输入")

                # 音频输入（支持录音和上传）
                audio_input = gr.Audio(
                    sources=["microphone", "upload"],
                    type="numpy",
                    label="音频输入（录音或上传）",
                )

                # 上下文输入
                context_input = gr.Textbox(
                    label="上下文信息（JSON 格式，可选）",
                    placeholder='{"user_id": "test_user", "session_id": "test_session"}',
                    lines=3,
                )

                # 按钮
                with gr.Row():
                    submit_btn = gr.Button("🚀 发送并处理", variant="primary", size="lg")
                    clear_btn = gr.ClearButton(components=[audio_input, context_input], value="🗑️ 清空")
                    health_btn = gr.Button("💚 检查服务状态", size="sm")

            with gr.Column(scale=3):
                gr.Markdown("### 📤 输出")

                # 状态信息
                status_output = gr.Markdown(label="处理状态")

                # ASR 识别结果
                asr_output = gr.Textbox(
                    label="🗣️ ASR 识别文本",
                    lines=2,
                    interactive=False,
                )

                # LLM 回复
                reply_output = gr.Textbox(
                    label="💬 LLM 回复文本",
                    lines=4,
                    interactive=False,
                )

                # 回复音频
                audio_output = gr.Audio(
                    label="🔊 TTS 合成音频",
                    type="filepath",
                )

        # 使用示例
        with gr.Accordion("📖 使用说明", open=False):
            gr.Markdown("""
            ## 使用步骤

            1. **启动服务**（如果还未启动）：
               ```bash
               python -m app.main
               ```

            2. **选择输入方式**：
               - 点击麦克风图标录制音频
               - 或上传音频文件（支持 WAV, MP3, OGG 等格式）

            3. **可选：添加上下文**：
               - 输入 JSON 格式的上下文信息
               - 例如：`{"user_id": "user123", "session_id": "abc"}`

            4. **点击发送**：
               - 点击"发送并处理"按钮
               - 等待处理完成

            5. **查看结果**：
               - 状态信息：显示处理状态和元数据
               - ASR 文本：语音识别的文本结果
               - LLM 回复：智能回复的文本
               - TTS 音频：合成的语音（如果有）

            ## 测试场景

            ### 固定指令测试
            说出以下指令之一：
            - "打开灯" / "关闭灯"
            - "打开空调" / "关闭空调"
            - "播放音乐" / "停止播放"
            - "今天天气"

            ### 问答测试
            提出问题：
            - "智能家居能做什么？"
            - "如何设置空调温度？"
            - "系统支持哪些场景模式？"

            ### 闲聊测试
            随意交谈：
            - "你好"
            - "今天天气怎么样"
            - "给我讲个笑话"
            """)

        # 预定义示例
        gr.Markdown("### 🎯 快速测试")
        gr.Markdown("点击下方按钮快速测试固定指令（需要先生成测试音频）")

        with gr.Row():
            example_btn1 = gr.Button("示例 1: 打开灯", size="sm")
            example_btn2 = gr.Button("示例 2: 查询天气", size="sm")
            example_btn3 = gr.Button("示例 3: 播放音乐", size="sm")

        # 事件处理
        submit_btn.click(
            fn=sync_process_voice_chat,
            inputs=[audio_input, context_input],
            outputs=[status_output, asr_output, reply_output, audio_output],
        )

        health_btn.click(
            fn=check_service_health,
            inputs=[],
            outputs=[status_output],
        )

        # 示例按钮（这些需要预先生成的音频文件）
        def load_example(text: str):
            return f'{{"text": "{text}"}}', f"示例：{text}\n\n请录制或上传音频文件"

        example_btn1.click(
            fn=lambda: load_example("打开灯"),
            inputs=[],
            outputs=[context_input, status_output],
        )

        example_btn2.click(
            fn=lambda: load_example("今天天气"),
            inputs=[],
            outputs=[context_input, status_output],
        )

        example_btn3.click(
            fn=lambda: load_example("播放音乐"),
            inputs=[],
            outputs=[context_input, status_output],
        )

        # 页脚
        gr.Markdown("""
        ---
        💡 **提示**：
        - 确保麦克风权限已开启
        - 录音时尽量在安静环境
        - 音频会自动转换为 16kHz 单声道格式
        - 如果服务未响应，请检查服务是否正常运行

        📚 **文档**：查看 [API.md](./API.md) 了解更多信息
        """)

    return demo


def main():
    """主函数"""
    import os
    
    # 创建项目内的临时目录，避免 /tmp 权限问题
    temp_dir = os.path.join(os.path.dirname(__file__), 'tmp', 'gradio')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 设置 Gradio 临时目录环境变量
    os.environ['GRADIO_TEMP_DIR'] = temp_dir
    
    # 检查服务是否运行
    print("=" * 60)
    print("语音聊天服务 - Gradio 测试平台")
    print("=" * 60)

    health_status = check_service_health()
    print("\n服务状态：")
    print(health_status)

    if "❌" in health_status:
        print("\n⚠️  警告：服务似乎未运行！")
        print("请先启动服务：python -m app.main")
        print("\n按 Ctrl+C 退出，或继续启动 Gradio（服务启动后即可使用）\n")

    # 创建并启动界面
    demo = create_interface()

    print("\n启动 Gradio 界面...")
    print("访问地址：http://localhost:8860")
    print("按 Ctrl+C 停止服务\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=8192,
        share=False,
        show_error=True,
        ssl_certfile="cert.pem",
        ssl_keyfile="key.pem",
        ssl_verify=False,
    )


if __name__ == "__main__":
    main()
