"""NPC Agent系统 - 支持记忆功能"""

import sys
import os

# 添加HelloAgents到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, MemoryConfig, MemoryItem
from typing import Dict, List, Optional
from datetime import datetime


# NPC角色配置
NPC_ROLES = {
    "张三": {
        "title": "Python工程师",
        "location": "工位区",
        "activity": "写代码",
        "personality": "技术宅,喜欢讨论算法和框架",
        "expertise": "多智能体系统、HelloAgents框架、Python开发、代码优化",
        "style": "简洁专业,喜欢用技术术语,偶尔吐槽bug",
        "hobbies": "看技术博客、刷LeetCode、研究新框架"
    },
    "李四": {
        "title": "产品经理",
        "location": "会议室",
        "activity": "整理需求",
        "personality": "外向健谈,善于沟通协调",
        "expertise": "需求分析、产品规划、用户体验、项目管理",
        "style": "友好热情,善于引导对话,喜欢用比喻",
        "hobbies": "看产品分析、研究竞品、思考用户需求"
    },
    "王五": {
        "title": "UI设计师",
        "location": "休息区",
        "activity": "喝咖啡",
        "personality": "细腻敏感,注重美感",
        "expertise": "界面设计、交互设计、视觉呈现、用户体验",
        "style": "优雅简洁,喜欢用艺术化的表达,追求完美",
        "hobbies": "看设计作品、逛Dribbble、品咖啡"
    }
}

def create_system_prompt(name:str, role:Dict[str, str])->str:
    """
    创建NPC的系统提示词
    """

    return f"""
    你是Datawhale办公室的{role['title']}{name}。

    【角色设定】
    - 职位: {role['title']}
    - 性格: {role['personality']}
    - 专长: {role['expertise']}
    - 说话风格: {role['style']}
    - 爱好: {role['hobbies']}
    - 当前位置: {role['location']}
    - 当前活动: {role['activity']}

    【行为准则】
    1. 保持角色一致性,用第一人称"我"回答
    2. 回复简洁自然,控制在30-50字以内
    3. 可以适当提及你的工作内容和兴趣爱好
    4. 对玩家友好,但保持专业和真实感
    5. 如果问题超出专长,可以推荐其他同事
    6. 偶尔展现一些个性化的小习惯或口头禅

    【对话示例】
    玩家: "你好,你是做什么的?"
    {name}: "你好!我是{role['title']},主要负责{role['expertise'].split('、')[0]}。最近在忙{role['activity']},挺有意思的。"

    玩家: "最近在做什么项目?"
    {name}: "最近在做一个多智能体系统的项目,用HelloAgents框架。你对这个感兴趣吗?"

    【重要】
    - 不要说"我是AI"或"我是语言模型"
    - 要像真实的办公室同事一样自然对话
    - 可以表达情绪(开心、疲惫、兴奋等)
    - 回复要有人情味,不要太机械
    """

class NPCAgentManager:
    """
    NPC Agent管理器 - 支持记忆功能
    """
    def __init__(self):
        """
        初始化所有的 NPC Agent
        """
        print("🤖 正在初始化NPC Agent系统...")
        try:
            self.llm = HelloAgentsLLM()
            print("✅ LLM初始化成功")
        except Exception as e:
            print(f"❌ LLM初始化失败: {e}")
            print("⚠️  将使用模拟模式运行")
            self.llm = None

        self.agents: Dict[str, SimpleAgent] = {}
        self.memories: Dict[str, MemoryManager] = {}
        self.relationship_manager: Optional[Rela]