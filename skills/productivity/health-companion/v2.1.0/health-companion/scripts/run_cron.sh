#!/bin/bash
# 健康关怀助手 - Cronjob 统一入口
# 根据当前时间自动判断应该执行的操作（允许 5 分钟内延迟）

SCRIPT_DIR="/root/.hermes/skills/productivity/health-companion/scripts"
PYTHON_SCRIPT="${SCRIPT_DIR}/generate_quote.py"
TEMP_DIR="/tmp"
DATE_STR=$(date +%Y%m%d)
USED_FILE="${TEMP_DIR}/health_companion_used_${DATE_STR}.txt"
MARKER_DIR="${TEMP_DIR}/health_companion_markers"

# 获取当前时间和日期信息
CURRENT_HOUR=$(date +%H)
CURRENT_MIN=$(date +%M)
WEEKDAY=$(date +%u)  # 1 (周一) - 7 (周日)

# 转换为分钟数（从 00:00 开始）- 去除前导零
CURRENT_HOUR_NUM=$((10#$CURRENT_HOUR))
CURRENT_MIN_NUM=$((10#$CURRENT_MIN))
CURRENT_TOTAL_MIN=$((CURRENT_HOUR_NUM * 60 + CURRENT_MIN_NUM))

# 创建标记目录（用于记录已执行的时间点）
mkdir -p "$MARKER_DIR"

# 只在工作日 (1-5) 运行
if [ "$WEEKDAY" -gt 5 ]; then
    echo "周末不运行"
    exit 0
fi

# 检查时间是否在目标时间的 5 分钟窗口内
# 参数：目标分钟数（从 00:00 开始计算）
check_time_window() {
    local target_min=$1
    local window=5  # 5 分钟窗口
    
    local diff=$((CURRENT_TOTAL_MIN - target_min))
    
    # 在 0-5 分钟范围内（允许延迟 5 分钟）
    if [ $diff -ge 0 ] && [ $diff -le $window ]; then
        return 0
    fi
    return 1
}

# 检查并设置标记（防止同一时间段重复执行）
check_and_set_marker() {
    local marker_name=$1
    local marker_file="${MARKER_DIR}/${DATE_STR}_${marker_name}"
    
    if [ -f "$marker_file" ]; then
        # 标记已存在，不重复执行
        return 1
    fi
    
    # 设置标记（使用 echo 而不是 touch 避免某些系统的权限问题）
    echo "" > "$marker_file"
    return 0
}

# 主逻辑
SCENE=""
ACTION=""

# 检查各个时间点
if check_time_window 570 && check_and_set_marker "kaigong"; then
    # 09:30 开工
    SCENE="kaigong"
    ACTION="create_temp"
    
elif check_time_window 1110 && check_and_set_marker "xiaban"; then
    # 18:30 下班
    SCENE="xiaban"
    ACTION="delete_temp"
    
elif check_time_window 750 && check_and_set_marker "xiuxi"; then
    # 12:30 午休
    SCENE="xiuxi"
    ACTION="generate"
    
elif [ $CURRENT_HOUR -ge 10 ] && [ $CURRENT_HOUR -le 18 ]; then
    # 健康关怀时间段 (10:00-18:00)
    HEALTH_MARKER="health_${CURRENT_HOUR}_${CURRENT_MIN}"
    if check_and_set_marker "$HEALTH_MARKER"; then
        SCENE="jiankang"
        ACTION="generate"
    fi
fi

# 执行操作
if [ -n "$SCENE" ]; then
    echo "=== ${SCENE} 关怀 ==="
    
    if [ "$ACTION" = "create_temp" ]; then
        python3 "${PYTHON_SCRIPT}" "${SCENE}" create_temp
        python3 "${PYTHON_SCRIPT}" "${SCENE}" generate
    elif [ "$ACTION" = "delete_temp" ]; then
        python3 "${PYTHON_SCRIPT}" "${SCENE}" generate
        python3 "${PYTHON_SCRIPT}" "${SCENE}" delete_temp
    else
        python3 "${PYTHON_SCRIPT}" "${SCENE}" generate
    fi
else
    echo "非运行时间或已执行"
    exit 0
fi
