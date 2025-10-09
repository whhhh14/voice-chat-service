#!/usr/bin/env python3
"""
生成测试音频文件
"""
import numpy as np
import sys
from pathlib import Path


def generate_silence(duration: float = 1.0, sample_rate: int = 16000) -> bytes:
    """
    生成静音音频
    
    Args:
        duration: 时长（秒）
        sample_rate: 采样率
        
    Returns:
        PCM 音频字节数据
    """
    num_samples = int(sample_rate * duration)
    audio = np.zeros(num_samples, dtype=np.int16)
    return audio.tobytes()


def generate_sine_wave(
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.3
) -> bytes:
    """
    生成正弦波音频
    
    Args:
        frequency: 频率（Hz）
        duration: 时长（秒）
        sample_rate: 采样率
        amplitude: 振幅（0-1）
        
    Returns:
        PCM 音频字节数据
    """
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples)
    audio_float = amplitude * np.sin(2 * np.pi * frequency * t)
    audio_int16 = (audio_float * 32767).astype(np.int16)
    return audio_int16.tobytes()


def generate_beep_sequence(
    beep_frequency: float = 880.0,
    beep_duration: float = 0.2,
    silence_duration: float = 0.2,
    num_beeps: int = 3,
    sample_rate: int = 16000
) -> bytes:
    """
    生成蜂鸣序列
    
    Args:
        beep_frequency: 蜂鸣音频率
        beep_duration: 蜂鸣时长
        silence_duration: 静音时长
        num_beeps: 蜂鸣次数
        sample_rate: 采样率
        
    Returns:
        PCM 音频字节数据
    """
    audio_parts = []
    
    for i in range(num_beeps):
        # 添加蜂鸣音
        beep = generate_sine_wave(beep_frequency, beep_duration, sample_rate)
        audio_parts.append(beep)
        
        # 添加静音（最后一个蜂鸣音后不加静音）
        if i < num_beeps - 1:
            silence = generate_silence(silence_duration, sample_rate)
            audio_parts.append(silence)
    
    return b"".join(audio_parts)


def generate_sweep(
    start_freq: float = 200.0,
    end_freq: float = 2000.0,
    duration: float = 2.0,
    sample_rate: int = 16000,
    amplitude: float = 0.3
) -> bytes:
    """
    生成扫频音频（频率逐渐变化）
    
    Args:
        start_freq: 起始频率
        end_freq: 结束频率
        duration: 时长
        sample_rate: 采样率
        amplitude: 振幅
        
    Returns:
        PCM 音频字节数据
    """
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples)
    
    # 线性扫频
    freq = np.linspace(start_freq, end_freq, num_samples)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    audio_float = amplitude * np.sin(phase)
    audio_int16 = (audio_float * 32767).astype(np.int16)
    return audio_int16.tobytes()


def main():
    """主函数"""
    print("=" * 50)
    print("  测试音频生成工具")
    print("=" * 50)
    
    # 创建输出目录
    output_dir = Path("test_audio")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n输出目录: {output_dir}")
    
    # 生成各种测试音频
    tests = [
        {
            "name": "silence_1s",
            "desc": "1秒静音",
            "generator": lambda: generate_silence(1.0)
        },
        {
            "name": "sine_440hz_1s",
            "desc": "440Hz 正弦波 1秒",
            "generator": lambda: generate_sine_wave(440.0, 1.0)
        },
        {
            "name": "sine_880hz_2s",
            "desc": "880Hz 正弦波 2秒",
            "generator": lambda: generate_sine_wave(880.0, 2.0)
        },
        {
            "name": "beep_sequence",
            "desc": "蜂鸣序列（3次）",
            "generator": lambda: generate_beep_sequence()
        },
        {
            "name": "frequency_sweep",
            "desc": "扫频 200-2000Hz",
            "generator": lambda: generate_sweep()
        },
        {
            "name": "short_beep",
            "desc": "短蜂鸣（测试VAD）",
            "generator": lambda: generate_sine_wave(1000.0, 0.1)
        },
        {
            "name": "long_tone",
            "desc": "长音调 5秒",
            "generator": lambda: generate_sine_wave(500.0, 5.0)
        },
    ]
    
    print("\n生成测试音频:")
    for test in tests:
        filename = output_dir / f"{test['name']}.pcm"
        print(f"\n  {test['desc']}")
        print(f"    文件: {filename}")
        
        audio_data = test['generator']()
        
        with open(filename, "wb") as f:
            f.write(audio_data)
        
        print(f"    大小: {len(audio_data)} 字节")
        print(f"    时长: {len(audio_data) / (16000 * 2):.2f} 秒")
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    print(f"\n所有测试音频已保存到: {output_dir}")
    print("\n使用方法:")
    print(f"  python examples/client_example.py {output_dir}/sine_440hz_1s.pcm")


if __name__ == "__main__":
    main()

