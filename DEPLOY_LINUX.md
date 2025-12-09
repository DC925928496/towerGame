# towerGame Linux 部署指南

> 目标：在一台 Linux 服务器上部署 towerGame，使用 Nginx 提供 `index.html` 静态页面，由 Python WebSocket 服务器提供游戏后台逻辑。

---

## 1. 推荐目录结构

假设在服务器上使用以下目录：

```bash
/opt/towerGame        # 后端代码目录（完整拷贝当前仓库）
/opt/towerGame/venv   # Python 虚拟环境
/var/www/towergame    # 前端静态资源目录，只放 index.html（及后续需要的静态文件）
```

你可以根据实际需要调整路径，但后续示例都会以这个结构说明。

---

## 2. 环境准备

### 2.1 必备组件

- 操作系统：任意主流 Linux 发行版（Ubuntu / Debian / CentOS / Rocky 等）  
- 软件：
  - Python ≥ 3.10（建议 3.11+）
  - `pip` / `venv`
  - Nginx

以 Debian/Ubuntu 为例：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
```

### 2.2 获取代码

可以通过 git 或直接打包上传：

```bash
sudo mkdir -p /opt/towerGame
sudo chown $USER:$USER /opt/towerGame
cd /opt/towerGame

# 如果你有 git 仓库
git clone <your-repo-url> .

# 或者直接把本地项目整体上传到 /opt/towerGame
```

---

## 3. Python 后端部署

### 3.1 创建虚拟环境并安装依赖

```bash
cd /opt/towerGame
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

> 说明：当前项目使用 `websockets` 等标准第三方库，`requirements.txt` 中已经列出所需依赖。

### 3.2 配置监听地址与端口

`game_server.py` 中已经改为通过环境变量控制监听地址和端口：

- `TOWERGAME_HOST`：默认 `0.0.0.0`（对外监听）  
- `TOWERGAME_PORT`：默认 `8080`

在多数情况下可以直接使用默认值，无需额外配置。如果需要自定义端口，例如改成 9000：

```bash
export TOWERGAME_PORT=9000
```

### 3.3 直接启动（调试用）

```bash
cd /opt/towerGame
source venv/bin/activate
python game_server.py
```

正常情况下，会看到类似输出：

```text
服务器已启动: ws://0.0.0.0:8080
请通过 Nginx 反向代理此端口，并在浏览器中访问部署好的 index.html 开始游戏
```

> 生产环境建议使用 systemd 管理后台进程，避免 SSH 断开导致服务停止。

### 3.4 使用 systemd 管理后台服务（推荐）

创建 service 文件（以 root 身份）：

```bash
sudo tee /etc/systemd/system/towergame.service >/dev/null << 'EOF'
[Unit]
Description=Tower Game WebSocket Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/towerGame
ExecStart=/opt/towerGame/venv/bin/python /opt/towerGame/game_server.py
Environment=TOWERGAME_HOST=0.0.0.0
Environment=TOWERGAME_PORT=8080
Restart=on-failure
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
EOF
```

> 注意：
> - `User`/`Group` 可根据你服务器实际用户调整（例如 `ubuntu` 或 `tower`），只要对 `/opt/towerGame` 目录有读写权限即可。  
> - 如果你使用数据库功能，请确保 `.env` / 数据库配置在该用户下可读。

加载并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable towergame
sudo systemctl start towergame

sudo systemctl status towergame
```

当状态为 `active (running)` 即表示 WebSocket 后端已经在监听端口（默认 8080）。

---

## 4. Nginx 静态资源与 WebSocket 反向代理

### 4.1 拷贝前端文件到 Nginx 静态目录

```bash
sudo mkdir -p /var/www/towergame
sudo chown $USER:$USER /var/www/towergame

