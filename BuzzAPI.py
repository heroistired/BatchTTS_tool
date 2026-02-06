#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buzz转录服务API封装

提供Buzz转录服务的API函数，支持音频文件上传、转换进程查询和字幕文件下载功能。
"""

import requests
import time
import os
import json
from tqdm import tqdm

class BuzzAPI:
    """
Buzz转录服务API类
    
    提供与Buzz转录服务交互的方法，包括音频文件上传、转换进程查询和字幕文件下载。
    """
    
    def __init__(self, base_url):
        """
        初始化BuzzAPI实例
        
        Args:
            base_url (str): Buzz转录服务的基础URL，例如 "http://116.62.7.179:10002"
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_status(self):
        """
        获取服务状态
        
        Returns:
            dict: 包含服务状态信息的字典，例如：
            {
                "is_processing": bool,  # 是否正在处理任务
                "current_task": str,    # 当前任务
                "progress": int,        # 进度百分比
                "last_task_id": str,    # 最后任务ID
                "task_history": list    # 任务历史
            }
            None: 如果获取状态失败
        """
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取状态失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取状态异常: {str(e)}")
            return None
    
    def upload_audio(self, audio_file):
        """
        上传音频文件到转录服务
        
        Args:
            audio_file (str): 音频文件路径
            
        Returns:
            tuple: (成功标志, 任务ID, 消息, SRT文件路径)
                例如：(True, "task_123", "上传成功", "output.srt")
                失败时：(False, None, "错误信息", None)
        """
        if not os.path.exists(audio_file):
            return False, None, f"文件不存在: {audio_file}", None
        
        try:
            # 检查服务状态
            status = self.get_status()
            if status and status['is_processing']:
                return False, None, "服务忙，正在处理其他任务", None
            
            # 读取文件内容
            with open(audio_file, 'rb') as f:
                file_content = f.read()
            
            # 准备文件数据
            files = {'file': (os.path.basename(audio_file), file_content, 'audio/wav')}
            
            # 发送请求
            response = self.session.post(
                f"{self.base_url}/transcribe/upload",
                files=files,
                stream=False
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('task_id'), result.get('message'), result.get('srt_file')
            else:
                return False, None, f"上传失败: {response.status_code} - {response.text}", None
        except Exception as e:
            return False, None, f"上传异常: {str(e)}", None
    
    def wait_for_completion(self, max_wait=300, check_interval=2):
        """
        等待转录完成
        
        Args:
            max_wait (int): 最大等待时间（秒），默认300秒
            check_interval (int): 检查间隔（秒），默认2秒
            
        Returns:
            dict: 完成时的服务状态
            None: 如果超时或出现错误
        """
        start_time = time.time()
        
        print("等待转录完成...")
        
        # 初始化进度条
        with tqdm(total=100, unit='%', desc='转换进度', ncols=80) as pbar:
            last_progress = 0
            
            while time.time() - start_time < max_wait:
                status = self.get_status()
                if not status:
                    time.sleep(check_interval)
                    continue
                
                # 更新进度条
                current_progress = status.get('progress', 0)
                if current_progress > last_progress:
                    pbar.update(current_progress - last_progress)
                    last_progress = current_progress
                
                # 显示详细信息
                current_task = status.get('current_task', '处理中')
                print(f"\r当前任务: {current_task} - 进度: {current_progress}%", end='')
                
                # 检查是否完成
                if not status['is_processing']:
                    print("\n转录已完成")
                    pbar.update(100 - last_progress)  # 确保进度条达到100%
                    return status
                
                time.sleep(check_interval)
            
            print(f"\n超时: 转录在 {max_wait} 秒内未完成")
            return None
    
    def download_srt(self, srt_file, output_folder='.'):
        """
        下载SRT字幕文件
        
        Args:
            srt_file (str): SRT文件路径或文件名
            output_folder (str): 输出文件夹路径，默认当前目录
            
        Returns:
            str: 下载后的文件路径
            None: 如果下载失败
        """
        if not srt_file:
            print("错误: 没有提供SRT文件路径")
            return None
        
        try:
            # 确保输出文件夹存在
            os.makedirs(output_folder, exist_ok=True)
            
            # 下载文件
            response = self.session.get(f"{self.base_url}/download/{srt_file}")
            if response.status_code == 200:
                # 生成下载路径
                filename = f"downloaded_{srt_file}"
                download_path = os.path.join(output_folder, filename)
                
                # 保存文件
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"SRT文件下载成功，保存为: {download_path}")
                print(f"文件大小: {os.path.getsize(download_path)} bytes")
                return download_path
            else:
                print(f"下载失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"下载异常: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_file, output_folder='.', max_wait=300):
        """
        完整的音频转录流程
        
        Args:
            audio_file (str): 音频文件路径
            output_folder (str): 输出文件夹路径，默认当前目录
            max_wait (int): 最大等待时间（秒），默认300秒
            
        Returns:
            str: 下载后的SRT文件路径
            None: 如果转录失败
        """
        print(f"开始转录音频: {audio_file}")
        print("=" * 60)
        
        # 1. 上传音频文件
        print("1. 上传音频文件...")
        success, task_id, message, srt_file = self.upload_audio(audio_file)
        
        if not success:
            print(f"上传失败: {message}")
            return None
        
        print(f"上传成功: {message}")
        if task_id:
            print(f"任务ID: {task_id}")
        
        # 2. 等待转录完成
        print("\n2. 等待转录完成...")
        status = self.wait_for_completion(max_wait=max_wait)
        
        if not status:
            print("转录未完成或超时")
            return None
        
        # 3. 下载SRT文件
        print("\n3. 下载SRT文件...")
        if not srt_file:
            # 如果上传时没有返回SRT文件路径，尝试从状态中获取
            task_history = status.get('task_history', [])
            if task_history:
                last_task = task_history[-1]
                srt_file = last_task.get('srt_file')
        
        if not srt_file:
            print("错误: 未找到SRT文件路径")
            return None
        
        downloaded_path = self.download_srt(srt_file, output_folder)
        
        print("\n" + "=" * 60)
        if downloaded_path:
            print(f"转录完成！SRT文件已保存到: {downloaded_path}")
        else:
            print("转录失败")
        
        return downloaded_path
    
    def batch_transcribe_from_json(self, json_file, output_folder='.', max_wait=300):
        """
        批量转换音频到字幕文件
        
        Args:
            json_file (str): 包含分镜信息的JSON文件路径
            output_folder (str): 输出文件夹路径，默认当前目录
            max_wait (int): 最大等待时间（秒），默认300秒
            
        Returns:
            bool: 批量转换是否成功
        """
        print(f"开始批量转录: {json_file}")
        print("=" * 80)
        
        # 1. 读取JSON文件
        if not os.path.exists(json_file):
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"错误: 读取JSON文件失败 - {str(e)}")
            return False
        
        # 2. 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)
        
        # 3. 遍历分镜对象
        total_scenes = len(data)
        print(f"发现 {total_scenes} 个分镜")
        print("=" * 80)
        
        success_count = 0
        failed_count = 0
        
        # 4. 处理每个分镜
        for i, scene_data in enumerate(data):
            scene_id = f"scene_{i+1}"
            print(f"\n处理分镜: {scene_id}")
            print("-" * 60)
            
            # 4.1 检查SRT_Update_Flag字段
            srt_update_flag = scene_data.get('SRT_Update_Flag', 1)
            if srt_update_flag == 0:
                print(f"分镜 {scene_id} 的SRT_Update_Flag为0，跳过字幕转换")
                continue
            
            # 4.2 检查audio字段
            audio_path = scene_data.get('audio')
            if not audio_path:
                print(f"警告: 分镜 {scene_id} 缺少audio字段，跳过")
                failed_count += 1
                continue
            
            # 4.2 检查音频文件是否存在
            if not os.path.exists(audio_path):
                # 尝试从JSON文件所在目录查找音频文件
                json_dir = os.path.dirname(json_file)
                relative_audio_path = os.path.join(json_dir, audio_path)
                if os.path.exists(relative_audio_path):
                    audio_path = relative_audio_path
                    print(f"使用相对路径找到音频文件: {audio_path}")
                else:
                    print(f"警告: 音频文件不存在 - {audio_path}，跳过")
                    failed_count += 1
                    continue
            
            # 4.3 生成SRT文件名
            audio_filename = os.path.basename(audio_path)
            srt_filename = os.path.splitext(audio_filename)[0] + '.srt'
            srt_path = os.path.join(output_folder, srt_filename)
            
            # 4.4 执行转录
            print(f"转录音频: {audio_filename}")
            result = self.transcribe_audio(audio_path, output_folder, max_wait)
            
            if result:
                # 4.5 重命名SRT文件
                if result != srt_path:
                    try:
                        # 如果目标SRT文件已存在，先删除它
                        if os.path.exists(srt_path):
                            os.remove(srt_path)
                            print(f"删除已存在的SRT文件: {srt_filename}")
                        # 重命名SRT文件
                        os.rename(result, srt_path)
                        print(f"重命名SRT文件: {os.path.basename(result)} -> {srt_filename}")
                    except Exception as e:
                        print(f"警告: 重命名SRT文件失败 - {str(e)}")
                
                # 4.6 更新分镜信息
                scene_data['SRT_Path'] = os.path.abspath(srt_path)
                success_count += 1
            else:
                print(f"失败: 转录分镜 {scene_id} 失败")
                failed_count += 1
            
        print("\n" + "=" * 80)
        print(f"批量转录完成")
        print(f"成功: {success_count} 个")
        print(f"失败: {failed_count} 个")
        print("=" * 80)
        
        # 5. 备份原JSON文件
        json_dir = os.path.dirname(json_file)
        json_basename = os.path.basename(json_file)
        json_name, json_ext = os.path.splitext(json_basename)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(json_dir, f"{json_name}_{timestamp}{json_ext}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"备份原JSON文件: {backup_file}")
        except Exception as e:
            print(f"警告: 备份JSON文件失败 - {str(e)}")
        
        # 6. 写入更新后的JSON文件
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"更新JSON文件: {json_file}")
        except Exception as e:
            print(f"错误: 写入JSON文件失败 - {str(e)}")
            return False
        
        return True

