# ATLI 相机实时处理系统

这是一个用于实时监控和处理 ATLI 相机上传图片的系统，支持 OCR 时间戳提取、像素坐标提取、图片标注和备份等功能。

## 🚀 功能特性

- **实时监控**: 使用 watchdog 实时监控相机上传目录
- **OCR 时间戳提取**: 使用 Tesseract OCR 提取图片中的时间戳信息
- **像素坐标提取**: 自动识别和提取图片中的关键点坐标
- **图片标注**: 在图片上绘制坐标点和编号
- **配置化管理**: 所有路径和参数都可通过配置文件管理
- **多环境支持**: 自动检测Windows/Linux环境，使用对应配置
- **多相机支持**: 同时监控多个相机目录
- **自动备份**: 处理后自动备份原始图片
- **服务化部署**: 支持 systemd 服务管理

## 📋 系统要求

### 硬件要求
- CPU: 4核心以上
- 内存: 8GB 以上
- 存储: 100GB 以上

### 软件要求
- Python 3.8+
- Tesseract OCR 4.0+
- CentOS 7/8 或 Ubuntu 18.04+

## 📁 项目结构

```
camera/
├── RT_Pixel_Ex.py          # 主程序文件
├── Ex_Pixel.py             # 像素坐标提取模块
├── Ex_center_yuan.py       # 圆心检测模块
├── ocr_Ex_time.py          # OCR 时间戳提取模块
├── config_loader.py        # 配置加载模块
├── config.yaml             # 主配置文件
├── requirements.txt        # Python 依赖列表
├── DEPLOYMENT.md          # 详细部署文档
├── README.md              # 项目说明文档
├── deploy.sh              # 一键部署脚本
├── atli_monitor.sh        # 服务管理脚本
├── check_env.py           # 环境检查脚本
└── Outdoor_RTCamProc.toml # 项目元信息
```

## ⚡ 快速开始

### 🪟 Windows 环境测试（推荐先测试）

```powershell
# 1. 初始化Windows测试环境
init_windows_env.bat

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行环境检查
python check_env.py

# 4. 启动测试
python RT_Pixel_Ex.py
```

### 🐧 Linux 服务器部署

#### 1. 一键部署（推荐）

```bash
# 下载项目文件到服务器
# 给部署脚本执行权限
chmod +x deploy.sh

# 以 root 权限运行部署脚本
sudo ./deploy.sh
```

#### 2. 手动部署

详细的手动部署步骤请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)

#### 3. 环境检查

在部署前可以运行环境检查脚本：

```bash
python3 check_env.py
```

## ⚙️ 配置说明

主要配置文件 `config.yaml`:

```yaml
# 路径配置
paths:
  base_upload_path: "/var/ftp/atli_uploads"    # 相机上传目录
  base_processed_path: "/var/ftp/atli_processed" # 处理结果目录

# Tesseract OCR 配置
tesseract:
  cmd_path: "/usr/bin/tesseract"

# OCR 区域配置
ocr:
  timestamp_region:
    x1: 182
    y1: 1893
    x2: 810
    y2: 1962

# 相机配置
cameras:
  camera1:
    polygon_pts:
      - [1099, 1608]
      - [1101, 825]
      - [2925, 835]
      - [2925, 1667]
    enabled: true
  
  camera2:
    # 相机2的配置...
```

## 🛠️ 管理命令

使用 `atli_monitor.sh` 脚本管理服务：

```bash
# 启动服务
sudo /opt/atli_camera_monitor/atli_monitor.sh start

# 停止服务
sudo /opt/atli_camera_monitor/atli_monitor.sh stop

# 重启服务
sudo /opt/atli_camera_monitor/atli_monitor.sh restart

# 查看状态
/opt/atli_camera_monitor/atli_monitor.sh status

# 查看日志
/opt/atli_camera_monitor/atli_monitor.sh logs

# 测试配置
/opt/atli_camera_monitor/atli_monitor.sh test
```

### 📊 监控和日志

## 🚀 部署到服务器后的日志查看指南

系统部署到腾讯云CentOS服务器后，所有日志都会自动记录到系统文件中。以下是详细的日志查看方法：

### 🔍 系统日志（Linux服务器）

#### systemd 服务日志（主要查看方式）
```bash
# 🔥 最重要的命令：查看实时日志（推荐）
sudo journalctl -u atli-camera-monitor -f

# 查看服务状态和最近日志
sudo systemctl status atli-camera-monitor

# 查看最近100行日志
sudo journalctl -u atli-camera-monitor -n 100

# 查看历史日志（按时间过滤）
sudo journalctl -u atli-camera-monitor --since "1 hour ago"
sudo journalctl -u atli-camera-monitor --since "today"
sudo journalctl -u atli-camera-monitor --since "2024-12-02 14:00:00"
sudo journalctl -u atli-camera-monitor --until "2024-12-02 16:00:00"

# 查看详细日志（包含精确时间）
sudo journalctl -u atli-camera-monitor -f --output=short-precise

# 查看错误和警告日志
sudo journalctl -u atli-camera-monitor --priority=warning

# 将日志保存到文件
sudo journalctl -u atli-camera-monitor --since "today" > /tmp/atli_logs_today.log
```

