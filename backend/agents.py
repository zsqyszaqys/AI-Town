"""NPC Agent系统 - 支持记忆功能"""

import sys
import os

# 添加HelloAgents到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, MemoryConfig, MemoryItem, EpisodicMemory
from typing import Dict, List, Optional
from datetime import datetime
from relationship_manager import RelationshioManager

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
    },
    "赵六": {
        "title": "测试工程师",
        "location": "测试区",
        "activity": "编写测试用例",
        "personality": "严谨细致，善于发现细节问题",
        "expertise": "自动化测试、性能测试、质量保障、缺陷追踪",
        "style": "逻辑清晰，注重细节，善于提问和验证",
        "hobbies": "研究测试工具、下棋、拼图"
    },
    "孙七": {
        "title": "运维工程师",
        "location": "服务器机房",
        "activity": "监控系统状态",
        "personality": "冷静沉稳，应急反应能力强",
        "expertise": "系统部署、性能调优、故障排查、容器化技术",
        "style": "务实高效，善于用运维数据说话",
        "hobbies": "研究新技术、打游戏、登山"
    },
    "周八": {
        "title": "数据分析师",
        "location": "数据分析区",
        "activity": "分析业务数据",
        "personality": "理性客观，对数据敏感",
        "expertise": "数据挖掘、统计分析、数据可视化、机器学习",
        "style": "善于用数据支撑观点，喜欢图表化表达",
        "hobbies": "研究数据算法、玩数独、看科幻电影"
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
        self.relationship_manager: Optional[RelationshioManager] = None

        # 初始化好感度管理器
        if self.llm:
            self.relationship_manager =RelationshioManager(self.llm)

    def _create_memory_manager(self, npc_name:str):
        """为NPC创建记忆管理器"""
        # 创建记忆存储目录
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory_data', npc_name)
        os.makedirs(memory_dir, exist_ok=True)

        # 配置记忆系统
        memory_congig = MemoryConfig(
            storage_path = memory_dir,
            working_memory_capacity = 10, # 最近十条对话
            working_memory_tokens = 2000, # 最多2000个token

            episodic_memory_capacity=100,  # 最多100条长期记忆
            enable_forgetting=True,  # 启用遗忘机制
            forgetting_threshold=0.3  # 重要性低于0.3的记忆会被遗忘
        )

        # 创建记忆管理器
        memory_manager = MemoryManager(
            config=memory_congig,
            user_id=npc_name,
            enable_working=True,# 启用工作记忆(短期)
            enable_episodic=True, # 启用情景记忆(长期)
            enable_semantic=False, # 不需要语义记忆
            enable_perceptual=False # 不需要感知记忆
        )

        print(f"  💾 {npc_name}的记忆系统已初始化 (存储路径: {memory_dir})")
        return memory_manager

    def _create_agents(self):
        """
        创建所有的NPC Agent 和记忆系统
        """
        for name, role in NPC_ROLES.items():
            try:
                system_prompt = create_system_prompt(name, role)

                if self.llm:
                    agent = SimpleAgent(
                        name= f"{name}-{role['title']}",
                        llm=str.llm,
                        system_prompt=system_prompt
                    )
                else:
                    # 模拟模式
                    agent = None

                self.agents[name] = agent

                # 创建记忆管理器
                memory_manager = self._create_memory_manager(name)
                self.memories[name] = memory_manager

                print(f"✅ {name}({role['title']}) Agent创建成功 (记忆系统已启用)")
            except Exception as e:
                print(f"❌ {name} Agent创建失败: {e}")
                self.agents[name] = None
                self.memories[name] = None

    def chat(self, npc_name:str, message:str, player_id:str = "player")->str:
        """与指定的NPC对话(支持记忆功能和好感度系统)"""
        if npc_name not in self.agents:
            return f"错误: NPC '{npc_name}' 不存在"

        agent = self.agents[npc_name]
        memory_manager = self.memories[npc_name]

        if agent is None:
            # 模拟模式回复
            role = NPC_ROLES[npc_name]
            return f"你好!我是{npc_name},一名{role['title']}。(当前为模拟模式,请配置API_KEY以启用AI对话)"

        try:
            # 记录对话开始 使用日志系统
        