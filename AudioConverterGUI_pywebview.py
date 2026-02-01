#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频转换GUI程序 - pywebview版本
"""

import webview
import json
import os
import threading
import re
import subprocess
import wave
from ConvertAudio import AudioConverter

class AudioConverterGUI:
    """
    音频转换GUI类
    """
    
    def __init__(self):
        """
        初始化音频转换GUI
        """
        self.audio_server_url = ""
        self.subtitle_server_url = ""
        self.json_file_path = ""
        self.output_folder = None
        self.tasks = []
        self.is_processing = False
        self.window = None
        self.converter = None
        
        # HTML模板
        self.html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>音频批量转换工具</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
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
            width: 120px;
            font-weight: bold;
        }
        .form-row input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            margin: 0 10px;
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
        }
        .table-container {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 3px;
            margin: 10px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            position: sticky;
            top: 0;
        }
        .status-passed {
            color: green;
            font-weight: bold;
        }
        .status-failed {
            color: red;
            font-weight: bold;
        }
        .button-small {
            padding: 5px 10px;
            margin: 0 2px;
            font-size: 12px;
        }
        .text-input {
            width: 300px;
        }
        .duration-column {
            width: 100px;
            text-align: center;
        }
        .status-column {
            width: 80px;
            text-align: center;
        }
        .button-column {
            width: 60px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>音频批量转换工具</h1>
        
        <!-- 配置区 -->
        <div class="section">
            <div class="section-title">配置区</div>
            
            <!-- 文件导入 -->
            <div class="form-row">
                <label for="file-path">JSON文件路径：</label>
                <input type="text" id="file-path" readonly placeholder="请选择JSON文件">
                <button onclick="select_file()">导入文件</button>
            </div>
            
            <!-- 转音频服务器地址 -->
            <div class="form-row">
                <label for="audio-server-url">转音频服务器地址：</label>
                <input type="text" id="audio-server-url" placeholder="http://192.168.31.194:9872/">
                <button onclick="set_audio_server_url()">设定转音频服务器地址</button>
            </div>
            
            <!-- 字幕服务器地址 -->
            <div class="form-row">
                <label for="subtitle-server-url">字幕服务器地址：</label>
                <input type="text" id="subtitle-server-url" placeholder="http://116.62.7.179:10002/">
                <button onclick="set_subtitle_server_url()">设定字幕服务器地址</button>
            </div>
            
            <!-- 输出文件夹 -->
            <div class="form-row">
                <label for="output-folder">输出文件夹：</label>
                <input type="text" id="output-folder" readonly placeholder="请选择输出文件夹">
                <button onclick="select_output_folder()">设置输出文件夹</button>
            </div>
        </div>
        
        <!-- 操作区 -->
        <div class="section">
            <div class="section-title">操作区</div>
            
            <!-- 批量转换、导出和字幕转换 -->
            <div class="form-row">
                <label for="convert-btn">音频操作：</label>
                <button id="convert-btn" onclick="batch_convert()" style="background-color: #2196F3;">批量转换</button>
                <button id="export-btn" onclick="export_audio()" style="background-color: #FF9800; margin-left: 10px;">导出</button>
                <button id="batch-subtitle-btn" onclick="batch_convert_subtitles()" style="background-color: #9C27B0; margin-left: 10px;">批量转换字幕</button>
            </div>
            
            <!-- 日志输出 -->
            <div class="log-area" id="log-area"></div>
            
            <!-- 表格 -->
            <div class="table-container">
                <table id="task-table">
                    <tr>
                        <th>文本</th>
                        <th class="duration-column">时长</th>
                        <th class="status-column">状态</th>
                        <th class="button-column">播放</th>
                        <th class="button-column">通过</th>
                        <th class="button-column">撤回</th>
                        <th class="button-column">字幕</th>
                    </tr>
                    <!-- 动态添加行 -->
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // 添加日志
        function add_log(message) {
            const logArea = document.getElementById('log-area');
            logArea.innerHTML += message + '<br>';
            logArea.scrollTop = logArea.scrollHeight;
        }
        
        // 选择文件
        function select_file() {
            window.pywebview.api.select_file().then(function(result) {
                if (result.success) {
                    document.getElementById('file-path').value = result.file_path;
                    add_log('✅ 成功导入JSON文件');
                    
                    // 更新表格
                    update_table(result.tasks);
                } else {
                    add_log('❌ 文件导入失败: ' + result.error);
                }
            });
        }
        
        // 更新表格
        function update_table(tasks) {
            const table = document.getElementById('task-table');
            
            // 清空现有行（保留表头）
            const rows = table.rows;
            for (let i = rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            
            // 添加新行
            tasks.forEach(function(task, index) {
                const row = table.insertRow();
                
                // 文本列
                const textCell = row.insertCell();
                const textArea = document.createElement('textarea');
                textArea.value = task.text;
                textArea.className = 'text-input';
                textArea.id = `text-${index}`;
                textArea.readOnly = true;
                textArea.style.width = '100%';
                textArea.style.minHeight = '60px';
                textArea.style.resize = 'vertical';
                textArea.style.boxSizing = 'border-box';
                textArea.style.padding = '5px';
                textArea.style.fontFamily = 'Arial, sans-serif';
                textArea.style.fontSize = '14px';
                textArea.style.border = '1px solid #ddd';
                textArea.style.borderRadius = '3px';
                
                // 自动调整高度
                textArea.style.height = 'auto';
                textArea.style.height = (textArea.scrollHeight) + 'px';
                
                textCell.appendChild(textArea);
                
                // 时长列
                const durationCell = row.insertCell();
                durationCell.className = 'duration-column';
                durationCell.innerHTML = `<input type="text" id="duration-${index}" value="${task.duration || 0}" readonly style="width: 60px; text-align: center; border: 1px solid #ddd; border-radius: 3px; padding: 3px; font-size: 14px;">`;
                
                // 状态列
                const statusCell = row.insertCell();
                statusCell.className = 'status-column';
                statusCell.innerHTML = `<span class="status-failed" id="status-${index}">未通过</span>`;
                
                // 播放按钮
                const playCell = row.insertCell();
                playCell.className = 'button-column';
                playCell.innerHTML = `<button class="button-small" onclick="play_audio(${index})">播放</button>`;
                
                // 通过按钮
                const passCell = row.insertCell();
                passCell.className = 'button-column';
                passCell.innerHTML = `<button class="button-small" onclick="pass_task(${index})">通过</button>`;
                
                // 撤回按钮
                const revertCell = row.insertCell();
                revertCell.className = 'button-column';
                revertCell.innerHTML = `<button class="button-small" onclick="revert_task(${index})">撤回</button>`;
                
                // 字幕按钮
                const subtitleCell = row.insertCell();
                subtitleCell.className = 'button-column';
                subtitleCell.innerHTML = `<button class="button-small" onclick="toggle_subtitles(${index})">展开</button>`;
                
            // 添加二级子表格容器行
            const subTableRow = table.insertRow();
            subTableRow.id = `subtitle-row-${index}`;
            subTableRow.style.display = 'none';
            const subTableCell = subTableRow.insertCell();
            subTableCell.colSpan = 7;  // 跨越所有列
            subTableCell.id = `subtitle-container-${index}`;
            subTableCell.innerHTML = `
                <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd; margin: 0 -10px;">
                    <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
                        <tr>
                            <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 150px;">时间戳</th>
                            <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: auto;">字幕内容</th>
                            <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 80px;">状态</th>
                            <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 120px;">操作</th>
                        </tr>
                        <tr>
                            <td colspan="4" style="padding: 10px; text-align: center; color: #666;">加载字幕中...</td>
                        </tr>
                    </table>
                </div>
            `;
            });
        }
        
        // 设置转音频服务器地址
        function set_audio_server_url() {
            const serverUrl = document.getElementById('audio-server-url').value;
            window.pywebview.api.set_audio_server_url(serverUrl).then(function(result) {
                if (result.success) {
                    add_log('✅ 转音频服务器地址设置成功');
                } else {
                    add_log('❌ 转音频服务器地址无效');
                }
            });
        }
        
        // 设置字幕服务器地址
        function set_subtitle_server_url() {
            const serverUrl = document.getElementById('subtitle-server-url').value;
            window.pywebview.api.set_subtitle_server_url(serverUrl).then(function(result) {
                if (result.success) {
                    add_log('✅ 字幕服务器地址设置成功');
                } else {
                    add_log('❌ 字幕服务器地址无效');
                }
            });
        }
        
        // 批量转换字幕
        function batch_convert_subtitles() {
            const subtitleServerUrl = document.getElementById('subtitle-server-url').value;
            if (!subtitleServerUrl) {
                add_log('⚠️ 请先设置字幕服务器地址');
                return;
            }
            
            if (!document.getElementById('file-path').value) {
                add_log('⚠️ 请先导入JSON文件');
                return;
            }
            
            const outputFolder = document.getElementById('output-folder').value;
            if (!outputFolder) {
                add_log('⚠️ 请先设置输出文件夹');
                return;
            }
            
            // 禁用按钮
            const btn = document.getElementById('batch-subtitle-btn');
            btn.disabled = true;
            btn.textContent = '转换中...';
            
            // 开始批量转换字幕
            window.pywebview.api.batch_convert_subtitles().then(function(result) {
                // 启用按钮
                btn.disabled = false;
                btn.textContent = '批量转换字幕';
                
                if (result.success) {
                    add_log('🎉 批量转换字幕完成！');
                    add_log(`📊 成功: ${result.success_count}, 失败: ${result.error_count}`);
                    
                    // 重新导入JSON文件以更新信息
                    const filePath = document.getElementById('file-path').value;
                    if (filePath) {
                        add_log('🔄 重新导入JSON文件以更新字幕信息');
                        // 调用Python的重新导入方法
                        window.pywebview.api.reimport_json_file().then(function(reimportResult) {
                            if (reimportResult.success) {
                                add_log('✅ JSON文件重新导入成功，信息已更新');
                                // 更新表格显示
                                update_table(reimportResult.tasks);
                            } else {
                                add_log('❌ JSON文件重新导入失败: ' + reimportResult.error);
                            }
                        });
                    }
                } else {
                    add_log('❌ 批量转换字幕失败: ' + result.error);
                }
            });
        }
        
        // 选择输出文件夹
        function select_output_folder() {
            window.pywebview.api.select_output_folder().then(function(result) {
                if (result.success) {
                    document.getElementById('output-folder').value = result.folder_path;
                    add_log('✅ 输出文件夹设置成功');
                } else {
                    add_log('❌ 文件夹选择失败: ' + result.error);
                }
            });
        }
        
        // 批量转换
        function batch_convert() {
            const serverUrl = document.getElementById('audio-server-url').value;
            if (!serverUrl) {
                add_log('⚠️ 请先设置转音频服务器地址');
                return;
            }
            
            // 获取所有任务文本 - 现在使用textarea
            const tasks = [];
            const table = document.getElementById('task-table');
            const rows = table.rows;
            
            // 遍历所有行，跳过字幕行
            let taskIndex = 0;
            for (let i = 1; i < rows.length; i += 2) { // 每两个行一组，跳过字幕行
                const textArea = document.getElementById(`text-${taskIndex}`);
                if (textArea) {
                    tasks.push(textArea.value);
                    taskIndex++;
                }
            }
            
            if (tasks.length === 0) {
                add_log('⚠️ 没有任务需要转换');
                return;
            }
            
            // 禁用转换按钮
            const convertBtn = document.getElementById('convert-btn');
            convertBtn.disabled = true;
            convertBtn.textContent = '转换中...';
            
            // 开始转换
            window.pywebview.api.batch_convert(tasks).then(function(result) {
                // 启用转换按钮
                convertBtn.disabled = false;
                convertBtn.textContent = '批量转换';
                
                if (result.success) {
                    add_log('🎉 批量转换完成！');
                    add_log(`📊 成功: ${result.success_count}, 失败: ${result.error_count}`);
                    
                    // 不再自动更新任务状态，由用户手动点击通过按钮修改
                } else {
                    add_log('❌ 批量转换失败: ' + result.error);
                }
            });
        }
        
        // 播放音频
        function play_audio(index) {
            window.pywebview.api.play_audio(index).then(function(result) {
                if (!result.success) {
                    add_log('❌ 播放失败: ' + result.error);
                }
            });
        }
        
        // 通过任务
        function pass_task(index) {
            window.pywebview.api.pass_task(index).then(function(result) {
                if (result.success) {
                    const statusSpan = document.getElementById(`status-${index}`);
                    statusSpan.className = 'status-passed';
                    statusSpan.textContent = '已通过';
                } else {
                    add_log('❌ 通过任务失败: ' + result.error);
                }
            });
        }
        
        // 撤回任务
        function revert_task(index) {
            window.pywebview.api.revert_task(index).then(function(result) {
                if (result.success) {
                    const statusSpan = document.getElementById(`status-${index}`);
                    statusSpan.className = 'status-failed';
                    statusSpan.textContent = '未通过';
                } else {
                    add_log('❌ 撤回任务失败: ' + result.error);
                }
            });
        }
        
        // 导出音频
        function export_audio() {
            window.pywebview.api.export_audio().then(function(result) {
                if (result.success) {
                    add_log('🎉 音频导出成功！');
                    add_log(`📁 导出文件: ${result.audio_file}`);
                    add_log(`📄 导出信息: ${result.info_file}`);
                    
                    // 重新导入JSON文件以更新信息
                    if (result.info_file) {
                        add_log('🔄 重新导入生成的ExportAudioInfo.json文件');
                        // 调用Python的重新导入方法，传入生成的info_file路径
                        window.pywebview.api.reimport_json_file(result.info_file).then(function(reimportResult) {
                            if (reimportResult.success) {
                                add_log('✅ ExportAudioInfo.json文件重新导入成功，信息已更新');
                                // 更新表格显示
                                update_table(reimportResult.tasks);
                                // 更新文件路径输入框
                                document.getElementById('file-path').value = result.info_file;
                            } else {
                                add_log('❌ ExportAudioInfo.json文件重新导入失败: ' + reimportResult.error);
                            }
                        });
                    }
                } else {
                    add_log('❌ 音频导出失败: ' + result.error);
                }
            });
        }
        
        // 切换字幕展开/折叠
        function toggle_subtitles(index) {
            const row = document.getElementById(`subtitle-row-${index}`);
            const button = event.target;
            
            if (row.style.display === 'none') {
                // 展开
                row.style.display = '';
                button.textContent = '收起';
                // 加载字幕
                load_subtitles(index);
            } else {
                // 折叠
                row.style.display = 'none';
                button.textContent = '展开';
            }
        }
        
        // 加载字幕
        function load_subtitles(index) {
            window.pywebview.api.get_subtitles(index).then(function(result) {
                const container = document.getElementById(`subtitle-container-${index}`);
                if (result.success) {
                    const subtitles = result.subtitles;
                    let html = `
                        <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd; margin: 0 -10px;">
                            <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
                                <tr>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 150px;">时间戳</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: auto;">字幕内容</th>
                                    <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 80px;">状态</th>
                                    <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 120px;">操作</th>
                                </tr>
                    `;
                    
                    if (subtitles.length === 0) {
                        html += `
                            <tr>
                                <td colspan="4" style="padding: 10px; text-align: center; color: #666;">无字幕内容</td>
                            </tr>
                        `;
                    } else {
                        subtitles.forEach((subtitle, subIndex) => {
                            const statusClass = subtitle.status === '已通过' ? 'status-passed' : 'status-failed';
                            html += `
                                <tr>
                                    <td style="padding: 5px; border-bottom: 1px solid #eee; width: 150px;">
                                        <input type="text" value="${subtitle.timestamp}" readonly style="width: 100%; border: 1px solid #ddd; border-radius: 3px; padding: 3px; font-size: 14px; box-sizing: border-box;">
                                    </td>
                                    <td style="padding: 5px; border-bottom: 1px solid #eee; width: auto;">
                                        <input type="text" value="${subtitle.text}" readonly style="width: 100%; border: 1px solid #ddd; border-radius: 3px; padding: 3px; font-size: 14px; box-sizing: border-box;">
                                    </td>
                                    <td style="padding: 5px; text-align: center; border-bottom: 1px solid #eee; width: 80px;">
                                        <span class="${statusClass}">${subtitle.status}</span>
                                    </td>
                                    <td style="padding: 5px; text-align: center; border-bottom: 1px solid #eee; width: 120px;">
                                        <div style="display: flex; justify-content: center; gap: 5px;">
                                            <button class="button-small" onclick="pass_subtitle(${index}, ${subIndex})">通过</button>
                                            <button class="button-small" onclick="revert_subtitle(${index}, ${subIndex})">撤回</button>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        });
                    }
                    
                    html += `
                            </table>
                        </div>
                    `;
                    
                    container.innerHTML = html;
                } else {
                    container.innerHTML = `
                        <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2;">时间戳</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2;">字幕内容</th>
                                    <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 80px;">状态</th>
                                    <th style="padding: 5px; text-align: center; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 100px;">操作</th>
                                </tr>
                                <tr>
                                    <td colspan="4" style="padding: 10px; text-align: center; color: #666;">${result.error}</td>
                                </tr>
                            </table>
                        </div>
                    `;
                }
            });
        }
        
        // 通过字幕
        function pass_subtitle(index, subIndex) {
            window.pywebview.api.pass_subtitle(index, subIndex).then(function(result) {
                if (result.success) {
                    // 重新加载字幕以更新状态
                    load_subtitles(index);
                }
            });
        }
        
        // 撤回字幕
        function revert_subtitle(index, subIndex) {
            window.pywebview.api.revert_subtitle(index, subIndex).then(function(result) {
                if (result.success) {
                    // 重新加载字幕以更新状态
                    load_subtitles(index);
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
            "音频批量转换工具",
            html=self.html,
            width=1200,
            height=800,
            resizable=True
        )
        
        # 暴露Python函数给JavaScript
        self.window.expose(
            self.select_file,
            self.set_audio_server_url,
            self.set_subtitle_server_url,
            self.select_output_folder,
            self.batch_convert,
            self.play_audio,
            self.pass_task,
            self.revert_task,
            self.export_audio,
            self.get_subtitles,
            self.pass_subtitle,
            self.revert_subtitle,
            self.batch_convert_subtitles,
            self.reimport_json_file
        )
        
        # 启动GUI
        webview.start()
    
    def select_output_folder(self):
        """
        选择输出文件夹
        """
        try:
            # 打开文件夹选择对话框
            # 使用与select_file方法相同的枚举常量
            folder_path = self.window.create_file_dialog(
                webview.FileDialog.FOLDER,
                allow_multiple=False
            )
            
            # 检查是否取消选择
            if folder_path is None:
                return {"success": False, "error": "未选择文件夹"}
            
            # 确保folder_path是字符串类型
            if isinstance(folder_path, tuple) or isinstance(folder_path, list):
                if len(folder_path) > 0:
                    folder_path = folder_path[0]
                else:
                    return {"success": False, "error": "未选择文件夹"}
            
            if not isinstance(folder_path, str):
                return {"success": False, "error": f"无效的文件夹路径类型: {type(folder_path)}"}
            
            if not folder_path:
                return {"success": False, "error": "未选择文件夹"}
            
            # 验证文件夹是否存在
            if not os.path.exists(folder_path):
                # 如果文件夹不存在，创建它
                try:
                    os.makedirs(folder_path, exist_ok=True)
                except Exception as e:
                    return {"success": False, "error": f"创建文件夹失败: {str(e)}"}
            
            if not os.path.isdir(folder_path):
                return {"success": False, "error": "选择的路径不是文件夹"}
            
            # 保存输出文件夹路径
            self.output_folder = folder_path
            
            return {
                "success": True,
                "folder_path": folder_path
            }
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件夹选择失败: {str(e)}\n详细错误: {error_detail}"}
    
    def select_file(self):
        """
        选择JSON文件
        """
        try:
            # 打开文件对话框
            # 使用最新的FileDialog.OPEN常量替代已过时的OPEN_DIALOG
            file_path = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False
                # 暂时移除file_types参数，避免解析错误
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
            
            # 保存文件路径
            self.json_file_path = file_path
            
            # 生成任务列表
            self.tasks = []
            for i, item in enumerate(json_data):
                # 从JSON文件中读取音频路径
                original_audio_path = item.get("audio", item.get("audio_path", None))
                
                task = {
                    "id": i,
                    "text": item["text"],
                    "duration": 0,
                    "status": "未通过",
                    "audio_path": original_audio_path,  # 初始使用JSON中的音频路径
                    "original_audio_path": original_audio_path,  # 保存原始音频路径
                    "chapter": item.get("chapter", item.get("Chapter", "")),
                    "description": item.get("description", item.get("Description", "")),
                    "subtitles": [],  # 字幕列表
                    "srt_path": item.get("SRT_Path", item.get("srt_path", None))  # 字幕文件路径
                }
                self.tasks.append(task)
            
            # 将所有对象的text字段抽取出来保存为同名的.txt文件
            txt_file_path = os.path.splitext(file_path)[0] + '.txt'
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                for item in json_data:
                    f.write(item["text"] + '\n')
            
            return {
                "success": True,
                "file_path": file_path,
                "tasks": self.tasks
            }
            
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON文件格式无效: {str(e)}"}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件导入失败: {str(e)}\n详细错误: {error_detail}"}
    
    def set_audio_server_url(self, *args):
        """
        设置转音频服务器地址
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                server_url = args[0][0]
            elif len(args) == 1:
                server_url = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(server_url, str):
                return {"success": False, "error": f"无效的服务器地址类型: {type(server_url)}"}
            
            if not server_url:
                return {"success": False, "error": "服务器地址不能为空"}
            
            if not re.match(r'^http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+/$', server_url):
                return {"success": False, "error": "无效的服务器地址格式"}
            
            self.audio_server_url = server_url
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置服务器地址失败: {str(e)}"}
    
    def set_subtitle_server_url(self, *args):
        """
        设置字幕服务器地址
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                server_url = args[0][0]
            elif len(args) == 1:
                server_url = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(server_url, str):
                return {"success": False, "error": f"无效的服务器地址类型: {type(server_url)}"}
            
            if not server_url:
                return {"success": False, "error": "服务器地址不能为空"}
            
            if not re.match(r'^http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+/$', server_url):
                return {"success": False, "error": "无效的服务器地址格式"}
            
            self.subtitle_server_url = server_url
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置服务器地址失败: {str(e)}"}
    
    def batch_convert_subtitles(self, *args):
        """
        批量转换字幕
        """
        try:
            if not self.subtitle_server_url:
                return {"success": False, "error": "未设置字幕服务器地址"}
            
            if not self.json_file_path:
                return {"success": False, "error": "未导入JSON文件"}
            
            if not self.output_folder:
                return {"success": False, "error": "未设置输出文件夹"}
            
            # 导入BuzzAPI
            try:
                from BuzzAPI import batch_transcribe_from_json
            except ImportError:
                return {"success": False, "error": "BuzzAPI模块导入失败"}
            
            # 执行批量转换字幕
            print(f"开始批量转换字幕: {self.json_file_path}")
            print(f"字幕服务器: {self.subtitle_server_url}")
            print(f"输出文件夹: {self.output_folder}")
            
            # 调用BuzzAPI的批量转换函数
            result = batch_transcribe_from_json(
                server_url=self.subtitle_server_url,
                json_file=self.json_file_path,
                output_folder=self.output_folder,
                max_wait=600
            )
            
            if result:
                return {
                    "success": True,
                    "success_count": "未知",  # 需要根据BuzzAPI的返回值调整
                    "error_count": 0
                }
            else:
                return {"success": False, "error": "批量转换字幕失败"}
                
        except Exception as e:
            print(f"批量转换字幕异常: {str(e)}")
            return {"success": False, "error": f"批量转换字幕失败: {str(e)}"}
    
    def reimport_json_file(self, *args):
        """
        重新导入JSON文件以更新信息
        
        Args:
            file_path (str, optional): 要重新导入的JSON文件路径
        """
        try:
            # 处理参数
            file_path = None
            if args:
                if len(args) == 1 and isinstance(args[0], (tuple, list)):
                    if args[0]:
                        file_path = args[0][0]
                elif len(args) == 1:
                    file_path = args[0]
            
            # 确定使用哪个文件路径
            if file_path:
                # 使用传入的文件路径
                current_file_path = file_path
                # 更新self.json_file_path
                self.json_file_path = file_path
            else:
                # 使用默认的文件路径
                if not self.json_file_path:
                    return {"success": False, "error": "未导入JSON文件"}
                current_file_path = self.json_file_path
            
            # 读取并验证JSON文件
            with open(current_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 验证每个对象是否包含text字段
            for item in json_data:
                if not isinstance(item, dict):
                    return {"success": False, "error": f"JSON文件格式无效：包含非对象元素"}
                if "text" not in item:
                    return {"success": False, "error": "JSON文件无效：缺少text字段"}
                if not isinstance(item["text"], str):
                    return {"success": False, "error": "JSON文件无效：text字段必须是字符串"}
            
            # 生成任务列表
            self.tasks = []
            for i, item in enumerate(json_data):
                # 从JSON文件中读取音频路径
                original_audio_path = item.get("audio", item.get("audio_path", None))
                
                task = {
                    "id": i,
                    "text": item["text"],
                    "duration": 0,
                    "status": "未通过",
                    "audio_path": original_audio_path,  # 初始使用JSON中的音频路径
                    "original_audio_path": original_audio_path,  # 保存原始音频路径
                    "chapter": item.get("chapter", item.get("Chapter", "")),
                    "description": item.get("description", item.get("Description", "")),
                    "subtitles": [],  # 字幕列表
                    "srt_path": item.get("SRT_Path", item.get("srt_path", None))  # 字幕文件路径
                }
                self.tasks.append(task)
            
            return {
                "success": True,
                "tasks": self.tasks
            }
            
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON文件格式无效: {str(e)}"}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件重新导入失败: {str(e)}"}


    def batch_convert(self, *args):
        """
        批量转换
        """
        try:
            if not self.audio_server_url:
                return {"success": False, "error": "未设置转音频服务器地址"}
            
            if not self.tasks:
                return {"success": False, "error": "没有任务需要转换"}
            
            # 初始化转换器
            self.converter = AudioConverter(server_url=self.audio_server_url)
            
            # 转换任务
            success_count = 0
            error_count = 0
            task_results = []
            
            # 过滤出状态为"未通过"的任务
            pending_tasks = [task for task in self.tasks if task["status"] == "未通过"]
            total_pending = len(pending_tasks)
            
            if total_pending == 0:
                return {"success": False, "error": "没有未通过的任务需要转换"}
            
            for i, task in enumerate(pending_tasks):
                try:
                    # 获取任务在self.tasks中的原始索引
                    original_index = self.tasks.index(task)
                    
                    # 调用转换函数
                    result = self.converter.ConvertBySingleText(task["text"])
                    
                    if "error" not in result or result["error"] is None:
                        # 转换成功
                        success_count += 1
                        audio_path = result.get("local_audio_path")
                        
                        # 如果设置了输出文件夹，将音频文件移动到该文件夹
                        if self.output_folder:
                            import shutil
                            import os
                            # 获取文件名
                            audio_filename = os.path.basename(audio_path)
                            # 生成新的保存路径
                            new_audio_path = os.path.join(self.output_folder, audio_filename)
                            # 移动文件
                            shutil.move(audio_path, new_audio_path)
                            # 更新audio_path为新路径
                            audio_path = new_audio_path
                        
                        task_results.append({"success": True, "audio_path": audio_path, "index": original_index})
                        
                        # 更新audio_path和duration
                        self.tasks[original_index]["audio_path"] = audio_path
                        
                        # 获取并更新音频时长
                        duration = self.get_audio_duration(audio_path)
                        self.tasks[original_index]["duration"] = duration
                        
                        # 更新GUI中的时长显示
                        self.window.evaluate_js(f"document.getElementById('duration-{original_index}').value = {duration}")
                        
                        # 更新日志
                        message = f"✅ 第 {i+1}/{total_pending} 条转换成功，时长: {duration}秒"
                        self.window.evaluate_js(f"add_log({json.dumps(message)})")
                    else:
                        # 转换失败
                        error_count += 1
                        task_results.append({"success": False, "error": result["error"], "index": original_index})
                        
                        # 更新日志
                        error_message = f"❌ 第 {i+1}/{total_pending} 条转换失败: {result['error']}"
                        self.window.evaluate_js(f"add_log({json.dumps(error_message)})")
                        
                except Exception as e:
                    error_count += 1
                    task_results.append({"success": False, "error": str(e), "index": original_index})
                    
                    # 更新日志
                    error_message = f"❌ 第 {i+1}/{total_pending} 条转换异常: {str(e)}"
                    self.window.evaluate_js(f"add_log({json.dumps(error_message)})")
            
            return {
                "success": True,
                "success_count": success_count,
                "error_count": error_count,
                "task_results": task_results
            }
        except Exception as e:
            return {"success": False, "error": f"批量转换失败: {str(e)}"}

    def play_audio(self, *args):
        """
        播放音频
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                index = args[0][0]
            elif len(args) == 1:
                index = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            
            if index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            task = self.tasks[index]
            
            # 优先使用转换后的音频路径
            audio_to_play = task["audio_path"]
            
            # 检查音频文件是否存在
            if not audio_to_play or not os.path.exists(audio_to_play):
                # 如果转换后的音频不存在，尝试使用原始音频路径
                if task.get("original_audio_path") and os.path.exists(task["original_audio_path"]):
                    audio_to_play = task["original_audio_path"]
                else:
                    return {"success": False, "error": "没有可用的音频文件"}
            
            # 使用系统默认播放器播放音频
            subprocess.Popen([audio_to_play], shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pass_task(self, *args):
        """
        通过任务
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                index = args[0][0]
            elif len(args) == 1:
                index = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            
            if index < 0 or index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            # 检查是否有音频文件绑定
            if not self.tasks[index]["audio_path"]:
                return {"success": False, "error": "没有音频文件"}
            
            # 更新任务状态
            self.tasks[index]["status"] = "已通过"
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def revert_task(self, *args):
        """
        撤回任务
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                index = args[0][0]
            elif len(args) == 1:
                index = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            
            if index < 0 or index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            # 检查是否有音频文件绑定
            if not self.tasks[index]["audio_path"]:
                return {"success": False, "error": "没有音频文件"}
            
            # 更新任务状态
            self.tasks[index]["status"] = "未通过"
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_audio_duration(self, audio_path):
        """
        获取音频文件的时长，单位：秒
        """
        try:
            if not audio_path or not os.path.exists(audio_path):
                return 0
            
            # 使用wave模块获取WAV文件时长
            with wave.open(audio_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return round(duration, 2)
        except Exception as e:
            return 0
    
    def get_subtitles(self, *args):
        """
        获取字幕内容
        """
        try:
            # 处理参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                index = args[0][0]
            elif len(args) == 1:
                index = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            
            if index < 0 or index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            task = self.tasks[index]
            
            # 尝试获取SRT文件路径
            srt_path = task.get("srt_path")
            
            # 打印调试信息
            print(f"调试: 任务 {index} 的srt_path: {srt_path}")
            
            # 如果没有SRT路径，尝试从音频路径生成
            if not srt_path and task.get("audio_path"):
                audio_dir = os.path.dirname(task["audio_path"])
                audio_name = os.path.splitext(os.path.basename(task["audio_path"]))[0]
                srt_path = os.path.join(audio_dir, f"{audio_name}.srt")
                print(f"调试: 从音频路径生成的srt_path: {srt_path}")
            
            # 检查SRT文件是否存在
            if not srt_path:
                print(f"调试: 没有找到SRT文件路径")
                return {"success": True, "subtitles": []}
            
            # 规范化路径格式
            srt_path = os.path.normpath(srt_path)
            print(f"调试: 规范化后的srt_path: {srt_path}")
            
            if not os.path.exists(srt_path):
                print(f"调试: SRT文件不存在: {srt_path}")
                # 尝试其他可能的路径
                # 1. 检查当前目录
                current_dir_srt = os.path.join(os.getcwd(), os.path.basename(srt_path))
                if os.path.exists(current_dir_srt):
                    print(f"调试: 在当前目录找到SRT文件: {current_dir_srt}")
                    srt_path = current_dir_srt
                # 2. 检查output_audio目录
                output_audio_srt = os.path.join("output_audio", os.path.basename(srt_path))
                if os.path.exists(output_audio_srt):
                    print(f"调试: 在output_audio目录找到SRT文件: {output_audio_srt}")
                    srt_path = output_audio_srt
                else:
                    return {"success": True, "subtitles": []}
            
            print(f"调试: 最终使用的SRT文件路径: {srt_path}")
            
            # 读取并解析SRT文件
            subtitles = []
            try:
                with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 改进的SRT解析
                lines = content.strip().split('\n')
                i = 0
                while i < len(lines):
                    # 跳过空行
                    if not lines[i].strip():
                        i += 1
                        continue
                    
                    # 尝试解析序号
                    try:
                        int(lines[i].strip())
                        i += 1
                        
                        # 解析时间戳
                        if i < len(lines):
                            timestamp_line = lines[i].strip()
                            if ' --> ' in timestamp_line:
                                i += 1
                                
                                # 解析字幕内容
                                text_lines = []
                                while i < len(lines) and not lines[i].strip().isdigit():
                                    text_lines.append(lines[i].strip())
                                    i += 1
                                
                                text = ' '.join(text_lines)
                                if text:
                                    # 检查字幕状态
                                    subtitle_status = "未通过"
                                    # 尝试从任务的subtitles列表中获取状态
                                    if "subtitles" in task:
                                        for sub in task["subtitles"]:
                                            if sub.get("index") == len(subtitles):
                                                subtitle_status = sub.get("status", "未通过")
                                                break
                                    
                                    subtitles.append({
                                        "index": len(subtitles),
                                        "timestamp": timestamp_line,
                                        "text": text,
                                        "status": subtitle_status
                                    })
                    except ValueError:
                        i += 1
            except Exception as e:
                print(f"调试: 解析SRT文件失败: {str(e)}")
                return {"success": True, "subtitles": []}
            
            # 更新任务的字幕信息
            task["subtitles"] = subtitles
            
            print(f"调试: 解析到 {len(subtitles)} 条字幕")
            return {"success": True, "subtitles": subtitles}
        except Exception as e:
            print(f"调试: 获取字幕异常: {str(e)}")
            return {"success": False, "error": f"获取字幕失败: {str(e)}"}
    
    def pass_subtitle(self, *args):
        """
        通过字幕
        """
        try:
            # 处理参数
            if len(args) == 2:
                if isinstance(args[0], (tuple, list)):
                    index, sub_index = args[0][0], args[1]
                else:
                    index, sub_index = args[0], args[1]
            elif len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                index, sub_index = args[0][0], args[0][1]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            if not isinstance(sub_index, int):
                sub_index = int(sub_index)
            
            if index < 0 or index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            task = self.tasks[index]
            
            # 确保subtitles列表存在
            if "subtitles" not in task:
                task["subtitles"] = []
            
            # 更新字幕状态
            found = False
            for sub in task["subtitles"]:
                if sub.get("index") == sub_index:
                    sub["status"] = "已通过"
                    found = True
                    break
            
            # 如果没找到，添加新的字幕状态
            if not found:
                task["subtitles"].append({
                    "index": sub_index,
                    "status": "已通过"
                })
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"通过字幕失败: {str(e)}"}
    
    def revert_subtitle(self, *args):
        """
        撤回字幕
        """
        try:
            # 处理参数
            if len(args) == 2:
                if isinstance(args[0], (tuple, list)):
                    index, sub_index = args[0][0], args[1]
                else:
                    index, sub_index = args[0], args[1]
            elif len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                index, sub_index = args[0][0], args[0][1]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(index, int):
                index = int(index)
            if not isinstance(sub_index, int):
                sub_index = int(sub_index)
            
            if index < 0 or index >= len(self.tasks):
                return {"success": False, "error": "无效的任务索引"}
            
            task = self.tasks[index]
            
            # 确保subtitles列表存在
            if "subtitles" not in task:
                task["subtitles"] = []
            
            # 更新字幕状态
            found = False
            for sub in task["subtitles"]:
                if sub.get("index") == sub_index:
                    sub["status"] = "未通过"
                    found = True
                    break
            
            # 如果没找到，添加新的字幕状态
            if not found:
                task["subtitles"].append({
                    "index": sub_index,
                    "status": "未通过"
                })
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"撤回字幕失败: {str(e)}"}
    
    def export_audio(self, *args):
        """
        导出音频
        """
        try:
            # 检查所有任务是否都已通过
            for task in self.tasks:
                if task["status"] != "已通过":
                    return {"success": False, "error": "存在未通过的音频，无法导出"}
            
            if not self.tasks:
                return {"success": False, "error": "没有任务需要导出"}
            
            # 检查所有任务是否都有音频文件
            for task in self.tasks:
                if not task["audio_path"] or not os.path.exists(task["audio_path"]):
                    return {"success": False, "error": f"任务 {task['id']} 缺少音频文件"}
            
            # 确定导出文件保存路径
            if self.output_folder:
                base_audio_path = os.path.join(self.output_folder, "ExportAudio.wav")
                base_info_path = os.path.join(self.output_folder, "ExportAudioInfo.json")
            else:
                base_audio_path = "ExportAudio.wav"
                base_info_path = "ExportAudioInfo.json"
            
            # 处理同名文件备份
            import time
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            
            # 备份音频文件
            if os.path.exists(base_audio_path):
                backup_audio_path = f"{os.path.splitext(base_audio_path)[0]}_{timestamp}.wav"
                import shutil
                shutil.copy2(base_audio_path, backup_audio_path)
                print(f"备份音频文件: {backup_audio_path}")
            
            # 备份信息文件
            if os.path.exists(base_info_path):
                backup_info_path = f"{os.path.splitext(base_info_path)[0]}_{timestamp}.json"
                import shutil
                shutil.copy2(base_info_path, backup_info_path)
                print(f"备份信息文件: {backup_info_path}")
            
            export_audio_path = base_audio_path
            export_info_path = base_info_path
            
            # 读取第一个音频文件的参数
            first_audio = self.tasks[0]["audio_path"]
            with wave.open(first_audio, 'rb') as wf:
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                comptype = wf.getcomptype()
                compname = wf.getcompname()
            
            # 打开输出文件
            with wave.open(export_audio_path, 'wb') as output:
                output.setnchannels(nchannels)
                output.setsampwidth(sampwidth)
                output.setframerate(framerate)
                output.setcomptype(comptype, compname)
                
                # 逐个读取并写入音频数据
                for task in self.tasks:
                    with wave.open(task["audio_path"], 'rb') as wf:
                        # 检查音频参数是否一致
                        if (wf.getnchannels() != nchannels or
                            wf.getsampwidth() != sampwidth or
                            wf.getframerate() != framerate):
                            return {"success": False, "error": f"任务 {task['id']} 的音频参数与其他音频不一致"}
                        
                        # 读取并写入音频数据
                        output.writeframes(wf.readframes(wf.getnframes()))
            
            # 生成导出信息JSON
            export_info = []
            for task in self.tasks:
                # 使用绝对路径作为audio字段
                absolute_audio_path = os.path.abspath(task["audio_path"])
                export_info.append({
                    "text": task["text"],
                    "audio": absolute_audio_path,
                    "duration": task["duration"],
                    "chapter": task["chapter"],
                    "description": task["description"]
                })
            
            with open(export_info_path, 'w', encoding='utf-8') as f:
                json.dump(export_info, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "audio_file": export_audio_path,
                "info_file": export_info_path
            }
        except Exception as e:
            return {"success": False, "error": f"导出失败: {str(e)}"}

# 运行GUI
if __name__ == "__main__":
    app = AudioConverterGUI()
    app.start()
