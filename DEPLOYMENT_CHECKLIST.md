# ATLI 相机监控系统部署检查清单

## 📋 部署前检查

### ✅ 文件准备
- [ ] `RT_Pixel_Ex.py` - 主程序文件
- [ ] `Ex_Pixel.py` - 像素坐标提取模块
- [ ] `Ex_center_yuan.py` - 圆心检测模块  
- [ ] `ocr_Ex_time.py` - OCR 时间戳提取模块
- [ ] `config_loader.py` - 配置加载模块
- [ ] `config.yaml` - 主配置文件（支持多环境）
- [ ] `requirements.txt` - Python 依赖列表
- [ ] `deploy.sh` - 一键部署脚本（Linux）
- [ ] `atli_monitor.sh` - 服务管理脚本（Linux）
- [ ] `init_windows_env.bat` - Windows环境初始化脚本
- [ ] `init_windows_env.ps1` - Windows环境初始化脚本（PowerShell）
- [ ] `check_env.py` - 环境检查脚本
- [ ] `DEPLOYMENT.md` - 详细部署文档
- [ ] `README.md` - 项目说明文档

### ✅ 系统要求
- [ ] 操作系统: CentOS 7/8 或 Ubuntu 18.04+
- [ ] Python: 3.8 或更高版本
- [ ] 内存: 8GB 或更多
- [ ] 磁盘空间: 100GB 或更多
- [ ] Root 权限

## 🚀 部署步骤

### 🪟 Windows 环境测试（可选）

在部署到服务器前，可以先在Windows环境下进行测试：

```powershell
# 1. 初始化Windows测试环境
# 运行批处理脚本
init_windows_env.bat

# 或运行PowerShell脚本
powershell -ExecutionPolicy Bypass -File init_windows_env.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行环境检查
python check_env.py

# 4. 测试系统
python RT_Pixel_Ex.py
```

**Windows环境配置路径**：
- 监控目录: `D:\pic_back\atli_uploads\camera1`, `D:\pic_back\atli_uploads\camera2`
- 输出目录: `D:\pic_back\atli_processed`
- Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 🐧 Linux 服务器部署

### 1. 上传文件到服务器
```bash
# 创建临时目录
mkdir -p /tmp/atli_deploy
cd /tmp/atli_deploy

# 上传所有项目文件到这个目录
# 使用 scp, rsync, 或其他方式
```

### 2. 运行一键部署脚本
```bash
cd /tmp/atli_deploy
chmod +x deploy.sh
sudo ./deploy.sh
```

### 3. 验证部署结果
```bash
# 检查服务状态
sudo systemctl status atli-camera-monitor

# 检查配置
python3 /opt/atli_camera_monitor/check_env.py

# 测试配置加载
cd /opt/atli_camera_monitor
sudo -u atli_monitor bash -c "source venv/bin/activate && python config_loader.py"
```

## 🔧 手动部署步骤（备选）

如果一键部署失败，可以按照以下步骤手动部署：

### 1. 安装系统依赖
```bash
# CentOS
sudo yum update -y
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python38 python38-pip python38-devel
sudo yum install -y epel-release
sudo yum install -y tesseract tesseract-langpack-eng

# Ubuntu
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3.8 python3.8-pip python3.8-dev python3.8-venv
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

### 2. 创建用户和目录
```bash
sudo useradd -m -s /bin/bash atli_monitor
sudo mkdir -p /opt/atli_camera_monitor
sudo mkdir -p /var/ftp/atli_uploads/camera{1,2}
sudo mkdir -p /var/ftp/atli_processed
sudo mkdir -p /var/log/atli_monitor

# 设置权限
sudo chown -R atli_monitor:atli_monitor /opt/atli_camera_monitor
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_uploads
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_processed
sudo chown -R atli_monitor:atli_monitor /var/log/atli_monitor
```

### 3. 部署项目文件
```bash
sudo cp *.py /opt/atli_camera_monitor/
sudo cp config.yaml /opt/atli_camera_monitor/
sudo cp requirements.txt /opt/atli_camera_monitor/
sudo cp atli_monitor.sh /opt/atli_camera_monitor/
sudo chmod +x /opt/atli_camera_monitor/atli_monitor.sh
sudo chown -R atli_monitor:atli_monitor /opt/atli_camera_monitor
```

### 4. 安装 Python 依赖
```bash
cd /opt/atli_camera_monitor
sudo -u atli_monitor python3.8 -m venv venv
sudo -u atli_monitor bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
```

### 5. 创建系统服务
```bash
sudo tee /etc/systemd/system/atli-camera-monitor.service << 'EOF'
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

