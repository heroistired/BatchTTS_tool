import json
from gradio_client import Client

def TTS_API_change_choices(server_url):
    """
    获取服务器上的模型列表
    :param server_url: 服务器地址，如 http://192.168.31.194:9872/
    :return: JSON格式的模型列表，包含SoVITS模型列表和GPT模型列表
    """
    client = Client(server_url)
    try:
        result = client.predict(
            api_name="/change_choices"
        )
        
        # 提取实际的模型列表
        sovits_models = [choice[0] for choice in result[0]["choices"]]
        gpt_models = [choice[0] for choice in result[1]["choices"]]
        
        # 构建返回的JSON结构
        return {
            "sovits_model_list": sovits_models,
            "gpt_model_list": gpt_models
        }
    except Exception as e:
        # 增强错误处理
        error_msg = f"API调用失败: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "sovits_model_list": [],
            "gpt_model_list": []
        }

def TTS_API_get_tts_wav(server_url, input_params):
    """
    调用TTS服务生成语音文件
    :param server_url: 服务器地址，如 http://192.168.31.194:9872/
    :param input_params: JSON格式的输入参数，包含以下字段：
        - ref_wav_path: 参考音频文件路径（必填）
        - prompt_text: 参考音频的文本（默认：""）
        - prompt_language: 参考音频的语种（默认："中文"）
        - text: 需要合成的文本（默认：""）
        - text_language: 需要合成的语种（默认："中文"）
        - how_to_cut: 切割方式（默认："不切"）
        - top_k: GPT采样参数top_k（默认：20）
        - top_p: GPT采样参数top_p（默认：0.6）
        - temperature: GPT采样参数temperature（默认：0.6）
        - ref_free: 是否开启无参考文本模式（默认：False）
        - speed: 语速（默认：1）
        - if_freeze: 是否直接对上次合成结果调整语速和音色（默认：False）
        - inp_refs: 多个参考音频文件路径列表（默认：None）
        - sample_steps: 采样步数（默认：8）
        - if_sr: 是否开启超分（默认：False）
        - pause_second: 句间停顿秒数（默认：0.3）
    :return: JSON格式的输出结果，包含生成的语音文件路径和本地拷贝路径
    """
    import os
    import shutil
    from datetime import datetime
    from gradio_client import file
    
    client = Client(server_url)
    
    # 设置默认参数（与服务器端保持一致）
    default_params = {
        "prompt_text": "",
        "prompt_language": "中文",
        "text": "",
        "text_language": "中文",
        "how_to_cut": "不切",
        "top_k": 20,
        "top_p": 0.6,
        "temperature": 0.6,
        "ref_free": False,
        "speed": 1,
        "if_freeze": False,
        "inp_refs": None,
        "sample_steps": 8,
        "if_sr": False,
        "pause_second": 0.3
    }
    
    # 合并默认参数和输入参数
    merged_params = {**default_params, **input_params}
    
    # 处理ref_wav_path参数，转换为file对象
    ref_wav_path = file(merged_params["ref_wav_path"])
    
    # 处理inp_refs参数，如果有值则转换为file对象列表
    inp_refs = merged_params["inp_refs"]
    if inp_refs:
        inp_refs = [file(ref) for ref in inp_refs]
    
    try:
        result = client.predict(
            ref_wav_path=ref_wav_path,
            prompt_text=merged_params["prompt_text"],
            prompt_language=merged_params["prompt_language"],
            text=merged_params["text"],
            text_language=merged_params["text_language"],
            how_to_cut=merged_params["how_to_cut"],
            top_k=merged_params["top_k"],
            top_p=merged_params["top_p"],
            temperature=merged_params["temperature"],
            ref_free=merged_params["ref_free"],
            speed=merged_params["speed"],
            if_freeze=merged_params["if_freeze"],
            inp_refs=inp_refs,
            sample_steps=merged_params["sample_steps"],
            if_sr=merged_params["if_sr"],
            pause_second=merged_params["pause_second"],
            api_name="/get_tts_wav"
        )
    
        # 构建返回的JSON结构
        output_json = {
            "output_wav_path": result
        }
        
        # 如果成功生成了文件路径，进行拷贝操作
        if result:
            # 获取当前代码所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 创建output_audio文件夹（如果不存在）
            output_dir = os.path.join(current_dir, "output_audio")
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取当前时间，格式化为英文格式时间（如：20240104_120000）
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 生成目标文件名和路径
            target_filename = f"{current_time}.wav"
            target_path = os.path.join(output_dir, target_filename)
            
            # 拷贝文件
            shutil.copy2(result, target_path)
            
            # 在输出JSON中添加拷贝后的文件路径
            output_json["local_audio_path"] = target_path
        
        return output_json
    except Exception as e:
        # 增强错误处理
        error_msg = f"API调用失败: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "output_wav_path": None,
            "local_audio_path": None
        }

