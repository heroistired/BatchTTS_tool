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
        self.server_url = ""
        self.json_file_path = ""
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
            
            <!-- 服务器地址 -->
            <div class="form-row">
                <label for="server-url">服务器地址：</label>
                <input type="text" id="server-url" placeholder="http://192.168.31.194:9872/">
                <button onclick="set_server_url()">设定服务器地址</button>
            </div>
        </div>
        
        <!-- 操作区 -->
        <div class="section">
            <div class="section-title">操作区</div>
            
            <!-- 批量转换和导出 -->
            <div class="form-row">
                <label for="convert-btn">音频操作：</label>
                <button id="convert-btn" onclick="batch_convert()" style="background-color: #2196F3;">批量转换</button>
                <button id="export-btn" onclick="export_audio()" style="background-color: #FF9800; margin-left: 10px;">导出</button>
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
            });
        }
        
        // 设置服务器地址
        function set_server_url() {
            const serverUrl = document.getElementById('server-url').value;
            window.pywebview.api.set_server_url(serverUrl).then(function(result) {
                if (result.success) {
                    add_log('✅ 服务器地址设置成功');
                } else {
                    add_log('❌ 服务器地址无效');
                }
            });
        }
        
        // 批量转换
        function batch_convert() {
            const serverUrl = document.getElementById('server-url').value;
            if (!serverUrl) {
                add_log('⚠️ 请先设置服务器地址');
                return;
            }
            
            // 获取所有任务文本 - 现在使用textarea
            const tasks = [];
            const table = document.getElementById('task-table');
            const rows = table.rows;
            
            for (let i = 1; i < rows.length; i++) {
                const textArea = document.getElementById(`text-${i-1}`);
                tasks.push(textArea.value);
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
                } else {
                    add_log('❌ 音频导出失败: ' + result.error);
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
            self.set_server_url,
            self.batch_convert,
            self.play_audio,
            self.pass_task,
            self.revert_task,
            self.export_audio
        )
        
        # 启动GUI
        webview.start()
    
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
                task = {
                    "id": i,
                    "text": item["text"],
                    "duration": 0,
                    "status": "未通过",
                    "audio_path": None
                }
                self.tasks.append(task)
            
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
    
    def set_server_url(self, *args):
        """
        设置服务器地址
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
            
            self.server_url = server_url
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"设置服务器地址失败: {str(e)}"}

    def batch_convert(self, *args):
        """
        批量转换
        """
        try:
            if not self.server_url:
                return {"success": False, "error": "未设置服务器地址"}
            
            if not self.tasks:
                return {"success": False, "error": "没有任务需要转换"}
            
            # 初始化转换器
            self.converter = AudioConverter(server_url=self.server_url)
            
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
                        task_results.append({"success": True, "audio_path": audio_path, "index": original_index})
                        
                        # 更新audio_path和duration
                        self.tasks[original_index]["audio_path"] = audio_path
                        
                        # 获取并更新音频时长
                        duration = self.get_audio_duration(audio_path)
                        self.tasks[original_index]["duration"] = duration
                        
                        # 更新GUI中的时长显示
                        self.window.evaluate_js(f"document.getElementById('duration-{original_index}').value = {duration}")
                        
                        # 更新日志
                        self.window.evaluate_js(f"add_log('✅ 第 {i+1}/{total_pending} 条转换成功，时长: {duration}秒')")
                    else:
                        # 转换失败
                        error_count += 1
                        task_results.append({"success": False, "error": result["error"], "index": original_index})
                        
                        # 更新日志
                        self.window.evaluate_js(f"add_log('❌ 第 {i+1}/{total_pending} 条转换失败: {result['error']}')")
                        
                except Exception as e:
                    error_count += 1
                    task_results.append({"success": False, "error": str(e), "index": original_index})
                    
                    # 更新日志
                    self.window.evaluate_js(f"add_log('❌ 第 {i+1}/{total_pending} 条转换异常: {str(e)}')")
            
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
            
            if not task["audio_path"]:
                return {"success": False, "error": "没有音频文件"}
            
            # 使用系统默认播放器播放音频
            subprocess.Popen([task["audio_path"]], shell=True)
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
            
            # 拼接音频文件
            export_audio_path = "ExportAudio.wav"
            
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
                audio_filename = os.path.basename(task["audio_path"])
                export_info.append({
                    "text": task["text"],
                    "audio": audio_filename,
                    "duration": task["duration"]
                })
            
            export_info_path = "ExportAudioInfo.json"
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
