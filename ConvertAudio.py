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
import json
from datetime import datetime

# 尝试导入moviepy库，用于视频处理
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
except ImportError:
    print("⚠️ 缺少moviepy库，视频处理功能将不可用")
    print("💡 请安装所需库: pip install moviepy")

# 尝试导入ffmpeg库，用于音视频压制
try:
    import ffmpeg
except ImportError:
    print("⚠️ 缺少ffmpeg库，音视频压制功能将不可用")
    print("💡 请安装所需库: pip install ffmpeg-python")

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


def parse_srt_time(time_str):
    """
    解析SRT字幕时间格式 (HH:MM:SS,mmm) 为秒数
    :param time_str: SRT格式的时间字符串，如 "00:00:01,000"
    :return: 时间（秒）
    """
    parts = time_str.replace(',', '.').split(':')
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_srt_time(seconds):
    """
    将秒数格式化为SRT字幕时间格式 (HH:MM:SS,mmm)
    :param seconds: 时间（秒）
    :return: SRT格式的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')


def shift_srt_times(srt_content, offset):
    """
    对SRT字幕内容应用时间轴偏移
    :param srt_content: SRT字幕文件内容
    :param offset: 时间轴偏移（秒）
    :return: 应用了时间轴偏移的SRT字幕内容
    """
    lines = srt_content.split('\n')
    shifted_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是时间轴行
        if '-->' in line:
            # 解析时间轴
            time_range = line.split(' --> ')
            if len(time_range) == 2:
                start_time = parse_srt_time(time_range[0])
                end_time = parse_srt_time(time_range[1])
                
                # 应用偏移
                shifted_start = start_time + offset
                shifted_end = end_time + offset
                
                # 格式化回SRT时间格式
                shifted_time_line = f"{format_srt_time(shifted_start)} --> {format_srt_time(shifted_end)}"
                shifted_lines.append(shifted_time_line)
                i += 1
                continue
        
        # 其他行直接添加
        shifted_lines.append(line)
        i += 1
    
    return '\n'.join(shifted_lines)


def backup_file(file_path):
    """
    备份文件，在文件名后添加时间戳
    
    Args:
        file_path: 要备份的文件路径
    
    Returns:
        备份文件的路径
    """
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在，无法备份: {file_path}")
        return None
    
    # 获取文件目录和文件名
    dir_path = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    
    # 生成带时间戳的备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name}_{timestamp}{ext}"
    backup_path = os.path.join(dir_path, backup_name)
    
    # 复制文件
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✅ 文件已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份文件失败: {str(e)}")
        return None


def adjust_video_speed(video_path, target_duration, output_path):
    """
    调整视频速度，使其时长与目标时长一致
    
    Args:
        video_path: 输入视频文件路径
        target_duration: 目标时长（秒）
        output_path: 输出视频文件路径
    
    Returns:
        调整后的视频文件路径
    """
    try:
        # 检查moviepy是否已导入
        if 'VideoFileClip' not in globals():
            print("❌ 缺少moviepy库，无法调整视频速度")
            return None
        
        # 打开视频文件
        clip = VideoFileClip(video_path)
        
        # 获取原始视频时长
        original_duration = clip.duration
        print(f"📹 原始视频时长: {original_duration:.2f} 秒")
        print(f"🎯 目标视频时长: {target_duration:.2f} 秒")
        
        # 计算速度因子
        speed_factor = original_duration / target_duration
        print(f"⚡ 速度调整因子: {speed_factor:.2f}")
        
        # 调整视频速度
        adjusted_clip = clip.with_speed_scaled(speed_factor)
        
        # 保存调整后的视频
        adjusted_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # 关闭视频
        clip.close()
        adjusted_clip.close()
        
        print(f"✅ 视频速度调整完成，保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ 调整视频速度失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def concatenate_videos(video_paths, output_path):
    """
    合成多个视频为一个大视频
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频文件路径
    
    Returns:
        合成后的视频文件路径
    """
    try:
        # 检查moviepy是否已导入
        if 'VideoFileClip' not in globals():
            print("❌ 缺少moviepy库，无法合成视频")
            return None
        
        # 检查输出文件是否存在，如果存在则备份
        if os.path.exists(output_path):
            print(f"⚠️ 输出文件已存在，将备份原文件")
            backup_file(output_path)
        
        # 加载所有视频文件
        clips = []
        for video_path in video_paths:
            if os.path.exists(video_path):
                clip = VideoFileClip(video_path)
                clips.append(clip)
                print(f"✅ 加载视频: {os.path.basename(video_path)}")
            else:
                print(f"⚠️ 视频文件不存在，跳过: {video_path}")
        
        if not clips:
            print("❌ 没有可合成的视频文件")
            return None
        
        # 合成视频
        final_clip = concatenate_videoclips(clips)
        
        # 保存合成后的视频
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # 关闭所有视频
        for clip in clips:
            clip.close()
        final_clip.close()
        
        print(f"✅ 视频合成完成，保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ 合成视频失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def ProcessVideos(json_file_path, output_dir):
    """
    将每个分镜的视频处理为长度与音频一致
    
    Args:
        json_file_path: JSON文件地址
        output_dir: 输出文件地址
    
    Returns:
        处理后的视频文件路径
    """
    print(f"\n=== 开始处理视频文件 ===")
    print(f"输入JSON文件: {json_file_path}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 1. 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 2. 验证JSON数据格式
        if not isinstance(json_data, list):
            print(f"❌ JSON文件格式错误，预期为列表格式")
            return None
        
        print(f"🔍 共发现 {len(json_data)} 个分镜")
        
        # 3. 处理每个分镜的视频
        processed_videos = []
        
        for i, shot in enumerate(json_data):
            print(f"\n=== 处理分镜 {i+1}/{len(json_data)} ===")
            
            # 3.1 读取Video.filepath字段
            video_info = shot.get("Video", {})
            video_path = video_info.get("filepath", None)
            
            if not video_path:
                print(f"⚠️ 分镜 {i+1} 缺少Video.filepath字段，跳过处理")
                continue
            
            # 3.2 检查视频文件是否存在
            if not os.path.exists(video_path):
                print(f"⚠️ 分镜 {i+1} 的视频文件不存在: {video_path}，跳过处理")
                continue
            
            # 3.3 读取duration字段
            target_duration = shot.get("duration", 0)
            try:
                target_duration = float(target_duration)
            except (ValueError, TypeError):
                print(f"⚠️ 分镜 {i+1} 的duration字段无效，跳过处理")
                continue
            
            if target_duration <= 0:
                print(f"⚠️ 分镜 {i+1} 的duration字段小于等于0，跳过处理")
                continue
            
            print(f"📄 视频文件: {video_path}")
            print(f"⏰ 目标时长: {target_duration:.2f} 秒")
            
            # 3.4 备份原视频文件
            backup_path = backup_file(video_path)
            if not backup_path:
                print(f"⚠️ 无法备份原视频文件，跳过处理")
                continue
            
            # 3.5 调整视频速度
            # 使用原视频文件路径作为输出路径（覆盖原文件）
            adjusted_video_path = adjust_video_speed(video_path, target_duration, video_path)
            if not adjusted_video_path:
                print(f"⚠️ 无法调整视频速度，跳过处理")
                continue
            
            # 3.6 添加到处理后的视频列表
            processed_videos.append(adjusted_video_path)
            print(f"✅ 分镜 {i+1} 处理成功")
        
        # 4. 合成所有处理后的视频
        if processed_videos:
            print(f"\n=== 合成视频 ===")
            print(f"🎬 共 {len(processed_videos)} 个视频文件需要合成")
            
            # 生成输出文件路径
            output_filename = 'ExportAudioInfo.mp4'
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"📋 输出文件名: {output_filename}")
            print(f"💾 输出文件路径: {output_path}")
            
            # 合成视频
            final_video_path = concatenate_videos(processed_videos, output_path)
            if final_video_path:
                print(f"✅ 视频合成成功")
                print(f"📊 共处理 {len(processed_videos)} 个视频文件，合成为一个视频文件")
                return final_video_path
            else:
                print(f"❌ 视频合成失败")
                return None
        else:
            print(f"❌ 没有成功处理的视频文件，无法合成")
            return None
        
    except Exception as e:
            print(f"❌ 处理视频文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def MergeAudioVideoSRT(json_file_path, output_dir):
    """
    将音频、字幕和视频压制为一个视频
    
    Args:
        json_file_path: JSON文件地址
        output_dir: 输出文件地址
    
    Returns:
        压制后的视频文件路径
    """
    print(f"\n=== 开始压制音视频字幕 ===")
    print(f"输入JSON文件: {json_file_path}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 检查ffmpeg是否已导入
        if 'ffmpeg' not in globals():
            print("❌ 缺少ffmpeg库，无法执行音视频压制")
            return None
        
        # 1. 获取JSON文件的基本信息
        json_dir = os.path.dirname(json_file_path)
        json_filename = os.path.basename(json_file_path)
        base_name = os.path.splitext(json_filename)[0]
        
        # 2. 构建输入文件路径
        video_path = os.path.join(json_dir, f"{base_name}.mp4")
        audio_path = os.path.join(json_dir, f"{base_name}.wav")
        srt_path = os.path.join(json_dir, f"{base_name}.srt")
        
        print(f"\n=== 输入文件信息 ===")
        print(f"视频文件: {video_path}")
        print(f"音频文件: {audio_path}")
        print(f"字幕文件: {srt_path}")
        
        # 3. 检查输入文件是否存在
        missing_files = []
        if not os.path.exists(video_path):
            missing_files.append(f"视频文件: {video_path}")
        if not os.path.exists(audio_path):
            missing_files.append(f"音频文件: {audio_path}")
        if not os.path.exists(srt_path):
            missing_files.append(f"字幕文件: {srt_path}")
        
        if missing_files:
            print(f"❌ 缺少以下文件:")
            for file in missing_files:
                print(f"   - {file}")
            return None
        
        # 4. 构建输出文件路径
        output_filename = f"{base_name}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n=== 输出文件信息 ===")
        print(f"输出文件: {output_path}")
        
        # 5. 如果输出文件已存在，备份原文件
        if os.path.exists(output_path):
            print(f"⚠️ 输出文件已存在，将备份原文件")
            backup_path = backup_file(output_path)
            if backup_path:
                print(f"✅ 原文件已备份到: {backup_path}")
        
        # 6. 使用ffmpeg压制音视频字幕
        print(f"\n=== 开始压制 ===")
        print(f"使用ffmpeg将音频、字幕和视频压制为一个视频...")
        
        try:
            # 构建ffmpeg命令
            # 注意：使用指定路径下的ffmpeg可执行文件
            ffmpeg_path = r"D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\ffmpeg\bin\ffmpeg.exe"
            
            # 检查ffmpeg可执行文件是否存在
            if not os.path.exists(ffmpeg_path):
                print(f"❌ ffmpeg可执行文件不存在: {ffmpeg_path}")
                return None
            
            # 使用subprocess直接调用ffmpeg命令，避免ffmpeg-python库的map参数问题
            import subprocess
            import shutil
            
            # 创建临时目录来处理文件，避免路径问题
            import tempfile
            temp_dir = tempfile.mkdtemp()
            print(f"✅ 创建临时目录: {temp_dir}")
            
            # 拷贝文件到临时目录，使用更简单的文件名
            temp_video = os.path.join(temp_dir, "v.mp4")
            temp_audio = os.path.join(temp_dir, "a.wav")
            temp_subs = os.path.join(temp_dir, "s.srt")
            temp_out = os.path.join(temp_dir, "out.mp4")
            
            try:
                shutil.copy2(video_path, temp_video)
                shutil.copy2(audio_path, temp_audio)
                shutil.copy2(srt_path, temp_subs)
                print(f"✅ 文件已拷贝到临时目录")
            except Exception as e:
                print(f"❌ 拷贝文件失败: {e}")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return None
            
            # 创建临时输出文件路径
            temp_output_path = os.path.splitext(output_path)[0] + "_temp" + os.path.splitext(output_path)[1]
            
            # 切换到临时目录执行ffmpeg命令，避免路径问题
            # 构建ffmpeg命令行参数，使用subtitles滤镜硬编码字幕
            # 注意：在某些ffmpeg版本中，subtitles滤镜不支持直接设置样式参数
            # 可以使用以下方法来控制字幕样式：
            # 1. 使用ASS格式字幕文件，在文件中定义样式
            # 2. 使用filter_complex组合多个滤镜
            # 3. 使用drawtext滤镜手动绘制字幕
            
            # 方法1：基本的subtitles滤镜（无样式控制）
            # cmd = [
            #     ffmpeg_path,
            #     '-i', "v.mp4",
            #     '-i', "a.wav",
            #     '-vf', "subtitles=s.srt",
            #     '-c:v', 'libx264',
            #     '-c:a', 'aac',
            #     '-shortest',
            #     '-y',
            #     "out.mp4"
            # ]
            
            # 方法2：使用filter_complex和subtitles滤镜（支持基本样式控制）
            # 注意：不同ffmpeg版本支持的参数可能不同
            # 使用force_style参数来调整字幕字体大小为27号
            force_style = "FontSize=27"
            
            # 添加scale滤镜将视频调整为1080P分辨率（1920x1080）
            # 滤镜链：先调整分辨率，再添加字幕
            filter_complex = f"[0:v]scale=1920:1080,subtitles=s.srt:force_style='{force_style}'[outv]"
            
            cmd = [
                ffmpeg_path,
                '-i', "v.mp4",
                '-i', "a.wav",
                '-filter_complex', filter_complex,
                '-map', "[outv]",
                '-map', "1:a",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-y',  # 覆盖输出文件
                "out.mp4"
            ]
            
            # 方法3：使用drawtext滤镜（完全控制样式，但需要解析字幕文件）
            # 这种方法需要手动解析SRT文件并为每个字幕创建drawtext滤镜
            # 示例代码（需要额外实现）：
            # srt_entries = parse_srt_file("s.srt")
            # drawtext_filters = []
            # for entry in srt_entries:
            #     drawtext_filters.append(f"drawtext=text='{entry.text}':fontsize=24:fontcolor=white:bordercolor=black:borderwidth=1:x=(w-text_w)/2:y=h-100:enable='between(t,{entry.start},{entry.end})'")
            # filter_complex = "[0:v]" + "+"".join(drawtext_filters) + "[outv]"

            
            print(f"执行命令: {' '.join(cmd)}")
            
            # 执行ffmpeg命令，在临时目录中执行
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=temp_dir  # 在临时目录中执行命令
                )
                print(f"✅ ffmpeg命令执行成功")
                print(f"stdout: {result.stdout}")
                
                # 将临时目录中的输出文件复制到目标位置
                if os.path.exists(temp_out):
                    shutil.copy2(temp_out, temp_output_path)
                    print(f"✅ 临时文件已复制到目标位置")
                    
                    # 将临时输出文件重命名为最终输出文件
                    if os.path.exists(temp_output_path):
                        os.replace(temp_output_path, output_path)
                        print(f"✅ 临时文件已重命名为最终输出文件")
                    else:
                        print(f"❌ 临时输出文件不存在: {temp_output_path}")
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                        return None
                else:
                    print(f"❌ 临时目录中的输出文件不存在: {temp_out}")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    return None
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ ffmpeg命令执行失败: {e}")
                print(f"stderr: {e.stderr}")
                # 清理临时文件和目录
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return None
            except Exception as e:
                print(f"❌ 处理临时文件失败: {e}")
                # 清理临时文件和目录
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return None
            finally:
                # 清理临时目录
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        print(f"✅ 临时目录已清理: {temp_dir}")
                    else:
                        print(f"⚠️ 临时目录不存在，跳过清理: {temp_dir}")
                except Exception as e:
                    print(f"❌ 清理临时目录失败: {e}")
            
            print(f"✅ 音视频字幕压制成功！")
            print(f"📋 输出文件: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 压制失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"❌ 执行音视频压制失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def ExportFullSRT(json_file_path, output_dir):
    """
    将每个分镜的SRT字幕文件合并成一个整体的字幕文件
    
    Args:
        json_file_path: JSON文件地址
        output_dir: 输出文件地址
    
    Returns:
        合并后的字幕文件路径
    """
    print(f"\n=== 开始合并SRT字幕文件 ===")
    print(f"输入JSON文件: {json_file_path}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 1. 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 2. 验证JSON数据格式
        if not isinstance(json_data, list):
            print(f"❌ JSON文件格式错误，预期为列表格式")
            return None
        
        print(f"🔍 共发现 {len(json_data)} 个分镜")
        
        # 3. 创建主字幕文件内容
        main_subtitle_content = []
        subtitle_index = 1
        total_offset = 0
        
        # 4. 遍历每个分镜
        for i, shot in enumerate(json_data):
            print(f"\n=== 处理分镜 {i+1}/{len(json_data)} ===")
            
            # 4.1 读取SRT_Path字段
            srt_path = shot.get("SRT_Path", None)
            if not srt_path:
                print(f"⚠️ 分镜 {i+1} 缺少SRT_Path字段，跳过处理")
                continue
            
            # 4.2 检查SRT文件是否存在
            if not os.path.exists(srt_path):
                print(f"⚠️ 分镜 {i+1} 的SRT文件不存在: {srt_path}，跳过处理")
                continue
            
            print(f"📄 读取SRT文件: {srt_path}")
            
            # 4.3 读取SRT文件内容
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # 4.4 计算时间轴偏移
            if i > 0:
                # 累加之前所有分镜的duration
                # 注意：应该获取前一个分镜(i-1)的duration值，而不是当前分镜(i)的duration值
                prev_shot = json_data[i-1]
                prev_duration = prev_shot.get("duration", 0)
                try:
                    total_offset += float(prev_duration)
                except (ValueError, TypeError):
                    print(f"⚠️ 分镜 {i-1} 的duration字段无效，跳过偏移计算")
            
            print(f"⏰ 时间轴偏移: {total_offset:.2f} 秒")
            
            # 4.5 应用时间轴偏移
            shifted_content = shift_srt_times(srt_content, total_offset)
            
            # 4.6 重新编号字幕索引并添加到主字幕文件
            # 分割SRT内容为字幕块
            subtitle_blocks = shifted_content.split('\n\n')
            
            for block in subtitle_blocks:
                block = block.strip()
                if not block:
                    continue
                
                # 替换字幕索引
                lines = block.split('\n')
                if lines and lines[0].isdigit():
                    lines[0] = str(subtitle_index)
                else:
                    # 如果没有索引，添加索引
                    lines.insert(0, str(subtitle_index))
                
                # 添加到主字幕内容
                main_subtitle_content.append('\n'.join(lines))
                subtitle_index += 1
            
            print(f"✅ 分镜 {i+1} 处理成功")
        
        # 5. 生成输出文件路径
        json_filename = os.path.basename(json_file_path)
        output_filename = os.path.splitext(json_filename)[0] + '.srt'
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n=== 保存主字幕文件 ===")
        print(f"📋 输出文件名: {output_filename}")
        print(f"💾 输出文件路径: {output_path}")
        
        # 6. 保存主字幕文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(main_subtitle_content))
        
        print(f"✅ 主字幕文件保存成功")
        print(f"📊 共处理 {len(json_data)} 个分镜，合并为一个字幕文件")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 合并SRT字幕文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_ConvertBySingleText():
    """
    测试ConvertBySingleText函数
    """
    print("=== 测试ConvertBySingleText函数 ===")
    
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
        return False
    else:
        print("✅ 转换成功！")
        return True


def test_ExportFullSRT():
    """
    测试ExportFullSRT函数
    """
    print("=== 测试ExportFullSRT函数 ===")
    
    # 测试参数
    test_json_file = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\output_1\\ExportAudioInfo.json"
    test_output_dir = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\01 BatchTTS_tool\\output_1"
    
    # 调用函数
    result_file = ExportFullSRT(test_json_file, test_output_dir)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的主字幕文件: {result_file}")
        return True
    else:
        print(f"\n❌ 测试失败！")
        return False


def test_ProcessVideos():
    """
    测试ProcessVideos函数
    """
    print("=== 测试ProcessVideos函数 ===")
    
    # 测试参数
    test_json_file = "D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1\ExportAudioInfo.json"
    test_output_dir = "D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1"
    
    # 调用函数
    result_file = ProcessVideos(test_json_file, test_output_dir)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的视频文件: {result_file}")
        return True
    else:
        print(f"\n❌ 测试失败！")
        return False


def test_MergeAudioVideoSRT():
    """
    测试MergeAudioVideoSRT函数
    """
    print("=== 测试MergeAudioVideoSRT函数 ===")
    
    # 测试参数
    test_json_file = "D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1\ExportAudioInfo.json"
    test_output_dir = "D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1"
    
    # 调用函数
    result_file = MergeAudioVideoSRT(test_json_file, test_output_dir)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的视频文件: {result_file}")
        return True
    else:
        print(f"\n❌ 测试失败！")
        return False


def ExportFullVideo(json_file_path, output_dir):
    """
    从json文件导出剪辑好的视频
    
    Args:
        json_file_path: JSON文件地址
        output_dir: 输出文件地址
    
    Returns:
        导出的视频文件路径
    """
    print(f"\n=== 开始导出完整视频 ===")
    print(f"输入JSON文件: {json_file_path}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 1. 调用ExportFullSRT处理字幕
        print("\n=== 1. 处理字幕文件 ===")
        srt_result = ExportFullSRT(json_file_path, output_dir)
        if not srt_result:
            print("❌ 字幕处理失败，无法继续导出")
            return None
        print(f"✅ 字幕处理成功: {srt_result}")
        
        # 2. 调用ProcessVideos处理视频
        print("\n=== 2. 处理视频文件 ===")
        video_result = ProcessVideos(json_file_path, output_dir)
        if not video_result:
            print("❌ 视频处理失败，无法继续导出")
            return None
        print(f"✅ 视频处理成功: {video_result}")
        
        # 3. 调用MergeAudioVideoSRT处理合成视频
        print("\n=== 3. 合成音视频字幕 ===")
        final_result = MergeAudioVideoSRT(json_file_path, output_dir)
        if not final_result:
            print("❌ 音视频合成失败")
            return None
        print(f"✅ 音视频合成成功: {final_result}")
        
        print(f"\n=== 完整视频导出成功！ ===")
        print(f"📋 最终输出文件: {final_result}")
        return final_result
        
    except Exception as e:
        print(f"❌ 导出完整视频失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_ExportFullVideo():
    """
    测试ExportFullVideo函数
    """
    print("=== 测试ExportFullVideo函数 ===")
    
    # 测试参数，使用原始字符串避免转义问题
    test_json_file = r"D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1\ExportAudioInfo.json"
    test_output_dir = r"D:\05 SelfMidea\98 SelfDevelopedTools\01 BatchTTS_tool\output_1"
    
    # 调用函数
    result_file = ExportFullVideo(test_json_file, test_output_dir)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的视频文件: {result_file}")
        return True
    else:
        print(f"\n❌ 测试失败！")
        return False


def show_test_menu():
    """
    显示测试菜单
    """
    print("\n=== 测试函数选择菜单 ===")
    print("1. 测试 ConvertBySingleText (文本转语音)")
    print("2. 测试 ExportFullSRT (合并SRT字幕文件)")
    print("3. 测试 ProcessVideos (处理视频文件)")
    print("4. 测试 MergeAudioVideoSRT (压制音视频字幕)")
    print("5. 测试 ExportFullVideo (导出完整视频)")
    print("6. 测试所有函数")
    print("0. 退出")
    print("=======================")


def run_test(choice):
    """
    根据选择执行对应的测试函数
    
    Args:
        choice: 用户选择的测试选项
    """
    print(f"\n=== 执行测试选择: {choice} ===")
    if choice == "1":
        test_ConvertBySingleText()
    elif choice == "2":
        test_ExportFullSRT()
    elif choice == "3":
        test_ProcessVideos()
    elif choice == "4":
        test_MergeAudioVideoSRT()
    elif choice == "5":
        test_ExportFullVideo()
    elif choice == "6":
        # 测试所有函数
        print("\n=== 开始测试所有函数 ===")
        test_ConvertBySingleText()
        test_ExportFullSRT()
        test_ProcessVideos()
        test_MergeAudioVideoSRT()
        test_ExportFullVideo()
        print("\n=== 所有函数测试完成 ===")
    elif choice == "0":
        print("\n=== 退出测试 ===")
        return False
    else:
        print(f"\n❌ 无效的选择: {choice}")
    return True


# 测试代码
if __name__ == "__main__":
    print("=== ConvertAudio.py 执行 ===")
    
    # 检查命令行参数
    import sys
    if len(sys.argv) > 1:
        # 从命令行参数获取测试选择
        choice = sys.argv[1]
        run_test(choice)
    else:
        # 交互式菜单选择
        while True:
            show_test_menu()
            choice = input("请输入您要测试的函数编号 (0-4): ")
            if not run_test(choice):
                break
    
    print("\n=== 执行完成 ===")
