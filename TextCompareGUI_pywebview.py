#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档比较工具 - pywebview版本
"""

import webview
import json
import os
import re

class TextCompareGUI:
    """
    文档比较GUI类
    """
    
    def __init__(self):
        """
        初始化文档比较GUI
        """
        self.json_file_path = ""
        self.md_file_path = ""
        self.json_data = []
        self.md_content = ""
        self.window = None
        
        # HTML模板
        self.html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档比较工具</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #333;
            text-align: center;
        }
        
        .section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #555;
        }
        
        .form-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        
        .form-row label {
            width: 150px;
            font-weight: bold;
        }
        
        .form-row input[type="text"] {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            margin: 0 10px;
            background-color: #f9f9f9;
        }
        
        .form-row button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        
        .form-row button:hover {
            background-color: #45a049;
        }
        
        .log-area {
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 3px;
            height: 100px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        
        .operation-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .table-container {
            flex: 2;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 4px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            position: sticky;
            top: 0;
        }
        
        /* 定义列宽度 */
        th:nth-child(1), td:nth-child(1) {
            width: 100%;
        }
        
        th:nth-child(n+2), td:nth-child(n+2) {
            white-space: nowrap;
            width: fit-content;
        }
        
        .text-input {
            width: 100%;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        
        .button-small {
            padding: 3px 8px;
            margin: 0 1px;
            font-size: 11px;
        }
        
        .markdown-display {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            height: 400px;
            overflow-y: auto;
            background-color: #f9f9f9;
            white-space: pre-wrap;
            font-family: Arial, sans-serif;
            font-size: 14px;
            user-select: text;
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
            cursor: text;
        }
        
        .highlight {
            color: blue;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>文档比较工具</h1>
        
        <!-- 配置区 -->
        <div class="section">
            <div class="section-title">配置区</div>
            
            <!-- 文件导入控件1 - 分镜脚本文件 -->
            <div class="form-row">
                <label for="json-file-path">分镜脚本文件：</label>
                <input type="text" id="json-file-path" readonly placeholder="请选择JSON文件">
                <button onclick="select_json_file()">导入分镜脚本文件</button>
            </div>
            
            <!-- 文件导入控件2 - 解说词文件 -->
            <div class="form-row">
                <label for="md-file-path">解说词文件：</label>
                <input type="text" id="md-file-path" readonly placeholder="请选择MD文件">
                <button onclick="select_md_file()">导入解说词文件</button>
            </div>
        </div>
        
        <!-- 操作区 -->
        <div class="section">
            <div class="section-title">操作区</div>
            
            <!-- 日志输出 -->
            <div class="log-area" id="log-area"></div>
            
            <!-- 操作区域 -->
            <div class="operation-area">
                <!-- 表格 -->
                <div class="table-container">
                    <table id="text-table">
                        <tr>
                            <th>文本内容</th>
                            <th>操作</th>
                        </tr>
                        <!-- 动态添加行 -->
                    </table>
                </div>
                
                <!-- 解说词显示框 -->
                <div class="markdown-display" id="markdown-display" contenteditable="false"></div>
            </div>
        </div>
    </div>
    
    <script>
        // 添加日志
        function add_log(message) {
            const logArea = document.getElementById('log-area');
            logArea.innerHTML += message + '<br>';
            logArea.scrollTop = logArea.scrollHeight;
            
            // 只保留最新的5行日志
            const lines = logArea.innerHTML.split('<br>');
            if (lines.length > 6) { // 多一个空行
                lines.splice(0, lines.length - 6);
                logArea.innerHTML = lines.join('<br>');
            }
        }
        
        // 选择分镜脚本文件（JSON）
        function select_json_file() {
            window.pywebview.api.select_json_file().then(function(result) {
                if (result.success) {
                    document.getElementById('json-file-path').value = result.file_path;
                    add_log('✅ 成功导入分镜脚本文件');
                    
                    // 更新表格
                    update_table(result.json_data);
                } else {
                    add_log('❌ JSON文件导入失败: ' + result.error);
                }
            });
        }
        
        // 选择解说词文件（MD）
        function select_md_file() {
            window.pywebview.api.select_md_file().then(function(result) {
                if (result.success) {
                    document.getElementById('md-file-path').value = result.file_path;
                    document.getElementById('markdown-display').textContent = result.content;
                    add_log('✅ 成功导入解说词文件');
                } else {
                    add_log('❌ MD文件导入失败: ' + result.error);
                }
            });
        }
        
        // 更新表格
        function update_table(json_data) {
            const table = document.getElementById('text-table');
            
            // 清空现有行（保留表头）
            const rows = table.rows;
            for (let i = rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            
            // 添加新行
            json_data.forEach(function(item, index) {
                const row = table.insertRow();
                
                // 文本列
                const textCell = row.insertCell();
                const textArea = document.createElement('textarea');
                textArea.value = item.text;
                textArea.className = 'text-input';
                textArea.id = `text-${index}`;
                textArea.style.width = '100%';
                textArea.style.height = '80px';
                textArea.style.resize = 'vertical';
                textArea.style.padding = '5px';
                textArea.style.fontFamily = 'Arial, sans-serif';
                textArea.style.fontSize = '14px';
                
                textCell.appendChild(textArea);
                
                // 按钮列 - 将三个按钮放在同一个单元格中
                const buttonCell = row.insertCell();
                buttonCell.innerHTML = `
                    <button class="button-small" onclick="locate_text(${index})">定位</button>
                    <button class="button-small" onclick="save_text(${index})">保存</button>
                    <button class="button-small" onclick="revert_text(${index})">撤回</button>
                `;
            });
        }
        
        // 定位文本
        function locate_text(index) {
            // 获取当前显示的文本内容，兼容textarea和div
            const textArea = document.getElementById(`text-${index}`);
            const divElement = document.getElementById(`text-div-${index}`);
            let currentText;
            let currentHeight;
            
            if (divElement) {
                currentText = divElement.textContent;
                currentHeight = divElement.style.height;
            } else if (textArea) {
                currentText = textArea.value;
                currentHeight = textArea.style.height;
            } else {
                add_log('❌ 未找到文本元素');
                return;
            }
            
            // 调用Python API进行定位
            window.pywebview.api.locate_text(currentText, index).then(function(result) {
                const targetStr = result.target_str;
                const count1 = result.count1;
                const count2 = result.count2;
                const originalText = result.original_text;
                
                // 无论成功与否，都在日志中打印选定的4个字符和字数计算结果
                if (result.success) {
                    const markdownDisplay = document.getElementById('markdown-display');
                    const content = result.highlighted_content;
                    
                    markdownDisplay.innerHTML = content;
                    
                    // 滚动到高亮位置，使其位于显示框中间
                    setTimeout(() => {
                        // 找到所有高亮元素
                        const highlightElements = markdownDisplay.querySelectorAll('span[style*="color: red; font-weight: bold;"]');
                        if (highlightElements.length > 0) {
                            const targetElement = highlightElements[0];
                            const elementRect = targetElement.getBoundingClientRect();
                            const displayRect = markdownDisplay.getBoundingClientRect();
                            
                            // 计算滚动位置，使高亮元素居中
                            const scrollTo = markdownDisplay.scrollTop + elementRect.top - displayRect.top - displayRect.height / 2 + elementRect.height / 2;
                            markdownDisplay.scrollTop = scrollTo;
                        } else {
                            // 如果没有找到红色高亮，尝试找到蓝色高亮
                            const blueElements = markdownDisplay.querySelectorAll('span[style*="color: blue; font-weight: bold;"]');
                            if (blueElements.length > 0) {
                                const targetElement = blueElements[0];
                                const elementRect = targetElement.getBoundingClientRect();
                                const displayRect = markdownDisplay.getBoundingClientRect();
                                
                                // 计算滚动位置，使高亮元素居中
                                const scrollTo = markdownDisplay.scrollTop + elementRect.top - displayRect.top - displayRect.height / 2 + elementRect.height / 2;
                                markdownDisplay.scrollTop = scrollTo;
                            }
                        }
                    }, 100); // 延迟执行，确保DOM已更新
                    
                    add_log(`✅ 文本定位成功，匹配字符: ${targetStr}，字数1: ${count1}，字数2: ${count2}`);
                } else {
                    add_log(`❌ 文本定位失败: ${result.error}，匹配字符: ${targetStr}，字数1: ${count1}，字数2: ${count2}`);
                }
                
                // 在文本显示框中将这4个字符加粗显示
                if (targetStr) {
                    // 创建加粗显示的文本
                    const highlightedText = originalText.replace(targetStr, `<span style="font-weight: bold;">${targetStr}</span>`);
                    
                    // 确保只有一个显示元素（要么是div，要么是textarea）
                    if (divElement) {
                        // 如果已经有div元素，直接更新其内容
                        divElement.innerHTML = highlightedText;
                        divElement.style.height = currentHeight;
                    } else if (textArea) {
                        // 先检查是否已经存在div元素（可能是之前创建的）
                        const existingDiv = document.getElementById(`text-div-${index}`);
                        if (existingDiv) {
                            // 如果已经存在div元素，直接更新其内容
                            existingDiv.innerHTML = highlightedText;
                            existingDiv.style.height = currentHeight;
                        } else {
                            // 创建一个替换的div元素
                            const newDiv = document.createElement('div');
                            newDiv.id = `text-div-${index}`;
                            newDiv.className = 'text-input';
                            newDiv.contentEditable = true;
                            newDiv.style.width = '100%';
                            newDiv.style.height = currentHeight;
                            newDiv.style.resize = 'vertical';
                            newDiv.style.padding = '5px';
                            newDiv.style.fontFamily = 'Arial, sans-serif';
                            newDiv.style.fontSize = '14px';
                            newDiv.style.border = '1px solid #ddd';
                            newDiv.style.borderRadius = '3px';
                            
                            // 当div内容改变时，同步更新到textarea（隐藏的）
                            newDiv.addEventListener('input', function() {
                                const textArea = document.getElementById(`text-${index}`);
                                if (textArea) {
                                    textArea.value = this.textContent;
                                }
                            });
                            
                            // 设置div的内容
                            newDiv.innerHTML = highlightedText;
                            
                            // 替换textarea
                            const parent = textArea.parentNode;
                            parent.replaceChild(newDiv, textArea);
                            
                            // 隐藏原始textarea，但不删除，以便保存功能使用
                            textArea.style.display = 'none';
                            parent.appendChild(textArea);
                        }
                    }
                }
            });
        }
        
        // 获取文本内容，兼容textarea和contenteditable div
        function get_text_content(index) {
            const textArea = document.getElementById(`text-${index}`);
            const divElement = document.getElementById(`text-div-${index}`);
            
            if (divElement) {
                return divElement.textContent;
            } else if (textArea) {
                return textArea.value;
            }
            return '';
        }
        
        // 保存文本
        function save_text(index) {
            const new_text = get_text_content(index);
            window.pywebview.api.save_text(new_text, index).then(function(result) {
                if (result.success) {
                    add_log('✅ 文本保存成功');
                } else {
                    add_log('❌ 文本保存失败: ' + result.error);
                }
            });
        }
        
        // 撤回文本
        function revert_text(index) {
            window.pywebview.api.revert_text(index).then(function(result) {
                if (result.success) {
                    const textArea = document.getElementById(`text-${index}`);
                    const divElement = document.getElementById(`text-div-${index}`);
                    const original_text = result.original_text;
                    
                    if (divElement) {
                        // 如果是div，直接设置文本内容（不保留加粗效果）
                        divElement.textContent = original_text;
                    } else if (textArea) {
                        textArea.value = original_text;
                    }
                    
                    add_log('✅ 文本撤回成功');
                } else {
                    add_log('❌ 文本撤回失败: ' + result.error);
                }
            });
        }
    </script>
</body>
</html>
        """
    
    def start(self):
        """
        启动GUI
        """
        # 创建窗口
        self.window = webview.create_window(
            "文档比较工具",
            html=self.html,
            width=1200,
            height=800,
            resizable=True
        )
        
        # 暴露Python函数给JavaScript
        self.window.expose(
            self.select_json_file,
            self.select_md_file,
            self.locate_text,
            self.save_text,
            self.revert_text
        )
        
        # 启动GUI
        webview.start()
    
    def select_json_file(self):
        """
        选择JSON文件
        """
        try:
            # 打开文件对话框
            file_path = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False
            )
            
            # 检查是否取消选择
            if file_path is None:
                return {"success": False, "error": "未选择文件"}
            
            # 确保file_path是字符串类型
            if isinstance(file_path, tuple) or isinstance(file_path, list):
                if len(file_path) > 0:
                    file_path = file_path[0]
                else:
                    return {"success": False, "error": "未选择文件"}
            
            if not isinstance(file_path, str):
                return {"success": False, "error": f"无效的文件路径类型: {type(file_path)}，值: {file_path}"}
            
            if not file_path:
                return {"success": False, "error": "未选择文件"}
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.json'):
                return {"success": False, "error": "只能选择JSON格式文件"}
            
            # 读取并验证JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 验证每个对象是否包含text字段
            for item in json_data:
                if not isinstance(item, dict):
                    return {"success": False, "error": f"JSON文件格式无效：包含非对象元素"}
                if "text" not in item:
                    return {"success": False, "error": "JSON文件无效：缺少text字段"}
                if not isinstance(item["text"], str):
                    return {"success": False, "error": "JSON文件无效：text字段必须是字符串"}
            
            # 保存文件路径和数据
            self.json_file_path = file_path
            self.json_data = json_data
            
            return {
                "success": True,
                "file_path": file_path,
                "json_data": json_data
            }
            
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON文件格式无效: {str(e)}"}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件导入失败: {str(e)}\n详细错误: {error_detail}"}
    
    def select_md_file(self):
        """
        选择MD文件
        """
        try:
            # 打开文件对话框
            file_path = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False
            )
            
            # 检查是否取消选择
            if file_path is None:
                return {"success": False, "error": "未选择文件"}
            
            # 确保file_path是字符串类型
            if isinstance(file_path, tuple) or isinstance(file_path, list):
                if len(file_path) > 0:
                    file_path = file_path[0]
                else:
                    return {"success": False, "error": "未选择文件"}
            
            if not isinstance(file_path, str):
                return {"success": False, "error": f"无效的文件路径类型: {type(file_path)}，值: {file_path}"}
            
            if not file_path:
                return {"success": False, "error": "未选择文件"}
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.md'):
                return {"success": False, "error": "只能选择MD格式文件"}
            
            # 读取MD文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 保存文件路径和内容
            self.md_file_path = file_path
            self.md_content = content
            
            return {
                "success": True,
                "file_path": file_path,
                "content": content
            }
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件导入失败: {str(e)}\n详细错误: {error_detail}"}
    
    def locate_text(self, text, index):
        """
        定位文本
        """
        try:
            # 确保re模块被导入
            import re
            import random
            
            # 从文本中提取连续4个非标点字符
            # 先过滤掉标点符号，只保留汉字、字母、数字
            filtered_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
            
            if len(filtered_text) < 4:
                return {
                    "success": False, 
                    "error": "文本太短，无法提取4个连续字符",
                    "target_str": "",
                    "count1": 0,
                    "count2": 0,
                    "original_text": text
                }
            
            # 随机选择4个连续字符（每次点击都重新选择）
            # 确保有足够的空间选择4个字符
            start_pos = random.randint(0, len(filtered_text) - 4)
            target_str = filtered_text[start_pos:start_pos+4]
            
            # 确保target_str是连续的且不包含标点符号
            # 由于我们是从过滤后的文本中选择的，所以这一点已经保证
            
            # 在原text中找到target_str的所有可能位置
            # 使用正则表达式来找到准确的位置
            matches = list(re.finditer(re.escape(target_str), text))
            
            if not matches:
                # 如果找不到完整的target_str，尝试使用其他方法
                # 先找第一个字符的位置
                first_char = target_str[0]
                first_char_pos = text.find(first_char)
                if first_char_pos == -1:
                    return {
                        "success": False, 
                        "error": "无法找到字符位置",
                        "target_str": target_str,
                        "count1": 0,
                        "count2": 0,
                        "original_text": text
                    }
                
                # 使用第一个字符的位置作为基准
                actual_pos = first_char_pos
            else:
                # 使用第一个匹配项
                actual_pos = matches[0].start()
            
            # 计算字数1和字数2
            first_index = actual_pos
            last_index = actual_pos + len(target_str) - 1
            
            count1 = first_index
            count2 = len(text) - last_index - 1
            
            # 如果未导入解说词文件，仍然返回基本信息
            if not self.md_content:
                return {
                    "success": False, 
                    "error": "未导入解说词文件",
                    "target_str": target_str,
                    "count1": count1,
                    "count2": count2,
                    "original_text": text
                }
            
            # 在解说词中匹配target_str
            match_index = self.md_content.find(target_str)
            if match_index == -1:
                return {
                    "success": False, 
                    "error": "在解说词中未找到匹配的文本",
                    "target_str": target_str,
                    "count1": count1,
                    "count2": count2,
                    "original_text": text
                }
            
            # 计算高亮范围
            # 整个高亮区域：start到end
            start = max(0, match_index - count1 - 10)
            end = min(len(self.md_content), match_index + len(target_str) + count2 + 10)
            
            # 蓝色高亮加粗区域：
            # 1. 选中字符之前的字数1长度的文字
            # 2. 选中字符之后的字数2长度的文字
            # 3. 选中的4个字符（红色高亮）
            
            # 分割内容
            before_all = self.md_content[:start]
            highlight_segment = self.md_content[start:end]
            after_all = self.md_content[end:]
            
            # 在highlight_segment中找到target_str的位置
            target_pos_in_segment = highlight_segment.find(target_str)
            
            if target_pos_in_segment != -1:
                # 计算蓝色高亮区域
                # 前蓝色区域：target_str之前，长度为count1
                blue_before_start = target_pos_in_segment - count1
                if blue_before_start < 0:
                    blue_before_start = 0
                
                blue_before_end = target_pos_in_segment
                
                # 后蓝色区域：target_str之后，长度为count2
                blue_after_start = target_pos_in_segment + len(target_str)
                blue_after_end = blue_after_start + count2
                if blue_after_end > len(highlight_segment):
                    blue_after_end = len(highlight_segment)
                
                # 构建高亮内容 - 按正确顺序拼接
                highlighted_content = before_all + \
                                    highlight_segment[0:blue_before_start] + \
                                    f'<span style="color: blue; font-weight: bold;">{highlight_segment[blue_before_start:blue_before_end]}</span>' + \
                                    f'<span style="color: red; font-weight: bold;">{target_str}</span>' + \
                                    f'<span style="color: blue; font-weight: bold;">{highlight_segment[blue_after_start:blue_after_end]}</span>' + \
                                    highlight_segment[blue_after_end:] + \
                                    after_all
            else:
                # 如果找不到target_str，使用默认高亮
                highlighted_content = before_all + \
                                    highlight_segment.replace(target_str, f'<span style="color: red; font-weight: bold;">{target_str}</span>') + \
                                    after_all
            
            return {
                "success": True,
                "highlighted_content": highlighted_content,
                "position": match_index,
                "target_str": target_str,
                "count1": count1,
                "count2": count2,
                "original_text": text
            }
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            current_text = text if 'text' in locals() else ""
            # 确保返回有效的target_str
            target_str = "" 
            if 'target_str' in locals():
                target_str = locals()['target_str']
            return {
                "success": False, 
                "error": str(e),
                "target_str": target_str,
                "count1": 0,
                "count2": 0,
                "original_text": current_text
            }
    
    def save_text(self, new_text, index):
        """
        保存文本
        """
        try:
            if not self.json_file_path:
                return {"success": False, "error": "未导入分镜脚本文件"}
            
            if index < 0 or index >= len(self.json_data):
                return {"success": False, "error": "无效的索引"}
            
            # 创建编辑后的JSON文件
            base_name = os.path.splitext(self.json_file_path)[0]
            edit_file_path = f"{base_name}_edit.json"
            
            # 如果文件不存在，先复制原文件内容
            if not os.path.exists(edit_file_path):
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    edit_data = json.load(f)
            else:
                with open(edit_file_path, 'r', encoding='utf-8') as f:
                    edit_data = json.load(f)
            
            # 更新对应的text字段
            if index < len(edit_data):
                edit_data[index]["text"] = new_text
            
            # 保存到文件
            with open(edit_file_path, 'w', encoding='utf-8') as f:
                json.dump(edit_data, f, ensure_ascii=False, indent=2)
            
            return {"success": True}
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"保存失败: {str(e)}\n详细错误: {error_detail}"}
    
    def revert_text(self, index):
        """
        撤回文本
        """
        try:
            if not self.json_file_path:
                return {"success": False, "error": "未导入分镜脚本文件"}
            
            if index < 0 or index >= len(self.json_data):
                return {"success": False, "error": "无效的索引"}
            
            # 获取原始文本
            original_text = self.json_data[index]["text"]
            
            return {
                "success": True,
                "original_text": original_text
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# 运行GUI
if __name__ == "__main__":
    app = TextCompareGUI()
    app.start()