def TTS_API_change_sovits_weights(server_url, input_params):
    """
    切换SoVITS模型权重
    :param server_url: 服务器地址，如 http://192.168.31.194:9872/
    :param input_params: JSON格式的输入参数，包含以下字段：
        - sovits_path: SoVITS模型路径（默认："GPT_SoVITS/pretrained_models/s2G488k.pth"）
        - prompt_language: 参考音频的语种（默认："中文"）
        - text_language: 需要合成的语种（默认："中文"）
    :return: JSON格式的输出结果，包含服务器返回的10个元素
    """
    client = Client(server_url)
    
    # 设置默认参数
    default_params = {
        "sovits_path": "GPT_SoVITS/pretrained_models/s2G488k.pth",
        "prompt_language": "中文",
        "text_language": "中文"
    }
    
    # 合并默认参数和输入参数
    merged_params = {**default_params, **input_params}
    
    # 打印调试信息，确认传递的模型路径
    print(f"正在请求切换SoVITS模型到: {merged_params['sovits_path']}")
    
    try:
        # 直接传递参数
        result = client.predict(
            sovits_path=merged_params["sovits_path"],
            prompt_language=merged_params["prompt_language"],
            text_language=merged_params["text_language"],
            api_name="/change_sovits_weights"
        )
        
        # 处理生成器返回的多个结果，只取最后一个
        if hasattr(result, '__iter__') and not isinstance(result, (list, tuple)):
            # 如果是生成器，遍历获取所有结果，只保留最后一个
            final_result = None
            for res in result:
                final_result = res
            result = final_result
        
        # 构建返回的JSON结构
        return {
            "prompt_language_1": result[0],
            "text_language_1": result[1],
            "prompt_text": result[2],
            "prompt_language_2": result[3],
            "text": result[4],
            "text_language_2": result[5],
            "sample_steps": result[6],
            "inp_refs": result[7],
            "ref_free": result[8],
            "if_sr": result[9],
            "requested_sovits_path": merged_params["sovits_path"]  # 添加请求的模型路径，用于验证
        }
    except Exception as e:
        # 增强错误处理
        error_msg = f"API调用失败: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "requested_sovits_path": merged_params["sovits_path"]  # 添加请求的模型路径，用于验证
        }

def TTS_API_change_gpt_weights(server_url, input_params):
    """
    切换GPT模型权重
    :param server_url: 服务器地址，如 http://192.168.31.194:9872/
    :param input_params: JSON格式的输入参数，包含以下字段：
        - gpt_path: GPT模型路径（默认："GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"）
    :return: JSON格式的输出结果，包含服务器返回的结果
    """
    client = Client(server_url)
    
    # 设置默认参数
    default_params = {
        "gpt_path": "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"
    }
    
    # 合并默认参数和输入参数
    merged_params = {**default_params, **input_params}
    
    try:
        result = client.predict(
            gpt_path=merged_params["gpt_path"],
            api_name="/change_gpt_weights"
        )
        
        # 构建返回的JSON结构
        return {
            "result": result
        }
    except Exception as e:
        # 增强错误处理
        error_msg = f"API调用失败: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "result": None
        }

