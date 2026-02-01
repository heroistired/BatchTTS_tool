#!/usr/bin/env python3
"""
Generation Prompt LLM using DeepSeek with LangChain
用于生成视频分镜的首帧提示词和视频提示词
"""

import json
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

class GenerationPromptLLM:
    """
    Generation Prompt LLM using DeepSeek API
    用于生成视频分镜的首帧提示词和视频提示词
    """
    
    def __init__(self):
        # DeepSeek API Key
        self.api_key = "sk-d435e8c67d4a44a88f00ee0310371757"
        
        # Create ChatDeepSeek instance
        self.llm = ChatDeepSeek(
            api_key=self.api_key,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=2048
        )
        
        # Create output parser
        self.output_parser = StrOutputParser()
        
        # Default system prompt for generation prompt
        self.default_system_prompt = '''你是一位复合型人才，同时具备专业的自媒体视频制作人和专业的提示词工程师的技能，你的任务是根据我提供的视频解说词的概要、以及分镜信息（json格式），完成以下任务：
1、分析给出的分镜信息是否合适，可以进行修改或者改进。
2、撰写生成此分镜视频首帧的提示词（英文），要求如下：
2.1、核心信息完整：必须精准提炼分镜中首帧的画面主体、场景环境、人物 / 物体状态、核心动作等关键内容，确保画面与分镜描述一致。
2.2、画质与风格明确：默认要求 8K 超高清分辨率、电影级画质、极致细节刻画，风格需贴合分镜整体调性（如写实、治愈、科幻、悬疑等），若分镜未明确风格则按写实风格生成。
2.3、光影与氛围适配：根据分镜描述的场景氛围，明确光影方向（如侧光、逆光）、色调（暖黄、冷蓝、高饱和等）、氛围感关键词（如温馨、压抑、宏大、静谧），增强画面的情绪表达。
2.4、构图与细节优化：补充构图逻辑（如对称构图、特写镜头、全景视角），明确画面虚实关系（如背景虚化突出主体），标注无水印、无多余元素、色彩饱和度适中的优化要求。
2.5、格式清晰易懂：需按 "核心主体 + 场景环境 + 动作状态 + 光影氛围 + 画质参数 + 优化要求" 的逻辑排序，语言简洁精准，适配主流文生图模型的识别习惯。
3、撰写根据视频首帧图片生成此分镜视频的提示词（英文），提示词要求如下：
3.1、从我提供给你的分镜信息中提取出此段分镜的长度，按照每2秒一个画面环节，需清晰描述画面的视觉内容、镜头运动、场景变化及元素演进，确保过渡自然连贯。
3.2、例如，分镜长度6.5秒，则划分3个画面环境，提示词中可以描述"首先，xxx，然后xxx，最后xx"
3.3、严格贴合分镜描述的核心情节、风格基调、人物 / 场景设定，同时以首帧图片为视觉基础，延续其色彩、画质、构图质感；

给你提供的视频解说词梗概有如下特征：
1、篇幅不要超过300字，简洁清楚，保留关键信息。
2、如果有章节标题，会在梗概中包含。

给你提供的分镜json格式信息示例如下：
{
    "text": "每一个角落都可能上演着一场惊心动魄的猫鼠游戏。这群人，就是来自世界各国的情报人员，我们通常称之为\"特工\"。",
    "audio": "20260106_155632.wav",
    "duration": 9.06,
    "chapter": "第一章：看不见的战场：机场里的猫鼠游戏",
    "description": "镜头色调转为冷峻、悬疑。画面是机场监视器的视角，镜头在机场大厅的人群中快速扫过，最终定格在一个模糊的、看不清脸的背影上。配以紧张的音乐氛围。"
  }
其中：
1、text字段：内容为这段分镜对应的具体解说词内容
2、duration字段：内容为这段分镜对应的时长，单位为秒
3、chapter字段：内容为这个分镜所属的章节名
4、description字段：内容为这个分镜的具体描述

你直接输出json格式给我，包含
1、原分镜信息json中的text、audio、duration、chapter字段的信息
2、description字段：优化或修改后的分镜描述信息
3、Prompt_Figure字段：生成此分镜视频首帧的提示词
4、Prompt_Video字段：根据视频首帧图片生成此分镜视频的提示词

请提供详细、准确的回答。'''
        
        # New system prompt with Process and duration fields
        self.new_system_prompt = '''你是一位复合型人才，同时具备专业的自媒体视频制作人和专业的提示词工程师的技能，你的任务是根据我提供的视频解说词的概要、以及分镜信息（json格式），完成以下任务：
1、分析给出的分镜信息是否合适，可以进行修改或者改进。
2、撰写生成此分镜视频首帧的提示词（中文），要求如下：
2.1、核心信息完整：必须精准提炼分镜中首帧的画面主体、场景环境、人物/物体状态、核心动作等关键内容，确保画面与分镜描述一致。
2.2、画质与风格明确：默认要求8K超高清分辨率、电影级画质、极致细节刻画，风格需贴合分镜整体调性（如写实、治愈、科幻、悬疑等），若分镜未明确风格则按写实风格生成。
2.3、光影与氛围适配：根据分镜描述的场景氛围，明确光影方向（如侧光、逆光）、色调（暖黄、冷蓝、高饱和等）、氛围感关键词（如温馨、压抑、宏大、静谧），增强画面的情绪表达。
2.4、构图与细节优化：补充构图逻辑（如对称构图、特写镜头、全景视角），明确画面虚实关系（如背景虚化突出主体），标注无水印、无多余元素、色彩饱和度适中的优化要求。
2.5、格式清晰易懂：需按 "核心主体+场景环境+动作状态+光影氛围+画质参数+优化要求" 的逻辑排序，语言简洁精准，适配主流文生图模型的识别习惯。
2.6、人物面孔、装扮必须是明朝人，禁止任何现代元素
3、撰写根据视频首帧图片生成此分镜视频的提示词（中文），提示词要求如下：
3.1、从我提供给你的分镜信息中提取出此段分镜的长度（duration字段），按照不超过3秒的标准来划分画面环节数量，画面环节数大于等于duration/3+1。
3.2、每个画面环节中需清晰描述画面的视觉内容、镜头运动、场景变化及元素演进，确保过渡自然连贯。
3.3、对每个环节单独生成提示词，并且要考虑到需要以前一个环节的尾帧作为下一个环节的首帧。
3.4、严格贴合分镜描述的核心情节、风格基调、人物/场景设定，同时以首帧图片为视觉基础，延续其色彩、画质、构图质感；
3.5、人物面孔、装扮必须是明朝人，禁止任何现代元素
3.6、提示词尽量用通用，非简写的词语或文字，避免歧义

给你提供的视频解说词梗概有如下特征：
1、篇幅不要超过300字，简洁清楚，保留关键信息。
2、如果有章节标题，会在梗概中包含。

给你提供的分镜json格式信息示例如下：
{
    "text": "每一个角落都可能上演着一场惊心动魄的猫鼠游戏。这群人，就是来自世界各国的情报人员，我们通常称之为\"特工\"。",
    "audio": "20260106_155632.wav",
    "duration": 9.06,
    "chapter": "第一章：看不见的战场：机场里的猫鼠游戏",
    "description": "镜头色调转为冷峻、悬疑。画面是机场监视器的视角，镜头在机场大厅的人群中快速扫过，最终定格在一个模糊的、看不清脸的背影上。配以紧张的音乐氛围。"
  }
其中：
1、text字段：内容为这段分镜对应的具体解说词内容
2、duration字段：内容为这段分镜对应的时长，单位为秒
3、chapter字段：内容为这个分镜所属的章节名
4、description字段：内容为这个分镜的具体描述

你直接输出json格式给我，包含
1、原分镜信息json中的text、audio、duration、chapter字段的信息
2、description字段：优化或修改后的分镜描述信息
3、Prompt_Figure字段：生成此分镜视频首帧的提示词
4、Prompt_Video字段：根据视频首帧图片生成此分镜视频的提示词，针对同一分镜的多个环节分别写内容，其下属字段格式为：
4.1、Process字段：下属字段1、2、3....存储各个环节对应的视频提示词
4.2、duration字段：下属字段1、2、3....存储各个环节对应的视频长度（注意，环节数量不限，各环节视频长度之和要与分镜总长度保持一致，各环节视频长度长度不得超过3）

请提供详细、准确的回答。'''
    
    def create_prompt_template(self, system_prompt, user_prompt):
        """
        Create a chat prompt template
        
        Args:
            system_prompt: System prompt string
            user_prompt: User prompt string
        
        Returns:
            ChatPromptTemplate instance
        """
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    def get_response(self, system_prompt, user_prompt):
        """
        Get response from LLM
        
        Args:
            system_prompt: System prompt string
            user_prompt: User prompt string
        
        Returns:
            LLM response string
        """
        # Create prompt template
        prompt_template = self.create_prompt_template(system_prompt, user_prompt)
        
        # Create chain
        chain = prompt_template | self.llm | self.output_parser
        
        # Invoke chain and get response
        response = chain.invoke({})
        
        return response
    
    def validate_response(self, response_str):
        """
        Validate LLM response
        
        Args:
            response_str: LLM response string
        
        Returns:
            Tuple (is_valid, response_dict) where:
                is_valid: bool indicating if response is valid
                response_dict: parsed response dictionary if valid, None otherwise
        """
        try:
            # Remove code block markers if present
            cleaned_response = response_str.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON response
            response_dict = json.loads(cleaned_response)
            
            # Check if response has correct structure
            if not isinstance(response_dict, dict):
                return False, None
            
            # Check required fields
            required_fields = ["text", "audio", "duration", "chapter", "description", "Prompt_Figure", "Prompt_Video"]
            for field in required_fields:
                if field not in response_dict:
                    return False, None
            
            return True, response_dict
        except json.JSONDecodeError:
            # Not a valid JSON
            return False, None
        except Exception as e:
            # Other errors
            return False, None
    
    def generate_prompt(self, video_summary, shot_json, max_retries=5):
        """
        Generate prompt using LLM with retry mechanism
        
        Args:
            video_summary: Video summary string
            shot_json: Shot information JSON string or dictionary
            max_retries: Maximum number of retries (default: 5)
        
        Returns:
            Dictionary with generated prompt information
        """
        # Convert dictionary to JSON string if needed
        if isinstance(shot_json, dict):
            shot_json = json.dumps(shot_json, ensure_ascii=False)
        
        # Create user prompt
        user_prompt = f"视频解说词梗概：\n{video_summary}\n\n分镜json信息：\n{shot_json}"
        
        # Set system prompt
        system_prompt = self.default_system_prompt
        
        # Retry loop
        for retry_count in range(max_retries):
            print(f"\n=== 第 {retry_count + 1} 次尝试 ===")
            print(f"用户提示词: {user_prompt}")
            
            # Get response from LLM
            raw_response = self.get_response(system_prompt, user_prompt)
            print(f"大模型原始响应: {raw_response}")
            
            # Validate response
            is_valid, validated_response = self.validate_response(raw_response)
            if is_valid:
                print(f"响应验证通过")
                return validated_response
            else:
                print(f"响应验证失败，将重试")
        
        # Max retries exceeded
        print(f"超过最大重试次数 ({max_retries})，返回错误")
        return {"error": "无法生成提示词"}
    
    def generate_prompt_with_process(self, video_summary, shot_json, max_retries=5):
        """
        Generate prompt using LLM with Process and duration fields in Prompt_Video
        
        Args:
            video_summary: Video summary string
            shot_json: Shot information JSON string or dictionary
            max_retries: Maximum number of retries (default: 5)
        
        Returns:
            Dictionary with generated prompt information, including Process and duration fields in Prompt_Video
        """
        # Convert dictionary to JSON string if needed
        if isinstance(shot_json, dict):
            shot_json = json.dumps(shot_json, ensure_ascii=False)
        
        # Create user prompt
        user_prompt = f"视频解说词梗概：\n{video_summary}\n\n分镜json信息：\n{shot_json}"
        
        # Set system prompt to the new one with Process and duration fields
        system_prompt = self.new_system_prompt
        
        # Retry loop
        for retry_count in range(max_retries):
            print(f"\n=== 第 {retry_count + 1} 次尝试 ===")
            print(f"用户提示词: {user_prompt}")
            
            # Get response from LLM
            raw_response = self.get_response(system_prompt, user_prompt)
            print(f"大模型原始响应: {raw_response}")
            
            # Validate response
            is_valid, validated_response = self.validate_response(raw_response)
            if is_valid:
                print(f"响应验证通过")
                return validated_response
            else:
                print(f"响应验证失败，将重试")
        
        # Max retries exceeded
        print(f"超过最大重试次数 ({max_retries})，返回错误")
        return {"error": "无法生成提示词"}

