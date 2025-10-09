#!/usr/bin/env python3
"""
WebSocket 客户端示例
演示如何连接到语音聊天服务并发送/接收消息
"""
import asyncio
import websockets
import json
import base64
import sys
from pathlib import Path


async def test_voice_chat(audio_file: str = None):
    """
    测试语音聊天服务
    
    Args:
        audio_file: 音频文件路径（PCM格式）
    """
    uri = "ws://localhost:8000/ws"
    
    print(f"正在连接到 {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ 连接成功")
            
            # 准备音频数据
            if audio_file and Path(audio_file).exists():
                print(f"读取音频文件: {audio_file}")
                with open(audio_file, "rb") as f:
                    audio_data = f.read()
                print(f"音频大小: {len(audio_data)} 字节")
            else:
                print("生成测试音频数据...")
                # 生成1秒的测试音频（正弦波）
                import numpy as np
                sample_rate = 16000
                duration = 1  # 秒
                frequency = 440  # Hz (A4音符)
                
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_float = 0.3 * np.sin(2 * np.pi * frequency * t)
                audio_int16 = (audio_float * 32767).astype(np.int16)
                audio_data = audio_int16.tobytes()
                print(f"测试音频大小: {len(audio_data)} 字节")
            
            # Base64 编码
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建消息
            message = {
                "type": "audio",
                "data": audio_base64,
                "context": {
                    "user_id": "test_user_001",
                    "session_id": "test_session_001",
                    "timestamp": asyncio.get_event_loop().time()
                },
                "is_end": True
            }
            
            # 发送消息
            print("\n发送音频消息...")
            await websocket.send(json.dumps(message))
            print("✓ 消息已发送")
            
            # 接收响应
            print("\n等待服务器响应...")
            response = await websocket.recv()
            result = json.loads(response)
            
            # 打印结果
            print("\n" + "=" * 50)
            print("收到响应:")
            print("=" * 50)
            print(f"消息类型: {result.get('type')}")
            
            if result.get('type') == 'result':
                print(f"技能ID: {result.get('skill_id')}")
                print(f"回复文本: {result.get('text')}")
                print(f"是否固定指令: {result.get('metadata', {}).get('is_fixed_command')}")
                
                if result.get('metadata'):
                    print(f"\n元数据:")
                    for key, value in result['metadata'].items():
                        print(f"  {key}: {value}")
                
                # 保存返回的音频
                if result.get('audio'):
                    audio_bytes = base64.b64decode(result['audio'])
                    output_file = "response_audio.pcm"
                    with open(output_file, "wb") as f:
                        f.write(audio_bytes)
                    print(f"\n✓ 音频已保存到: {output_file}")
                    print(f"  音频大小: {len(audio_bytes)} 字节")
                else:
                    print("\n(未返回音频数据)")
                    
            elif result.get('type') == 'error':
                print(f"错误代码: {result.get('code')}")
                print(f"错误消息: {result.get('message')}")
                if result.get('details'):
                    print(f"错误详情: {result.get('details')}")
            
            print("=" * 50)
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_heartbeat():
    """测试心跳功能"""
    uri = "ws://localhost:8000/ws"
    
    print(f"正在连接到 {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ 连接成功")
            
            # 发送心跳
            heartbeat_msg = {
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            print("\n发送心跳消息...")
            await websocket.send(json.dumps(heartbeat_msg))
            print("✓ 心跳已发送")
            
            # 接收响应
            print("等待心跳响应...")
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"\n✓ 收到心跳响应: {result}")
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 50)
    print("  语音聊天服务 - 客户端示例")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--heartbeat":
            print("\n测试模式: 心跳")
            asyncio.run(test_heartbeat())
        else:
            print(f"\n测试模式: 发送音频文件")
            asyncio.run(test_voice_chat(sys.argv[1]))
    else:
        print("\n测试模式: 发送测试音频")
        asyncio.run(test_voice_chat())


if __name__ == "__main__":
    main()

