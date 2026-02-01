#!/usr/bin/env python3
"""
Improve Srt Results LLM using DeepSeek with LangChain
用于校对字幕文件，根据原始文稿纠正识别错误
"""

import json
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

class ImproveSrtResultsLLM:
    """
    Improve Srt Results LLM using DeepSeek API
    用于校对字幕文件，根据原始文稿纠正识别错误
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
        
        # System prompt for subtitle correction
        self.system_prompt = '''你精通字幕校对工作，你的任务是根据我提供给你的原始文稿和软件识别的字幕文件（存在不准确），为我校对字幕：
1、忠于字幕文件识别的断句，不要擅自修改
2、禁止修改时间线的内容
2、根据原始文稿，纠正字幕文件识别的文字错误，标点错误（中间的标点符号需要，结尾的标点符号根据情况保留，叹号，问号等可以保留）等。

给你提供的原始文稿示例如下：
大家好，欢迎收看本期节目。今天，我们将一同走进一个普通人既熟悉又陌生的世界——国际机场。

给你提供的字幕文件内容示例如下：
1
00:00:00,000 --> 00:00:02,240
大家好 欢迎收看本期节目

2
00:00:02,240 --> 00:00:04,360
今天我们将一同走进一个

3
00:00:04,360 --> 00:00:07,160
普通人计熟悉陌生的世界国际机场

你直接输出修改后的字幕文件内容给我，如下：
1
00:00:00,000 --> 00:00:02,240
大家好 欢迎收看本期节目

2
00:00:02,240 --> 00:00:04,360
今天我们将一同走进一个

3
00:00:04,360 --> 00:00:07,160
我们将一同走进一个普通人既熟悉又陌生的世界——国际机场
'''
    
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
            Tuple (is_valid, response) where:
                is_valid: bool indicating if response is valid
                response: cleaned response string if valid, None otherwise
        """
        try:
            # Remove code block markers if present
            cleaned_response = response_str.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            return True, cleaned_response
        except Exception as e:
            # Other errors
            return False, None
    
    def improve_srt(self, original_script, srt_content, max_retries=5):
        """
        Improve SRT results using LLM with retry mechanism
        
        Args:
            original_script: Original script string
            srt_content: SRT content string
            max_retries: Maximum number of retries (default: 5)
        
        Returns:
            String with improved SRT content
        """
        # Create user prompt
        user_prompt = f"原始文稿：\n{original_script}\n\n字幕文件内容：\n{srt_content}"
        
        # Set system prompt
        system_prompt = self.system_prompt
        
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
        return "无法校对字幕"

# Example usage for external calls
def improve_srt(original_script, srt_content, max_retries=5):
    """
    External interface for SRT improvement
    
    Args:
        original_script: Original script string
        srt_content: SRT content string
        max_retries: Maximum number of retries (default: 5)
    
    Returns:
        String with improved SRT content
    """
    # Create LLM instance
    llm = ImproveSrtResultsLLM()
    
    # Call improve_srt method
    return llm.improve_srt(original_script, srt_content, max_retries)

if __name__ == "__main__":
    # Example usage
    print("=== Improve Srt Results LLM ===")
    
    # Test original script
    test_original_script = "对于我们大多数人来说，机场是旅行的起点和终点，是充满期待和疲惫的中转站。但对于一群特殊的人来说，这里却是危机四伏的战场，"
    
    # Test SRT content
    test_srt_content = """1
00:00:00,000 --> 00:00:02,000
对于我们大多数人来说

2
00:00:02,000 --> 00:00:04,000
机场是旅行的起点和终点

3
00:00:04,000 --> 00:00:07,000
是充满期待和疲惫的中转站

4
00:00:07,000 --> 00:00:09,000
但对于一群特殊的人来说

5
00:00:09,000 --> 00:00:11,000
这里却是位机似浮的战场"""
    
    # Test external interface
    print("\n=== 测试 improve_srt 方法 ===")
    result = improve_srt(test_original_script, test_srt_content)
    print("\n=== 校对后的字幕内容 ===")
    print(result)
    
    print("\n=== 执行完成 ===")
