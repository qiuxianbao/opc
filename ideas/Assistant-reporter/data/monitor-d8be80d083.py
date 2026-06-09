#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术趋势监测脚本
用于定期扫描配置的信源，提取大模型、Agent Skill、OpenSpec等技术前沿内容。
具备基本的去重和分类功能。
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import feedparser  # 用于RSS订阅

# 配置文件路径
CONFIG_FILE = "../data/信源配置.json"
# 数据存储目录
DATA_DIR = "../data/raw"
# 去重记录文件
SEEN_HASHES_FILE = "../data/seen_hashes.json"
# 输出目录
OUTPUT_DIR = "../outputs/周报"

def load_config(config_path: str) -> Dict[str, Any]:
    """加载信源配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def ensure_directories():
    """确保必要的目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_content_hash(content: str) -> str:
    """生成内容哈希值用于去重"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_seen_hashes() -> set:
    """加载已处理内容的哈希值"""
    if os.path.exists(SEEN_HASHES_FILE):
        with open(SEEN_HASHES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get("hashes", []))
    return set()

def save_seen_hashes(hashes: set):
    """保存已处理的哈希值"""
    data = {"hashes": list(hashes), "updated_at": datetime.now().isoformat()}
    with open(SEEN_HASHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_webpage(url: str, headers: Optional[Dict] = None) -> Optional[str]:
    """获取网页内容"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"获取网页失败 {url}: {e}")
        return None

def parse_github_trending(html: str, tags: List[str]) -> List[Dict[str, Any]]:
    """解析GitHub Trending页面，提取相关标签的项目"""
    soup = BeautifulSoup(html, 'html.parser')
    projects = []
    
    # GitHub Trending的实际HTML结构可能变化，这里提供示例解析逻辑
    for article in soup.select('article'):
        title_elem = article.select_one('h2 a')
        if not title_elem:
            continue
        title = title_elem.text.strip()
        url = "https://github.com" + title_elem.get('href', '')
        desc_elem = article.select_one('p')
        description = desc_elem.text.strip() if desc_elem else ""
        
        # 检查是否包含目标标签
        content = title + " " + description
        matched_tags = [tag for tag in tags if tag in content]
        if matched_tags:
            projects.append({
                "title": title,
                "url": url,
                "description": description,
                "tags": matched_tags,
                "source": "GitHub Trending",
                "fetched_at": datetime.now().isoformat()
            })
    return projects