cd /opt/towerGame
cp index.html /var/www/towergame/
```

如果后续有其他静态资源（图片、CSS、JS 单独文件），同样放在 `/var/www/towergame` 下即可。

### 4.2 Nginx 站点配置示例

创建一个新的 server 配置（以默认 80 端口为例）：

```bash
sudo tee /etc/nginx/sites-available/towergame.conf >/dev/null << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # 前端静态页面
    root /var/www/towergame;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # WebSocket 反向代理到 Python 服务器
    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 60s;
    }
}
EOF
```

> 请将 `YOUR_DOMAIN_OR_IP` 替换为你的域名或服务器 IP。  
> 如果你使用 HTTPS（推荐），再配合 `certbot` / `acme.sh` 等工具为该 server 块配置证书即可。

启用该站点并重载 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/towergame.conf /etc/nginx/sites-enabled/towergame.conf
sudo nginx -t
sudo systemctl reload nginx
```

此时通过浏览器访问：

```text
http://YOUR_DOMAIN_OR_IP/
```

即可加载 `/var/www/towergame/index.html`，前端会自动使用：

```js
new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws')
```

连接到 Nginx 暴露的 `/ws` 路径，而 Nginx 会将该路径反代到 `127.0.0.1:8080` 的 Python WebSocket 服务器。

---

## 5. 生产环境运行与更新流程

### 5.1 首次部署完整步骤小结

1. **拷贝项目代码** 到 `/opt/towerGame`。  
2. **创建并激活虚拟环境**，执行 `pip install -r requirements.txt`。  
3. **创建 systemd 服务** `towergame.service`，启用并启动服务。  
4. **拷贝 `index.html`** 到 `/var/www/towergame/`。  
5. **创建 Nginx 站点** `towergame.conf`，指向静态目录并配置 `/ws` 反代到后端端口。  
6. `nginx -t` 校验配置、`systemctl reload nginx` 生效。  
7. 在浏览器访问 `http://YOUR_DOMAIN_OR_IP/` 验证游戏是否正常运行。

### 5.2 升级代码

当你在本地对项目做了修改并准备上线时：

```bash
cd /opt/towerGame
git pull   # 或者重新拷贝覆盖代码

source venv/bin/activate
pip install -r requirements.txt  # 如有依赖变化

sudo systemctl restart towergame

# 如 index.html 有更新
cp index.html /var/www/towergame/
sudo systemctl reload nginx
```

---

## 6. 常见问题排查

1. **页面能打开但提示“未连接”**  
   - 检查 Nginx `/ws` 配置是否存在、是否指向正确端口。  
   - 检查 `towergame` 服务是否在运行：`sudo systemctl status towergame`。  
   - 使用 `ss -ltnp | grep 8080` 确认后端端口是否在监听。

2. **浏览器控制台提示 WebSocket 握手失败**  
   - 如果在 HTTPS 站点上访问，浏览器会使用 `wss://`，请确保：  
     - Nginx 使用了真实证书，且没有混合内容；  
     - `/ws` 的反向代理目标仍为 `http://127.0.0.1:8080`，这是正常的（Nginx 负责 TLS 终止）。  

3. **数据库相关错误**  
   - 若你尚未在 Linux 服务器上配置数据库，可以暂时不设置数据库；`game_server.py` 在检测到数据库不可用时会自动退回本地模式。  
   - 未来需要持久化存档时，再根据 `config/database_config.py` 和 README 的数据库章节单独做配置。

---

## 7. 与项目结构相关的说明

- 后端：仍然使用仓库根目录中的 `game_server.py` 作为唯一入口，部署时只需在 Linux 服务器上运行该文件。  
- 前端：单文件 `index.html`，可放在 Nginx 任意静态目录下，本指南默认 `/var/www/towergame`。  
- 配置：
  - 监听地址与端口已经参数化为 `TOWERGAME_HOST` / `TOWERGAME_PORT`，更适合在不同环境（开发/测试/生产）中部署。  
  - 其余游戏参数依旧集中在 `config/game_config.py` 中，Linux 与本地环境完全共用。

只要遵循本指南的目录与服务划分，你就可以在 Linux 服务器上稳定运行 towerGame，并通过 Nginx 暴露统一的 HTTP/WS 入口。

