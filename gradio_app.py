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
from typing import Optional, Tuple, Dict
from datetime import datetime
import os
import loguru
import time
import hashlib
from pathlib import Path

logger = loguru.logger
logger.add("logs/gradio_app.log", rotation="10 MB", retention="7 days", enqueue=True, encoding="utf-8")

# 数据存储目录配置
DATA_DIR = Path(os.getcwd()) / "tmp"
INPUT_AUDIO_DIR = DATA_DIR / "input_audio"
OUTPUT_AUDIO_DIR = DATA_DIR / "tts_output"
RESULTS_DIR = DATA_DIR / "results"
GRADIO_TEMP_DIR = DATA_DIR / "gradio"

# 确保目录存在
for directory in [INPUT_AUDIO_DIR, OUTPUT_AUDIO_DIR, RESULTS_DIR, GRADIO_TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def calculate_audio_hash(audio_data: bytes) -> str:
    """
    计算音频数据的哈希值，用于去重
    
    Args:
        audio_data: 音频字节数据
        
    Returns:
        MD5 哈希值（16进制字符串）
    """
    return hashlib.md5(audio_data).hexdigest()


def save_audio_with_hash(audio_data: bytes, audio_float: np.ndarray, sample_rate: int, prefix: str = "input") -> Tuple[str, str, bool]:
    """
    保存音频文件，基于哈希值避免重复保存
    
    Args:
        audio_data: PCM 音频字节数据
        audio_float: 浮点音频数组
        sample_rate: 采样率
        prefix: 文件名前缀
        
    Returns:
        (文件路径, 哈希值, 是否新文件)
    """
    # 计算哈希
    audio_hash = calculate_audio_hash(audio_data)
    
    # 检查是否已存在
    target_dir = INPUT_AUDIO_DIR if prefix == "input" else OUTPUT_AUDIO_DIR
    existing_files = list(target_dir.glob(f"*_{audio_hash}.wav"))
    
    if existing_files:
        logger.info(f"音频已存在（哈希: {audio_hash}），跳过保存")
        return str(existing_files[0]), audio_hash, False
    
    # 生成新文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    duration = len(audio_float) / sample_rate
    filename = f"{timestamp}_{prefix}_{duration:.2f}s_{audio_hash}.wav"
    filepath = target_dir / filename
    
    # 保存为 WAV 文件
    try:
        wav_bytes = pcm_bytes_to_wav_bytes(audio_data, sample_rate)
        with open(filepath, 'wb') as f:
            f.write(wav_bytes)
        logger.info(f"音频已保存: {filepath} (哈希: {audio_hash})")
        return str(filepath), audio_hash, True
    except Exception as e:
        logger.error(f"保存音频失败: {e}")
        return "", audio_hash, False


def save_result_json(result_data: Dict, audio_hash: str) -> str:
    """
    保存处理结果为 JSON 文件
    
    Args:
        result_data: 结果数据字典
        audio_hash: 音频哈希值
        
    Returns:
        JSON 文件路径
    """
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_result_{audio_hash}.json"
        filepath = RESULTS_DIR / filename
        
        # 添加时间戳
        result_data["saved_at"] = datetime.now().isoformat()
        result_data["audio_hash"] = audio_hash
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        return ""


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


async def process_voice_chat(audio_input, context_str: str, ws_url: str) -> Tuple[str, str, Optional[str]]:
    """
    处理语音聊天

    Args:
        audio_input: 音频输入
        context_str: 上下文 JSON 字符串
        ws_url: WebSocket 服务端地址

    Returns:
        (状态信息, 识别文本, 回复文本, 回复音频路径)
    """
    request_start_time = time.time()
    input_audio_path = ""
    output_audio_path = ""
    audio_hash = ""
    
    try:
        logger.info("=" * 80)
        logger.info("开始处理语音聊天请求")
        
        # 处理音频
        logger.info("步骤 1: 处理输入音频")
        audio_float, sample_rate = process_audio_file(audio_input)
        if audio_float is None:
            logger.error("音频处理失败")
            return "❌ 音频处理失败", "", "", None

        # 转换为 PCM 字节
        pcm_data = audio_array_to_pcm_bytes(audio_float)
        audio_duration = len(audio_float) / sample_rate
        logger.info(f"音频处理完成: 时长 {audio_duration:.2f}秒, 大小 {len(pcm_data)} 字节")
        
        # 保存输入音频（带去重）
        logger.info("步骤 2: 保存输入音频")
        input_audio_path, audio_hash, is_new_audio = save_audio_with_hash(
            pcm_data, audio_float, sample_rate, prefix="input"
        )
        if is_new_audio:
            logger.info(f"新音频已保存: {input_audio_path}")
        else:
            logger.info(f"音频已存在，使用现有文件: {input_audio_path}")

        # 解析上下文
        logger.info("步骤 3: 解析上下文信息")
        try:
            context = json.loads(context_str) if context_str.strip() else {}
            logger.info(f"上下文: {context}")
        except json.JSONDecodeError:
            context = {"note": context_str}
            logger.warning(f"上下文JSON解析失败，作为普通文本处理: {context_str}")

        # 添加时间戳
        context["timestamp"] = datetime.now().isoformat()

        # 发送到服务器
        logger.info(f"步骤 4: 发送音频到服务器 ({ws_url})")
        client = VoiceChatClient(ws_url=ws_url)
        ws_start_time = time.time()
        result = await client.send_audio(pcm_data, context)
        ws_duration = time.time() - ws_start_time
        logger.info(f"服务器响应耗时: {ws_duration:.2f}秒")

        if result is None:
            logger.error("服务器无响应")
            return "❌ 服务器无响应", "", "", None

        # 解析结果
        logger.info("步骤 5: 解析服务器响应")
        if result.get("type") == "error":
            error_msg = result.get("message", "未知错误")
            logger.error(f"服务器返回错误: {error_msg}")
            
            # 保存错误结果
            result_data = {
                "status": "error",
                "error_message": error_msg,
                "input_audio_path": input_audio_path,
                "ws_url": ws_url,
                "context": context,
                "audio_duration": audio_duration,
                "processing_time": time.time() - request_start_time,
            }
            save_result_json(result_data, audio_hash)
            
            return f"❌ 错误: {error_msg}", "", "", None

        if result.get("type") == "result":
            skill_id = result.get("skill_id", "unknown")
            reply_text = result.get("text", "")
            metadata = result.get("metadata", {})
            asr_text = metadata.get("asr_text", "")
            confidence = metadata.get("confidence", 0)
            is_fixed_command = metadata.get("is_fixed_command", False)
            
            logger.info(f"识别成功 - 技能: {skill_id}, ASR: {asr_text}, 置信度: {confidence:.2%}")

            # 处理返回的音频
            audio_output = None
            output_audio_hash = ""
            if result.get("audio"):
                logger.info("步骤 6: 处理TTS输出音频")
                try:
                    audio_bytes = base64.b64decode(result["audio"])
                    logger.info(f"TTS音频大小: {len(audio_bytes)} 字节")
                    
                    # 计算输出音频的哈希
                    output_audio_hash = calculate_audio_hash(audio_bytes)
                    
                    # 检查是否已存在
                    existing_output = list(OUTPUT_AUDIO_DIR.glob(f"*_{output_audio_hash}.wav"))
                    if existing_output:
                        audio_output = str(existing_output[0])
                        logger.info(f"TTS音频已存在，使用现有文件: {audio_output}")
                    else:
                        # 保存新的TTS音频
                        timestamp_prefix = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp_prefix}_tts_output_{output_audio_hash}.wav"
                        audio_output = str(OUTPUT_AUDIO_DIR / filename)
                        
                        with open(audio_output, 'wb') as f:
                            f.write(pcm_bytes_to_wav_bytes(audio_bytes))
                        logger.info(f"TTS音频已保存: {audio_output}")
                    
                    output_audio_path = audio_output
                    
                except Exception as e:
                    logger.error(f"音频解码失败: {e}", exc_info=True)
            else:
                logger.info("无TTS音频输出")

            # 总耗时
            total_duration = time.time() - request_start_time
            logger.info(f"总处理耗时: {total_duration:.2f}秒")
            
            # 保存完整结果
            logger.info("步骤 7: 保存处理结果")
            # 移除音频数据，避免保存到结果中
            result.pop("audio", None)

            result_data = {
                "status": "success",
                "skill_id": skill_id,
                "asr_text": asr_text,
                "reply_text": reply_text,
                "confidence": confidence,
                "is_fixed_command": is_fixed_command,
                "input_audio_path": input_audio_path,
                "output_audio_path": output_audio_path,
                "output_audio_hash": output_audio_hash,
                "is_new_input_audio": is_new_audio,
                "audio_duration": audio_duration,
                "ws_url": ws_url,
                "context": context,
                "metadata": metadata,
                "timing": {
                    "ws_duration": ws_duration,
                    "total_duration": total_duration,
                },
                "server_response": result,
            }
            result_json_path = save_result_json(result_data, audio_hash)
            logger.info(f"结果已保存到: {result_json_path}")
            
            # 构建状态信息
            status = f"""✅ 处理成功

**技能 ID**: {skill_id}
**置信度**: {confidence:.2%}
**固定指令**: {'是' if is_fixed_command else '否'}
**音频时长**: {audio_duration:.2f} 秒
**处理耗时**: {total_duration:.2f} 秒
"""
            logger.info("处理完成!")
            logger.info("=" * 80)
            
            return status, asr_text, reply_text, audio_output

        logger.warning(f"未知响应类型: {result.get('type')}")
        return "❌ 未知响应类型", "", "", None

    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        
        # 保存错误信息
        try:
            result_data = {
                "status": "exception",
                "error": str(e),
                "error_type": type(e).__name__,
                "input_audio_path": input_audio_path,
                "ws_url": ws_url,
                "processing_time": time.time() - request_start_time,
            }
            if audio_hash:
                save_result_json(result_data, audio_hash)
        except:
            pass
            
        logger.info("=" * 80)
        return f"❌ 异常: {str(e)}", "", "", None