def transcribe_audio(server_url, audio_file, output_folder='.', max_wait=300):
    """
    便捷函数：转录音频文件
    
    Args:
        server_url (str): Buzz转录服务的URL
        audio_file (str): 音频文件路径
        output_folder (str): 输出文件夹路径，默认当前目录
        max_wait (int): 最大等待时间（秒），默认300秒
        
    Returns:
        str: 下载后的SRT文件路径
        None: 如果转录失败
    """
    api = BuzzAPI(server_url)
    return api.transcribe_audio(audio_file, output_folder, max_wait)

def batch_transcribe_from_json(server_url, json_file, output_folder='.', max_wait=300):
    """
    便捷函数：批量转换音频到字幕文件
    
    Args:
        server_url (str): Buzz转录服务的URL
        json_file (str): 包含分镜信息的JSON文件路径
        output_folder (str): 输出文件夹路径，默认当前目录
        max_wait (int): 最大等待时间（秒），默认300秒
        
    Returns:
        bool: 批量转换是否成功
    """
    api = BuzzAPI(server_url)
    return api.batch_transcribe_from_json(json_file, output_folder, max_wait)

def test_buzz_api():
    """
    测试BuzzAPI功能
    
    使用指定的服务器地址、音频文件和输出文件夹测试转录功能
    服务器地址：http://116.62.7.179:10002/
    测试音频：d:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\ExportAudio.wav
    输出文件夹：d:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_audio
    """
    print("测试BuzzAPI功能")
    print("=" * 70)
    
    # 配置参数
    SERVER_URL = "http://116.62.7.179:10002"
    AUDIO_FILE = "d:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\ExportAudio.wav"
    OUTPUT_FOLDER = "d:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\output_audio"
    MAX_WAIT = 600  # 最大等待时间（秒）
    
    print(f"服务器地址: {SERVER_URL}")
    print(f"测试音频: {AUDIO_FILE}")
    print(f"输出文件夹: {OUTPUT_FOLDER}")
    print(f"最大等待时间: {MAX_WAIT}秒")
    print("=" * 70)
    
    # 检查音频文件是否存在
    if not os.path.exists(AUDIO_FILE):
        print(f"错误: 音频文件不存在 - {AUDIO_FILE}")
        return False
    
    # 确保输出文件夹存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    try:
        # 使用便捷函数测试
        print("\n开始转录测试...")
        srt_path = transcribe_audio(
            SERVER_URL,
            AUDIO_FILE,
            output_folder=OUTPUT_FOLDER,
            max_wait=MAX_WAIT
        )
        
        print("\n" + "=" * 70)
        if srt_path:
            print(f"✅ 测试成功！")
            print(f"SRT文件已保存到: {srt_path}")
            return True
        else:
            print(f"❌ 测试失败！")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_transcribe():
    """
    测试批量转录功能
    
    使用指定的服务器地址、JSON文件和输出文件夹进行测试
    """
    # 测试参数
    server_url = "http://116.62.7.179:10002/"
    json_file = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\output_audio\\ExportAudioInfo.json"
    output_folder = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\output_audio"
    max_wait = 600  # 10分钟超时
    
    print("=" * 80)
    print("测试批量转录功能")
    print("=" * 80)
    print(f"服务器地址: {server_url}")
    print(f"JSON文件: {json_file}")
    print(f"输出文件夹: {output_folder}")
    print(f"最大等待时间: {max_wait}秒")
    print("=" * 80)
    
    # 执行批量转录
    result = batch_transcribe_from_json(server_url, json_file, output_folder, max_wait)
    
    print("=" * 80)
    if result:
        print("✅ 批量转录测试成功！")
    else:
        print("❌ 批量转录测试失败！")
    print("=" * 80)

