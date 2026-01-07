#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频转换脚本，用于将文本转换为语音
"""

# 导入GradioAPI模块
import sys
import os
import tempfile
import shutil

# 添加当前目录到Python路径，确保能正确导入GradioAPI
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GradioAPI import (
    TTS_API_change_sovits_weights,
    TTS_API_change_gpt_weights,
    TTS_API_get_tts_wav
)


def get_ref_wav_path():
    """
    获取ref.WAV文件的正确路径，支持打包环境和开发环境
    """
    # 检查是否在打包环境中
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 在打包环境中，从临时目录读取
        meipass_dir = sys._MEIPASS
        ref_wav_path = os.path.join(meipass_dir, "ref.WAV")
        if os.path.exists(ref_wav_path):
            return ref_wav_path
        
        # 如果在temp目录中，尝试查找
        temp_dir = tempfile.gettemp()
        for root, dirs, files in os.walk(temp_dir):
            if '_MEI' in root and 'ref.WAV' in files:
                return os.path.join(root, 'ref.WAV')
        
        # 如果找不到，返回临时目录中的路径（由gradio_client处理）
        return os.path.join(temp_dir, "ref.WAV")
    else:
        # 在开发环境中，使用脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "ref.WAV")


class AudioConverter:
    """
    音频转换类，用于将文本转换为语音
    """
    
    def __init__(self, server_url="http://192.168.31.194:9872/"):
        """
        初始化音频转换类
        :param server_url: Gradio服务器地址
        """
        self.server_url = server_url
        # 获取ref.WAV文件的正确路径
        self.default_ref_wav = get_ref_wav_path()
        print(f"ref.WAV路径: {self.default_ref_wav}")
        print(f"ref.WAV文件是否存在: {os.path.exists(self.default_ref_wav)}")
        # 创建共享的Client对象，避免每次API调用都创建新的连接
        from gradio_client import Client
        self.client = Client(server_url)
    
    def ConvertBySingleText(self, text):
        """
        将单条文本转换为语音
        :param text: 要转换的文本字符串
        :return: 语音生成结果，包含输出文件路径等信息
        """
        print(f"\n开始转换文本为语音")
        print(f"输入文本: {text}")
        print(f"服务器地址: {self.server_url}")
        
        try:
            # 1. 调用TTS_API_change_sovits_weights设置SoVITS模型权重
            print("\n1. 设置SoVITS模型权重...")
            sovits_params = {
                "sovits_path": "SoVITS_weights_v4/chenhuanVoice_e2_s352_l32.pth",
                "prompt_language": "中文",
                "text_language": "中文"
            }
            sovits_result = TTS_API_change_sovits_weights(self.server_url, sovits_params, self.client)
            print(f"SoVITS模型权重设置完成: {sovits_result.get('requested_sovits_path')}")
            
            # 2. 调用TTS_API_change_gpt_weights设置GPT模型权重
            print("\n2. 设置GPT模型权重...")
            gpt_params = {
                "gpt_path": "GPT_weights_v4/chenhuanVoice-e15.ckpt"
            }
            gpt_result = TTS_API_change_gpt_weights(self.server_url, gpt_params, self.client)
            print(f"GPT模型权重设置完成")
            
            # 3. 调用TTS_API_get_tts_wav生成语音
            print("\n3. 生成语音...")
            tts_params = {
                "ref_wav_path": self.default_ref_wav,
                "prompt_text": "尊敬的各位评委老师，我是电机系陈欢，很荣幸向您汇报。",
                "prompt_language": "中文",
                "text_language": "中文",
                "how_to_cut": "按标点符号切",
                "top_k": 100,
                "top_p": 1,
                "temperature": 0.2,
                "ref_free": False,
                "speed": 1.15,
                "if_freeze": False,
                "inp_refs": None,
                "sample_steps": 32,
                "if_sr": True,
                "pause_second": 0.2,
                "text": text  # 添加外部传入的文本参数
            }
            
            tts_result = TTS_API_get_tts_wav(self.server_url, tts_params, self.client)
            print(f"语音生成完成")
            
            # 返回生成结果
            return tts_result
            
        except Exception as e:
            print(f"文本转语音失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "output_wav_path": None,
                "local_audio_path": None
            }


# 测试代码
if __name__ == "__main__":
    # 初始化音频转换器
    converter = AudioConverter()
    
    # 测试示例文本
    test_text = "白日依山尽，黄河入海流，欲穷千里目，更上一层楼。"
    
    # 调用转换函数
    result = converter.ConvertBySingleText(test_text)
    
    # 打印结果
    print("\n=== 转换结果 ===")
    print(f"输出文件路径: {result.get('output_wav_path')}")
    print(f"本地保存路径: {result.get('local_audio_path')}")
    if "error" in result:
        print(f"错误信息: {result['error']}")
    else:
        print("✅ 转换成功！")