StandardOutput=journal
StandardError=journal
SyslogIdentifier=atli-camera-monitor

LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable atli-camera-monitor
```

## ✅ 部署后验证

### 1. 检查服务状态
```bash
sudo systemctl status atli-camera-monitor
```

### 2. 检查日志
```bash
sudo journalctl -u atli-camera-monitor -f
```

### 3. 测试目录结构
```bash
ls -la /var/ftp/atli_uploads/
ls -la /var/ftp/atli_processed/
ls -la /opt/atli_camera_monitor/
```

### 4. 运行环境检查
```bash
cd /opt/atli_camera_monitor
sudo -u atli_monitor bash -c "source venv/bin/activate && python check_env.py"
```

### 5. 启动服务
```bash
sudo systemctl start atli-camera-monitor
sudo systemctl status atli-camera-monitor
```

## 🎯 功能测试

### 1. 上传测试图片
```bash
# 复制一张测试图片到监控目录
sudo cp test_image.jpg /var/ftp/atli_uploads/camera1/20251202142000_0001.jpg
sudo chown atli_monitor:atli_monitor /var/ftp/atli_uploads/camera1/20251202142000_0001.jpg
```

### 2. 检查处理结果
```bash
# 查看处理后的目录
ls -la /var/ftp/atli_processed/camera1/

# 查看日志确认处理过程
sudo journalctl -u atli-camera-monitor --since "5 minutes ago"
```

## 🔧 常用管理命令

```bash
# 启动服务
sudo /opt/atli_camera_monitor/atli_monitor.sh start

# 停止服务  
sudo /opt/atli_camera_monitor/atli_monitor.sh stop

# 重启服务
sudo /opt/atli_camera_monitor/atli_monitor.sh restart

# 查看状态
sudo /opt/atli_camera_monitor/atli_monitor.sh status

# 查看日志
sudo /opt/atli_camera_monitor/atli_monitor.sh logs

# 测试配置
sudo /opt/atli_camera_monitor/atli_monitor.sh test
```

## 📞 故障排除

### 如果 Tesseract 无法找到
```bash
# 查找 Tesseract 路径
which tesseract
whereis tesseract

# 更新配置文件
sudo -u atli_monitor vim /opt/atli_camera_monitor/config.yaml
# 修改 tesseract.cmd_path 为正确路径
```

### 如果 Python 依赖安装失败
```bash
cd /opt/atli_camera_monitor
sudo -u atli_monitor bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u atli_monitor bash -c "source venv/bin/activate && pip install -r requirements.txt --no-cache-dir"
```

### 如果权限问题
```bash
sudo chown -R atli_monitor:atli_monitor /opt/atli_camera_monitor
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_uploads
sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_processed
sudo chmod -R 755 /var/ftp/atli_uploads
sudo chmod -R 755 /var/ftp/atli_processed
```

## 🌍 多环境配置说明

系统现在支持自动环境检测，根据操作系统选择相应的配置：

### 环境配置
```yaml
# config.yaml 支持多环境配置
environments:
  windows:  # Windows 测试环境
    paths:
      base_upload_path: "D:\\pic_back\\atli_uploads"
      base_processed_path: "D:\\pic_back\\atli_processed"
    tesseract:
      cmd_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
  
  linux:    # Linux 生产环境
    paths:
      base_upload_path: "/var/ftp/atli_uploads"
      base_processed_path: "/var/ftp/atli_processed"
    tesseract:
      cmd_path: "/usr/bin/tesseract"
```

### 环境检测逻辑
- **Windows**: 自动使用 `environments.windows` 配置
- **Linux/Unix**: 自动使用 `environments.linux` 配置
- **备用**: 如果环境特定配置不存在，使用默认配置

### 手动指定环境
```python
from config_loader import load_config

# 自动检测环境
config = load_config()

# 手动指定环境
config = load_config(env='windows')  # 强制使用Windows配置
config = load_config(env='linux')    # 强制使用Linux配置
```

---

**部署完成后**：
- **Windows环境**: 系统监控 `D:\pic_back\atli_uploads` 目录
- **Linux环境**: 系统监控 `/var/ftp/atli_uploads` 目录
- 处理结果自动保存到对应的 processed 目录

**联系方式**: 2985045154@qq.com