if __name__ == "__main__":
    """
    示例用法
    """
    # 运行测试函数
    # test_buzz_api()
    
    # 测试批量转录功能
    test_batch_transcribe()
    
    # 示例1: 使用类方法
    # print("\n示例1: 使用BuzzAPI类")
    # print("=" * 60)
    # 
    # # 初始化API实例
    # api = BuzzAPI("http://116.62.7.179:10002")
    # 
    # # 测试服务状态
    # print("\n1. 测试服务状态:")
    # status = api.get_status()
    # if status:
    #     print(f"服务状态: {'处理中' if status['is_processing'] else '空闲'}")
    #     print(f"当前任务: {status['current_task']}")
    #     print(f"进度: {status['progress']}%")
    # 
    # # 示例2: 使用便捷函数
    # print("\n示例2: 使用便捷函数")
    # print("=" * 60)
    # 
    # # 查找测试音频文件
    # test_files = []
    # for ext in ['.wav', '.mp3', '.m4a']:
    #     files = [f for f in os.listdir('.') if f.endswith(ext)]
    #     test_files.extend(files)
    # 
    # if test_files:
    #     test_file = test_files[0]
    #     print(f"使用测试文件: {test_file}")
    #     
    #     # 转录音频
    #     output_folder = 'subtitles'
    #     srt_path = transcribe_audio(
    #         "http://116.62.7.179:10002",
    #         test_file,
    #         output_folder=output_folder,
    #         max_wait=600
    #     )
    #     
    #     if srt_path:
    #         print(f"\n最终结果: SRT文件已保存到 {srt_path}")
    #     else:
    #         print("\n最终结果: 转录失败")
    # else:
    #     print("错误: 未找到测试音频文件")
    #     print("请确保当前目录有音频文件（如wav、mp3等）")
