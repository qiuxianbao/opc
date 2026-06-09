#!/usr/bin/env python3
"""
经典台词下载工具
用于从网络搜索并整理电影/文学作品的经典台词，保存到指定目录
支持情感分类：励志/鼓舞、爱情/温情、幽默/讽刺、哲理/感悟、经典/脍炙人口
"""

import os
import re
import json
from datetime import datetime

# 情感分类体系
EMOTION_CATEGORIES = {
    '励志/鼓舞': '积极向上、激励人心的台词（适合开工提醒、鼓舞士气）',
    '爱情/温情': '表达爱意、亲情、友情的台词（适合情感类内容）',
    '幽默/讽刺': '搞笑、讽刺、黑色幽默的台词（适合轻松场景、缓解压力）',
    '哲理/感悟': '蕴含人生哲理、深度思考的台词（适合深度对话、反思时刻）',
    '经典/脍炙人口': '广为流传、最具代表性的台词（通用场景）'
}

DEFAULT_CATEGORIES = list(EMOTION_CATEGORIES.keys())


def sanitize_filename(name):
    """清理文件名，去除特殊字符"""
    # 去除书名号、引号等
    name = re.sub(r'[《》""\'\'\./\\:*?\"<>|]', '', name)
    # 替换空格为下划线
    name = name.replace(' ', '_')
    return name


def format_quotes_content(title, author, work_info, quotes_by_category, source=""):
    """
    格式化台词内容（支持情感分类）
    
    Args:
        title: 作品标题
        author: 作者/导演
        work_info: 作品信息字典（主演、年份、类型等）
        quotes_by_category: 按情感分类的台词典，格式为 {'分类名': ['台词 1', '台词 2', ...]}
        source: 来源说明
    
    Returns:
        str: 格式化后的 Markdown 内容
    """
    content = f"""# 《{title}》经典台词

**作品信息：**
- 作者/导演：{author}
"""
    
    # 添加其他信息
    for key, value in work_info.items():
        if value:
            content += f"- {key}: {value}\n"
    
    content += "\n---\n\n## 经典台词（按情感分类）\n"
    
    # 按情感分类输出台词
    for category in DEFAULT_CATEGORIES:
        quotes = quotes_by_category.get(category, [])
        if quotes:  # 只输出有台词的分类
            content += f"\n### {category}\n"
            for quote in quotes:
                if isinstance(quote, dict):
                    # 如果有角色/场景信息
                    text = quote.get('content', '')
                    speaker = quote.get('speaker', '')
                    if speaker:
                        content += f'> "{text}"\n> —— {speaker}\n\n'
                    else:
                        content += f'> "{text}"\n\n'
                else:
                    # 简单字符串格式
                    content += f'> "{quote}"\n\n'
    
    # 添加备注
    content += "\n---\n\n"
    content += f"**备注：** 以上台词整理自 {source if source else '网络公开资料'}，部分可能因版本不同略有差异。\n"
    content += f"**整理时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"**情感分类说明：** 按{len(DEFAULT_CATEGORIES)}类整理，便于定时任务按需引用\n"
    
    return content


def save_quotes_file(author, title, content, base_dir="/root/data"):
    """
    保存台词文件
    
    Args:
        author: 作者名
        title: 作品名
        content: 文件内容
        base_dir: 基础目录
    
    Returns:
        str: 保存的文件路径
    """
    # 确保目录存在
    os.makedirs(base_dir, exist_ok=True)
    
    # 生成文件名
    safe_author = sanitize_filename(author)
    safe_title = sanitize_filename(title)
    filename = f"{safe_author}_{safe_title}.md"
    filepath = os.path.join(base_dir, filename)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def extract_movie_info_from_search(search_results):
    """
    从搜索结果中提取电影信息
    
    Args:
        search_results: 搜索结果列表
    
    Returns:
        dict: 包含导演、主演、年份等信息的字典
    """
    info = {
        '主演': '',
        '上映时间': '',
        '类型': '',
        '获奖情况': ''
    }
    
    # 简单的信息提取逻辑，可根据实际需要扩展
    for result in search_results:
        text = result.get('description', '') + result.get('title', '')
        
        # 提取主演
        if '主演' in text or '主演：' in text:
            match = re.search(r'主演 [：:](.+?)(?:,|。|$)', text)
            if match:
                info['主演'] = match.group(1).strip()
        
        # 提取年份
        year_match = re.search(r'(19|20)\d{2}', text)
        if year_match and not info['上映时间']:
            info['上映时间'] = year_match.group(0) + '年'
    
    return info