def parse_coze_blog(html: str) -> List[Dict[str, Any]]:
    """解析Coze官网博客"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # 假设博客文章在特定CSS选择器下
    for article_elem in soup.select('article.blog-post'):
        title_elem = article_elem.select_one('h2 a')
        if not title_elem:
            continue
        title = title_elem.text.strip()
        url = title_elem.get('href', '')
        if url and not url.startswith('http'):
            url = "https://www.coze.cn" + url
        date_elem = article_elem.select_one('time')
        date = date_elem.get('datetime') if date_elem else ""
        content_elem = article_elem.select_one('.post-content')
        content = content_elem.text.strip() if content_elem else ""
        
        articles.append({
            "title": title,
            "url": url,
            "date": date,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "source": "Coze官网博客",
            "fetched_at": datetime.now().isoformat()
        })
    return articles

def check_keywords(content: str, keywords: List[str]) -> List[str]:
    """检查内容中是否包含关键词，返回匹配的关键词列表"""
    matched = []
    for keyword in keywords:
        if keyword in content:
            matched.append(keyword)
    return matched

def classify_content(title: str, content: str, keywords: List[str]) -> str:
    """根据内容分类：技术突破、工具更新、行业动态、趋势研判"""
    content_lower = (title + " " + content).lower()
    
    # 分类规则
    if any(word in content_lower for word in ['论文', '研究', '突破', '创新', '新方法', '模型']):
        return "技术突破"
    elif any(word in content_lower for word in ['发布', '更新', '版本', '工具', '框架', 'sdk', 'api', '库']):
        return "工具更新"
    elif any(word in content_lower for word in ['融资', '合作', '并购', '政策', '监管', '市场', '竞争']):
        return "行业动态"
    else:
        return "趋势研判"

def process_source(source_config: Dict[str, Any], keywords: List[str], seen_hashes: set) -> List[Dict[str, Any]]:
    """处理单个信源，提取新内容"""
    results = []
    source_type = source_config.get("type", "unknown")
    
    if source_type == "github_trending":
        url = source_config.get("url")
        tags = source_config.get("tags", [])
        html = fetch_webpage(url)
        if html:
            items = parse_github_trending(html, tags)
            for item in items:
                content = item.get("description", "")
                content_hash = get_content_hash(item["title"] + content)
                if content_hash in seen_hashes:
                    continue
                matched_keywords = check_keywords(content, keywords)
                if matched_keywords:
                    item["category"] = classify_content(item["title"], content, keywords)
                    item["matched_keywords"] = matched_keywords
                    item["content_hash"] = content_hash
                    results.append(item)
                    seen_hashes.add(content_hash)
    
    elif source_type == "coze_blog":
        url = source_config.get("url")
        html = fetch_webpage(url)
        if html:
            items = parse_coze_blog(html)
            for item in items:
                content = item.get("content_preview", "")
                content_hash = get_content_hash(item["title"] + content)
                if content_hash in seen_hashes:
                    continue
                matched_keywords = check_keywords(content, keywords)
                if matched_keywords:
                    item["category"] = classify_content(item["title"], content, keywords)
                    item["matched_keywords"] = matched_keywords
                    item["content_hash"] = content_hash
                    results.append(item)
                    seen_hashes.add(content_hash)
    
    # 其他信源类型可以继续扩展
    
    return results

def main():
    """主函数：执行监测任务"""
    print("开始技术趋势监测...")
    start_time = time.time()
    
    # 确保目录存在
    ensure_directories()
    
    # 加载配置
    config = load_config(CONFIG_FILE)
    keywords = config.get("搜索关键词", [])
    
    # 加载已处理内容哈希
    seen_hashes = load_seen_hashes()
    
    # 准备信源配置
    sources = []
    # GitHub Trending
    sources.append({
        "type": "github_trending",
        "url": "https://github.com/trending?l=python&since=daily&spoken_language_code=zh",
        "tags": ["大模型", "Agent", "LLM", "AI"]
    })
    # Coze博客
    sources.append({
        "type": "coze_blog",
        "url": "https://www.coze.cn/blog"
    })
    # 公众号需要特殊处理，这里先占位
    # sources.append({"type": "wechat", "name": "阿里云开发者"})
    
    all_results = []
    
    # 处理每个信源
    for source in sources:
        try:
            results = process_source(source, keywords, seen_hashes)
            all_results.extend(results)
            print(f"处理信源 {source.get('type')}: 找到 {len(results)} 条新内容")
        except Exception as e:
            print(f"处理信源 {source.get('type')} 时出错: {e}")
    
    # 保存结果
    if all_results:
        output_file = os.path.join(DATA_DIR, f"raw_{datetime.now().strftime('%Y%m%d')}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "fetched_at": datetime.now().isoformat(),
                "count": len(all_results),
                "results": all_results
            }, f, ensure_ascii=False, indent=2)
        print(f"保存 {len(all_results)} 条结果到 {output_file}")
    
    # 保存已处理的哈希值
    save_seen_hashes(seen_hashes)
    
    # 按分类汇总
    categories = {}
    for item in all_results:
        category = item.get("category", "未分类")
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # 生成简要报告
    report = f"""# 技术趋势监测报告 {datetime.now().strftime('%Y-%m-%d')}

本次监测扫描了 {len(sources)} 个信源，共发现 {len(all_results)} 条新内容。

## 分类统计
"""
    for category, items in categories.items():
        report += f"- **{category}**: {len(items)} 条\n"
    
    report += "\n## 详细内容\n"
    for category, items in categories.items():
        report += f"\n### {category}\n"
        for item in items:
            report += f"- **{item['title']}** ({item['source']})\n"
            report += f"  链接: {item['url']}\n"
            report += f"  匹配关键词: {', '.join(item.get('matched_keywords', []))}\n"
            if item.get('description'):
                desc = item['description'][:100] + "..." if len(item['description']) > 100 else item['description']
                report += f"  摘要: {desc}\n"
            report += "\n"
    
    # 保存报告
    report_file = os.path.join(OUTPUT_DIR, f"监测报告_{datetime.now().strftime('%Y%m%d')}.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"生成报告: {report_file}")
    print(f"监测完成，耗时 {time.time() - start_time:.2f} 秒")

if __name__ == "__main__":
    main()