#### 应用程序日志
```bash
# 📂 应用日志文件位置（服务器上的主要日志文件）
/var/log/atli_monitor/atli_camera_monitor.log

# 🔥 查看实时应用日志（最重要的命令）
tail -f /var/log/atli_monitor/atli_camera_monitor.log

# 查看最近的日志
tail -n 100 /var/log/atli_monitor/atli_camera_monitor.log
tail -n 500 /var/log/atli_monitor/atli_camera_monitor.log

# 搜索特定内容（故障排查时非常有用）
grep "ERROR\|WARNING" /var/log/atli_monitor/atli_camera_monitor.log
grep "camera1\|camera2" /var/log/atli_monitor/atli_camera_monitor.log
grep "OCR\|时间戳" /var/log/atli_monitor/atli_camera_monitor.log
grep "像素坐标" /var/log/atli_monitor/atli_camera_monitor.log
grep "处理完成" /var/log/atli_monitor/atli_camera_monitor.log

# 搜索特定时间段的日志
grep "2024-12-02 14:" /var/log/atli_monitor/atli_camera_monitor.log
grep "$(date '+%Y-%m-%d %H')" /var/log/atli_monitor/atli_camera_monitor.log

# 查看文件大小和权限
ls -lh /var/log/atli_monitor/
du -sh /var/log/atli_monitor/

# 将日志复制到临时目录查看
cp /var/log/atli_monitor/atli_camera_monitor.log /tmp/atli_log_backup.log
```

### 📱 Windows 环境日志

#### 程序运行日志
```powershell
# 直接运行程序时的控制台输出
python RT_Pixel_Ex.py

# 重定向输出到文件
python RT_Pixel_Ex.py > logs/runtime.log 2>&1
```

#### 图片传输模拟日志
```powershell
# 运行图片传输模拟器
python sim_Pic_Trans.py

# 日志文件位置：logs/sim_pic_trans_YYYYMMDD_HHMMSS.log
# 例如：logs/sim_pic_trans_20241202_143052.log
```

### 📍 日志位置快速查找表

| 环境 | 日志类型 | 日志位置 | 查看命令 |
|------|----------|----------|----------|
| **Linux服务器** | systemd服务日志 | 系统journal | `sudo journalctl -u atli-camera-monitor -f` |
| **Linux服务器** | 应用程序日志 | `/var/log/atli_monitor/atli_camera_monitor.log` | `tail -f /var/log/atli_monitor/atli_camera_monitor.log` |
| **Windows测试** | 程序运行日志 | `D:\code\camera\logs\atli_monitor_YYYYMMDD_HHMMSS.log` | 直接打开文件查看 |
| **Windows测试** | 图片传输日志 | `D:\code\camera\logs\sim_pic_trans_YYYYMMDD_HHMMSS.log` | 直接打开文件查看 |

### 🗂️ 日志文件结构

#### Linux 服务器日志目录
```
/var/log/atli_monitor/
├── atli_camera_monitor.log         # 主程序日志
├── atli_camera_monitor.log.1       # 轮转日志（昨天）
├── atli_camera_monitor.log.2.gz    # 压缩日志（前天）
└── ...
```

#### Windows 测试环境日志目录
```
D:\code\camera\logs\
├── runtime.log                     # 程序运行日志
├── sim_pic_trans_20241202_143052.log  # 图片传输模拟日志
└── ...
```

### 📋 关键日志内容说明

#### 系统启动日志
```log
2024-12-02 14:30:15,123 - atli_monitor - INFO - 日志系统已启动，日志文件: /var/log/atli_monitor/atli_camera_monitor.log
2024-12-02 14:30:15,124 - atli_monitor - INFO - 系统启动中...
2024-12-02 14:30:15,125 - atli_monitor - INFO - 检测到运行环境: linux
2024-12-02 14:30:15,126 - atli_monitor.camera_monitor - INFO - 初始化相机监控器 - 相机数量: 2
2024-12-02 14:30:15,127 - atli_monitor.camera_monitor - INFO - 监控路径: /var/ftp/atli_uploads
2024-12-02 14:30:15,128 - atli_monitor.camera_monitor - INFO - 处理路径: /var/ftp/atli_processed
2024-12-02 14:30:15,129 - atli_monitor.camera_monitor - INFO - 开始监控相机: camera1 - 路径: /var/ftp/atli_uploads/camera1
2024-12-02 14:30:15,130 - atli_monitor.camera_monitor - INFO - 开始监控相机: camera2 - 路径: /var/ftp/atli_uploads/camera2
```

