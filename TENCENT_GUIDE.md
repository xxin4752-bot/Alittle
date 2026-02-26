# 腾讯云 Ubuntu 服务器部署指南

本指南将帮助您在腾讯云 Ubuntu 服务器上部署 Crypto Portfolio Tracker 网站。

## 准备工作

1.  **购买服务器**：
    *   登录腾讯云控制台。
    *   购买一台 **轻量应用服务器** (Lighthouse) 或 **云服务器** (CVM)。
    *   **操作系统**：推荐选择 **Ubuntu 22.04 LTS** 或 **Ubuntu 24.04 LTS**。
    *   **防火墙/安全组**：确保 **80 (HTTP)** 和 **443 (HTTPS)** 端口已开放。

2.  **连接服务器**：
    *   使用 SSH 连接到您的服务器（推荐使用 Termius, Putty 或 Mac 终端）。
    *   命令示例：`ssh ubuntu@your_server_ip`
    *   默认用户名通常是 `ubuntu`。如果是 `root` 用户，请将下面命令中的 `/home/ubuntu` 替换为 `/root`，并去掉 `sudo`。

## 一键安装

1.  **更新系统并安装 git**：
    ```bash
    sudo apt update
    sudo apt install -y git
    ```

2.  **克隆代码仓库**：
    ```bash
    git clone https://github.com/xxin4752-bot/Alittle.git crypto-portfolio
    cd crypto-portfolio
    ```

3.  **运行安装脚本**：
    ```bash
    chmod +x deploy/install.sh
    ./deploy/install.sh
    ```

4.  **完成！**
    *   脚本运行完成后，直接在浏览器输入您的 **服务器 IP 地址** 即可访问网站。

## 高级配置 (可选)

### 配置域名和 HTTPS (SSL 证书)

如果您有域名，建议配置 HTTPS 以保证安全。

1.  **解析域名**：
    *   在域名控制台将域名 (A 记录) 解析到您的服务器 IP。

2.  **安装 Certbot**：
    ```bash
    sudo apt install -y certbot python3-certbot-nginx
    ```

3.  **申请证书**：
    ```bash
    sudo certbot --nginx -d yourdomain.com
    ```
    (将 `yourdomain.com` 替换为您的真实域名)

4.  **自动续期**：
    Certbot 会自动配置定时任务进行续期，无需手动操作。

## 常用命令

*   **查看服务状态**：
    ```bash
    sudo systemctl status crypto_portfolio
    ```
*   **重启服务** (代码更新后)：
    ```bash
    cd ~/crypto-portfolio
    git pull
    sudo systemctl restart crypto_portfolio
    ```
*   **查看日志**：
    ```bash
    journalctl -u crypto_portfolio -f
    ```
