#!/bin/bash
# ATLI 相机监控系统一键部署脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="atli_camera_monitor"
PROJECT_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="atli-camera-monitor"
USER_NAME="atli_monitor"

# 显示横幅
show_banner() {
    echo -e "${BLUE}"
    echo "======================================================"
    echo "    ATLI 相机实时处理系统 - 一键部署脚本"
    echo "    版本: 1.0.0"
    echo "    作者: Gong Wei <2985045154@qq.com>"
    echo "======================================================"
    echo -e "${NC}"
}

# 显示进度
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查并创建目录的辅助函数
create_dir_if_not_exists() {
    local dir_path="$1"
    local description="$2"

    if [[ ! -d "$dir_path" ]]; then
        mkdir -p "$dir_path"
        log_success "创建${description}: $dir_path"
        return 0
    else
        log_warning "${description}已存在: $dir_path"
        return 1
    fi
}

# 检查目录权限的辅助函数
check_dir_permissions() {
    local dir_path="$1"
    local description="$2"

    if [[ -d "$dir_path" ]]; then
        if [[ -w "$dir_path" ]]; then
            log_info "${description}权限正常: $dir_path"
            return 0
        else
            log_warning "${description}无写权限: $dir_path"
            return 1
        fi
    else
        log_warning "${description}不存在: $dir_path"
        return 1
    fi
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        log_info "检测到 CentOS/RHEL 系统"
    elif [[ -f /etc/debian_version ]]; then
        OS="ubuntu"
        log_info "检测到 Ubuntu/Debian 系统"
    else
        log_error "不支持的操作系统"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖包..."

    if [[ "$OS" == "centos" ]]; then
        yum update -y
        yum groupinstall -y "Development Tools"
        yum install -y python38 python38-pip python38-devel
        yum install -y opencv opencv-devel
        yum install -y epel-release
        yum install -y tesseract tesseract-langpack-eng tesseract-langpack-chi-sim
    elif [[ "$OS" == "ubuntu" ]]; then
        apt update && apt upgrade -y
        apt install -y build-essential
        apt install -y python3.8 python3.8-pip python3.8-dev python3.8-venv
        apt install -y libopencv-dev python3-opencv
        apt install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim
        apt install -y libtesseract-dev
    fi

    log_success "系统依赖安装完成"
}

