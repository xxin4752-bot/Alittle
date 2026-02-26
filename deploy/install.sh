#!/bin/bash

# Exit on error
set -e

echo "开始安装 Crypto Portfolio Tracker..."

# Update system
echo "更新系统软件源..."
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev build-essential libpq-dev git nginx

# Create directory
APP_DIR="/home/ubuntu/crypto-portfolio"
REPO_URL="https://github.com/xxin4752-bot/Alittle.git"

if [ -d "$APP_DIR" ]; then
    echo "目录已存在，拉取最新代码..."
    cd $APP_DIR
    git pull
else
    echo "克隆代码仓库..."
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Setup Virtual Environment
echo "配置 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn uvicorn

# Setup Systemd
echo "配置 Systemd 服务..."
# Replace User/Group/Path in service file if needed
# Assuming default ubuntu user for simplicity
sudo cp deploy/systemd/crypto_portfolio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crypto_portfolio
sudo systemctl restart crypto_portfolio

# Setup Nginx
echo "配置 Nginx 反向代理..."
sudo cp deploy/nginx/crypto_portfolio /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/crypto_portfolio /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "========================================="
echo "安装完成！"
echo "请访问您的服务器 IP 地址查看网站。"
echo "如果需要配置域名和 HTTPS，请参考部署指南。"
echo "========================================="