def sync_process_voice_chat(audio_input, context_str: str, ws_url: str):
    """同步包装器"""
    return asyncio.run(process_voice_chat(audio_input, context_str, ws_url))


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

                # ws_url 输入
                ws_url_input = gr.Textbox(
                    label="WebSocket 服务地址",
                    value="ws://192.168.111.9:8900/ws",
                    placeholder="ws://your.server:8900/ws",
                    lines=1,
                )

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
                    label="💬 回复文本",
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

            1. **输入 WebSocket 服务地址**：
               - 输入 WebSocket 服务地址，默认值为 `ws://192.168.111.9:8900/ws`

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

            ### 1. 固定指令测试
            说出以下指令之一 (更多指令请参考需求文档)：
            - Turn off Camera
            - Turn on Camera
            - Enable AI Tracking
            - Turn off AI Tracking
            - Call / Call mom / Call husband / Call wife / Call dad / Call son / Call daughter
            - Hang up
            - Take photo
            - Start recording
            - Stop recording

            ### 2. 宝宝啼哭场景
            问题示例：
            - Let me know when the baby cries. 
            - Let me know if the baby cries. 
            - Tell me when the baby cries. 
            - Tell me if the baby starts crying. 
            - Give me a heads-up when the baby cries. 
            - Notify me when the baby cries. 
            - Alert me when the baby cries. 

            ### 3. 包裹问询场景
            问题示例：
            - Is there a package at the door?
            - Any packages at the front door?
            - Do I have a package outside?
            - Anything delivered at the door?
            - Did any packages get delivered today?
            - Were there any deliveries today?
            - Did I get any packages today?
            - Anything delivered today?
            """)

        # 预定义示例
        # gr.Markdown("### 🎯 快速测试")
        # gr.Markdown("点击下方按钮快速测试固定指令（需要先生成测试音频）")

        # with gr.Row():
        #     example_btn1 = gr.Button("示例 1: 打开灯", size="sm")
        #     example_btn2 = gr.Button("示例 2: 查询天气", size="sm")
        #     example_btn3 = gr.Button("示例 3: 播放音乐", size="sm")

        # 事件处理
        submit_btn.click(
            fn=sync_process_voice_chat,
            inputs=[audio_input, context_input, ws_url_input],
            outputs=[status_output, asr_output, reply_output, audio_output],
        )

        # 示例按钮（这些需要预先生成的音频文件）
        def load_example(text: str):
            return f'{{"text": "{text}"}}', f"示例：{text}\n\n请录制或上传音频文件"

        # example_btn1.click(
        #     fn=lambda: load_example("打开灯"),
        #     inputs=[],
        #     outputs=[context_input, status_output],
        # )

        # example_btn2.click(
        #     fn=lambda: load_example("今天天气"),
        #     inputs=[],
        #     outputs=[context_input, status_output],
        # )

        # example_btn3.click(
        #     fn=lambda: load_example("播放音乐"),
        #     inputs=[],
        #     outputs=[context_input, status_output],
        # )

        # 页脚
        gr.Markdown("""
        ---
        💡 **提示**：
        - 确保麦克风权限已开启
        - 录音时尽量在安静环境
        - 音频会自动转换为 16kHz 单声道格式
        """)

    return demo


def main():
    """主函数"""    
    # 设置 Gradio 临时目录环境变量
    os.environ['GRADIO_TEMP_DIR'] = str(GRADIO_TEMP_DIR)
    
    # 打印数据存储目录信息
    print("=" * 60)
    print("语音聊天服务 - Gradio 测试平台")
    print("=" * 60)
    print(f"\n📁 数据存储目录:")
    print(f"  - 输入音频: {INPUT_AUDIO_DIR}")
    print(f"  - 输出音频: {OUTPUT_AUDIO_DIR}")
    print(f"  - 结果JSON: {RESULTS_DIR}")
    print(f"  - Gradio临时: {GRADIO_TEMP_DIR}")
    print()

    # 创建并启动界面
    demo = create_interface()

    print("\n启动 Gradio 界面...")
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