def classify_quote_emotion(quote_text, search_context=""):
    """
    根据台词内容判断其情感分类
    
    Args:
        quote_text: 台词文本
        search_context: 搜索上下文（可选）
    
    Returns:
        str: 情感分类名称
    """
    # 情感关键词匹配（更丰富的关键词库）
    emotion_keywords = {
        '励志/鼓舞': [
            '努力', '奋斗', '坚持', '梦想', '成功', '加油', '勇敢', '向前', '不放弃',
            '公平', '正义', '站着', '挣钱', '理想', '信念', '希望', '未来', '奋斗'
        ],
        '爱情/温情': [
            '爱', '喜欢', '幸福', '温暖', '陪伴', '家', '亲人', '朋友', '友情',
            '等待', '十年', '缘分', '牵挂', '思念', '守候', '一生', '永远'
        ],
        '幽默/讽刺': [
            '搞笑', '幽默', '讽刺', '笑话', '逗', '乐', '哈哈', '滑稽', '荒唐',
            '翻译', '惊喜', '师爷', '县长', '硬', '高', '扯蛋', '扯淡'
        ],
        '哲理/感悟': [
            '人生', '意义', '思考', '哲学', '感悟', '道理', '智慧', '深刻',
            '活着', '死', '路', '选择', '命运', '人性', '社会', '现实', '相信'
        ]
    }
    
    # 特殊规则：某些特定台词直接分类
    special_rules = {
        '公平': '励志/鼓舞',
        '站着': '励志/鼓舞',
        '让子弹飞': '经典/脍炙人口',
        '一万年': '爱情/温情',
        '曾经有一份': '爱情/温情',
        '爱你一万年': '爱情/温情',
        '地主家': '幽默/讽刺',
        '余粮': '幽默/讽刺',
        '扯蛋': '幽默/讽刺',
        '精神胜利': '哲理/感悟',
        '儿子打老子': '哲理/感悟',
    }
    
    # 检查特殊规则
    for keyword, emotion in special_rules.items():
        if keyword in quote_text:
            return emotion
    
    # 统计各分类的匹配度
    emotion_scores = {cat: 0 for cat in DEFAULT_CATEGORIES}
    
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in quote_text.lower():
                emotion_scores[emotion] += 2  # 关键词匹配加 2 分
            # 部分匹配也加分
            if len(keyword) >= 2 and keyword in quote_text:
                emotion_scores[emotion] += 1
    
    # 返回得分最高的分类
    best_emotion = max(emotion_scores, key=emotion_scores.get)
    
    # 如果最高分大于 0，返回该分类；否则返回默认分类
    if emotion_scores[best_emotion] > 0:
        return best_emotion
    
    # 默认归类为经典
    return '经典/脍炙人口'


# 示例用法
if __name__ == "__main__":
    # 测试数据 - 按情感分类组织
    test_quotes_by_category = {
        '励志/鼓舞': [
            {'content': '我来鹅城只办三件事：公平！公平！还是 TMD 公平！', 'speaker': '张麻子'},
            {'content': '我要站着，还把钱挣了！', 'speaker': '张麻子'}
        ],
        '幽默/讽刺': [
            {'content': '翻译翻译，什么叫惊喜？', 'speaker': '张麻子'},
            {'content': '师爷，你给翻译翻译，什么叫惊喜？', 'speaker': '张麻子'}
        ],
        '经典/脍炙人口': [
            {'content': '让子弹飞一会儿', 'speaker': '张麻子'}
        ]
    }
    
    content = format_quotes_content(
        title="让子弹飞",
        author="姜文",
        work_info={
            '主演': '姜文、葛优、周润发',
            '上映时间': '2010 年',
            '类型': '喜剧/动作'
        },
        quotes_by_category=test_quotes_by_category,
        source="网络公开资料"
    )
    
    filepath = save_quotes_file("姜文", "让子弹飞", content)
    print(f"已保存到：{filepath}")
    print(f"文件大小：{os.path.getsize(filepath)} 字节")
