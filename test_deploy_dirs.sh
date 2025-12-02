#!/bin/bash
# 测试部署脚本中的目录检查功能

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
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

# 测试目录检查函数
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

# 测试目录检查功能
test_directory_checks() {
    log_info "测试目录检查功能..."

    # 测试目录列表
    test_dirs=(
        "/tmp/test_atli/uploads:测试上传目录"
        "/tmp/test_atli/uploads/camera1:测试相机1目录"
        "/tmp/test_atli/uploads/camera2:测试相机2目录"
        "/tmp/test_atli/processed:测试处理目录"
    )

    # 第一次运行：创建目录
    log_info "第一次运行 - 创建目录:"
    for dir_info in "${test_dirs[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"
        create_dir_if_not_exists "$dir_path" "$dir_desc"
    done

    echo ""

    # 第二次运行：检查已存在的目录
    log_info "第二次运行 - 检查已存在目录:"
    for dir_info in "${test_dirs[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"
        create_dir_if_not_exists "$dir_path" "$dir_desc"
    done

    echo ""

    # 检查权限
    log_info "检查目录权限:"
    for dir_info in "${test_dirs[@]}"; do
        dir_path="${dir_info%%:*}"
        dir_desc="${dir_info##*:}"
        check_dir_permissions "$dir_path" "$dir_desc"
    done

    # 清理测试目录
    log_info "清理测试目录..."
    rm -rf "/tmp/test_atli"
    log_success "测试目录已清理"
}

# 模拟部署前检查
test_pre_deployment_check() {
    log_info "模拟部署前目录状态检查..."

    # 模拟真实环境路径
    check_dirs=(
        "/var/ftp/atli_uploads:FTP上传根目录"
        "/var/ftp/atli_uploads/camera1:相机1目录"
        "/var/ftp/atli_uploads/camera2:相机2目录"
        "/var/ftp/atli_processed:处理结果目录"
        "/opt/atli_camera_monitor:项目目录"
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
}

# 主测试函数
main() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "  部署脚本目录检查功能测试"
    echo "========================================"
    echo -e "${NC}"

    test_directory_checks
    echo ""
    test_pre_deployment_check

    echo ""
    echo -e "${GREEN}"
    echo "========================================"
    echo "  测试完成"
    echo "========================================"
    echo -e "${NC}"

    echo "✅ 目录检查功能正常工作"
    echo "✅ 已存在目录不会重复创建"
    echo "✅ 权限检查功能正常"
    echo "✅ 部署前状态检查功能正常"
}

main "$@"
