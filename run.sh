#!/bin/bash

# 语音聊天服务启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  语音聊天服务启动脚本${NC}"
echo -e "${GREEN}================================${NC}"

# 检查 Python 版本
echo -e "\n${YELLOW}检查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "当前 Python 版本: ${GREEN}$python_version${NC}"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "\n${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "${GREEN}虚拟环境已激活${NC}"

# 安装依赖
echo -e "\n${YELLOW}安装依赖包...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}依赖安装完成${NC}"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}未找到 .env 文件，从 env_example 复制...${NC}"
    if [ -f "env_example" ]; then
        cp env_example .env
        echo -e "${GREEN}.env 文件已创建${NC}"
        echo -e "${RED}请编辑 .env 文件，填入实际配置后再启动服务${NC}"
        exit 0
    else
        echo -e "${RED}未找到 env_example 文件${NC}"
        exit 1
    fi
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}  启动语音聊天服务${NC}"
echo -e "${GREEN}================================${NC}\n"

python -m app.main

