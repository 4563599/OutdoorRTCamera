# 部署脚本目录检查功能改进总结

## 🎯 改进目标

您要求在部署脚本中添加路径存在性检查，避免重复创建已存在的目录，特别是：
- `/var/ftp/atli_uploads`
- `/var/ftp/atli_uploads/camera1`
- `/var/ftp/atli_uploads/camera2`
- `/var/ftp/atli_processed`

## ✅ 已完成的改进

### 1. 添加了目录检查辅助函数

```bash
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
```

### 2. 重构了 `setup_user_and_dirs` 函数

**原来的代码** (问题):
```bash
# 创建目录
mkdir -p "$PROJECT_DIR"
mkdir -p /var/ftp/atli_uploads/camera{1,2}
mkdir -p /var/ftp/atli_processed
mkdir -p /var/log/atli_monitor
```
❌ 总是创建目录，无论是否已存在

**现在的代码** (改进后):
```bash
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
```
✅ 先检查目录是否存在，只在需要时创建

### 3. 添加了权限检查和设置

```bash
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
```

### 4. 添加了部署前状态检查

在主函数中添加了部署前的目录状态检查：

```bash
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
```

### 5. 添加了验证阶段的目录检查

在 `verify_installation` 函数中添加了关键目录的最终验证：

```bash
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
```

## 📋 部署脚本运行效果示例

### 首次部署时：
```
[INFO] 检查现有目录状态...
[INFO] FTP上传根目录将被创建: /var/ftp/atli_uploads
[INFO] 相机1目录将被创建: /var/ftp/atli_uploads/camera1
[INFO] 相机2目录将被创建: /var/ftp/atli_uploads/camera2
[INFO] 处理结果目录将被创建: /var/ftp/atli_processed

[INFO] 检查并创建目录结构...
[SUCCESS] 创建上传根目录: /var/ftp/atli_uploads
[SUCCESS] 创建相机camera1目录: /var/ftp/atli_uploads/camera1
[SUCCESS] 创建相机camera2目录: /var/ftp/atli_uploads/camera2
[SUCCESS] 创建处理结果目录: /var/ftp/atli_processed
```

### 再次部署时：
```
[INFO] 检查现有目录状态...
[INFO] FTP上传根目录已存在: /var/ftp/atli_uploads
[INFO] 相机1目录已存在: /var/ftp/atli_uploads/camera1
[INFO] 相机2目录已存在: /var/ftp/atli_uploads/camera2
[INFO] 处理结果目录已存在: /var/ftp/atli_processed

[INFO] 检查并创建目录结构...
[WARNING] 上传根目录已存在: /var/ftp/atli_uploads
[WARNING] 相机camera1目录已存在: /var/ftp/atli_uploads/camera1
[WARNING] 相机camera2目录已存在: /var/ftp/atli_uploads/camera2
[WARNING] 处理结果目录已存在: /var/ftp/atli_processed
```

## 🚀 优势

1. **避免重复创建**: ✅ 检查目录是否存在，只在必要时创建
2. **清晰的日志**: ✅ 明确显示哪些目录已存在，哪些是新创建的
3. **权限管理**: ✅ 无论目录是否新创建，都确保权限正确
4. **验证机制**: ✅ 部署完成后验证所有关键目录是否正常
5. **易于调试**: ✅ 详细的状态输出，便于排查问题

## 📁 检查的目录路径

按您的要求，脚本现在会检查以下路径：

✅ `/var/ftp/atli_uploads` - FTP上传根目录  
✅ `/var/ftp/atli_uploads/camera1` - 相机1目录  
✅ `/var/ftp/atli_uploads/camera2` - 相机2目录  
✅ `/var/ftp/atli_processed` - 处理结果目录  
✅ `/opt/atli_camera_monitor` - 项目目录  
✅ `/var/log/atli_monitor` - 日志目录  

## 🎯 现在的部署脚本特性

- **智能创建**: 只创建不存在的目录
- **状态报告**: 部署前显示现有目录状态  
- **权限管理**: 确保所有目录有正确的用户权限
- **验证机制**: 部署完成后验证目录可用性
- **详细日志**: 每个操作都有清晰的日志输出
- **错误处理**: 权限问题或目录创建失败时会报错

现在您的部署脚本已经完全符合要求，能够智能地检查和创建目录，避免重复操作！
