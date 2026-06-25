#!/bin/bash

echo "清理旧的构建目录..."
rm -rf build/ dist/

echo "激活虚拟环境..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "开始使用 PyInstaller 打包..."
pyinstaller ExcelIntelligentTranslator.spec --clean

echo "清理扩展属性与重新签名以绕过资源分支报错..."
find dist/ExcelIntelligentTranslator.app -name ".DS_Store" -delete
xattr -cr dist/ExcelIntelligentTranslator.app || true
find dist/ExcelIntelligentTranslator.app -exec xattr -c -s {} +
codesign --force --deep --sign - dist/ExcelIntelligentTranslator.app

echo "打包完成！"
