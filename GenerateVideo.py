#!/usr/bin/env python3
"""
Generate Video Script
用于生成视频提示词的批量处理脚本
"""

import json
import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from GenerationPromptLLM import generate_prompt, generate_prompt_with_process
from QwenImageGenerator import QwenImageGenerator
from ImageToVideoGenerator import ImageToVideoGenerator


def BatchGeneratePrompt(json_file_path, video_summary):
    """
    批量生成视频提示词
    
    Args:
        json_file_path: JSON文件路径，包含分镜信息
        video_summary: 视频梗概描述文本
    
    Returns:
        生成的包含提示词的JSON文件路径
    """
    print(f"\n=== 开始批量生成提示词 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📝 视频梗概: {video_summary[:100]}...")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 批量生成提示词
    results = []
    for i, shot in enumerate(data):
        print(f"\n=== 处理分镜 {i+1}/{len(data)} ===")
        print(f"📄 分镜内容: {shot.get('text', '')[:50]}...")
        
        # 调用generate_prompt函数
        try:
            result = generate_prompt(video_summary, shot)
            if result and "error" not in result:
                results.append(result)
                print(f"✅ 分镜 {i+1} 处理成功")
            else:
                print(f"❌ 分镜 {i+1} 处理失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"❌ 分镜 {i+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存结果到新的JSON文件
    if results:
        # 构建输出文件路径
        base_name = os.path.splitext(json_file_path)[0]
        output_file_path = f"{base_name}_AddPrompt.json"
        
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n🎉 批量生成完成！")
            print(f"💾 结果保存到: {output_file_path}")
            print(f"📊 成功处理 {len(results)}/{len(data)} 个分镜")
            return output_file_path
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")
            return None
    else:
        print(f"\n❌ 所有分镜处理失败")
        return None


def BatchGeneratePromptConcurrent(json_file_path, video_summary, max_workers=30):
    """
    批量生成视频提示词（多线程并发版本）
    
    Args:
        json_file_path: JSON文件路径，包含分镜信息
        video_summary: 视频梗概描述文本
        max_workers: 最大线程数，默认为4
    
    Returns:
        生成的包含提示词的JSON文件路径
    """
    print(f"\n=== 开始并发批量生成提示词 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📝 视频梗概: {video_summary[:100]}...")
    print(f"🔧 最大线程数: {max_workers}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 批量生成提示词（并发版本）
    results = [None] * len(data)  # 预分配结果列表，保持顺序
    
    # 定义单个分镜处理函数
    def process_shot(index, shot):
        print(f"\n=== 线程处理分镜 {index+1}/{len(data)} ===")
        print(f"📄 分镜内容: {shot.get('text', '')[:50]}...")
        
        try:
            result = generate_prompt_with_process(video_summary, shot)
            if result and "error" not in result:
                print(f"✅ 分镜 {index+1} 处理成功")
                return index, result
            else:
                print(f"❌ 分镜 {index+1} 处理失败: {result.get('error', '未知错误')}")
                return index, None
        except Exception as e:
            print(f"❌ 分镜 {index+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return index, None
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = [executor.submit(process_shot, i, shot) for i, shot in enumerate(data)]
        
        # 收集结果
        for future in as_completed(futures):
            index, result = future.result()
            results[index] = result
    
    # 过滤掉失败的结果
    valid_results = [result for result in results if result is not None]
    
    # 保存结果到新的JSON文件
    if valid_results:
        # 2. 对输入的json文件改名，在原来的名字后面加上"_时间戳"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 构建备份文件名（原文件名+_时间戳+扩展名）
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 3. 写入的新文件的文件名为原输入的json文件名
        output_file_path = json_file_path
        
        try:
            # 备份原文件
            os.rename(json_file_path, backup_file_path)
            print(f"📋 原文件已备份为: {backup_file_path}")
            
            # 写入新文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(valid_results, f, ensure_ascii=False, indent=2)
            print(f"\n🎉 并发批量生成完成！")
            print(f"💾 结果保存到: {output_file_path}")
            print(f"📊 成功处理 {len(valid_results)}/{len(data)} 个分镜")
            return output_file_path
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print(f"\n❌ 所有分镜处理失败")
        return None


def test_BatchGeneratePromptConcurrent():
    """
    测试BatchGeneratePromptConcurrent函数
    """
    print("=== 测试BatchGeneratePromptConcurrent函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo.json"
    test_video_summary = "一份泄露的中情局\"机场二次安检生存指南\"揭示了间谍与安检系统的秘密对抗。\n引言：一份泄露的绝密指南\n2014年，维基解密曝光了一份中情局机密文件《如何在二次安检中活下来》，旨在指导特工用假身份通过全球机场的严密审查。\n第一章：无声的战场——二次安检\n二次安检是包含严苛盘问、法医级设备搜查和生物信息采集的深度审查。对特工而言，进入此处即意味着身份暴露的高风险。\n第二章：鹰眼无处不在——谁在盯着你\n监控网络无处不在。除明显问题外，紧张神态、临期单程机票、旅行历史矛盾等细节都可能引致怀疑，甚至存在随机抽查。\n第三章：特工的真实梦魇——全球机场案例实录\n文件记录了真实案例：有特工因着装与外交身份不符、行李检测出爆炸物痕迹而被审查；在某些国家，电子设备中的可疑内容会招致大祸。\n第四章：终极守则——无论如何，守住你的秘密\n核心建议是\"保持身份掩护\"。必须准备天衣无缝的虚假背景故事，确保所有物品和数字痕迹与之匹配，盘问时冷静、简洁。\n结语：你我皆是局中人\n这份间谍指南映射出现代社会无处不在的监控。它提醒人们，在便捷出行的背后，行为与数据正被持续记录和分析。"
    
    # 调用函数
    result_file = BatchGeneratePromptConcurrent(test_json_file, test_video_summary, max_workers=30)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def BatchGeneratePromptConcurrentByCondition(json_file_path, video_summary, max_workers=30):
    """
    批量生成视频提示词（多线程并发版本）
    
    Args:
        json_file_path: JSON文件路径，包含分镜信息
        video_summary: 视频梗概描述文本
        max_workers: 最大线程数，默认为4
    
    Returns:
        生成的包含提示词的JSON文件路径
    """
    print(f"\n=== 开始根据条件并发批量生成提示词 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📝 视频梗概: {video_summary[:100]}...")
    print(f"🔧 最大线程数: {max_workers}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 批量生成提示词（并发版本）
    results = [None] * len(data)  # 预分配结果列表，保持顺序
    
    # 定义单个分镜处理函数
    def process_shot(index, shot):
        print(f"\n=== 线程处理分镜 {index+1}/{len(data)} ===")
        print(f"📄 分镜内容: {shot.get('text', '')[:50]}...")
        
        # 2.1 提取三个Flag字段
        prompt_update_flag = shot.get("Prompt_Update_Flag", 0)
        figure_update_flag = shot.get("Figure_Update_Flag", 0)
        video_update_flag = shot.get("Video_Update_Flag", 0)
        
        print(f"📋 Flag状态 - Prompt: {prompt_update_flag}, Figure: {figure_update_flag}, Video: {video_update_flag}")
        
        # 2.2 如果Prompt_Update_Flag为0，则跳过生成提示词，直接返回原数据
        if prompt_update_flag == 0:
            print(f"⚠️ 分镜 {index+1} Prompt_Update_Flag为0，跳过生成提示词")
            # 复制原数据，确保包含所有Flag字段
            result = shot.copy()
            return index, result
        
        # 2.3 生成提示词
        try:
            # 保存原始数据的副本，确保所有字段都被保留
            original_shot = shot.copy()
            
            result = generate_prompt_with_process(video_summary, shot)
            if result and "error" not in result:
                # 2.4 生成成功，更新Flag字段
                print(f"✅ 分镜 {index+1} 提示词生成成功")
                
                # 2.4.1 将原始数据的所有字段合并到结果中，只覆盖需要更新的字段
                # 这样可以确保Audio_Update_Flag、SRT_Update_Flag、SRT_Path等字段被保留
                merged_result = original_shot.copy()
                # 更新生成的提示词字段
                merged_result.update(result)
                # 2.4.2 设置Flag字段
                merged_result["Prompt_Update_Flag"] = 0
                merged_result["Figure_Update_Flag"] = 1
                merged_result["Video_Update_Flag"] = 1
                print(f"📝 已更新Flag状态 - Prompt: 0, Figure: 1, Video: 1")
                return index, merged_result
            else:
                print(f"❌ 分镜 {index+1} 提示词生成失败: {result.get('error', '未知错误')}")
                return index, None
        except Exception as e:
            print(f"❌ 分镜 {index+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return index, None
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = [executor.submit(process_shot, i, shot) for i, shot in enumerate(data)]
        
        # 收集结果
        for future in as_completed(futures):
            index, result = future.result()
            results[index] = result
    
    # 过滤掉失败的结果，保留所有有效的结果（包括跳过生成的）
    valid_results = [result for result in results if result is not None]
    
    # 保存结果到新的JSON文件
    if valid_results:
        # 1. 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 2. 解析输入文件路径
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 3. 构建备份文件名（原文件名+_时间戳+扩展名）
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 4. 输出文件路径为原输入文件名
        output_file_path = json_file_path
        
        print(f"\n=== 开始保存结果 ===")
        print(f"📋 原文件名: {input_file_name}")
        print(f"📋 备份文件名: {backup_file_name}")
        print(f"📋 输出文件名: {input_file_name}")
        
        try:
            # 5. 备份原文件
            import shutil
            shutil.copy2(json_file_path, backup_file_path)
            print(f"✅ 原文件已成功备份为: {backup_file_path}")
            
            # 6. 写入新文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(valid_results, f, ensure_ascii=False, indent=2)
            print(f"✅ 新文件已成功写入: {output_file_path}")
            
            print(f"\n🎉 并发批量生成完成！")
            print(f"💾 结果保存到: {output_file_path}")
            print(f"📊 成功处理 {len(valid_results)}/{len(data)} 个分镜")
            return output_file_path
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print(f"\n❌ 所有分镜处理失败")
        return None


def test_BatchGeneratePromptConcurrentByCondition():
    """
    测试BatchGeneratePromptConcurrentByCondition函数
    """
    print("=== 测试BatchGeneratePromptConcurrentByCondition函数 ===")
    
    # 测试参数
   # test_json_file = "ExportAudioInfo.json"
   # test_video_summary = "一份泄露的中情局\"机场二次安检生存指南\"揭示了间谍与安检系统的秘密对抗。\n引言：一份泄露的绝密指南\n2014年，维基解密曝光了一份中情局机密文件《如何在二次安检中活下来》，旨在指导特工用假身份通过全球机场的严密审查。\n第一章：无声的战场——二次安检\n二次安检是包含严苛盘问、法医级设备搜查和生物信息采集的深度审查。对特工而言，进入此处即意味着身份暴露的高风险。\n第二章：鹰眼无处不在——谁在盯着你\n监控网络无处不在。除明显问题外，紧张神态、临期单程机票、旅行历史矛盾等细节都可能引致怀疑，甚至存在随机抽查。\n第三章：特工的真实梦魇——全球机场案例实录\n文件记录了真实案例：有特工因着装与外交身份不符、行李检测出爆炸物痕迹而被审查；在某些国家，电子设备中的可疑内容会招致大祸。\n第四章：终极守则——无论如何，守住你的秘密\n核心建议是\"保持身份掩护\"。必须准备天衣无缝的虚假背景故事，确保所有物品和数字痕迹与之匹配，盘问时冷静、简洁。\n结语：你我皆是局中人\n这份间谍指南映射出现代社会无处不在的监控。它提醒人们，在便捷出行的背后，行为与数据正被持续记录和分析。"

    test_json_file = "ExportAudioInfo copy.json"
    test_video_summary = "无"
    
    # 调用函数
    result_file = BatchGeneratePromptConcurrentByCondition(test_json_file, test_video_summary, max_workers=30)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def test_BatchGeneratePrompt():
    """
    测试BatchGeneratePrompt函数
    """
    print("=== 测试BatchGeneratePrompt函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy.json"
    test_video_summary = "一份泄露的中情局\"机场二次安检生存指南\"揭示了间谍与安检系统的秘密对抗。\n引言：一份泄露的绝密指南\n2014年，维基解密曝光了一份中情局机密文件《如何在二次安检中活下来》，旨在指导特工用假身份通过全球机场的严密审查。\n第一章：无声的战场——二次安检\n二次安检是包含严苛盘问、法医级设备搜查和生物信息采集的深度审查。对特工而言，进入此处即意味着身份暴露的高风险。\n第二章：鹰眼无处不在——谁在盯着你\n监控网络无处不在。除明显问题外，紧张神态、临期单程机票、旅行历史矛盾等细节都可能引致怀疑，甚至存在随机抽查。\n第三章：特工的真实梦魇——全球机场案例实录\n文件记录了真实案例：有特工因着装与外交身份不符、行李检测出爆炸物痕迹而被审查；在某些国家，电子设备中的可疑内容会招致大祸。\n第四章：终极守则——无论如何，守住你的秘密\n核心建议是\"保持身份掩护\"。必须准备天衣无缝的虚假背景故事，确保所有物品和数字痕迹与之匹配，盘问时冷静、简洁。\n结语：你我皆是局中人\n这份间谍指南映射出现代社会无处不在的监控。它提醒人们，在便捷出行的背后，行为与数据正被持续记录和分析。"
    
    # 调用函数
    result_file = BatchGeneratePrompt(test_json_file, test_video_summary)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def BatchGenerateFigure(json_file_path, server_url):
    """
    批量生成图片
    
    Args:
        json_file_path: 包含Prompt_Figure字段的JSON文件路径
        server_url: 服务器地址
    
    Returns:
        处理后的JSON文件路径
    """
    print(f"\n=== 开始批量生成图片 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"🔌 服务器地址: {server_url}")
    
    # 创建Output文件夹（如果不存在）
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Output")
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 创建QwenImageGenerator实例
    generator = QwenImageGenerator(server_url=server_url)
    
    # 批量生成图片
    for i, item in enumerate(data):
        print(f"\n=== 处理分镜 {i+1}/{len(data)} ===")
        
        # 提取Prompt_Figure字段
        prompt_figure = item.get("Prompt_Figure", "")
        if not prompt_figure:
            print(f"⚠️ 分镜 {i+1} 缺少Prompt_Figure字段，跳过处理")
            continue
        
        print(f"📝 提示词: {prompt_figure[:50]}...")
        
        # 调用生成函数
        try:
            result = generator.generate(
                prompt=prompt_figure,
                seed=None
            )
            
            if result and result.get("success"):
                # 获取生成的图片信息
                local_filename = result.get("local_filename")
                if local_filename and os.path.exists(local_filename):
                    # 生成新的文件名（日期时间戳）
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    new_filename = f"{timestamp}.png"
                    new_filepath = os.path.join(output_dir, new_filename)
                    
                    # 复制文件到Output文件夹
                    import shutil
                    shutil.copy2(local_filename, new_filepath)
                    print(f"💾 图片已保存到: {new_filepath}")
                    
                    # 更新json对象，添加Figure字段
                    item["Figure"] = {
                        "filename": new_filename,
                        "filepath": new_filepath,
                        "original_filename": local_filename,
                        "prompt": prompt_figure,
                        "timestamp": timestamp
                    }
                    print(f"✅ 分镜 {i+1} 处理成功")
                else:
                    print(f"❌ 分镜 {i+1} 生成的图片文件不存在")
            else:
                print(f"❌ 分镜 {i+1} 图片生成失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"❌ 分镜 {i+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存更新后的json文件
    try:
        # 1. 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 2. 解析输入文件路径
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 3. 构建备份文件名（原文件名+_时间戳+扩展名）
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 4. 输出文件路径为原输入文件名
        output_file_path = json_file_path
        
        print(f"\n=== 开始保存结果 ===")
        print(f"📋 原文件名: {input_file_name}")
        print(f"📋 备份文件名: {backup_file_name}")
        print(f"📋 输出文件名: {input_file_name}")
        
        # 5. 备份原文件
        os.rename(json_file_path, backup_file_path)
        print(f"✅ 原文件已成功备份为: {backup_file_path}")
        
        # 6. 写入新文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 新文件已成功写入: {output_file_path}")
        
        print(f"\n🎉 批量生成完成！")
        print(f"💾 结果保存到: {output_file_path}")
        return output_file_path
    except Exception as e:
        print(f"❌ 保存更新后的JSON文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def BatchGenerateVideo(json_file_path, server_url, frame_length=16):
    """
    批量生成视频
    
    Args:
        json_file_path: JSON文件路径，包含Figure.filepath和Prompt_Video字段
        server_url: 服务器地址
        frame_length: 生成的帧数，默认为16。如果为None，则从每个分镜的duration字段计算
    
    Returns:
        更新后的JSON文件路径
    """
    print(f"\n=== 开始批量生成视频 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"🔌 服务器地址: {server_url}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 创建ImageToVideoGenerator实例
    generator = ImageToVideoGenerator(server_url=server_url)
    
    # 批量生成视频
    for i, item in enumerate(data):
        print(f"\n=== 处理分镜 {i+1}/{len(data)} ===")
        
        # 提取Figure.filepath字段
        figure_info = item.get("Figure", {})
        image_path = figure_info.get("filepath", "")
        if not image_path or not os.path.exists(image_path):
            print(f"⚠️ 分镜 {i+1} 缺少Figure.filepath字段或文件不存在，跳过处理")
            continue
        
        # 提取Prompt_Video字段
        prompt_video = item.get("Prompt_Video", "")
        if not prompt_video:
            print(f"⚠️ 分镜 {i+1} 缺少Prompt_Video字段，跳过处理")
            continue
        
        # 计算当前分镜的帧数
        current_frame_length = frame_length
        if frame_length is None:
            # 从当前分镜的duration字段计算帧数
            duration = item.get("duration", 0)
            current_frame_length = round(duration * 16)
            print(f"📋 分镜 {i+1} duration: {duration}秒")
        
        print(f"🖼️  首帧图片: {image_path}")
        print(f"📝 视频提示词: {prompt_video[:50]}...")
        print(f"🎬 生成帧数: {current_frame_length}")
        
        # 调用生成函数
        try:
            result = generator.generate_video(
                image_path=image_path,
                video_prompt=prompt_video,
                frame_length=current_frame_length
            )
            
            if result and result.get("success"):
                # 获取生成的视频信息
                local_filename = result.get("local_filename")
                if local_filename and os.path.exists(local_filename):
                    # 获取视频文件名和路径
                    video_filename = os.path.basename(local_filename)
                    video_filepath = local_filename
                    
                    print(f"💾 视频已保存到: {video_filepath}")
                    
                    # 更新json对象，添加Video字段
                    item["Video"] = {
                        "filename": video_filename,
                        "filepath": video_filepath,
                        "prompt": prompt_video,
                        "frame_length": 16,
                        "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    }
                    print(f"✅ 分镜 {i+1} 处理成功")
                else:
                    print(f"❌ 分镜 {i+1} 生成的视频文件不存在")
            else:
                print(f"❌ 分镜 {i+1} 视频生成失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"❌ 分镜 {i+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # 保存更新后的json文件
    try:
        # 1. 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 2. 解析输入文件路径
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 3. 构建备份文件名（原文件名+_时间戳+扩展名）
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 4. 输出文件路径为原输入文件名
        output_file_path = json_file_path
        
        print(f"\n=== 开始保存结果 ===")
        print(f"📋 原文件名: {input_file_name}")
        print(f"📋 备份文件名: {backup_file_name}")
        print(f"📋 输出文件名: {input_file_name}")
        
        # 5. 备份原文件
        os.rename(json_file_path, backup_file_path)
        print(f"✅ 原文件已成功备份为: {backup_file_path}")
        
        # 6. 写入新文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 新文件已成功写入: {output_file_path}")
        
        print(f"\n🎉 批量生成完成！")
        print(f"💾 结果保存到: {output_file_path}")
        return output_file_path
    except Exception as e:
        print(f"❌ 保存更新后的JSON文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_BatchGenerateFigure():
    """
    测试BatchGenerateFigure函数
    """
    print("=== 测试BatchGenerateFigure函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy_AddPrompt_Concurrent.json"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    
    # 调用函数
    result_file = BatchGenerateFigure(test_json_file, test_server_url)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 更新后的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def BatchGenerateFigureAndVideo(json_file_path, server_url):
    """
    批量生成图片和视频
    
    Args:
        json_file_path: JSON文件路径，包含分镜信息
        server_url: 服务器地址
    
    Returns:
        更新后的JSON文件路径
    """
    print(f"\n=== 开始批量生成图片和视频 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"🔌 服务器地址: {server_url}")
    
    # 1. 调用BatchGenerateFigure生成图片，支持重试一次
    print(f"\n=== 第一步：生成图片 ===")
    result_file = BatchGenerateFigure(json_file_path, server_url)
    
    if not result_file:
        print(f"❌ 第一次生成图片失败，准备重试...")
        # 重试一次
        result_file = BatchGenerateFigure(json_file_path, server_url)
        if not result_file:
            print(f"❌ 第二次生成图片失败，退出程序")
            return None
    
    # 3. 调用BatchGenerateVideo生成视频，支持重试一次
    print(f"\n=== 第三步：生成视频 ===")
    # 设置frame_length为None，让BatchGenerateVideo为每个分镜单独计算帧数
    result_file = BatchGenerateVideo(json_file_path, server_url, frame_length=None)
    
    if not result_file:
        print(f"❌ 第一次生成视频失败，准备重试...")
        # 重试一次
        result_file = BatchGenerateVideo(json_file_path, server_url, frame_length=None)
        if not result_file:
            print(f"❌ 第二次生成视频失败，退出程序")
            return None
    
    print(f"\n🎉 批量生成图片和视频完成！")
    print(f"📋 更新后的JSON文件: {result_file}")
    return result_file


def test_BatchGenerateFigureAndVideo():
    """
    测试BatchGenerateFigureAndVideo函数
    """
    print("=== 测试BatchGenerateFigureAndVideo函数 ===")
    
    # 测试参数
    #test_json_file = "ExportAudioInfo_AddPrompt.json"
    test_json_file = "ExportAudioInfo copy_AddPrompt.json"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    
    # 调用函数
    result_file = BatchGenerateFigureAndVideo(test_json_file, test_server_url)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 更新后的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def test_BatchGenerateVideo():
    """
    测试BatchGenerateVideo函数
    """
    print("=== 测试BatchGenerateVideo函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy_AddPrompt.json"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    test_frame_length = 8  # 将帧数设置为8
    
    # 调用函数
    result_file = BatchGenerateVideo(test_json_file, test_server_url, frame_length=test_frame_length)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 更新后的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def get_last_frame(video_path, output_path):
    """
    提取视频的最后一帧并保存为PNG格式
    
    Args:
        video_path: 视频文件路径
        output_path: 最后一帧图片的保存路径及名称
        
    Returns:
        保存的图片文件路径
    """
    print(f"\n=== 提取视频最后一帧 ===")
    print(f"📹 输入视频文件: {video_path}")
    print(f"💾 输出图片路径: {output_path}")
    
    try:
        # 延迟导入所需库，避免未安装时的错误
        import cv2
        from PIL import Image
        import numpy as np
        
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            return None
        
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            print(f"📁 已创建输出目录: {output_dir}")
        
        # 使用OpenCV打开视频
        cap = cv2.VideoCapture(video_path)
        
        # 检查视频是否成功打开
        if not cap.isOpened():
            print(f"❌ 无法打开视频文件: {video_path}")
            return None
        
        # 获取视频总帧数
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"🔢 视频总帧数: {total_frames}")
        
        if total_frames == 0:
            print(f"❌ 视频文件为空: {video_path}")
            cap.release()
            return None
        
        # 定位到最后一帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        
        # 读取最后一帧
        ret, frame = cap.read()
        if not ret:
            print(f"❌ 无法读取最后一帧")
            # 尝试定位到倒数第二帧
            print(f"⚠️ 尝试定位到倒数第二帧")
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 2))
            ret, frame = cap.read()
            if not ret:
                print(f"❌ 无法读取倒数第二帧，提取失败")
                cap.release()
                return None
            print(f"✅ 成功读取倒数第二帧")
        else:
            print(f"✅ 成功读取最后一帧")
        
        # 关闭视频
        cap.release()
        
        # 将BGR格式转换为RGB格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 将帧数据转换为PIL图像
        img = Image.fromarray(frame_rgb)
        
        # 保存为PNG
        img.save(output_path, format='PNG')
        print(f"✅ 最后一帧已保存到: {output_path}")
        
        return output_path
    except ImportError as e:
        print(f"❌ 缺少必要的库: {str(e)}")
        print(f"💡 请安装所需库: pip install opencv-python pillow numpy")
        return None
    except Exception as e:
        print(f"❌ 提取视频最后一帧失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_get_last_frame():
    """
    测试get_last_frame函数
    """
    print("=== 测试get_last_frame函数 ===")
    
    # 测试参数
    test_video_path = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\TestOutput_Full\20260109_165431_955\20260109_165431_955_4.mp4"
    test_output_path = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\TestOutput_Full\20260109_165431_955\20260109_165431_955_4_LastFrame.png"
    
    # 调用函数
    result = get_last_frame(test_video_path, test_output_path)
    
    if result:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的最后一帧图片: {result}")
    else:
        print(f"\n❌ 测试失败！")


def GenerateVideoByStoryboard(storyboard_json, save_dir, server_url):
    """
    根据分镜信息生成视频
    
    Args:
        storyboard_json: 包含分镜信息的json对象
        save_dir: 保存地址字符串
        server_url: 服务器地址
        
    Returns:
        更新后的分镜信息json对象，包含Video字段
    """
    print(f"\n=== 开始根据分镜信息生成视频 ===")
    print(f"📁 保存地址: {save_dir}")
    print(f"🔌 服务器地址: {server_url}")
    
    try:
        # 1. 从分镜信息中获取基本信息
        figure_info = storyboard_json.get("Figure", {})
        figure_filename = figure_info.get("filename", "")
        if not figure_filename:
            print(f"❌ 分镜信息中缺少Figure.filename字段")
            return storyboard_json
        
        print(f"🖼️  分镜图片文件名: {figure_filename}")
        
        # 2. 创建工作目录
        # 从Figure.filename中获取文件名（不含扩展名）
        base_filename = os.path.splitext(figure_filename)[0]
        # 工作目录路径
        work_dir = os.path.join(save_dir, base_filename)
        # 创建工作目录（如果不存在）
        os.makedirs(work_dir, exist_ok=True)
        print(f"📁 工作目录: {work_dir}")
        
        # 3. 统计视频环节数
        prompt_video = storyboard_json.get("Prompt_Video", {})
        process_dict = prompt_video.get("Process", {})
        video_steps = len(process_dict)
        print(f"🔢 视频环节数: {video_steps}")
        
        if video_steps == 0:
            print(f"❌ 分镜信息中缺少Prompt_Video.Process字段")
            return storyboard_json
        
        # 4. 循环生成视频
        generated_videos = []
        last_frame_path = ""
        
        for step in range(1, video_steps + 1):
            print(f"\n=== 处理环节 {step}/{video_steps} ===")
            
            # 4.1 准备参数
            # 首帧图片地址
            if step == 1:
                # 第1个环节，使用分镜信息中的首帧图片
                frame_image_path = figure_info.get("filepath", "")
                if not frame_image_path:
                    print(f"❌ 分镜信息中缺少Figure.filepath字段")
                    continue
                print(f"🖼️  首帧图片地址: {frame_image_path}")
            else:
                # 后续环节，使用上一个环节的视频最后一帧
                frame_image_path = last_frame_path
                if not frame_image_path or not os.path.exists(frame_image_path):
                    print(f"❌ 上一个环节的最后一帧不存在: {frame_image_path}")
                    continue
                print(f"🖼️  首帧图片地址: {frame_image_path}")
            
            # 视频提示词
            process_key = str(step)
            video_prompt = process_dict.get(process_key, "")
            if not video_prompt:
                print(f"❌ 分镜信息中缺少Prompt_Video.Process.{process_key}字段")
                continue
            print(f"📝 视频提示词: {video_prompt[:50]}...")
            
            # 生成帧数
            duration_dict = prompt_video.get("duration", {})
            duration = duration_dict.get(process_key, 0)
            frame_length = round(duration * 16)
            print(f"⏱️  环节时长: {duration}秒")
            print(f"🎬 生成帧数: {frame_length}")
            
            # 4.2 生成视频
            # 创建ImageToVideoGenerator实例
            from ImageToVideoGenerator import ImageToVideoGenerator
            generator = ImageToVideoGenerator(server_url=server_url)
            
            # 调用generate_video函数生成视频
            result = generator.generate_video(
                image_path=frame_image_path,
                video_prompt=video_prompt,
                frame_length=frame_length
            )
            
            if not result.get("success"):
                print(f"❌ 环节 {step} 视频生成失败: {result.get('error', '未知错误')}")
                continue
            
            # 获取生成的视频路径
            generated_video_path = result.get("local_filename", "")
            if not generated_video_path or not os.path.exists(generated_video_path):
                print(f"❌ 环节 {step} 视频生成成功，但文件不存在: {generated_video_path}")
                continue
            
            # 4.3 复制视频到工作目录
            # 生成视频文件名
            video_extension = os.path.splitext(generated_video_path)[1]
            step_video_filename = f"{base_filename}_{step}{video_extension}"
            step_video_path = os.path.join(work_dir, step_video_filename)
            
            # 复制视频文件
            import shutil
            shutil.copy2(generated_video_path, step_video_path)
            print(f"💾 环节 {step} 视频已保存到: {step_video_path}")
            
            # 添加到生成视频列表
            generated_videos.append(step_video_path)
            
            # 4.4 提取视频的最后一帧
            step_last_frame_filename = f"{base_filename}_{step}.png"
            step_last_frame_path = os.path.join(work_dir, step_last_frame_filename)
            
            # 调用get_last_frame函数提取最后一帧
            last_frame_result = get_last_frame(step_video_path, step_last_frame_path)
            if last_frame_result:
                print(f"✅ 环节 {step} 视频最后一帧已提取: {step_last_frame_path}")
                # 更新last_frame_path，用于下一个环节
                last_frame_path = step_last_frame_path
            else:
                print(f"❌ 环节 {step} 视频最后一帧提取失败")
                # 如果提取失败，使用当前视频的首帧作为下一个环节的首帧
                last_frame_path = frame_image_path
        
        # 5. 合成视频
        if generated_videos:
            print(f"\n=== 开始合成视频 ===")
            print(f"🎬 共 {len(generated_videos)} 个视频片段需要合成")
            
            # 5.1 导入moviepy库
            from moviepy.video.io.VideoFileClip import VideoFileClip
            from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
            
            # 5.2 加载所有视频片段
            video_clips = []
            for video_path in generated_videos:
                try:
                    clip = VideoFileClip(video_path)
                    video_clips.append(clip)
                    print(f"✅ 加载视频片段: {os.path.basename(video_path)}")
                except Exception as e:
                    print(f"❌ 加载视频片段失败 {video_path}: {str(e)}")
            
            if not video_clips:
                print(f"❌ 没有可用的视频片段进行合成")
                return storyboard_json
            
            # 5.3 合成视频
            final_clip = concatenate_videoclips(video_clips)
            
            # 5.4 保存合成视频
            # 合成视频文件名
            final_video_filename = f"{base_filename}.mp4"
            final_video_path = os.path.join(save_dir, final_video_filename)
            
            # 保存合成视频
            final_clip.write_videofile(final_video_path, codec="libx264")
            print(f"🎉 合成视频已保存到: {final_video_path}")
            
            # 5.5 关闭所有视频片段
            for clip in video_clips:
                clip.close()
            final_clip.close()
            
            # 5.6 更新分镜信息json，添加Video字段
            storyboard_json["Video"] = {
                "filename": final_video_filename,
                "filepath": final_video_path,
                "steps": video_steps,
                "generated_videos": generated_videos,
                "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            }
            print(f"✅ 分镜信息已更新，添加了Video字段")
        else:
            print(f"❌ 没有生成任何视频，无法合成")
        
        print(f"\n=== 根据分镜信息生成视频完成 ===")
        return storyboard_json
    except Exception as e:
        print(f"❌ 生成视频失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return storyboard_json


def test_GenerateVideoByStoryboard():
    """
    测试GenerateVideoByStoryboard函数
    """
    print("=== 测试GenerateVideoByStoryboard函数 ===")
    
    # 测试参数
    test_storyboard_json = {
        "text": "大家好，欢迎收看本期节目。二零一四年，维基解密网站公布了一份来自美国中央情报局的内部文件，标题触目惊心，\"如何在二次安检中活下来\"。",
        "audio": "20260106_175704.wav",
        "duration": 11.83,
        "chapter": "引言",
        "description": "镜头从节目LOGO或主持人（身着正式服装，表情严肃）的特写开始，营造专业、可信的节目开场氛围。随后，镜头快速推近并切换至一个昏暗房间内的电脑屏幕特写。屏幕上清晰显示着维基解密网站的界面，一份名为《如何在二次安检中活下来》的PDF文件被打开，其标题被一道醒目的红色高光框或光标选中，暗示其机密与敏感性。整个画面色调冷峻，以蓝灰为主，光线主要来自屏幕光，在操作者（仅出现手部或模糊背影）脸上投下阴影，强化神秘、悬疑的氛围。",
        "Prompt_Figure": "A high-resolution 8K cinematic shot, extreme detail. The core subject is a close-up of a laptop screen in a dimly lit room. The screen clearly displays the WikiLeaks website interface, with a PDF document titled \"How to Survive Secondary Screening\" opened and its title highlighted by a bright red rectangular glow or cursor selection. The environment is a shadowy, nondescript workspace, with the primary light source being the cold, blue-tinged glow from the monitor, casting dramatic shadows. The atmosphere is mysterious, tense, and suspenseful. The composition is a tight, focused shot on the screen, with the background softly blurred to emphasize the document. The style is hyper-realistic, with a cool color palette dominated by blues and grays. No watermarks, no extraneous elements, moderate color saturation.",
        "Prompt_Video": {
            "Process": {
                "1": "Cinematic 8K, hyper-realistic, cool tone. Opening shot: A professional, serious-looking host in a studio setting, or a close-up of the program's sleek, modern logo. The camera holds steady for a moment, establishing credibility. Duration: 2.5 seconds.",
                "2": "Cinematic 8K, hyper-realistic. A quick, smooth zoom-in transition from the host/logo, dissolving into an extreme close-up of a laptop screen in a dark room. The screen shows the WikiLeaks homepage. The camera movement is a subtle push-in towards the screen. The color tone shifts to a colder, more mysterious blue-grey palette. Duration: 2.5 seconds.",
                "3": "Cinematic 8K, hyper-realistic, cool tone. Continuation from previous frame. On the laptop screen, a user's hand (out of focus) uses a mouse or trackpad. The cursor moves and clicks on a link or file. A PDF document titled \"How to Survive Secondary Screening\" begins to load and open on the screen. The camera remains in a tight close-up on the screen. Duration: 2.5 seconds.",
                "4": "Cinematic 8K, hyper-realistic, cool tone. Continuation from previous frame. The PDF document is now fully open on the screen. A vivid, pulsating red highlight box or a cursor slowly draws a rectangle around the shocking title \"How to Survive Secondary Screening\", emphasizing its significance. The screen's glow is the only strong light source, creating high contrast and deep shadows in the room. The camera holds the shot, letting the title sink in. The atmosphere is tense and clandestine. Duration: 2.5 seconds.",
                "5": "Cinematic 8K, hyper-realistic, cool tone. Final shot of the sequence. A slow, very slight push-in on the highlighted title, making it the absolute focal point. The red highlight seems to glow faintly. The background of the room remains in deep shadow, enhancing the feeling of a leaked secret viewed in isolation. The shot holds to conclude the introduction. Duration: 1.83 seconds."
            },
            "duration": {
                "1": 2.5,
                "2": 2.5,
                "3": 2.5,
                "4": 2.5,
                "5": 1.83
            }
        },
        "Figure": {
            "filename": "20260109_142622_439.png",
            "filepath": "D:\\05 SelfMidea\\98 SelfDevelopedTools\\02 BatchComfyuiTool\\Output\\20260109_142622_439.png",
            "original_filename": "output_189bd873-b734-4388-a7b6-36757716d13d_ComfyUI_00046_.png",
            "prompt": "A high-resolution 8K cinematic shot, extreme detail. The core subject is a close-up of a laptop screen in a dimly lit room. The screen clearly displays the WikiLeaks website interface, with a PDF document titled \"How to Survive Secondary Screening\" opened and its title highlighted by a bright red rectangular glow or cursor selection. The environment is a shadowy, nondescript workspace, with the primary light source being the cold, blue-tinged glow from the monitor, casting dramatic shadows. The atmosphere is mysterious, tense, and suspenseful. The composition is a tight, focused shot on the screen, with the background softly blurred to emphasize the document. The style is hyper-realistic, with a cool color palette dominated by blues and grays. No watermarks, no extraneous elements, moderate color saturation.",
            "timestamp": "20260109_142622_439"
        }
    }
    
    test_save_dir = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\Output"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    
    # 调用函数
    result_json = GenerateVideoByStoryboard(test_storyboard_json, test_save_dir, test_server_url)
    
    if "Video" in result_json:
        print(f"\n✅ 测试成功！")
        print(f"📋 生成的视频信息: {result_json['Video']}")
    else:
        print(f"\n❌ 测试失败！")
    
    return result_json


def BatchGenerateFigureAndVideoByStoryboard(json_file_path, save_dir, server_url):
    """
    批量生成图片和视频，并将视频拼接为一个大视频
    
    Args:
        json_file_path: 包含分镜信息的json文件路径
        save_dir: 保存地址字符串
        server_url: 服务器地址
        
    Returns:
        处理结果，成功返回True，失败返回False
    """
    print(f"\n=== 开始批量生成图片和视频并拼接 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📁 保存地址: {save_dir}")
    print(f"🔌 服务器地址: {server_url}")
    
    try:
        # 创建保存地址目录（如果不存在）
        os.makedirs(save_dir, exist_ok=True)
        print(f"📁 已确保保存地址目录存在: {save_dir}")
        
        # 2. 调用BatchGenerateFigure生成图片
        print(f"\n=== 第一步：生成图片 ===")
        result_file = BatchGenerateFigure(json_file_path, server_url)
        
        # 如果生成出现问题，则重试一次
        if not result_file:
            print(f"❌ 第一次生成图片失败，准备重试...")
            result_file = BatchGenerateFigure(json_file_path, server_url)
            if not result_file:
                print(f"❌ 第二次生成图片失败，退出程序")
                return False
        
        print(f"✅ 图片生成成功，结果文件: {result_file}")
        
        # 3. 读取分镜信息json文件
        print(f"\n=== 第二步：读取分镜信息 ===")
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                storyboard_data = json.load(f)
        except Exception as e:
            print(f"❌ 读取分镜信息json文件失败: {str(e)}")
            return False
        
        if not isinstance(storyboard_data, list):
            print(f"❌ 分镜信息json文件格式错误，预期为列表格式")
            return False
        
        print(f"🔍 共发现 {len(storyboard_data)} 个分镜")
        
        # 4. 依次生成视频
        print(f"\n=== 第三步：生成视频 ===")
        processed_storyboards = []
        video_files = []
        
        for i, storyboard in enumerate(storyboard_data):
            print(f"\n=== 处理分镜 {i+1}/{len(storyboard_data)} ===")
            
            # 调用GenerateVideoByStoryboard生成视频，失败则重试一次
            result_json = None
            
            # 第一次尝试
            try:
                result_json = GenerateVideoByStoryboard(storyboard, save_dir, server_url)
            except Exception as e:
                print(f"❌ 第一次生成视频失败: {str(e)}")
            
            # 如果第一次失败，重试一次
            if not result_json or "Video" not in result_json:
                print(f"❌ 第一次生成视频失败，准备重试...")
                try:
                    result_json = GenerateVideoByStoryboard(storyboard, save_dir, server_url)
                except Exception as e:
                    print(f"❌ 第二次生成视频失败: {str(e)}")
                
                if not result_json or "Video" not in result_json:
                    print(f"❌ 第二次生成视频失败，退出程序")
                    return False
            
            print(f"✅ 分镜 {i+1} 视频生成成功")
            processed_storyboards.append(result_json)
            
            # 收集视频文件信息
            video_info = result_json.get("Video", {})
            video_filepath = video_info.get("filepath", "")
            if video_filepath and os.path.exists(video_filepath):
                video_files.append(video_filepath)
                print(f"🎬 收集到视频文件: {video_filepath}")
        
        # 5. 保存所有处理后的分镜信息为一个大的json文件
        print(f"\n=== 第四步：保存处理后的分镜信息 ===")
        # 生成输出文件名
        base_name = os.path.splitext(json_file_path)[0]
        output_json_filename = f"{base_name}_WithVideo.json"
        
        try:
            with open(output_json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_storyboards, f, ensure_ascii=False, indent=2)
            print(f"🎉 处理后的分镜信息已保存到: {output_json_filename}")
        except Exception as e:
            print(f"❌ 保存处理后的分镜信息失败: {str(e)}")
            return False
        
        # 6. 拼接所有视频为一个大视频
        print(f"\n=== 第五步：拼接视频 ===")
        if video_files:
            print(f"🎬 共收集到 {len(video_files)} 个视频文件，准备拼接")
            
            # 生成输出视频文件名
            output_video_filename = f"{os.path.splitext(os.path.basename(json_file_path))[0]}.mp4"
            output_video_path = os.path.join(save_dir, output_video_filename)
            
            try:
                # 导入moviepy库
                from moviepy.video.io.VideoFileClip import VideoFileClip
                from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
                
                # 加载所有视频片段
                video_clips = []
                for video_path in video_files:
                    try:
                        clip = VideoFileClip(video_path)
                        video_clips.append(clip)
                        print(f"✅ 加载视频片段: {os.path.basename(video_path)}")
                    except Exception as e:
                        print(f"❌ 加载视频片段失败 {video_path}: {str(e)}")
                        # 关闭已加载的视频片段
                        for loaded_clip in video_clips:
                            loaded_clip.close()
                        return False
                
                if not video_clips:
                    print(f"❌ 没有可用的视频片段进行拼接")
                    return False
                
                # 拼接视频
                final_clip = concatenate_videoclips(video_clips)
                
                # 保存拼接后的视频
                final_clip.write_videofile(output_video_path, codec="libx264")
                print(f"🎉 拼接视频已保存到: {output_video_path}")
                
                # 关闭所有视频片段
                for clip in video_clips:
                    clip.close()
                final_clip.close()
            except Exception as e:
                print(f"❌ 拼接视频失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print(f"❌ 没有收集到任何视频文件，无法拼接")
            return False
        
        print(f"\n🎉 批量生成图片和视频并拼接完成！")
        print(f"📋 处理后的分镜信息文件: {output_json_filename}")
        print(f"🎬 拼接后的视频文件: {output_video_path}")
        return True
    except Exception as e:
        print(f"❌ 批量生成图片和视频并拼接失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_BatchGenerateFigureAndVideoByStoryboard():
    """
    测试BatchGenerateFigureAndVideoByStoryboard函数
    """
    print("=== 测试BatchGenerateFigureAndVideoByStoryboard函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo_AddPrompt_Concurrent.json"
    test_save_dir = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\TestOutput_Full"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    
    # 调用函数
    result = BatchGenerateFigureAndVideoByStoryboard(test_json_file, test_save_dir, test_server_url)
    
    if result:
        print(f"\n✅ 测试成功！")
    else:
        print(f"\n❌ 测试失败！")
    
    return result


def TaskCheck(json_file_path):
    """
    检查提供的json文件是否有待完成的生成任务
    
    Args:
        json_file_path: JSON文件路径，包含分镜信息
        
    Returns:
        更新后的JSON数据，列表格式
    """
    print(f"\n=== 开始检查任务状态 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 处理每个分镜
    for i, item in enumerate(data):
        print(f"\n=== 处理分镜 {i+1}/{len(data)} ===")
        
        # 2.1 检查必要字段
        required_fields = ['text', 'audio', 'duration', 'chapter', 'description']
        missing_fields = [field for field in required_fields if field not in item]
        if missing_fields:
            print(f"❌ 分镜 {i+1} 缺少必要字段: {missing_fields}")
            return None
        
        print(f"✅ 分镜 {i+1} 必要字段检查通过")
        
        # 2.2 检查并创建Update_Flag字段
        for flag in ['Prompt_Update_Flag', 'Figure_Update_Flag', 'Video_Update_Flag']:
            if flag not in item:
                item[flag] = 0
        
        # 2.3 检查Prompt_Figure和Prompt_Video字段
        if 'Prompt_Figure' not in item or 'Prompt_Video' not in item:
            item['Prompt_Update_Flag'] = 1
            print(f"⚠️  分镜 {i+1} 缺少Prompt字段，设置Prompt_Update_Flag=1")
        
        # 2.4 检查Figure字段
        if 'Figure' not in item:
            item['Figure_Update_Flag'] = 1
            print(f"⚠️  分镜 {i+1} 缺少Figure字段，设置Figure_Update_Flag=1")
        else:
            figure_filepath = item['Figure'].get('filepath', '')
            if not figure_filepath or not os.path.exists(figure_filepath):
                item['Figure_Update_Flag'] = 1
                print(f"⚠️  分镜 {i+1} Figure文件不存在，设置Figure_Update_Flag=1")
        
        # 2.5 检查Video字段
        if 'Video' not in item:
            item['Video_Update_Flag'] = 1
            print(f"⚠️  分镜 {i+1} 缺少Video字段，设置Video_Update_Flag=1")
        else:
            video_filepath = item['Video'].get('filepath', '')
            if not video_filepath or not os.path.exists(video_filepath):
                item['Video_Update_Flag'] = 1
                print(f"⚠️  分镜 {i+1} Video文件不存在，设置Video_Update_Flag=1")
    
    # 保存更新后的JSON文件
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 任务检查完成！")
        print(f"💾 结果保存到: {json_file_path}")
        
        # 统计需要更新的任务
        prompt_update_count = sum(1 for item in data if item.get('Prompt_Update_Flag', 0) == 1)
        figure_update_count = sum(1 for item in data if item.get('Figure_Update_Flag', 0) == 1)
        video_update_count = sum(1 for item in data if item.get('Video_Update_Flag', 0) == 1)
        
        print(f"📊 需要更新的任务统计:")
        print(f"   - 需要生成提示词的分镜: {prompt_update_count}")
        print(f"   - 需要生成图片的分镜: {figure_update_count}")
        print(f"   - 需要生成视频的分镜: {video_update_count}")
        
        return data
    except Exception as e:
        print(f"❌ 保存结果失败: {str(e)}")
        return None


def show_test_menu():
    """
    显示测试菜单
    """
    print("\n=== 测试函数选择菜单 ===")
    print("1. 测试 BatchGeneratePrompt (串行版本)")
    print("2. 测试 BatchGeneratePromptConcurrent (并发版本)")
    print("3. 测试 BatchGeneratePromptConcurrentByCondition (根据条件并发生成提示词)")
    print("4. 测试 BatchGenerateFigure (生成图片)")
    print("5. 测试 BatchGenerateVideo (生成视频)")
    print("6. 测试 BatchGenerateFigureAndVideo (生成图片和视频)")
    print("7. 测试 get_last_frame (提取视频最后一帧)")
    print("8. 测试 GenerateVideoByStoryboard (根据分镜生成视频)")
    print("9. 测试 BatchGenerateFigureAndVideoByStoryboard (批量生成图片和视频并拼接)")
    print("10. 测试 TaskCheck (检查任务状态)")
    print("11. 测试 BatchGenerateFigureByCondition (根据条件生成图片)")
    print("12. 测试 BatchGeneratePromptFigureVideoByStoryboardByCondition (批量生成提示词、图片和视频)")
    print("13. 测试 BatchGenerateAll_AutoDL_Management (批量生成视频并管理AutoDL实例)")
    print("14. 测试所有函数")
    print("0. 退出")
    print("=======================")


def BatchGenerateFigureByCondition(json_file_path, save_dir, server_url):
    """
    根据条件批量生成图片
    
    Args:
        json_file_path: 包含分镜信息的JSON文件路径
        save_dir: 保存地址字符串
        server_url: 服务器地址
        
    Returns:
        处理后的JSON文件路径
    """
    print(f"\n=== 开始根据条件批量生成图片 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📁 保存地址: {save_dir}")
    print(f"🔌 服务器地址: {server_url}")
    
    # 创建保存地址目录（如果不存在）
    os.makedirs(save_dir, exist_ok=True)
    print(f"📁 已确保保存地址目录存在: {save_dir}")
    
    # 读取输入JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {str(e)}")
        return None
    
    # 检查数据格式
    if not isinstance(data, list):
        print(f"❌ JSON文件格式错误，预期为列表格式")
        return None
    
    print(f"🔍 共发现 {len(data)} 个分镜")
    
    # 创建QwenImageGenerator实例
    generator = QwenImageGenerator(server_url=server_url)
    
    # 批量生成图片
    for i, item in enumerate(data):
        print(f"\n=== 处理分镜 {i+1}/{len(data)} ===")
        
        # 2.1 检查Prompt_Update_Flag
        prompt_update_flag = item.get("Prompt_Update_Flag", 0)
        if prompt_update_flag == 1:
            print(f"⚠️ 分镜 {i+1} 需要先生成提示词！")
            continue
        
        # 2.2 检查Figure_Update_Flag
        figure_update_flag = item.get("Figure_Update_Flag", 0)
        if figure_update_flag == 0:
            print(f"⚠️ 分镜 {i+1} 无需生成图片，跳过处理")
            continue
        
        # 2.3 设置Video_Update_Flag为1
        item["Video_Update_Flag"] = 1
        print(f"📝 已设置Video_Update_Flag为1")
        
        # 2.4 提取Prompt_Figure字段
        prompt_figure = item.get("Prompt_Figure", "")
        if not prompt_figure:
            print(f"⚠️ 分镜 {i+1} 缺少Prompt_Figure字段，跳过处理")
            continue
        
        print(f"📝 提示词: {prompt_figure[:50]}...")
        
        # 调用生成函数
        try:
            result = generator.generate(
                prompt=prompt_figure,
                seed=None
            )
            
            if result and result.get("success"):
                # 获取生成的图片信息
                local_filename = result.get("local_filename")
                if local_filename and os.path.exists(local_filename):
                    # 生成成功后，将Figure_Update_Flag改为0
                    item["Figure_Update_Flag"] = 0
                    print(f"📝 已将Figure_Update_Flag设置为0")
                    
                    # 生成新的文件名（日期时间戳）
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    new_filename = f"{timestamp}.png"
                    new_filepath = os.path.join(save_dir, new_filename)
                    
                    # 复制文件到保存地址
                    import shutil
                    shutil.copy2(local_filename, new_filepath)
                    print(f"💾 图片已保存到: {new_filepath}")
                    
                    # 更新json对象，添加Figure字段
                    item["Figure"] = {
                        "filename": new_filename,
                        "filepath": new_filepath,
                        "original_filename": local_filename,
                        "prompt": prompt_figure,
                        "timestamp": timestamp
                    }
                    print(f"✅ 分镜 {i+1} 处理成功")
                else:
                    print(f"❌ 分镜 {i+1} 生成的图片文件不存在")
            else:
                print(f"❌ 分镜 {i+1} 图片生成失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"❌ 分镜 {i+1} 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存更新后的json文件
    try:
        # 1. 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 2. 解析输入文件路径
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 3. 构建备份文件名（原文件名+_时间戳+扩展名）
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 4. 输出文件路径为原输入文件名
        output_file_path = json_file_path
        
        print(f"\n=== 开始保存结果 ===")
        print(f"📋 原文件名: {input_file_name}")
        print(f"📋 备份文件名: {backup_file_name}")
        print(f"📋 输出文件名: {input_file_name}")
        
        # 5. 备份原文件
        os.rename(json_file_path, backup_file_path)
        print(f"✅ 原文件已成功备份为: {backup_file_path}")
        
        # 6. 写入新文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 新文件已成功写入: {output_file_path}")
        
        print(f"\n🎉 批量生成完成！")
        print(f"💾 结果保存到: {output_file_path}")
        return output_file_path
    except Exception as e:
        print(f"❌ 保存更新后的JSON文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_BatchGenerateFigureByCondition():
    """
    测试BatchGenerateFigureByCondition函数
    """
    print("=== 测试 BatchGenerateFigureByCondition 函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy_AddPrompt_Concurrent_WithVideo.json"
    test_save_dir = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\02 BatchComfyuiTool\\TestOutput"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    
    # 调用函数
    result_file = BatchGenerateFigureByCondition(test_json_file, test_save_dir, test_server_url)
    
    if result_file:
        print(f"\n✅ 测试成功！")
        print(f"📋 更新后的结果文件: {result_file}")
    else:
        print(f"\n❌ 测试失败！")


def BatchGeneratePromptFigureVideoByStoryboardByCondition(json_file_path, save_dir, server_url, video_summary):
    """
    批量生成提示词、图片和视频，并拼接为大视频
    
    Args:
        json_file_path: 包含分镜信息的JSON文件路径
        save_dir: 保存地址字符串
        server_url: 服务器地址
        video_summary: 视频梗概描述文本
    
    Returns:
        处理结果，成功返回True，失败返回False
    """
    print(f"\n=== 开始批量生成提示词、图片和视频 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📁 保存地址: {save_dir}")
    print(f"🔌 服务器地址: {server_url}")
    print(f"📝 视频梗概: {video_summary[:100]}...")
    
    # 创建保存地址目录（如果不存在）
    os.makedirs(save_dir, exist_ok=True)
    print(f"📁 已确保保存地址目录存在: {save_dir}")
    
    # 2. 调用TaskCheck函数处理分镜信息
    print(f"\n=== 第一步：检查任务状态 ===")
    task_data = TaskCheck(json_file_path)
    if not task_data:
        print(f"❌ TaskCheck处理失败，退出程序")
        return False
    print(f"✅ TaskCheck处理成功")
    
    # 3. 调用BatchGeneratePromptConcurrentByCondition生成提示词
    print(f"\n=== 第二步：生成提示词 ===")
    prompt_result = BatchGeneratePromptConcurrentByCondition(json_file_path, video_summary)
    
    # 如果生成出现问题，则重试一次
    if not prompt_result:
        print(f"❌ 第一次生成提示词失败，准备重试...")
        prompt_result = BatchGeneratePromptConcurrentByCondition(json_file_path, video_summary)
        if not prompt_result:
            print(f"❌ 第二次生成提示词失败，退出程序")
            return False
    print(f"✅ 提示词生成成功")
    
    # 4. 调用BatchGenerateFigureByCondition生成图片
    print(f"\n=== 第三步：生成图片 ===")
    figure_result = BatchGenerateFigureByCondition(json_file_path, save_dir, server_url)
    
    # 如果生成出现问题，则重试一次
    if not figure_result:
        print(f"❌ 第一次生成图片失败，准备重试...")
        figure_result = BatchGenerateFigureByCondition(json_file_path, save_dir, server_url)
        if not figure_result:
            print(f"❌ 第二次生成图片失败，退出程序")
            return False
    print(f"✅ 图片生成成功")
    
    # 5. 依次处理每个分镜，生成视频
    print(f"\n=== 第四步：生成视频 ===")
    
    # 读取分镜信息
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            storyboard_data = json.load(f)
    except Exception as e:
        print(f"❌ 读取分镜信息失败: {str(e)}")
        return False
    
    if not isinstance(storyboard_data, list):
        print(f"❌ 分镜信息格式错误，预期为列表格式")
        return False
    
    print(f"🔍 共发现 {len(storyboard_data)} 个分镜")
    
    processed_storyboards = []
    video_files = []
    
    for i, storyboard in enumerate(storyboard_data):
        print(f"\n=== 处理分镜 {i+1}/{len(storyboard_data)} ===")
        
        # 4.1 检查Video_Update_Flag
        video_update_flag = storyboard.get("Video_Update_Flag", 0)
        if video_update_flag == 0:
            print(f"⚠️ 分镜 {i+1} Video_Update_Flag为0，跳过生成视频")
            # 检查是否已存在Video字段，如果存在则收集视频文件路径
            video_info = storyboard.get("Video", {})
            video_filepath = video_info.get("filepath", "")
            if video_filepath and os.path.exists(video_filepath):
                video_files.append(video_filepath)
                print(f"🎬 分镜 {i+1} 已存在视频，收集到视频文件: {video_filepath}")
            processed_storyboards.append(storyboard)
            continue
        
        # 4.2 调用GenerateVideoByStoryboard生成视频，支持重试
        result_json = None
        
        # 第一次尝试
        try:
            result_json = GenerateVideoByStoryboard(storyboard, save_dir, server_url)
        except Exception as e:
            print(f"❌ 第一次生成视频失败: {str(e)}")
        
        # 如果第一次失败，重试一次
        if not result_json or "Video" not in result_json:
            print(f"❌ 第一次生成视频失败，准备重试...")
            try:
                result_json = GenerateVideoByStoryboard(storyboard, save_dir, server_url)
            except Exception as e:
                print(f"❌ 第二次生成视频失败: {str(e)}")
            
            if not result_json or "Video" not in result_json:
                print(f"❌ 第二次生成视频失败，退出程序")
                return False
        
        # 4.3 生成成功，将返回的json对象的Video_Update_Flag字段设置为0，然后保存
        print(f"✅ 分镜 {i+1} 视频生成成功")
        result_json["Video_Update_Flag"] = 0
        print(f"📝 已将分镜 {i+1} 的Video_Update_Flag设置为0")
        processed_storyboards.append(result_json)
        
        # 收集视频文件信息
        video_info = result_json.get("Video", {})
        video_filepath = video_info.get("filepath", "")
        if video_filepath and os.path.exists(video_filepath):
            video_files.append(video_filepath)
            print(f"🎬 收集到视频文件: {video_filepath}")
    
    # 4.4 保存所有json对象到文件
    print(f"\n=== 第五步：保存分镜信息 ===")
    try:
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 解析输入文件路径
        input_file_dir = os.path.dirname(json_file_path)
        input_file_name = os.path.basename(json_file_path)
        input_file_base, input_file_ext = os.path.splitext(input_file_name)
        
        # 构建备份文件名
        backup_file_name = f"{input_file_base}_{timestamp}{input_file_ext}"
        backup_file_path = os.path.join(input_file_dir, backup_file_name)
        
        # 输出文件路径为原输入文件名
        output_file_path = json_file_path
        
        print(f"📋 原文件名: {input_file_name}")
        print(f"📋 备份文件名: {backup_file_name}")
        print(f"📋 输出文件名: {input_file_name}")
        
        # 备份原文件
        os.rename(json_file_path, backup_file_path)
        print(f"✅ 原文件已成功备份为: {backup_file_path}")
        
        # 写入新文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_storyboards, f, ensure_ascii=False, indent=2)
        print(f"✅ 新文件已成功写入: {output_file_path}")
    except Exception as e:
        print(f"❌ 保存分镜信息失败: {str(e)}")
        return False
    
    # 5. 拼接所有视频为一个大视频
    print(f"\n=== 第六步：拼接视频 ===")
    if video_files:
        print(f"🎬 共收集到 {len(video_files)} 个视频文件，准备拼接")
        
        # 生成输出视频文件名
        input_file_base = os.path.splitext(os.path.basename(json_file_path))[0]
        output_video_filename = f"{input_file_base}.mp4"
        output_video_path = os.path.join(save_dir, output_video_filename)
        
        # 检查输出文件是否存在，如果存在则备份
        if os.path.exists(output_video_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            backup_video_filename = f"{input_file_base}_{timestamp}.mp4"
            backup_video_path = os.path.join(save_dir, backup_video_filename)
            os.rename(output_video_path, backup_video_path)
            print(f"📋 原视频文件已备份为: {backup_video_path}")
        
        try:
            # 导入moviepy库
            from moviepy.video.io.VideoFileClip import VideoFileClip
            from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
            
            # 加载所有视频片段
            video_clips = []
            for video_path in video_files:
                try:
                    clip = VideoFileClip(video_path)
                    video_clips.append(clip)
                    print(f"✅ 加载视频片段: {os.path.basename(video_path)}")
                except Exception as e:
                    print(f"❌ 加载视频片段失败 {video_path}: {str(e)}")
                    # 关闭已加载的视频片段
                    for loaded_clip in video_clips:
                        loaded_clip.close()
                    return False
            
            if not video_clips:
                print(f"❌ 没有可用的视频片段进行拼接")
                return False
            
            # 拼接视频
            final_clip = concatenate_videoclips(video_clips)
            
            # 保存拼接后的视频
            final_clip.write_videofile(output_video_path, codec="libx264")
            print(f"🎉 拼接视频已保存到: {output_video_path}")
            
            # 关闭所有视频片段
            for clip in video_clips:
                clip.close()
            final_clip.close()
        except Exception as e:
            print(f"❌ 拼接视频失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"⚠️ 没有收集到任何视频文件，跳过视频拼接")
    
    print(f"\n🎉 批量生成提示词、图片和视频完成！")
    print(f"📋 处理后的分镜信息文件: {output_file_path}")
    if video_files:
        print(f"🎬 拼接后的视频文件: {output_video_path}")
    return True


def test_BatchGeneratePromptFigureVideoByStoryboardByCondition():
    """
    测试BatchGeneratePromptFigureVideoByStoryboardByCondition函数
    """
    print("=== 测试 BatchGeneratePromptFigureVideoByStoryboardByCondition 函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy.json"
    test_save_dir = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\TestOutput"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    test_video_summary = "一份泄露的中情局\"机场二次安检生存指南\"揭示了间谍与安检系统的秘密对抗。\n引言：一份泄露的绝密指南\n2014年，维基解密曝光了一份中情局机密文件《如何在二次安检中活下来》，旨在指导特工用假身份通过全球机场的严密审查。\n第一章：无声的战场——二次安检\n二次安检是包含严苛盘问、法医级设备搜查和生物信息采集的深度审查。对特工而言，进入此处即意味着身份暴露的高风险。\n第二章：鹰眼无处不在——谁在盯着你\n监控网络无处不在。除明显问题外，紧张神态、临期单程机票、旅行历史矛盾等细节都可能引致怀疑，甚至存在随机抽查。\n第三章：特工的真实梦魇——全球机场案例实录\n文件记录了真实案例：有特工因着装与外交身份不符、行李检测出爆炸物痕迹而被审查；在某些国家，电子设备中的可疑内容会招致大祸。\n第四章：终极守则——无论如何，守住你的秘密\n核心建议是\"保持身份掩护\"。必须准备天衣无缝的虚假背景故事，确保所有物品和数字痕迹与之匹配，盘问时冷静、简洁。\n结语：你我皆是局中人\n这份间谍指南映射出现代社会无处不在的监控。它提醒人们，在便捷出行的背后，行为与数据正被持续记录和分析。"
    
    # 调用函数
    result = BatchGeneratePromptFigureVideoByStoryboardByCondition(
        test_json_file, test_save_dir, test_server_url, test_video_summary
    )
    
    if result:
        print(f"\n✅ 测试成功！")
    else:
        print(f"\n❌ 测试失败！")
    
    return result


def BatchGenerateAll_AutoDL_Management(json_file_path, save_dir, server_url, autodl_token, instance_id, video_summary):
    """
    批量生成视频并管理AutoDL实例
    
    Args:
        json_file_path: 包含分镜信息的JSON文件路径
        save_dir: 保存地址字符串
        server_url: 服务器地址
        autodl_token: AutoDL的token
        instance_id: 实例id
        video_summary: 视频梗概描述文本
    
    Returns:
        处理结果，成功返回True，失败返回False
    """
    print(f"\n=== 开始批量生成视频并管理AutoDL实例 ===")
    print(f"📋 输入JSON文件: {json_file_path}")
    print(f"📁 保存地址: {save_dir}")
    print(f"🔌 服务器地址: {server_url}")
    print(f"🆔 实例ID: {instance_id}")
    print(f"📝 视频梗概: {video_summary[:100]}...")
    
    # 导入AutoDLAPI类
    from AutoDL_API import AutoDLAPI
    import time
    
    # 创建AutoDLAPI实例
    autodl_api = AutoDLAPI(token=autodl_token)
    
    # 2. 开机应用实例
    print(f"\n=== 第一步：开机AutoDL实例 ===")
    try:
        start_result = autodl_api.start_instance(instance_uuid=instance_id)
        if start_result and start_result.get("code") == "Success":
            print(f"✅ 成功调用开机API，正在等待实例启动...")
            # 等待30秒，让实例有足够时间启动
            time.sleep(60)
            print(f"✅ 实例启动等待完成")
        else:
            print(f"❌ 开机API调用失败: {start_result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 开机过程中发生异常: {str(e)}")
        return False
    
    # 3. 执行批量生成任务
    print(f"\n=== 第二步：执行批量生成任务 ===")
    try:
        # 调用BatchGeneratePromptFigureVideoByStoryboardByCondition函数
        generate_result = BatchGeneratePromptFigureVideoByStoryboardByCondition(
            json_file_path, save_dir, server_url, video_summary
        )
        print(f"📋 批量生成任务执行结果: {'成功' if generate_result else '失败'}")
    except Exception as e:
        print(f"❌ 批量生成任务执行过程中发生异常: {str(e)}")
        # 即使生成任务失败，也要确保实例能够关闭
        generate_result = False
    
    # 4. 关机应用实例，确保在各种情况下都能执行
    print(f"\n=== 第三步：关机AutoDL实例 ===")
    max_retry = 5  # 最大重试次数
    retry_interval = 15  # 重试间隔，秒
    shutdown_success = False
    
    for retry_count in range(max_retry):
        try:
            print(f"🔄 尝试关闭实例 (第 {retry_count+1}/{max_retry} 次)")
            stop_result = autodl_api.stop_instance(instance_uuid=instance_id)
            if stop_result and stop_result.get("code") == "Success":
                print(f"✅ 成功关闭AutoDL实例")
                shutdown_success = True
                break
            else:
                error_msg = stop_result.get('msg', '未知错误')
                print(f"❌ 第 {retry_count+1} 次关闭实例失败: {error_msg}")
                if retry_count < max_retry - 1:
                    print(f"⏱️  将在 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
        except Exception as e:
            print(f"❌ 第 {retry_count+1} 次关闭实例时发生异常: {str(e)}")
            if retry_count < max_retry - 1:
                print(f"⏱️  将在 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
    
    if not shutdown_success:
        print(f"❌ 多次尝试关闭实例失败，建议手动检查实例状态")
        return False
    
    print(f"\n🎉 批量生成视频并管理AutoDL实例完成！")
    print(f"📋 生成任务结果: {'成功' if generate_result else '失败'}")
    print(f"🖥️  实例管理结果: 成功关闭实例")
    
    return generate_result


def test_BatchGenerateAll_AutoDL_Management():
    """
    测试BatchGenerateAll_AutoDL_Management函数
    """
    print("=== 测试 BatchGenerateAll_AutoDL_Management 函数 ===")
    
    # 测试参数
    test_json_file = "ExportAudioInfo copy.json"
    test_save_dir = r"D:\05 SelfMidea\98 SelfDevelopedTools\02 BatchComfyuiTool\TestOutput"
    test_server_url = "https://u816948-7674d442b461.westd.seetacloud.com:8443/"
    test_autodl_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjgxNjk0OCwidXVpZCI6ImUwMzAzNjg5OWIxOTAzMGIiLCJpc19hZG1pbiI6ZmFsc2UsImJhY2tzdGFnZV9yb2xlIjoiIiwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJzdWJfbmFtZSI6IiIsInRlbmFudCI6ImF1dG9kbCIsInVwayI6IiJ9.GeK7Rw_sOejJ6T-lJRIC905u2yIxT3VnyHEpDJt-fClM_qXcKsZuDt1r5Hm0MGYG0VxwlVPz6NcGILwKDgWzvg"
    test_instance_id = "pro-7674d442b461"
    test_video_summary = "一份泄露的中情局\"机场二次安检生存指南\"揭示了间谍与安检系统的秘密对抗。\n引言：一份泄露的绝密指南\n2014年，维基解密曝光了一份中情局机密文件《如何在二次安检中活下来》，旨在指导特工用假身份通过全球机场的严密审查。\n第一章：无声的战场——二次安检\n二次安检是包含严苛盘问、法医级设备搜查和生物信息采集的深度审查。对特工而言，进入此处即意味着身份暴露的高风险。\n第二章：鹰眼无处不在——谁在盯着你\n监控网络无处不在。除明显问题外，紧张神态、临期单程机票、旅行历史矛盾等细节都可能引致怀疑，甚至存在随机抽查。\n第三章：特工的真实梦魇——全球机场案例实录\n文件记录了真实案例：有特工因着装与外交身份不符、行李检测出爆炸物痕迹而被审查；在某些国家，电子设备中的可疑内容会招致大祸。\n第四章：终极守则——无论如何，守住你的秘密\n核心建议是\"保持身份掩护\"。必须准备天衣无缝的虚假背景故事，确保所有物品和数字痕迹与之匹配，盘问时冷静、简洁。\n结语：你我皆是局中人\n这份间谍指南映射出现代社会无处不在的监控。它提醒人们，在便捷出行的背后，行为与数据正被持续记录和分析。"
    
    # 调用函数
    result = BatchGenerateAll_AutoDL_Management(
        test_json_file, test_save_dir, test_server_url, 
        test_autodl_token, test_instance_id, test_video_summary
    )
    
    if result:
        print(f"\n✅ 测试成功！")
    else:
        print(f"\n❌ 测试失败！")
    
    return result


def test_TaskCheck():
    """
    测试TaskCheck函数
    """
    print("=== 测试 TaskCheck 函数 ===")
    
    # 测试参数
    test_json_file = "D:\\05 SelfMidea\\98 SelfDevelopedTools\\02 BatchComfyuiTool\\ExportAudioInfo.json"
    
    # 调用函数
    result = TaskCheck(test_json_file)
    
    if result:
        print(f"\n✅ 测试成功！")
        print(f"📋 共处理 {len(result)} 个分镜")
    else:
        print(f"\n❌ 测试失败！")


def run_test(choice):
    """
    根据选择执行对应的测试函数
    
    Args:
        choice: 用户选择的测试选项
    """
    print(f"\n=== 执行测试选择: {choice} ===")
    if choice == "1":
        test_BatchGeneratePrompt()
    elif choice == "2":
        test_BatchGeneratePromptConcurrent()
    elif choice == "3":
        test_BatchGeneratePromptConcurrentByCondition()
    elif choice == "4":
        test_BatchGenerateFigure()
    elif choice == "5":
        test_BatchGenerateVideo()
    elif choice == "6":
        test_BatchGenerateFigureAndVideo()
    elif choice == "7":
        test_get_last_frame()
    elif choice == "8":
        test_GenerateVideoByStoryboard()
    elif choice == "9":
        test_BatchGenerateFigureAndVideoByStoryboard()
    elif choice == "10":
        test_TaskCheck()
    elif choice == "11":
        test_BatchGenerateFigureByCondition()
    elif choice == "12":
        test_BatchGeneratePromptFigureVideoByStoryboardByCondition()
    elif choice == "13":
        test_BatchGenerateAll_AutoDL_Management()
    elif choice == "14":
        # 测试所有函数
        print("\n=== 开始测试所有函数 ===")
        test_BatchGeneratePrompt()
        test_BatchGeneratePromptConcurrent()
        test_BatchGeneratePromptConcurrentByCondition()
        test_BatchGenerateFigure()
        test_BatchGenerateVideo()
        test_BatchGenerateFigureAndVideo()
        test_get_last_frame()
        test_GenerateVideoByStoryboard()
        test_BatchGenerateFigureAndVideoByStoryboard()
        test_TaskCheck()
        test_BatchGenerateFigureByCondition()
        test_BatchGeneratePromptFigureVideoByStoryboardByCondition()
        # 注意：AutoDL管理测试涉及实例开机/关机，不自动测试
        print("\n⚠️  跳过BatchGenerateAll_AutoDL_Management测试（涉及实例开机/关机操作）")
        print("\n=== 所有函数测试完成 ===")
    elif choice == "0":
        print("\n=== 退出测试 ===")
        return False
    else:
        print(f"\n❌ 无效的选择: {choice}")
    return True


if __name__ == "__main__":
    """
    主函数，支持根据选择测试各个函数
    """
    import sys
    
    print("=== GenerateVideo.py 执行 ===")
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 从命令行参数获取测试选择
        choice = sys.argv[1]
        run_test(choice)
    else:
        # 交互式菜单选择
        while True:
            show_test_menu()
            choice = input("请输入您要测试的函数编号 (0-12): ")
            if not run_test(choice):
                break
    
    print("\n=== 执行完成 ===")