# 创建用户和目录
setup_user_and_dirs() {
    log_info "创建用户和目录结构..."

    # 创建用户
    if ! id "$USER_NAME" &>/dev/null; then
        useradd -m -s /bin/bash "$USER_NAME"
        log_success "创建用户: $USER_NAME"
    else
        log_warning "用户 $USER_NAME 已存在"
    fi

    # 创建必要的目录结构
    log_info "检查并创建目录结构..."

    # 创建项目目录
    create_dir_if_not_exists "$PROJECT_DIR" "项目目录"

    # 创建FTP上传根目录
    create_dir_if_not_exists "/var/ftp/atli_uploads" "上传根目录"

    # 创建相机目录
    for camera in camera1 camera2; do
        create_dir_if_not_exists "/var/ftp/atli_uploads/$camera" "相机${camera}目录"
    done

    # 创建处理结果目录
    create_dir_if_not_exists "/var/ftp/atli_processed" "处理结果目录"

    # 创建日志目录
    create_dir_if_not_exists "/var/log/atli_monitor" "日志目录"

    # 检查目录权限
    log_info "检查目录权限..."
    directories=(
        "$PROJECT_DIR:项目目录"
        "/var/ftp/atli_uploads:上传根目录"
        "/var/ftp/atli_uploads/camera1:相机1目录"
        "/var/ftp/atli_uploads/camera2:相机2目录"
        "/var/ftp/atli_processed:处理结果目录"
        "/var/log/atli_monitor:日志目录"
    )

    # 设置权限（无论目录是否新创建都需要设置权限）
    log_info "设置目录权限..."
    for dir_info in "${directories[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"

        if [[ -d "$dir_path" ]]; then
            chown -R "$USER_NAME:$USER_NAME" "$dir_path"
            chmod -R 755 "$dir_path"
            log_info "设置${dir_desc}权限: $dir_path"
        else
            log_warning "${dir_desc}不存在，跳过权限设置: $dir_path"
        fi
    done

    # 验证目录权限
    log_info "验证目录权限..."
    for dir_info in "${directories[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"
        check_dir_permissions "$dir_path" "$dir_desc"
    done

    log_success "用户和目录设置完成"
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."

    local current_dir=$(dirname "$0")

    # 复制 Python 文件
    cp "$current_dir"/*.py "$PROJECT_DIR/"
    cp "$current_dir"/config.yaml "$PROJECT_DIR/"
    cp "$current_dir"/requirements.txt "$PROJECT_DIR/"
    cp "$current_dir"/atli_monitor.sh "$PROJECT_DIR/"

    chmod +x "$PROJECT_DIR/atli_monitor.sh"
    chown -R "$USER_NAME:$USER_NAME" "$PROJECT_DIR"

    log_success "项目文件复制完成"
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."

    cd "$PROJECT_DIR"

    # 创建虚拟环境
    sudo -u "$USER_NAME" python3.8 -m venv venv

    # 安装依赖
    sudo -u "$USER_NAME" bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

    log_success "Python 依赖安装完成"
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."

    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=ATLI Camera Monitor Service
After=network.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python RT_Pixel_Ex.py
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# 资源限制
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载 systemd 并启用服务
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME

    log_success "系统服务创建完成"
}

# 配置日志轮转
setup_log_rotation() {
    log_info "配置日志轮转..."

    cat > /etc/logrotate.d/$SERVICE_NAME << EOF
/var/log/atli_monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER_NAME $USER_NAME
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

    log_success "日志轮转配置完成"
}

# 验证安装
verify_installation() {
    log_info "验证安装..."

    # 检查 Tesseract
    if command -v tesseract >/dev/null 2>&1; then
        log_success "Tesseract 安装正常: $(tesseract --version | head -n1)"
    else
        log_error "Tesseract 未正确安装"
        return 1
    fi

    # 检查 Python 环境
    if sudo -u "$USER_NAME" bash -c "cd $PROJECT_DIR && source venv/bin/activate && python config_loader.py" >/dev/null 2>&1; then
        log_success "Python 环境和配置文件正常"
    else
        log_error "Python 环境或配置文件有问题"
        return 1
    fi

    # 检查服务状态
    if systemctl is-enabled $SERVICE_NAME >/dev/null 2>&1; then
        log_success "系统服务已启用"
    else
        log_error "系统服务未正确启用"
        return 1
    fi

    # 验证关键目录存在且有正确权限
    log_info "验证关键目录..."
    critical_dirs=(
        "/var/ftp/atli_uploads/camera1"
        "/var/ftp/atli_uploads/camera2"
        "/var/ftp/atli_processed"
        "$PROJECT_DIR"
    )

    for dir_path in "${critical_dirs[@]}"; do
        if [[ -d "$dir_path" ]] && [[ -w "$dir_path" ]]; then
            log_success "目录验证通过: $dir_path"
        else
            log_error "目录验证失败: $dir_path (不存在或无写权限)"
            return 1
        fi
    done

    log_success "安装验证通过"
}

# 显示部署完成信息
show_completion_info() {
    echo -e "${GREEN}"
    echo "======================================================"
    echo "             部署完成！"
    echo "======================================================"
    echo -e "${NC}"

    echo "📁 项目目录: $PROJECT_DIR"
    echo "👤 运行用户: $USER_NAME"
    echo "🔧 服务名称: $SERVICE_NAME"
    echo ""
    echo "🚀 启动服务: sudo systemctl start $SERVICE_NAME"
    echo "🔍 查看状态: sudo systemctl status $SERVICE_NAME"
    echo "📋 查看日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "🛠️  管理工具: $PROJECT_DIR/atli_monitor.sh"
    echo ""
    echo "📂 监控目录:"
    echo "   - /var/ftp/atli_uploads/camera1"
    echo "   - /var/ftp/atli_uploads/camera2"
    echo "📤 输出目录: /var/ftp/atli_processed"
    echo ""
    echo -e "${YELLOW}注意事项:${NC}"
    echo "1. 请确保 /var/ftp/atli_uploads 目录下有相机上传的图片"
    echo "2. 如需修改配置，请编辑 $PROJECT_DIR/config.yaml"
    echo "3. 修改配置后需要重启服务: sudo systemctl restart $SERVICE_NAME"
}

# 主函数
main() {
    show_banner

    check_root
    detect_os

    log_info "开始部署 ATLI 相机监控系统..."

    # 检查现有目录状态
    log_info "检查现有目录状态..."
    check_dirs=(
        "/var/ftp/atli_uploads:FTP上传根目录"
        "/var/ftp/atli_uploads/camera1:相机1目录"
        "/var/ftp/atli_uploads/camera2:相机2目录"
        "/var/ftp/atli_processed:处理结果目录"
        "$PROJECT_DIR:项目目录"
        "/var/log/atli_monitor:日志目录"
    )

    for dir_info in "${check_dirs[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"

        if [[ -d "$dir_path" ]]; then
            log_info "${dir_desc}已存在: $dir_path"
        else
            log_info "${dir_desc}将被创建: $dir_path"
        fi
    done

    install_system_deps
    setup_user_and_dirs
    copy_project_files
    install_python_deps
    create_systemd_service
    setup_log_rotation

    if verify_installation; then
        show_completion_info

        # 询问是否立即启动服务
        echo ""
        read -p "是否现在启动服务? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            systemctl start $SERVICE_NAME
            sleep 2
            systemctl status $SERVICE_NAME --no-pager
        fi

        log_success "部署完成！"
    else
        log_error "部署验证失败，请检查错误信息"
        exit 1
    fi
}

# 运行主函数
main "$@"