class GradioAPITester:
    """
    Gradio API 测试类，用于测试所有API函数
    """
    
    def __init__(self, server_url="http://192.168.31.194:9872/"):
        """
        初始化测试类
        :param server_url: 服务器地址，默认使用本地服务器
        """
        self.server_url = server_url
        self.default_ref_wav = "d:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\ref.WAV"
    
    def test_function(self, func, *args):
        """
        测试单个函数的通用方法
        :param func: 要测试的函数
        :param args: 函数参数
        :return: 测试结果
        """
        try:
            result = func(*args)
            print(f"✅ 测试结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_change_choices(self):
        """
        测试获取服务器上的模型列表
        """
        print("\n🚀 测试 TTS_API_change_choices - 获取服务器上的模型列表")
        print(f"📋 服务器地址: {self.server_url}")
        
        return self.test_function(TTS_API_change_choices, self.server_url)
    
    def test_change_sovits_weights(self):
        """
        测试切换SoVITS模型权重
        """
        print("\n🚀 测试 TTS_API_change_sovits_weights - 切换SoVITS模型权重")
        print(f"📋 服务器地址: {self.server_url}")
        
        # 准备测试参数
        test_params = {
            "sovits_path": "SoVITS_weights_v4/chenhuanVoice_e2_s352_l32.pth",
            "prompt_language": "中文",
            "text_language": "中文"
        }
        print(f"📝 测试参数: {json.dumps(test_params, ensure_ascii=False, indent=2)}")
        
        return self.test_function(TTS_API_change_sovits_weights, self.server_url, test_params)
    
    def test_change_gpt_weights(self):
        """
        测试切换GPT模型权重
        """
        print("\n🚀 测试 TTS_API_change_gpt_weights - 切换GPT模型权重")
        print(f"📋 服务器地址: {self.server_url}")
        
        # 准备测试参数
        test_params = {
            "gpt_path": "GPT_weights_v4/chenhuanVoice-e15.ckpt"
        }
        print(f"📝 测试参数: {json.dumps(test_params, ensure_ascii=False, indent=2)}")
        
        return self.test_function(TTS_API_change_gpt_weights, self.server_url, test_params)
    
    def test_get_tts_wav(self, simple=False):
        """
        测试调用TTS服务生成语音文件
        :param simple: 是否使用简单测试参数
        """
        print("\n🚀 测试 TTS_API_get_tts_wav - 调用TTS服务生成语音文件")
        print(f"📋 服务器地址: {self.server_url}")
        
        if simple:
            # 简单测试参数
            test_params = {
                "ref_wav_path": self.default_ref_wav,
                "text": "尊敬的各位评委老师，我是电机系陈欢，很荣幸向您汇报。",
                "text_language": "中文"
            }
        else:
            # 完整测试参数
            test_params = {
                "ref_wav_path": self.default_ref_wav,
                "prompt_text": "尊敬的各位评委老师，我是电机系陈欢，很荣幸向您汇报。",
                "prompt_language": "中文",
                "text": "这份文件告诉我们，二次安检，这个被官方称为\"对未通过初步审查的乘客进行的，可能漫长而详细的检查\"，是悬在每一位秘密旅行者头上的达摩克利斯之剑。",
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
                "pause_second": 0.2
            }
        
        print(f"📝 测试参数: {json.dumps(test_params, ensure_ascii=False, indent=2)}")
        
        return self.test_function(TTS_API_get_tts_wav, self.server_url, test_params)
    
    def test_all_functions(self):
        """
        测试所有API函数
        """
        print("=== 开始测试所有API函数 ===")
        
        results = []
        
        # 测试TTS_API_change_choices
        results.append(self.test_change_choices())
        
        # 测试TTS_API_change_sovits_weights
        results.append(self.test_change_sovits_weights())
        
        # 测试TTS_API_change_gpt_weights
        results.append(self.test_change_gpt_weights())
        
        # 测试TTS_API_get_tts_wav (简单测试)
        results.append(self.test_get_tts_wav(simple=True))
        
        print("\n=== 所有API函数测试完成 ===")
        
        # 统计测试结果
        passed = sum(results)
        total = len(results)
        print(f"📊 测试统计: {passed}/{total} 个测试通过")
        
        return passed == total
    
    def run_interactive_test(self):
        """
        运行交互式测试
        """
        while True:
            print("\n=== Gradio API 测试工具 ===")
            print("请选择要测试的函数:")
            print("1. TTS_API_change_choices - 获取服务器上的模型列表")
            print("2. TTS_API_change_sovits_weights - 切换SoVITS模型权重")
            print("3. TTS_API_change_gpt_weights - 切换GPT模型权重")
            print("4. TTS_API_get_tts_wav (简单) - 调用TTS服务生成语音文件")
            print("5. TTS_API_get_tts_wav (完整) - 调用TTS服务生成语音文件")
            print("6. 测试所有函数")
            print("0. 退出")
            
            choice = input("请输入选项 (0-6): ")
            
            if choice == "0":
                print("退出测试工具")
                break
            elif choice == "1":
                self.test_change_choices()
            elif choice == "2":
                self.test_change_sovits_weights()
            elif choice == "3":
                self.test_change_gpt_weights()
            elif choice == "4":
                self.test_get_tts_wav(simple=True)
            elif choice == "5":
                self.test_get_tts_wav(simple=False)
            elif choice == "6":
                self.test_all_functions()
            else:
                print("无效的选项，请重新输入")

def main():
    """
    主函数，启动交互式测试
    """
    tester = GradioAPITester()
    tester.run_interactive_test()

if __name__ == "__main__":
    main()