#!/usr/bin/env python3
"""
健康关怀助手 - 台词生成脚本
根据场景生成关怀消息，管理临时文件避免重复
"""

import os
import re
import random
import sys
from datetime import datetime

# 台词目录
DATA_DIR = "/root/data"
TEMP_DIR = "/tmp"

# 场景分类映射
SCENE_CATEGORIES = {
    "kaigong": "励志/正能量",
    "jiankang": "幽默/喜剧",
    "wucan": "温暖/关怀",
    "xiuxi": "温暖/关怀",
    "xiaban": "悲伤/感伤"
}

# 关怀模板
CARE_TEMPLATES = {
    "kaigong": "今天是{weekday}，再难搞的需求也怕有心人。先把咖啡倒上，咱们一件一件来！",
    "jiankang": "别硬撑了，你的腰椎不是铁打的。起来走两步，接杯水，远眺 5 分钟！",
    "wucan": "上午辛苦了，中午好好休息 15 分钟，让大脑也放个假。",
    "xiuxi": "上午辛苦了，中午好好休息 15 分钟，让大脑也放个假。",
    "xiaban": "今天又过去了，不管有没有摸鱼，至少你活下来了！回家好好休息，明天继续！"
}

# 表情符号
EMOJIS = {
    "kaigong": "💪☕",
    "jiankang": "🚶💦",
    "wucan": "😴⚡",
    "xiuxi": "😴⚡",
    "xiaban": "🎉🏠"
}

def get_temp_file_path():
    """获取临时文件路径"""
    today = datetime.now().strftime("%Y%m%d")
    return f"{TEMP_DIR}/health_companion_used_{today}.txt"

def read_used_quotes(temp_file):
    """读取已使用的台词"""
    if os.path.exists(temp_file):
        with open(temp_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def write_used_quotes(temp_file, quote):
    """写入已使用的台词"""
    with open(temp_file, 'a', encoding='utf-8') as f:
        f.write(quote + '\n')

def create_temp_file(temp_file):
    """创建临时文件"""
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("")
    print(f"临时文件已创建：{temp_file}")

def delete_temp_file(temp_file):
    """删除临时文件"""
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"临时文件已删除：{temp_file}")

def parse_quotes_from_file(filepath):
    """从 Markdown 文件中解析台词"""
    quotes = {}
    current_category = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按行解析
    lines = content.split('\n')
    for line in lines:
        # 匹配分类标题 ### 分类名
        match = re.match(r'^###\s+(.+)$', line.strip())
        if match:
            current_category = match.group(1).strip()
            if current_category not in quotes:
                quotes[current_category] = []
            continue
        
        # 匹配台词 > 台词内容
        if current_category and line.strip().startswith('>'):
            quote_text = line.strip()[1:].strip()
            # 跳过空行和注释
            if quote_text and not quote_text.startswith('—') and not quote_text.startswith('1997'):
                # 移除开头的数字编号（如 "1. "）
                quote_text = re.sub(r'^\d+\.\s*', '', quote_text)
                if quote_text:
                    quotes[current_category].append(quote_text)
    
    return quotes

def read_all_quotes():
    """从 /root/data/ 目录读取所有台词"""
    all_quotes = {}
    
    if not os.path.exists(DATA_DIR):
        print(f"警告：目录 {DATA_DIR} 不存在")
        return all_quotes
    
    # 读取所有 .md 文件
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(DATA_DIR, filename)
            file_quotes = parse_quotes_from_file(filepath)
            
            # 合并台词
            for category, quotes in file_quotes.items():
                if category not in all_quotes:
                    all_quotes[category] = []
                all_quotes[category].extend(quotes)
    
    return all_quotes

def select_quote(category, used_quotes, all_quotes):
    """从指定分类中选择一个未使用的台词"""
    available = []
    
    if category in all_quotes:
        for quote in all_quotes[category]:
            if quote not in used_quotes:
                available.append(quote)
    
    if available:
        return random.choice(available)
    
    # 如果没有可用台词，返回 None
    return None

def generate_care_message(scene, quote):
    """生成关怀消息"""
    weekday_map = {
        0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"
    }
    weekday = weekday_map.get(datetime.now().weekday(), "今天")
    
    # 获取关怀模板
    template = CARE_TEMPLATES.get(scene, "注意休息，保持好心情！")
    
    # 替换模板变量
    care_text = template.format(weekday=weekday)
    
    # 获取表情符号
    emoji = EMOJIS.get(scene, "😊")
    
    # 生成输出
    output = []
    output.append(f'【电影台词】"{quote}" ——《甲方乙方》')
    output.append(f'【关怀提醒】{care_text}')
    output.append(f'【表情符号】{emoji}')
    
    return '\n'.join(output)

def main():
    if len(sys.argv) < 2:
        print("用法：python3 generate_quote.py <scene> [action]")
        print("场景：kaigong, jiankang, wucan, xiuxi, xiaban")
        print("动作：create_temp (可选，创建临时文件)")
        sys.exit(1)
    
    scene = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 验证场景
    if scene not in SCENE_CATEGORIES:
        print(f"错误：未知场景 '{scene}'")
        print(f"可用场景：{', '.join(SCENE_CATEGORIES.keys())}")
        sys.exit(1)
    
    temp_file = get_temp_file_path()
    
    # 处理创建临时文件
    if action == "create_temp":
        create_temp_file(temp_file)
        return
    
    # 处理删除临时文件
    if action == "delete_temp":
        delete_temp_file(temp_file)
        return
    
    # 读取已用台词
    used_quotes = read_used_quotes(temp_file)
    
    # 读取所有台词
    all_quotes = read_all_quotes()
    
    if not all_quotes:
        print("错误：未找到任何台词文件")
        sys.exit(1)
    
    # 获取当前场景的分类
    category = SCENE_CATEGORIES[scene]
    
    # 选择台词
    quote = select_quote(category, used_quotes, all_quotes)
    
    if quote is None:
        # 如果没有可用台词，尝试使用任意分类
        for cat in all_quotes.keys():
            quote = select_quote(cat, used_quotes, all_quotes)
            if quote:
                break
    
    if quote is None:
        print("错误：没有可用台词")
        sys.exit(1)
    
    # 写入已用台词
    write_used_quotes(temp_file, quote)
    
    # 生成并输出关怀消息
    message = generate_care_message(scene, quote)
    print(message)

if __name__ == "__main__":
    main()