# Example usage for external calls
def generate_prompt(video_summary, shot_json, max_retries=5):
    """
    External interface for prompt generation
    
    Args:
        video_summary: Video summary string
        shot_json: Shot information JSON string or dictionary
        max_retries: Maximum number of retries (default: 5)
    
    Returns:
        Dictionary with generated prompt information
    """
    # Create LLM instance
    llm = GenerationPromptLLM()
    
    # Call generate_prompt method
    return llm.generate_prompt(video_summary, shot_json, max_retries)


def generate_prompt_with_process(video_summary, shot_json, max_retries=5):
    """
    External interface for prompt generation with Process and duration fields in Prompt_Video
    
    Args:
        video_summary: Video summary string
        shot_json: Shot information JSON string or dictionary
        max_retries: Maximum number of retries (default: 5)
    
    Returns:
        Dictionary with generated prompt information, including Process and duration fields in Prompt_Video
    """
    # Create LLM instance
    llm = GenerationPromptLLM()
    
    # Call generate_prompt_with_process method
    return llm.generate_prompt_with_process(video_summary, shot_json, max_retries)

if __name__ == "__main__":
    # Example usage
    print("=== Generation Prompt LLM ===")
    
    # Test video summary
    test_video_summary = "本视频解析中情局指导特工应对机场\"二次审查\"的内部文件。第一章：看不见的战场。机场是特工高危区。中情局文件旨在指导特工使用假身份时，如何通过被称为\"二次审查\"的严格安检，这是一场压力巨大的测试。"
    
    # Test shot JSON
    test_shot = {
        "text": "对于我们大多数人来说，机场是旅行的起点和终点，是充满期待和疲惫的中转站。但对于一群特殊的人来说，这里却是危机四伏的战场，",
        "audio": "20260106_155620.wav",
        "duration": 11.61,
        "chapter": "第一章：看不见的战场：机场里的猫鼠游戏",
        "description": "快速剪辑的蒙太奇镜头：1. 乘客在值机柜台前办理手续；2. 一家人拖着行李，面带兴奋地走向登机口；3. 一名商务人士疲惫地坐在候机椅上。镜头色调温暖、正常。"
    }
    
    # Test external interface (original method)
    print("\n=== 测试原始方法 generate_prompt ===")
    result = generate_prompt(test_video_summary, test_shot)
    print(f"\n=== 最终生成的提示词 ===")
    print(f"{json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test new method with Process and duration fields
    print("\n=== 测试新方法 generate_prompt_with_process ===")
    result_new = generate_prompt_with_process(test_video_summary, test_shot)
    print(f"\n=== 最终生成的提示词 (新格式) ===")
    print(f"{json.dumps(result_new, ensure_ascii=False, indent=2)}")
    
    print("\n=== 执行完成 ===")
