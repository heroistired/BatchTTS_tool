#!/usr/bin/env python3
"""
测试Buzz转录服务
"""

import requests
import time
import os
import sys
from tqdm import tqdm

# 服务URL
BASE_URL = "http://116.62.7.179:10002"

class BuzzServerTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_status(self):
        """测试服务状态接口"""
        print("=== 测试服务状态 ===")
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                status = response.json()
                print(f"服务状态: {'处理中' if status['is_processing'] else '空闲'}")
                print(f"当前任务: {status['current_task']}")
                print(f"进度: {status['progress']}%")
                print(f"最后任务ID: {status['last_task_id']}")
                print(f"任务历史: {len(status['task_history'])} 个任务")
                return True
            else:
                print(f"获取状态失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"测试状态接口异常: {str(e)}")
            return False
    
    def test_upload_transcribe(self, audio_file):
        """测试文件上传和转录功能"""
        print(f"\n=== 测试文件上传和转录: {audio_file} ===")
        
        if not os.path.exists(audio_file):
            print(f"错误: 文件不存在 - {audio_file}")
            return False
        
        try:
            # 检查服务状态
            status_response = self.session.get(f"{self.base_url}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                if status['is_processing']:
                    print("服务忙，正在处理其他任务")
                    return False
            
            # 获取文件大小
            file_size = os.path.getsize(audio_file)
            print(f"文件大小: {file_size} bytes")
            
            # 上传文件（带进度显示）
            print("正在上传文件...")
            
            # 使用简单的文件上传进度显示
            # 先读取文件内容
            with open(audio_file, 'rb') as f:
                file_content = f.read()
            
            # 显示上传进度条
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc='上传进度') as pbar:
                # 模拟上传进度（实际文件已经读取到内存）
                # 这里我们直接将进度设置为100%
                pbar.update(file_size)
                
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
                print(f"\n上传成功，任务ID: {result['task_id']}")
                print(f"消息: {result['message']}")
                
                if result.get('srt_file'):
                    print(f"生成的SRT文件: {result['srt_file']}")
                    return True, result['srt_file']
                else:
                    print("警告: 未返回SRT文件路径")
                    return True, None
            else:
                print(f"\n上传失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False, None
        except Exception as e:
            print(f"\n测试上传功能异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def test_download_srt(self, srt_file):
        """测试SRT文件下载功能"""
        if not srt_file:
            print("无SRT文件可下载")
            return False
        
        print(f"\n=== 测试SRT文件下载: {srt_file} ===")
        try:
            response = self.session.get(f"{self.base_url}/download/{srt_file}")
            if response.status_code == 200:
                # 保存下载的文件
                download_path = f"downloaded_{srt_file}"
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                print(f"SRT文件下载成功，保存为: {download_path}")
                print(f"文件大小: {os.path.getsize(download_path)} bytes")
                return True
            else:
                print(f"下载失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
        except Exception as e:
            print(f"测试下载功能异常: {str(e)}")
            return False
    
    def test_root(self):
        """测试根接口"""
        print("\n=== 测试根接口 ===")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                info = response.json()
                print(f"服务名称: {info['message']}")
                print("可用接口:")
                for endpoint, description in info['endpoints'].items():
                    print(f"  - {endpoint}: {description}")
                return True
            else:
                print(f"获取根接口失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"测试根接口异常: {str(e)}")
            return False

def main():
    """主测试函数"""
    print("Buzz转录服务测试")
    print("=" * 50)
    
    tester = BuzzServerTester(BASE_URL)
    
    # 测试根接口
    tester.test_root()
    
    # 测试服务状态
    tester.test_status()
    
    # 查找测试音频文件
    test_files = []
    for ext in ['.wav', '.mp3', '.m4a']:
        files = [f for f in os.listdir('.') if f.endswith(ext)]
        test_files.extend(files)
    
    if not test_files:
        print("\n错误: 未找到测试音频文件")
        print("请确保当前目录有音频文件（如wav、mp3等）")
        return 1
    
    # 选择第一个测试文件
    test_file = test_files[0]
    print(f"\n使用测试文件: {test_file}")
    
    # 测试上传和转录
    success, srt_file = tester.test_upload_transcribe(test_file)
    
    if success:
        # 等待转录完成
        print("\n=== 等待转录完成 ===")
        start_time = time.time()
        max_wait = 300  # 最大等待时间（秒）
        
        # 初始化进度条
        with tqdm(total=100, unit='%', desc='转换进度', ncols=80) as pbar:
            last_progress = 0
            
            while time.time() - start_time < max_wait:
                status_response = tester.session.get(f"{BASE_URL}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    # 更新进度条
                    current_progress = status.get('progress', 0)
                    if current_progress > last_progress:
                        pbar.update(current_progress - last_progress)
                        last_progress = current_progress
                        
                    # 显示详细信息
                    print(f"\r转换状态: {status.get('current_task', '处理中')} - 进度: {current_progress}%", end='')
                    
                    if not status['is_processing']:
                        print("\n转录已完成")
                        pbar.update(100 - last_progress)  # 确保进度条达到100%
                        break
                time.sleep(2)  # 缩短间隔，提高实时性
        
        # 再次测试状态
        tester.test_status()
        
        # 测试下载SRT文件
        if srt_file:
            tester.test_download_srt(srt_file)
    
    print("\n" + "=" * 50)
    print("测试完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