#### 图片处理详细日志
```log
2024-12-02 14:32:10,456 - atli_monitor.time_folder_handler - INFO - 检测到0001图片: TLS_0202_0001.jpg
2024-12-02 14:32:10,457 - atli_monitor.time_folder_handler - INFO - 等待 2 秒确保文件完全写入...
2024-12-02 14:32:12,458 - atli_monitor.time_folder_handler - INFO - 开始从图片提取时间戳: TLS_0202_0001.jpg
2024-12-02 14:32:12,789 - atli_monitor.time_folder_handler - INFO - 成功提取时间戳: 20241202143200
2024-12-02 14:32:12,790 - atli_monitor.time_folder_handler - INFO - 新图片待处理: TLS_0202_0001.jpg
2024-12-02 14:32:14,791 - atli_monitor.time_folder_handler - INFO - 开始处理图片: TLS_0202_0001.jpg
2024-12-02 14:32:14,792 - atli_monitor.time_folder_handler - INFO - 图片文件信息 - 大小: 2485376 bytes
2024-12-02 14:32:14,793 - atli_monitor.time_folder_handler - INFO - 开始提取像素坐标: TLS_0202_0001.jpg
2024-12-02 14:32:16,234 - atli_monitor.time_folder_handler - INFO - 像素坐标提取成功 - 点数: 12, 耗时: 1.441秒
2024-12-02 14:32:16,235 - atli_monitor.time_folder_handler - INFO - 保存像素坐标文件: /var/ftp/atli_processed/camera1/20241202143200/pixel/TLS_0202_0001.txt - 12个点
2024-12-02 14:32:16,236 - atli_monitor.time_folder_handler - INFO - 像素坐标文件保存完成，耗时: 0.001秒
2024-12-02 14:32:16,237 - atli_monitor.time_folder_handler - INFO - 开始生成标注图片: /var/ftp/atli_processed/camera1/20241202143200/img/TLS_0202_0001.jpg
2024-12-02 14:32:16,678 - atli_monitor.time_folder_handler - INFO - 标注图片生成完成，耗时: 0.441秒
2024-12-02 14:32:16,679 - atli_monitor.time_folder_handler - INFO - 原始图片已删除: /var/ftp/atli_uploads/camera1/TLS_0202/TLS_0202_0001.jpg (2485376 bytes)
2024-12-02 14:32:16,680 - atli_monitor.time_folder_handler - INFO - 图片处理完成: TLS_0202_0001.jpg -> 坐标文件: TLS_0202_0001.txt, 标注图片: TLS_0202_0001.jpg
```

#### 错误和警告日志示例
```log
2024-12-02 14:35:20,123 - atli_monitor.time_folder_handler - WARNING - 时间戳提取失败: TLS_0202_0001.jpg
2024-12-02 14:35:20,124 - atli_monitor.time_folder_handler - WARNING - 像素坐标提取失败: TLS_0202_0002.jpg
2024-12-02 14:35:20,125 - atli_monitor.time_folder_handler - ERROR - 处理图片异常: TLS_0202_0003.jpg - 错误: 图片读取失败
2024-12-02 14:35:20,126 - atli_monitor.time_folder_handler - ERROR - 异常堆栈: Traceback (most recent call last)...
```

#### 性能统计日志
```log
2024-12-02 14:40:15,789 - atli_monitor.time_folder_handler - INFO - 像素坐标提取成功 - 点数: 15, 耗时: 1.234秒
2024-12-02 14:40:15,790 - atli_monitor.time_folder_handler - INFO - 像素坐标文件保存完成，耗时: 0.002秒
2024-12-02 14:40:15,791 - atli_monitor.time_folder_handler - INFO - 标注图片生成完成，耗时: 0.567秒
```

### 🛠️ 日志查看工具

系统提供了便捷的日志查看脚本 `view_logs.sh`，部署后可直接使用：

```bash
# 给脚本执行权限
chmod +x /opt/atli_camera_monitor/view_logs.sh

# 实时查看日志（最常用）
/opt/atli_camera_monitor/view_logs.sh -f

# 查看服务状态
/opt/atli_camera_monitor/view_logs.sh -s

# 查看最近日志
/opt/atli_camera_monitor/view_logs.sh -r

# 查看错误和警告
/opt/atli_camera_monitor/view_logs.sh -e

# 查看指定相机的日志
/opt/atli_camera_monitor/view_logs.sh -c 1    # 查看camera1
/opt/atli_camera_monitor/view_logs.sh -c 2    # 查看camera2

# 查看OCR相关日志
/opt/atli_camera_monitor/view_logs.sh -o

# 查看图片处理日志
/opt/atli_camera_monitor/view_logs.sh -p

# 查看今天的日志
/opt/atli_camera_monitor/view_logs.sh -t

# 查看日志文件大小
/opt/atli_camera_monitor/view_logs.sh --size

# 显示帮助信息
/opt/atli_camera_monitor/view_logs.sh --help
```

