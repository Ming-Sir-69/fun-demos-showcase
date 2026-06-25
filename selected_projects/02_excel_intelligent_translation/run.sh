#!/bin/bash
# 激活虚拟环境并执行主程序

# 获取当前脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查虚拟环境是否存在
if [ ! -d "$DIR/.venv" ]; then
    echo "❌ 虚拟环境 .venv 不存在，请先配置环境。"
    exit 1
fi

# 激活并运行
source "$DIR/.venv/bin/activate"
python3 "$DIR/src/main.py"
