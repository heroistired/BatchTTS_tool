#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
提取解说文稿中的时间轴和文本，保存为JSON格式
"""

import re
import json


def extract_commentary(input_file, output_file):
    """
    提取解说文稿中的时间轴和文本，保存为JSON格式
    
    :param input_file: 输入文件路径
    :param output_file: 输出JSON文件路径
    """
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 时间轴正则表达式
    # 匹配格式：**[HH:MM - HH:MM]** 或 **[HH:MM - HH:MM] (音乐提示)**
    timeline_pattern = r'\*\*\[(\d{2}:\d{2} - \d{2}:\d{2})\]\*\*(?:\s*\(([^)]+)\))?'
    
    # 找到所有时间轴位置
    timeline_matches = list(re.finditer(timeline_pattern, content))
    
    # 提取时间轴和对应的文本
    commentary_list = []
    
    for i, match in enumerate(timeline_matches):
        # 获取时间轴
        timeline = match.group(1)
        # 获取音乐提示（如果有）
        music_note = match.group(2)
        
        # 获取当前时间轴的结束位置
        current_end = match.end()
        
        # 获取下一个时间轴的开始位置（如果有）
        next_start = timeline_matches[i+1].start() if i < len(timeline_matches) - 1 else len(content)
        
        # 提取当前时间轴对应的文本
        text_content = content[current_end:next_start].strip()
        
        # 构建时间轴项
        timeline_item = {
            "timeline": timeline,
            "text": text_content
        }
        
        # 如果有音乐提示，添加到项中
        if music_note:
            timeline_item["music_note"] = music_note
        
        # 添加到列表中
        commentary_list.append(timeline_item)
    
    # 将列表保存为JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(commentary_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 解说词提取完成，共提取 {len(commentary_list)} 个时间轴项")
    print(f"📁 输出文件：{output_file}")


if __name__ == "__main__":
    # 输入文件路径
    input_file = "d:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\视频解说文稿（修订版-带时间轴）.md"
    # 输出文件路径
    output_file = "d:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\Commentary.json"
    
    # 执行提取
    extract_commentary(input_file, output_file)