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
        self.video_server_url = ""
        self.json_file_path = ""
        self.summary_file_path = ""
        self.autodl_token = ""
        self.instance_id = ""
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
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <button onclick="import_config()" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">导入配置</button>
                <div class="section-title">配置区</div>
            </div>
            
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
            
            <!-- 视频服务器地址 -->
            <div class="form-row">
                <label for="video-server-url">视频服务器地址：</label>
                <input type="text" id="video-server-url" placeholder="http://192.168.31.194:9873/">
                <button onclick="set_video_server_url()">设定视频服务器地址</button>
            </div>
            
            <!-- 输出文件夹 -->
            <div class="form-row">
                <label for="output-folder">输出文件夹：</label>
                <input type="text" id="output-folder" readonly placeholder="请选择输出文件夹">
                <button onclick="select_output_folder()">设置输出文件夹</button>
            </div>
            
            <!-- 视频梗概文件导入 -->
            <div class="form-row">
                <label for="summary-file-path">视频梗概文件路径：</label>
                <input type="text" id="summary-file-path" readonly placeholder="请选择视频梗概文件">
                <button onclick="select_summary_file()">导入视频梗概文件</button>
            </div>
            
            <!-- AutoDL网站token -->
            <div class="form-row">
                <label for="autodl-token">AutoDL网站token：</label>
                <input type="text" id="autodl-token" placeholder="请输入AutoDL网站token">
                <button onclick="set_autodl_token()">设定AutoDL网站token</button>
            </div>
            
            <!-- 实例id -->
            <div class="form-row">
                <label for="instance-id">实例id：</label>
                <input type="text" id="instance-id" placeholder="请输入实例id">
                <button onclick="set_instance_id()">设定实例id</button>
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
                <button id="optimize-subtitle-btn" onclick="optimize_subtitles()" style="background-color: #FF5722; margin-left: 10px;">优化字幕</button>
                <button id="batch-expand-subtitle-btn" onclick="batch_toggle_subtitles()" style="background-color: #607D8B; margin-left: 10px;">批量展开字幕</button>
                <button id="batch-expand-video-btn" onclick="batch_toggle_videos()" style="background-color: #795548; margin-left: 10px;">批量展开视频</button>
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
                        <th class="button-column">视频</th>
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
                const statusClass = task.status === '已通过' ? 'status-passed' : 'status-failed';
                const statusText = task.status === '已通过' ? '已通过' : '未通过';
                statusCell.innerHTML = `<span class="${statusClass}" id="status-${index}">${statusText}</span>`;
                
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
                    
                    // 视频按钮
                    const videoCell = row.insertCell();
                    videoCell.className = 'button-column';
                    videoCell.innerHTML = `<button class="button-small" onclick="toggle_videos(${index})">展开</button>`;
                
            // 添加二级子表格容器行（字幕）
            const subTableRow = table.insertRow();
            subTableRow.id = `subtitle-row-${index}`;
            subTableRow.style.display = 'none';
            const subTableCell = subTableRow.insertCell();
            subTableCell.colSpan = 8;  // 跨越所有列
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
            
            // 添加二级子表格容器行（视频）
            const videoSubTableRow = table.insertRow();
            videoSubTableRow.id = `video-row-${index}`;
            videoSubTableRow.style.display = 'none';
            const videoSubTableCell = videoSubTableRow.insertCell();
            videoSubTableCell.colSpan = 8;  // 跨越所有列
            videoSubTableCell.id = `video-container-${index}`;
            videoSubTableCell.innerHTML = `
                <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd; margin: 0 -10px;">
                    <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
                        <tr>
                            <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: auto;">提示词</th>
                            <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 100px;">图片</th>
                            <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 100px;">视频</th>
                        </tr>
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: center; color: #666;">加载视频信息中...</td>
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
        
        // 设置视频服务器地址
        function set_video_server_url() {
            const serverUrl = document.getElementById('video-server-url').value;
            window.pywebview.api.set_video_server_url(serverUrl).then(function(result) {
                if (result.success) {
                    add_log('✅ 视频服务器地址设置成功');
                } else {
                    add_log('❌ 视频服务器地址无效');
                }
            });
        }
        
        // 选择视频梗概文件
        function select_summary_file() {
            window.pywebview.api.select_summary_file().then(function(result) {
                if (result.success) {
                    document.getElementById('summary-file-path').value = result.file_path;
                    add_log('✅ 成功导入视频梗概文件');
                } else {
                    add_log('❌ 文件导入失败: ' + result.error);
                }
            });
        }
        
        // 设置AutoDL网站token
        function set_autodl_token() {
            const token = document.getElementById('autodl-token').value;
            window.pywebview.api.set_autodl_token(token).then(function(result) {
                if (result.success) {
                    add_log('✅ AutoDL网站token设置成功');
                } else {
                    add_log('❌ AutoDL网站token无效');
                }
            });
        }
        
        // 设置实例id
        function set_instance_id() {
            const instanceId = document.getElementById('instance-id').value;
            window.pywebview.api.set_instance_id(instanceId).then(function(result) {
                if (result.success) {
                    add_log('✅ 实例id设置成功');
                } else {
                    add_log('❌ 实例id无效');
                }
            });
        }
        
        // 导入配置
        function import_config() {
            window.pywebview.api.import_config().then(function(result) {
                if (result.success) {
                    // 更新各个输入框的值
                    if (result.config.AudioServer) {
                        document.getElementById('audio-server-url').value = result.config.AudioServer;
                    }
                    if (result.config.SrtServer) {
                        document.getElementById('subtitle-server-url').value = result.config.SrtServer;
                    }
                    if (result.config.VideoServer) {
                        document.getElementById('video-server-url').value = result.config.VideoServer;
                    }
                    if (result.config.AutoDL_Token) {
                        document.getElementById('autodl-token').value = result.config.AutoDL_Token;
                    }
                    if (result.config.AutoDL_ID) {
                        document.getElementById('instance-id').value = result.config.AutoDL_ID;
                    }
                    add_log('✅ 配置导入成功');
                } else {
                    add_log('❌ 配置导入失败: ' + result.error);
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
        
        // 优化字幕
        function optimize_subtitles() {
            if (!document.getElementById('file-path').value) {
                add_log('⚠️ 请先导入JSON文件');
                return;
            }
            
            // 禁用按钮
            const btn = document.getElementById('optimize-subtitle-btn');
            btn.disabled = true;
            btn.textContent = '优化中...';
            
            // 开始优化字幕
            window.pywebview.api.optimize_subtitles().then(function(result) {
                // 启用按钮
                btn.disabled = false;
                btn.textContent = '优化字幕';
                
                if (result.success) {
                    add_log('🎉 优化字幕完成！');
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
                    add_log('❌ 优化字幕失败: ' + result.error);
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
        
        // 切换视频展开/折叠
        function toggle_videos(index) {
            const row = document.getElementById(`video-row-${index}`);
            const button = event.target;
            
            if (row.style.display === 'none') {
                // 展开
                row.style.display = '';
                button.textContent = '收起';
                // 加载视频信息
                load_videos(index);
            } else {
                // 折叠
                row.style.display = 'none';
                button.textContent = '展开';
            }
        }
        
        // 批量切换字幕展开/折叠
        function batch_toggle_subtitles() {
            const button = document.getElementById('batch-expand-subtitle-btn');
            const isExpanded = button.textContent === '批量收起字幕';
            
            // 遍历所有字幕行
            let i = 0;
            while (true) {
                const subtitleRow = document.getElementById(`subtitle-row-${i}`);
                const subtitleButton = document.querySelector(`button[onclick="toggle_subtitles(${i})"]`);
                
                if (!subtitleRow || !subtitleButton) {
                    break;
                }
                
                if (isExpanded) {
                    // 收起
                    subtitleRow.style.display = 'none';
                    subtitleButton.textContent = '展开';
                } else {
                    // 展开
                    subtitleRow.style.display = '';
                    subtitleButton.textContent = '收起';
                    // 加载字幕
                    load_subtitles(i);
                }
                
                i++;
            }
            
            // 切换按钮文字
            button.textContent = isExpanded ? '批量展开字幕' : '批量收起字幕';
        }
        
        // 批量切换视频展开/折叠
        function batch_toggle_videos() {
            const button = document.getElementById('batch-expand-video-btn');
            const isExpanded = button.textContent === '批量收起视频';
            
            // 遍历所有视频行
            let i = 0;
            while (true) {
                const videoRow = document.getElementById(`video-row-${i}`);
                const videoButton = document.querySelector(`button[onclick="toggle_videos(${i})"]`);
                
                if (!videoRow || !videoButton) {
                    break;
                }
                
                if (isExpanded) {
                    // 收起
                    videoRow.style.display = 'none';
                    videoButton.textContent = '展开';
                } else {
                    // 展开
                    videoRow.style.display = '';
                    videoButton.textContent = '收起';
                    // 加载视频信息
                    load_videos(i);
                }
                
                i++;
            }
            
            // 切换按钮文字
            button.textContent = isExpanded ? '批量展开视频' : '批量收起视频';
        }
        
        // 加载视频信息
        function load_videos(index) {
            window.pywebview.api.get_videos(index).then(function(result) {
                const container = document.getElementById(`video-container-${index}`);
                if (result.success) {
                    const task = result.task;
                    const promptUpdateFlag = task.Prompt_Update_Flag !== undefined ? task.Prompt_Update_Flag : 1;
                    const statusClass = promptUpdateFlag === 0 ? 'status-passed' : 'status-failed';
                    const statusText = promptUpdateFlag === 0 ? '已通过' : '未通过';
                    
                    let html = `
                        <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd; margin: 0 -10px;">
                            <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
                                <tr>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 10%;">提示词</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 45%;">图片</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2; width: 45%;">视频</th>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                        <div style="display: flex; flex-direction: column; gap: 10px;">
                                            <button class="button-small" onclick="view_prompt(${index})")>查看提示词</button>
                                            <button class="button-small ${statusClass}" onclick="toggle_prompt_status(${index})")>${statusText}</button>
                                        </div>
                                    </td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div style="max-width: 320px; max-height: 320px; border: 1px solid #ddd; border-radius: 3px; overflow: hidden; display: flex; align-items: center; justify-content: center; background-color: #f0f0f0;">
                                                ${task.Figure && task.Figure.filepath ? `<div id="image-container-${index}" style="display: flex; align-items: center; justify-content: center;"><span style="color: #666;">加载图片中...</span></div>` : '<span style="color: #666;">无图片</span>'}
                                            </div>
                                            <div>
                                                ${task.Figure_Update_Flag !== undefined ? `
                                                    <button class="button-small ${task.Figure_Update_Flag === 0 ? 'status-passed' : 'status-failed'}" onclick="toggle_figure_status(${index})")">${task.Figure_Update_Flag === 0 ? '已通过' : '未通过'}</button>
                                                ` : '<button class="button-small status-failed" onclick="toggle_figure_status(${index})")">未通过</button>'}
                                            </div>
                                        </div>
                                    </td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div style="max-width: 320px; max-height: 320px; border: 1px solid #ddd; border-radius: 3px; overflow: hidden; display: flex; align-items: center; justify-content: center; background-color: #f0f0f0;">
                                                ${task.Video && task.Video.filepath ? `<div id="video-display-${index}"><span style="color: #666;">加载视频中...</span></div>` : '<span style="color: #666;">无视频</span>'}
                                            </div>
                                            <div>
                                                ${task.Video_Update_Flag !== undefined ? `
                                                    <button class="button-small ${task.Video_Update_Flag === 0 ? 'status-passed' : 'status-failed'}" onclick="toggle_video_status(${index})")">${task.Video_Update_Flag === 0 ? '已通过' : '未通过'}</button>
                                                ` : '<button class="button-small status-failed" onclick="toggle_video_status(${index})")">未通过</button>'}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    `;
                    
                    container.innerHTML = html;
                    
                    // 加载图片
                    if (task.Figure && task.Figure.filepath) {
                        load_image(index, task.Figure.filepath);
                    }
                    
                    // 加载视频
                    if (task.Video && task.Video.filepath) {
                        load_video(index, task.Video.filepath);
                    }
                } else {
                    container.innerHTML = `
                        <div style="padding: 10px; background-color: #f9f9f9; border-top: 1px solid #ddd;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2;">提示词</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2;">图片</th>
                                    <th style="padding: 5px; text-align: left; border-bottom: 1px solid #ddd; background-color: #f2f2f2;">视频</th>
                                </tr>
                                <tr>
                                    <td colspan="3" style="padding: 10px; text-align: center; color: #666;">${result.error}</td>
                                </tr>
                            </table>
                        </div>
                    `;
                }
            });
        }
        
        // 加载图片
        function load_image(index, filepath) {
            window.pywebview.api.get_image_base64(filepath).then(function(result) {
                if (result.success) {
                    const imageContainer = document.getElementById(`image-container-${index}`);
                    if (imageContainer) {
                        // 创建图片对象来获取尺寸
                        const img = new Image();
                        img.onload = function() {
                            // 计算合适的显示尺寸
                            const maxWidth = 320;
                            const maxHeight = 320;
                            let displayWidth = img.width;
                            let displayHeight = img.height;
                            
                            // 计算宽高比
                            const aspectRatio = img.width / img.height;
                            
                            // 根据宽高比调整尺寸
                            if (img.width > maxWidth || img.height > maxHeight) {
                                if (aspectRatio > 1) {
                                    // 宽大于高，以宽度为基准
                                    displayWidth = maxWidth;
                                    displayHeight = Math.min(maxHeight, maxWidth / aspectRatio);
                                } else {
                                    // 高大于宽，以高度为基准
                                    displayHeight = maxHeight;
                                    displayWidth = Math.min(maxWidth, maxHeight * aspectRatio);
                                }
                            }
                            
                            // 设置容器大小
                            imageContainer.style.width = displayWidth + 'px';
                            imageContainer.style.height = displayHeight + 'px';
                            
                            // 显示图片
                            imageContainer.innerHTML = `<img src="data:image/png;base64,${result.base64}" style="width: 100%; height: 100%; object-fit: cover;">`;
                        };
                        img.onerror = function() {
                            imageContainer.innerHTML = `<span style="color: #666;">图片加载失败</span>`;
                        };
                        img.src = 'data:image/png;base64,' + result.base64;
                    }
                } else {
                    const imageContainer = document.getElementById(`image-container-${index}`);
                    if (imageContainer) {
                        imageContainer.innerHTML = `<span style="color: #666;">图片加载失败</span>`;
                    }
                    add_log('❌ 图片加载失败: ' + result.error);
                }
            });
        }
        
        // 查看提示词
        function view_prompt(index) {
            window.pywebview.api.get_prompt_details(index).then(function(result) {
                if (result.success) {
                    const details = result.details;
                    
                    // 创建模态对话框
                    let modalHtml = `
                        <div id="prompt-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.5); z-index: 1000; display: flex; justify-content: center; align-items: center;">
                            <div style="background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.3); max-width: 95%; width: 1600px; max-height: 90%; overflow-y: auto;">
                                <h3>提示词详情</h3>
                                <div style="margin: 10px 0;">
                                    <h4>章节名</h4>
                                    <textarea readonly style="width: 100%; min-height: 50px; padding: 10px; border: 1px solid #ddd; border-radius: 3px;">${details.chapter || '不存在信息'}</textarea>
                                </div>
                                <div style="margin: 10px 0;">
                                    <h4>分镜描述</h4>
                                    <textarea readonly style="width: 100%; min-height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 3px;">${details.description || '不存在信息'}</textarea>
                                </div>
                                <div style="margin: 10px 0;">
                                    <h4>首帧提示词</h4>
                                    <textarea readonly style="width: 100%; min-height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 3px;">${details.prompt_figure || '不存在信息'}</textarea>
                                </div>
                                <div style="margin: 10px 0;">
                                    <h4>视频提示词</h4>
                                    <textarea readonly style="width: 100%; min-height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 3px;">${typeof details.prompt_video === 'object' && details.prompt_video !== null && details.prompt_video.Process ? JSON.stringify(details.prompt_video.Process, null, 2) : (details.prompt_video || '不存在信息')}</textarea>
                                </div>
                                <div style="margin-top: 20px; text-align: right;">
                                    <button onclick="document.getElementById('prompt-modal').remove()">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // 将模态对话框添加到页面
                    document.body.insertAdjacentHTML('beforeend', modalHtml);
                }
            });
        }
        
        // 切换提示词状态
        function toggle_prompt_status(index) {
            window.pywebview.api.toggle_prompt_status(index).then(function(result) {
                if (result.success) {
                    // 重新加载视频信息以更新状态
                    load_videos(index);
                }
            });
        }
        
        // 切换图片状态
        function toggle_figure_status(index) {
            window.pywebview.api.toggle_figure_status(index).then(function(result) {
                if (result.success) {
                    // 重新加载视频信息以更新状态
                    load_videos(index);
                }
            });
        }
        
        // 切换视频状态
        function toggle_video_status(index) {
            window.pywebview.api.toggle_video_status(index).then(function(result) {
                if (result.success) {
                    // 重新加载视频信息以更新状态
                    load_videos(index);
                }
            });
        }
        
        // 加载视频
        function load_video(index, filepath) {
            // 检查文件是否存在
            window.pywebview.api.check_file_exists(filepath).then(function(existsResult) {
                if (existsResult.exists) {
                    const videoContainer = document.getElementById(`video-display-${index}`);
                    if (videoContainer) {
                        // 使用base64编码加载视频
                        window.pywebview.api.get_video_base64(filepath).then(function(result) {
                            if (result.success) {
                                // 创建视频元素
                                const video = document.createElement('video');
                                // 创建data URL
                                const mimeType = result.extension === '.mp4' ? 'video/mp4' : 
                                               result.extension === '.avi' ? 'video/avi' : 
                                               result.extension === '.mov' ? 'video/quicktime' : 
                                               result.extension === '.wmv' ? 'video/x-ms-wmv' : 
                                               result.extension === '.flv' ? 'video/x-flv' : 
                                               result.extension === '.mkv' ? 'video/x-matroska' : 'video/mp4';
                                video.src = `data:${mimeType};base64,${result.base64}`;
                                video.controls = true;
                                video.style.width = '100%';
                                video.style.height = '100%';
                                video.style.objectFit = 'cover';
                                
                                // 清空容器
                                videoContainer.innerHTML = '';
                                
                                // 当视频元数据加载完成后调整容器大小
                                video.onloadedmetadata = function() {
                                    // 计算合适的显示尺寸
                                    const maxWidth = 320;
                                    const maxHeight = 320;
                                    let displayWidth = video.videoWidth;
                                    let displayHeight = video.videoHeight;
                                    
                                    // 计算宽高比
                                    const aspectRatio = video.videoWidth / video.videoHeight;
                                    
                                    // 根据宽高比调整尺寸
                                    if (video.videoWidth > maxWidth || video.videoHeight > maxHeight) {
                                        if (aspectRatio > 1) {
                                            // 宽大于高，以宽度为基准
                                            displayWidth = maxWidth;
                                            displayHeight = Math.min(maxHeight, maxWidth / aspectRatio);
                                        } else {
                                            // 高大于宽，以高度为基准
                                            displayHeight = maxHeight;
                                            displayWidth = Math.min(maxWidth, maxHeight * aspectRatio);
                                        }
                                    }
                                    
                                    // 设置容器大小
                                    videoContainer.style.width = displayWidth + 'px';
                                    videoContainer.style.height = displayHeight + 'px';
                                    videoContainer.style.display = 'flex';
                                    videoContainer.style.alignItems = 'center';
                                    videoContainer.style.justifyContent = 'center';
                                    videoContainer.style.overflow = 'hidden';
                                    
                                    // 添加视频到容器
                                    videoContainer.appendChild(video);
                                };
                                
                                // 处理视频加载错误
                                video.onerror = function() {
                                    videoContainer.innerHTML = '<span style="color: #666;">视频加载失败</span>';
                                    add_log('❌ 视频加载失败: 无法播放视频');
                                };
                            } else {
                                videoContainer.innerHTML = '<span style="color: #666;">视频加载失败</span>';
                                add_log('❌ 视频加载失败: ' + result.error);
                            }
                        });
                    }
                } else {
                    const videoContainer = document.getElementById(`video-display-${index}`);
                    if (videoContainer) {
                        videoContainer.innerHTML = '<span style="color: #666;">视频不存在</span>';
                    }
                    add_log('❌ 视频不存在: ' + filepath);
                }
            });
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
            self.set_video_server_url,
            self.select_output_folder,
            self.select_summary_file,
            self.set_autodl_token,
            self.set_instance_id,
            self.import_config,
            self.batch_convert,
            self.play_audio,
            self.pass_task,
            self.revert_task,
            self.export_audio,
            self.get_subtitles,
            self.get_videos,
            self.get_prompt_details,
            self.toggle_prompt_status,
            self.toggle_figure_status,
            self.toggle_video_status,
            self.get_image_base64,
            self.get_video_base64,
            self.check_file_exists,
            self.pass_subtitle,
            self.revert_subtitle,
            self.batch_convert_subtitles,
            self.reimport_json_file,
            self.optimize_subtitles
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
            
            # 调用通用函数加载JSON文件
            result = self._load_json_file(file_path)
            
            if result["success"]:
                # 更新文件路径
                self.json_file_path = file_path
                # 更新任务列表
                self.tasks = result["tasks"]
                # 返回结果
                return {
                    "success": True,
                    "file_path": file_path,
                    "tasks": result["tasks"]
                }
            else:
                return result
            
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
    
    def set_video_server_url(self, *args):
        """
        设置视频服务器地址
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
            
            self.video_server_url = server_url
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置服务器地址失败: {str(e)}"}
    
    def select_summary_file(self, *args):
        """
        选择视频梗概文件
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
                return {"success": False, "error": f"无效的文件路径类型: {type(file_path)}"}
            
            if not file_path:
                return {"success": False, "error": "未选择文件"}
            
            # 检查文件扩展名
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in [".txt", ".md"]:
                return {"success": False, "error": "只支持.txt和.md格式的文件"}
            
            # 保存文件路径
            self.summary_file_path = file_path
            
            return {
                "success": True,
                "file_path": file_path
            }
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件导入失败: {str(e)}\n详细错误: {error_detail}"}
    
    def set_autodl_token(self, *args):
        """
        设置AutoDL网站token
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                token = args[0][0]
            elif len(args) == 1:
                token = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(token, str):
                return {"success": False, "error": f"无效的token类型: {type(token)}"}
            
            if not token:
                return {"success": False, "error": "token不能为空"}
            
            self.autodl_token = token
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置token失败: {str(e)}"}
    
    def set_instance_id(self, *args):
        """
        设置实例id
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                instance_id = args[0][0]
            elif len(args) == 1:
                instance_id = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(instance_id, str):
                return {"success": False, "error": f"无效的实例id类型: {type(instance_id)}"}
            
            if not instance_id:
                return {"success": False, "error": "实例id不能为空"}
            
            self.instance_id = instance_id
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置实例id失败: {str(e)}"}
    
    def _load_json_file(self, file_path):
        """
        通用的 JSON 文件加载函数
        :param file_path: JSON 文件路径
        :return: 包含成功/失败信息的字典
        """
        try:
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
            
            # 生成任务列表
            new_tasks = []
            for i, item in enumerate(json_data):
                # 从JSON文件中读取音频路径
                original_audio_path = item.get("audio", item.get("audio_path", None))
                # 从JSON文件中读取字幕路径
                new_srt_path = item.get("SRT_Path", item.get("srt_path", None))
                
                # 通过Audio_Update_Flag字段确定状态
                audio_update_flag = item.get("Audio_Update_Flag", 1)
                status = "已通过" if audio_update_flag == 0 else "未通过"
                
                # 创建任务对象
                task = {
                    "id": i,
                    "text": item["text"],
                    "duration": 0,
                    "status": status,
                    "audio_path": original_audio_path,
                    "original_audio_path": original_audio_path,
                    "chapter": item.get("chapter", item.get("Chapter", "")),
                    "description": item.get("description", item.get("Description", "")),
                    "subtitles": [],
                    "srt_path": new_srt_path,
                    "Prompt_Update_Flag": item.get("Prompt_Update_Flag", 1),
                    "Prompt_Figure": item.get("Prompt_Figure", None),
                    "Prompt_Video": item.get("Prompt_Video", None),
                    "Figure": item.get("Figure", None),
                    "Figure_Update_Flag": item.get("Figure_Update_Flag", 1),
                    "Video": item.get("Video", None),
                    "Video_Update_Flag": item.get("Video_Update_Flag", 1),
                    "Audio_Update_Flag": audio_update_flag
                }
                new_tasks.append(task)
            
            # 生成TXT文件
            txt_file_path = os.path.splitext(file_path)[0] + '.txt'
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                for item in json_data:
                    f.write(item["text"] + '\n')
            
            return {
                "success": True,
                "tasks": new_tasks,
                "file_path": file_path
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON文件格式无效: {str(e)}"}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"文件导入失败: {str(e)}\n详细错误: {error_detail}"}
    
    def import_config(self):
        """
        导入配置
        """
        try:
            # 检查脚本同目录下是否存在AllInOneToolConfig.json文件
            config_file_path = os.path.join(os.path.dirname(__file__), "AllInOneToolConfig.json")
            
            if not os.path.exists(config_file_path):
                return {"success": False, "error": "没有找到配置文件"}
            
            # 读取并解析JSON文件
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 检查是否包含所有必要的字段
            required_fields = ["AudioServer", "SrtServer", "VideoServer", "AutoDL_Token", "AutoDL_ID"]
            for field in required_fields:
                if field not in config_data:
                    return {"success": False, "error": "配置文件不完整"}
            
            # 更新配置
            if "AudioServer" in config_data:
                self.audio_server_url = config_data["AudioServer"]
            if "SrtServer" in config_data:
                self.subtitle_server_url = config_data["SrtServer"]
            if "VideoServer" in config_data:
                self.video_server_url = config_data["VideoServer"]
            if "AutoDL_Token" in config_data:
                self.autodl_token = config_data["AutoDL_Token"]
            if "AutoDL_ID" in config_data:
                self.instance_id = config_data["AutoDL_ID"]
            
            return {
                "success": True,
                "config": config_data
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"配置文件格式无效: {str(e)}"}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"success": False, "error": f"导入配置失败: {str(e)}"}

    
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
    
    def optimize_subtitles(self, *args):
        """
        优化字幕
        """
        try:
            if not self.json_file_path:
                return {"success": False, "error": "未导入JSON文件"}
            
            if not self.tasks:
                return {"success": False, "error": "没有任务需要优化"}
            
            # 导入ImproveSrtResultsLLM
            try:
                from ImproveSrtResultsLLM import improve_srt
            except ImportError:
                return {"success": False, "error": "ImproveSrtResultsLLM模块导入失败"}
            
            success_count = 0
            error_count = 0
            total_tasks = len(self.tasks)
            
            # 遍历每一个分镜
            for i, task in enumerate(self.tasks):
                try:
                    # 检查字幕状态是否有未通过的
                    subtitles = task.get("subtitles", [])
                    has_failed_subtitles = any(sub.get("status", "") == "未通过" for sub in subtitles)
                    
                    # 检查是否有SRT文件路径
                    srt_path = task.get("srt_path", None)
                    if not srt_path or not os.path.exists(srt_path):
                        print(f"分镜 {i+1}: 没有找到SRT文件，跳过")
                        error_count += 1
                        continue
                    
                    # 如果有未通过的字幕，进行优化
                    if has_failed_subtitles:
                        print(f"开始优化分镜 {i+1}/{total_tasks}")
                        
                        # 读取SRT文件内容
                        with open(srt_path, 'r', encoding='utf-8') as f:
                            srt_content = f.read()
                        
                        # 获取原始文稿（text字段）
                        original_script = task.get("text", "")
                        if not original_script:
                            print(f"分镜 {i+1}: 没有找到原始文稿，跳过")
                            error_count += 1
                            continue
                        
                        # 调用ImproveSrtResultsLLM进行优化
                        optimized_content = improve_srt(original_script, srt_content)
                        
                        # 将优化后的内容写回SRT文件
                        with open(srt_path, 'w', encoding='utf-8') as f:
                            f.write(optimized_content)
                        
                        print(f"分镜 {i+1}: 字幕优化成功")
                        success_count += 1
                    else:
                        print(f"分镜 {i+1}: 所有字幕都已通过，跳过")
                        
                except Exception as e:
                    print(f"分镜 {i+1}: 优化失败 - {str(e)}")
                    error_count += 1
            
            return {
                "success": True,
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            print(f"优化字幕异常: {str(e)}")
            return {"success": False, "error": f"优化字幕失败: {str(e)}"}
    
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
            
            # 调用通用函数加载JSON文件
            result = self._load_json_file(current_file_path)
            
            if result["success"]:
                # 更新任务列表
                self.tasks = result["tasks"]
                # 返回结果
                return {
                    "success": True,
                    "tasks": result["tasks"]
                }
            else:
                return result
            
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
    
    def get_videos(self, *args):
        """
        获取视频信息
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
            
            task = self.tasks[index]
            return {
                "success": True,
                "task": task
            }
        except Exception as e:
            print(f"调试: 获取视频信息异常: {str(e)}")
            return {"success": False, "error": f"获取视频信息失败: {str(e)}"}
    
    def get_prompt_details(self, *args):
        """
        获取提示词详情
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
            
            task = self.tasks[index]
            details = {
                "chapter": task.get("chapter", None),
                "description": task.get("description", None),
                "prompt_figure": task.get("Prompt_Figure", None),
                "prompt_video": task.get("Prompt_Video", None)
            }
            
            return {
                "success": True,
                "details": details
            }
        except Exception as e:
            print(f"调试: 获取提示词详情异常: {str(e)}")
            return {"success": False, "error": f"获取提示词详情失败: {str(e)}"}
    
    def toggle_prompt_status(self, *args):
        """
        切换提示词状态
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
            
            task = self.tasks[index]
            current_flag = task.get("Prompt_Update_Flag", 1)
            # 切换状态
            new_flag = 0 if current_flag == 1 else 1
            task["Prompt_Update_Flag"] = new_flag
            
            return {
                "success": True,
                "new_status": new_flag
            }
        except Exception as e:
            print(f"调试: 切换提示词状态异常: {str(e)}")
            return {"success": False, "error": f"切换提示词状态失败: {str(e)}"}
    
    def toggle_figure_status(self, *args):
        """
        切换图片状态
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
            
            task = self.tasks[index]
            current_flag = task.get("Figure_Update_Flag", 1)
            # 切换状态
            new_flag = 0 if current_flag == 1 else 1
            task["Figure_Update_Flag"] = new_flag
            
            return {
                "success": True,
                "new_status": new_flag
            }
        except Exception as e:
            print(f"调试: 切换图片状态异常: {str(e)}")
            return {"success": False, "error": f"切换图片状态失败: {str(e)}"}
    
    def get_image_base64(self, *args):
        """
        获取图片的base64编码
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                filepath = args[0][0]
            elif len(args) == 1:
                filepath = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(filepath, str):
                return {"success": False, "error": "无效的文件路径"}
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                return {"success": False, "error": f"文件不存在: {filepath}"}
            
            # 检查文件是否是图片
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                return {"success": False, "error": f"文件不是图片: {filepath}"}
            
            # 读取文件并转换为base64
            with open(filepath, 'rb') as f:
                import base64
                base64_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "success": True,
                "base64": base64_data
            }
        except Exception as e:
            print(f"调试: 获取图片base64异常: {str(e)}")
            return {"success": False, "error": f"获取图片base64失败: {str(e)}"}
    
    def get_video_base64(self, *args):
        """
        获取视频的base64编码
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                filepath = args[0][0]
            elif len(args) == 1:
                filepath = args[0]
            else:
                return {"success": False, "error": f"无效的参数数量: {len(args)}"}
            
            if not isinstance(filepath, str):
                return {"success": False, "error": "无效的文件路径"}
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                return {"success": False, "error": f"文件不存在: {filepath}"}
            
            # 检查文件是否是视频
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']:
                return {"success": False, "error": f"文件不是视频: {filepath}"}
            
            # 读取文件并转换为base64
            with open(filepath, 'rb') as f:
                import base64
                base64_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "success": True,
                "base64": base64_data,
                "extension": ext
            }
        except Exception as e:
            print(f"调试: 获取视频base64异常: {str(e)}")
            return {"success": False, "error": f"获取视频base64失败: {str(e)}"}
    
    def toggle_video_status(self, *args):
        """
        切换视频状态
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
            
            task = self.tasks[index]
            current_flag = task.get("Video_Update_Flag", 1)
            # 切换状态
            new_flag = 0 if current_flag == 1 else 1
            task["Video_Update_Flag"] = new_flag
            
            return {
                "success": True,
                "new_status": new_flag
            }
        except Exception as e:
            print(f"调试: 切换视频状态异常: {str(e)}")
            return {"success": False, "error": f"切换视频状态失败: {str(e)}"}
    
    def check_file_exists(self, *args):
        """
        检查文件是否存在
        """
        try:
            # 处理pywebview可能传递的元组参数
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                filepath = args[0][0]
            elif len(args) == 1:
                filepath = args[0]
            else:
                return {"exists": False}
            
            if not isinstance(filepath, str):
                return {"exists": False}
            
            # 检查文件是否存在
            exists = os.path.exists(filepath)
            return {"exists": exists}
        except Exception as e:
            print(f"调试: 检查文件存在异常: {str(e)}")
            return {"exists": False}
    
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
                # 计算Audio_Update_Flag
                audio_update_flag = 1 if task["status"] == "未通过" else 0
                export_info.append({
                    "text": task["text"],
                    "audio": absolute_audio_path,
                    "duration": task["duration"],
                    "chapter": task["chapter"],
                    "description": task["description"],
                    "Audio_Update_Flag": audio_update_flag
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
