#!/usr/bin/env python3
"""
语音聊天服务启动脚本（跨平台）
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"当前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("错误: 需要 Python 3.9 或更高版本")
        sys.exit(1)


def create_venv():
    """创建虚拟环境"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("\n创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("虚拟环境创建完成")
    else:
        print("\n虚拟环境已存在")


def get_venv_python():
    """获取虚拟环境的Python路径"""
    if sys.platform == "win32":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")


def install_dependencies():
    """安装依赖"""
    print("\n安装依赖包...")
    venv_python = get_venv_python()
    
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True
    )
    
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
        check=True
    )
    
    print("依赖安装完成")


def check_env_file():
    """检查环境变量文件"""
    env_file = Path(".env")
    env_example = Path("env_example")
    
    if not env_file.exists():
        print("\n未找到 .env 文件")
        if env_example.exists():
            print("从 env_example 复制...")
            import shutil
            shutil.copy(env_example, env_file)
            print(".env 文件已创建")
            print("请编辑 .env 文件，填入实际配置后再启动服务")
            return False
        else:
            print("错误: 未找到 env_example 文件")
            return False
    
    return True


def create_logs_dir():
    """创建日志目录"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("日志目录已创建")


def start_service():
    """启动服务"""
    print("\n" + "=" * 50)
    print("  启动语音聊天服务")
    print("=" * 50 + "\n")
    
    venv_python = get_venv_python()
    
    try:
        subprocess.run([str(venv_python), "-m", "app.main"], check=True)
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 50)
    print("  语音聊天服务启动脚本")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 创建虚拟环境
    create_venv()
    
    # 安装依赖
    install_dependencies()
    
    # 检查环境变量文件
    if not check_env_file():
        sys.exit(0)
    
    # 创建日志目录
    create_logs_dir()
    
    # 启动服务
    start_service()


if __name__ == "__main__":
    main()