### 🛠️ 日志管理命令

#### 清理日志
```bash
# Linux - 清理旧日志
sudo find /var/log/atli_monitor -name "*.log.*" -mtime +7 -delete

# Windows - 清理日志
Remove-Item -Path "logs\*.log" -Force
```

#### 日志大小监控
```bash
# 检查日志文件大小
du -sh /var/log/atli_monitor/
ls -lh /var/log/atli_monitor/
```

#### 实时监控多个日志
```bash
# 同时监控系统日志和应用日志
sudo tail -f /var/log/atli_monitor/atli_camera_monitor.log &
sudo journalctl -u atli-camera-monitor -f
```

### 🚨 故障排除日志

#### 常见错误日志及解决方案

**1. Tesseract 路径错误**
```log
[ERROR] 提取时间戳时发生错误: [Errno 2] No such file or directory: 'tesseract'
```
解决方案：检查配置文件中的 tesseract.cmd_path

**2. 权限错误**
```log
[ERROR] 创建目录失败: /var/ftp/atli_processed/camera1/20241202142000 - Permission denied
```
解决方案：检查目录权限 `sudo chown -R atli_monitor:atli_monitor /var/ftp/`

**3. OCR 失败**
```log
[WARNING] 时间戳提取失败，跳过图片处理
```
解决方案：检查图片质量和 OCR 区域配置

### 📊 日志分析工具

#### 统计处理成功率
```bash
# 统计成功处理的图片数量
grep -c "处理图片完成" /var/log/atli_monitor/atli_camera_monitor.log

# 统计错误数量
grep -c "ERROR" /var/log/atli_monitor/atli_camera_monitor.log
```

#### 性能分析
```bash
# 查看处理时间较长的操作
grep "耗时" /var/log/atli_monitor/atli_camera_monitor.log

# 分析每小时处理量
grep "$(date '+%Y-%m-%d %H')" /var/log/atli_monitor/atli_camera_monitor.log | grep "处理图片" | wc -l
```

## 🔧 故障排除

### 常见问题

1. **Tesseract 路径错误**
   ```bash
   which tesseract
   # 更新 config.yaml 中的 tesseract.cmd_path
   ```

2. **权限问题**
   ```bash
   sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_uploads
   sudo chown -R atli_monitor:atli_monitor /var/ftp/atli_processed
   ```

3. **Python 依赖问题**
   ```bash
   cd /opt/atli_camera_monitor
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 性能优化

- 根据硬件配置调整处理参数
- 定期清理旧的处理文件
- 监控系统资源使用情况
- 配置合适的日志轮转策略

## 📈 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   相机上传      │    │   实时监控      │    │   结果输出      │
│ /var/ftp/       │───▶│  watchdog       │───▶│ /var/ftp/       │
│ atli_uploads/   │    │  监控服务       │    │ atli_processed/ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   处理模块        │
                    │ - OCR 时间戳      │
                    │ - 坐标提取        │
                    │ - 图片标注        │
                    └───────────────────┘
```

## 🌍 多环境配置

系统支持自动环境检测，根据操作系统选择相应配置：

### 环境自动识别
- **Windows**: 自动使用 `D:\pic_back\` 路径进行测试
- **Linux**: 自动使用 `/var/ftp/` 路径进行生产

### 配置文件结构
```yaml
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

### 环境切换
```python
from config_loader import load_config

# 自动检测环境（推荐）
config = load_config()

# 手动指定环境
config = load_config(env='windows')  # 强制Windows
config = load_config(env='linux')    # 强制Linux
```

## 🔒 安全注意事项

- 使用专用用户运行服务
- 限制文件访问权限
- 定期更新系统和依赖包
- 配置防火墙规则
- 实施数据备份策略

## 📝 开发说明

### 添加新相机

1. 在 `config.yaml` 中添加相机配置
2. 创建对应的上传目录
3. 重启服务

### 自定义处理逻辑

主要的处理逻辑在以下模块中：
- `RT_Pixel_Ex.py`: 主程序和文件监控
- `Ex_Pixel.py`: 像素坐标提取
- `ocr_Ex_time.py`: OCR 时间戳处理

## 📞 技术支持

- 作者: Gong Wei
- 邮箱: 2985045154@qq.com
- 项目: Outdoor_RTCamProc v1.0.0

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🔄 版本历史

- v1.0.0: 初始版本，支持双相机监控和处理
- 配置文件化管理
- 服务化部署
- 完整的部署和管理工具

---

*感谢使用 ATLI 相机实时处理系统！*
