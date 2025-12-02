# ATLI 相机实时处理系统 - 服务器部署指南

## 概述

本系统用于实时监控和处理 ATLI 相机上传的图片，包括 OCR 时间戳提取、像素坐标提取、图片标注和备份功能。

## 系统要求

### 硬件要求
- CPU: 4核心以上
- 内存: 8GB 以上
- 存储空间: 100GB 以上（用于图片存储）
- 网络: 稳定的网络连接

### 软件要求
- 操作系统: CentOS 7/8 或 Ubuntu 18.04+
- Python: 3.8
- Tesseract OCR: 4.0+

## 部署步骤

### 1. 系统准备

#### 1.1 更新系统
```bash
# CentOS
sudo yum update -y

# Ubuntu
sudo apt update && sudo apt upgrade -y
```

#### 1.2 安装必要的系统包
```bash
# CentOS
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python38 python38-pip python38-devel
sudo yum install -y opencv opencv-devel
sudo yum install -y epel-release
sudo yum install -y tesseract tesseract-langpack-eng tesseract-langpack-chi-sim

# Ubuntu
sudo apt install -y build-essential
sudo apt install -y python3.8 python3.8-pip python3.8-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim
sudo apt install -y libtesseract-dev
```

#### 1.3 验证 Tesseract 安装
```bash
tesseract --version
# 应该显示版本信息，如 tesseract 4.1.1
```

### 2. 创建项目目录和用户

#### 2.1 创建专用用户（可选但推荐）
```bash
sudo useradd -m -s /bin/bash atli_monitor
sudo usermod -aG wheel atli_monitor  # CentOS
sudo usermod -aG sudo atli_monitor   # Ubuntu
```

#### 2.2 创建项目目录结构
```bash
sudo mkdir -p /opt/atli_camera_monitor
sudo mkdir -p /var/ftp/atli_uploads/camera1
sudo mkdir -p /var/ftp/atli_uploads/camera2
sudo mkdir -p /var/ftp/atli_processed
sudo mkdir -p /var/log/atli_monitor

# 设置目录权限
sudo chown -R atli_monitor:atli_monitor /opt/atli_camera_monitor
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_uploads
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_processed
sudo chown -R atli_monitor:atli_monitor /var/log/atli_monitor
```

### 3. 部署应用代码

#### 3.1 切换到项目用户
```bash
sudo su - atli_monitor
```

#### 3.2 上传项目文件
将以下文件上传到 `/opt/atli_camera_monitor/` 目录：
- `RT_Pixel_Ex.py`
- `Ex_Pixel.py`
- `Ex_center_yuan.py`
- `ocr_Ex_time.py`
- `config_loader.py`
- `config.yaml`
- `requirements.txt`

#### 3.3 创建虚拟环境
```bash
cd /opt/atli_camera_monitor
python3.8 -m venv venv
source venv/bin/activate
```

#### 3.4 安装 Python 依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置系统

#### 4.1 修改配置文件
编辑 `/opt/atli_camera_monitor/config.yaml`，确保路径配置正确：

```yaml
# 路径配置
paths:
  # 相机上传图片的根目录（监听源）
  base_upload_path: "/var/ftp/atli_uploads"
  
  # 处理结果输出的根目录（像素坐标和备份图片）
  base_processed_path: "/var/ftp/atli_processed"

# Tesseract OCR 配置
tesseract:
  # Tesseract 可执行文件路径
  cmd_path: "/usr/bin/tesseract"

# 其他配置保持不变...
```

#### 4.2 验证配置
```bash
cd /opt/atli_camera_monitor
source venv/bin/activate
python config_loader.py
```

### 5. 创建系统服务

#### 5.1 创建 systemd 服务文件
```bash
sudo tee /etc/systemd/system/atli-camera-monitor.service << EOF
[Unit]
Description=ATLI Camera Monitor Service
After=network.target

[Service]
Type=simple
User=atli_monitor
Group=atli_monitor
WorkingDirectory=/opt/atli_camera_monitor
Environment=PATH=/opt/atli_camera_monitor/venv/bin
ExecStart=/opt/atli_camera_monitor/venv/bin/python RT_Pixel_Ex.py
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=atli-camera-monitor

# 资源限制
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

#### 5.2 启用并启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable atli-camera-monitor.service
sudo systemctl start atli-camera-monitor.service
```

#### 5.3 检查服务状态
```bash
sudo systemctl status atli-camera-monitor.service
```

### 6. 配置日志轮转

#### 6.1 创建日志轮转配置
```bash
sudo tee /etc/logrotate.d/atli-camera-monitor << EOF
/var/log/atli_monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 atli_monitor atli_monitor
    postrotate
        systemctl reload atli-camera-monitor.service > /dev/null 2>&1 || true
    endscript
}
EOF
```

### 7. 防火墙配置（如果需要）

如果需要通过网络访问文件，可能需要配置防火墙：

```bash
# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=21/tcp  # FTP
sudo firewall-cmd --reload

# Ubuntu (ufw)
sudo ufw allow 21/tcp
```

### 8. 监控和维护

#### 8.1 查看实时日志
```bash
# 查看系统日志
sudo journalctl -u atli-camera-monitor.service -f

# 查看应用日志
tail -f /var/log/atli_monitor/atli_camera_monitor.log
```

#### 8.2 重启服务
```bash
sudo systemctl restart atli-camera-monitor.service
```

#### 8.3 停止服务
```bash
sudo systemctl stop atli-camera-monitor.service
```

#### 8.4 检查磁盘空间
```bash
df -h /var/ftp/
```

## 故障排除

### 1. Tesseract 相关错误

如果出现 Tesseract 路径错误：
```bash
# 查找 Tesseract 安装路径
which tesseract
whereis tesseract

# 更新配置文件中的路径
vim /opt/atli_camera_monitor/config.yaml
```

### 2. 权限问题

如果出现权限错误：
```bash
# 检查目录权限
ls -la /var/ftp/
ls -la /opt/atli_camera_monitor/

# 修正权限
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_uploads
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_processed
```

### 3. Python 依赖问题

如果出现 Python 包导入错误：
```bash
cd /opt/atli_camera_monitor
source venv/bin/activate
pip list
pip install --upgrade -r requirements.txt
```

### 4. 内存不足

如果系统内存不足：
```bash
# 创建 swap 文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久添加到 fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 性能优化建议

### 1. 系统优化
- 增加文件描述符限制
- 优化磁盘 I/O 性能
- 配置合适的 swap 空间

### 2. 应用优化
- 根据相机数量调整处理线程
- 定期清理旧的处理文件
- 监控内存使用情况

### 3. 存储优化
- 使用 SSD 存储提高性能
- 配置自动清理策略
- 实施数据备份策略

## 安全注意事项

1. **用户权限**: 使用专用用户运行服务
2. **文件权限**: 限制文件访问权限
3. **网络安全**: 如果开放网络访问，配置防火墙
4. **定期更新**: 保持系统和依赖包更新

## 联系信息

如有问题，请联系：
- 邮箱: 2985045154@qq.com
- 项目: Outdoor_RTCamProc v1.0.0

---

*部署完成后，系统将自动监控 `/var/ftp/atli_uploads/camera1` 和 `/var/ftp/atli_uploads/camera2` 目录中的新图片，并将处理结果保存到 `/var/ftp/atli_processed` 目录。*
