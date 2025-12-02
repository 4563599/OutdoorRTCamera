#!/bin/bash
# ATLI 相机监控系统 - 日志查看工具脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称和日志文件路径
SERVICE_NAME="atli-camera-monitor"
LOG_FILE="/var/log/atli_monitor/atli_camera_monitor.log"

show_help() {
    echo -e "${BLUE}ATLI 相机监控系统 - 日志查看工具${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --follow      实时跟踪日志 (推荐)"
    echo "  -s, --status      查看服务状态"
    echo "  -r, --recent      查看最近日志 (最近100行)"
    echo "  -e, --errors      查看错误和警告日志"
    echo "  -t, --today       查看今天的日志"
    echo "  -h, --hour        查看最近1小时的日志"
    echo "  -c, --camera N    查看指定相机的日志 (N=1或2)"
    echo "  -o, --ocr         查看OCR相关日志"
    echo "  -p, --process     查看图片处理日志"
    echo "  --size            查看日志文件大小"
    echo "  --help            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -f             实时查看所有日志"
    echo "  $0 -e             查看所有错误和警告"
    echo "  $0 -c 1           查看camera1相关日志"
    echo "  $0 -t             查看今天的所有日志"
}

# 检查服务状态
check_service_status() {
    echo -e "${BLUE}=== 服务状态 ===${NC}"
    systemctl status $SERVICE_NAME --no-pager
    echo ""
}

# 查看实时日志
show_live_logs() {
    echo -e "${GREEN}实时跟踪日志 (按 Ctrl+C 退出)${NC}"
    echo -e "${YELLOW}同时显示 systemd 日志和应用程序日志${NC}"
    echo ""

    # 优先显示应用程序日志，如果不存在则显示systemd日志
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}应用程序日志文件不存在，显示 systemd 日志:${NC}"
        journalctl -u $SERVICE_NAME -f
    fi
}

# 查看最近日志
show_recent_logs() {
    local lines=${1:-100}
    echo -e "${BLUE}=== 最近 $lines 行日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        tail -n $lines "$LOG_FILE"
    else
        echo -e "${YELLOW}应用程序日志文件不存在，显示 systemd 日志:${NC}"
        journalctl -u $SERVICE_NAME -n $lines --no-pager
    fi
}

# 查看错误日志
show_error_logs() {
    echo -e "${RED}=== 错误和警告日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        grep -E "(ERROR|WARNING|WARN)" "$LOG_FILE" | tail -20
        echo ""
        echo -e "${YELLOW}systemd 错误日志:${NC}"
        journalctl -u $SERVICE_NAME --priority=warning -n 10 --no-pager
    else
        journalctl -u $SERVICE_NAME --priority=warning --no-pager
    fi
}

# 查看今天的日志
show_today_logs() {
    echo -e "${BLUE}=== 今天的日志 ===${NC}"
    local today=$(date '+%Y-%m-%d')

    if [[ -f "$LOG_FILE" ]]; then
        grep "$today" "$LOG_FILE"
    else
        journalctl -u $SERVICE_NAME --since "today" --no-pager
    fi
}

# 查看最近1小时的日志
show_hour_logs() {
    echo -e "${BLUE}=== 最近1小时的日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        # 获取1小时前的时间戳
        hour_ago=$(date -d '1 hour ago' '+%Y-%m-%d %H:')
        current_hour=$(date '+%Y-%m-%d %H:')
        grep -E "($hour_ago|$current_hour)" "$LOG_FILE"
    else
        journalctl -u $SERVICE_NAME --since "1 hour ago" --no-pager
    fi
}

# 查看指定相机的日志
show_camera_logs() {
    local camera_num=$1
    echo -e "${BLUE}=== Camera$camera_num 相关日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        grep "camera$camera_num" "$LOG_FILE" | tail -20
    else
        journalctl -u $SERVICE_NAME --no-pager | grep "camera$camera_num" | tail -20
    fi
}

# 查看OCR相关日志
show_ocr_logs() {
    echo -e "${BLUE}=== OCR 相关日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        grep -E "(OCR|时间戳|timestamp)" "$LOG_FILE" | tail -20
    else
        journalctl -u $SERVICE_NAME --no-pager | grep -E "(OCR|时间戳)" | tail -20
    fi
}

# 查看图片处理日志
show_process_logs() {
    echo -e "${BLUE}=== 图片处理日志 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        grep -E "(处理图片|像素坐标|处理完成)" "$LOG_FILE" | tail -20
    else
        journalctl -u $SERVICE_NAME --no-pager | grep -E "(处理图片|像素坐标)" | tail -20
    fi
}

# 查看日志文件大小
show_log_size() {
    echo -e "${BLUE}=== 日志文件信息 ===${NC}"

    if [[ -f "$LOG_FILE" ]]; then
        ls -lh "$LOG_FILE"
        echo ""
        du -sh /var/log/atli_monitor/
    else
        echo -e "${YELLOW}应用程序日志文件不存在: $LOG_FILE${NC}"
    fi

    echo ""
    echo -e "${BLUE}systemd 日志大小:${NC}"
    journalctl -u $SERVICE_NAME --disk-usage
}

# 主程序
main() {
    case "$1" in
        -f|--follow)
            show_live_logs
            ;;
        -s|--status)
            check_service_status
            ;;
        -r|--recent)
            show_recent_logs ${2:-100}
            ;;
        -e|--errors)
            show_error_logs
            ;;
        -t|--today)
            show_today_logs
            ;;
        -h|--hour)
            show_hour_logs
            ;;
        -c|--camera)
            if [[ -n "$2" && "$2" =~ ^[12]$ ]]; then
                show_camera_logs "$2"
            else
                echo -e "${RED}错误: 请指定相机编号 1 或 2${NC}"
                echo "例如: $0 -c 1"
                exit 1
            fi
            ;;
        -o|--ocr)
            show_ocr_logs
            ;;
        -p|--process)
            show_process_logs
            ;;
        --size)
            show_log_size
            ;;
        --help|"")
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
