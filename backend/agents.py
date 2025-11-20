"""NPC Agent系统 - 支持记忆功能"""

import sys
import os

# 添加HelloAgents到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, MemoryConfig, MemoryItem, EpisodicMemory
from typing import Dict, List, Optional
from datetime import datetime
from relationship_manager import RelationshipManager
from logger import (
    log_dialogue_start, log_affinity, log_memory_retrieval,
    log_generating_response, log_npc_response, log_analyzing_affinity,
    log_affinity_change, log_memory_saved, log_dialogue_end, log_info
)


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
        self.relationship_manager: Optional[RelationshipManager] = None

        # 初始化好感度管理器
        if self.llm:
            self.relationship_manager =RelationshipManager(self.llm)

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

    def _build_memory_context(self, memories:List[MemoryItem])->str:
        """构建记忆上下文"""
        if not memories:
            return ""

        context_parts = ["【之前的对话记忆】"]
        for memory in memories:
            # 格式化时间
            time_str = memory.timestamp.strftime("%H:%M")
            # 添加记忆内容
            context_parts.append(f"[{time_str}] {memory.content}")

        context_parts.append("") # 空行分离
        return "\n".join(context_parts)

    def _save_conversation_to_memoty(
            self,
            memory_manager:MemoryManager,
            npc_name:str,
            player_message:str,
            npc_response:str,
            player_id:str,
            affinity_info:Optional[Dict] = None
    ):
        """保存对话到记忆系统中(包含好感度消息)"""
        current_time = datetime.now()

        # 获取好感度消息
        affinity = affinity_info.get("new_affinity", affinity_info.get("affinity", 50.0)) if affinity_info else 50.0
        affinity_change = affinity_info.get("change_amount", 0) if affinity_info else 0
        sentiment = affinity_info.get("sentiment", "neutral") if affinity_info else "neutral"

        # 保存玩家消息
        memory_manager.add_memory(
            content=f"玩家说: {player_message}",
            memory_type="working",
            importance=0.5,
            metadata={
                "speaker": "player",
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  # ⭐ 记录当时的好感度
                "affinity_change": affinity_change,  # ⭐ 记录好感度变化
                "sentiment": sentiment,  # ⭐ 记录情感倾向
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        # 保存NPC回复
        memory_manager.add_memory(
            content=f"我说: {npc_response}",
            memory_type="working",
            importance=0.6,
            metadata={
                "speaker": npc_name,
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  #  记录当时的好感度
                "sentiment": sentiment,  #  记录情感倾向
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        print(f"  💾 对话已保存到{npc_name}的记忆中")

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
            # 记录对话开始 ⭐ 使用日志系统
            log_dialogue_start(npc_name, message)

            # 1.获取当前好感度
            affinity_context = ""
            if self.relationship_manager:
                affinity = self.relationship_manager.gete_affinity(npc_name, player_id)
                affinity_level = self.relationship_manager.get_affinity_level(affinity)
                affinity_modifier = self.relationship_manager.get_affinity_modifier()
                affinity_context = f"""
                【当前关系】
                你与玩家的关系: {affinity_level} (好感度: {affinity:.0f}/100)
                【对话风格】{affinity_modifier}
                """
                log_affinity(npc_name, affinity, affinity_level)

            # 2.检索相关记忆
            relevent_memories = []
            if memory_manager:
                relevent_memories = memory_manager.retrieve_memories(
                    query=message,
                    memory_types=["working", "episodic"],
                    limit=5,
                    min_importance=0.3 # 只检索重要性 >= 0.3 的记忆
                )
                log_memory_retrieval(npc_name, len(relevent_memories), relevent_memories)

            # 3.构建增强的提示词(包含好感度和上下文)
            memory_context = self._build_memory_context(relevent_memories)

            enhanced_message = affinity_context
            if memory_context:
                enhanced_message += f"{memory_context}\n\n"
            enhanced_message += f"【当前对话】\n玩家: {message}"

            # 4.调用Agent生成回复
            log_generating_response()
            response = agent.run(enhanced_message)
            log_npc_response(npc_name, response)

            # 5.分析并更新好感度
            log_analyzing_affinity()
            if self.relationship_manager:
                affinity_result = self.relationship_manager.analyze_and_update_affinaty(
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id
                )

                # 记录好感度变化详情
                log_affinity_change(affinity_result)
            else:
                affinity_result = {"changed": False, "affinity": 50.0}

            # 6.保存对话到记忆(包含好感度消息)
            if memory_manager:
                self._save_conversation_to_memoty(
                    memory_manager=memory_manager,
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id,
                    affinity_info=affinity_result
                )
                log_memory_saved(npc_name)

            # 记录对话结束 ⭐ 使用日志系统
            log_dialogue_end()

            return response
        except Exception as e:
            print(f"❌ {npc_name}对话失败: {e}")
            import traceback
            traceback.print_exc()
            return f"抱歉,我现在有点忙,等会儿再聊吧。(错误: {str(e)})"

    def get_npc_info(self, npc_name:str)->Dict[str, str]:
        """获取NPC信息"""
        if npc_name not in NPC_ROLES:
            return {}

        role = NPC_ROLES[npc_name]
        return {
            "name": npc_name,
            "title": role["title"],
            "location": role["location"],
            "activity": role["activity"],
            "available": self.agents.get(npc_name) is not None
        }

    def get_all_npcs(self)->list:
        """获取所有的NPC信息"""
        return [self.get_npc_info(name) for name in NPC_ROLES.keys()]

    def get_npc_memories(self, npc_name:str, player_id:str = "player", limit:int = 10)->List[Dict]:
        """获取NPC的记忆列表(用于调试与展示)"""
        if npc_name not in self.memories:
            return []

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            return []

        try:
            # 检索所有的记忆
            memories = memory_manager.retrieve_memories(
                query="", # 空查询返回所有的记忆
                memory_types=["working", "episodic"],
                limit=limit
            )

            # 转化为字典格式
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata
                })

            return memory_list
        except Exception as e:
            print(f"❌ 获取{npc_name}记忆失败: {e}")
            return []

    def clear_npc_memoriy(self, npc_name:str, memory_type:Optional[str] = None):
        """清空NPC的记忆(用于调试)"""
        if npc_name not in self.memories:
            print(f"❌ NPC '{npc_name}' 不存在")
            return

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            print(f"❌ {npc_name}没有记忆系统")
            return

        try:
            if memory_type:
                # 清空指定类型的记忆
                memory_manager.clear_memory_type(memory_type)
                print(f"✅ 已清空{npc_name}的{memory_type}记忆")
            else:
                try:
                    memory_manager.clear_all_memories()
                    print(f"✅ 已清空{npc_name}的所有记忆")
                except:
                    pass
        except Exception as e:
            print(f"❌ 清空{npc_name}记忆失败: {e}")

    def get_npc_affinity(self, npc_name:str, player_id:str = "player", ) -> Dict:
        """
        获取NPC对玩家的好感度信息
        :param npc_name:npc名称
        :param player_id:玩家ID
        :return:好感度信息字典
        """

        if not self.relationship_manager:
            return {
                "affinity": 50.0,
                "level": "熟悉",
                "modifier": "礼貌友善,正常交流,保持专业"
            }

        affinity = self.relationship_manager.gete_affinity(npc_name, player_id)
        level =  self.relationship_manager.get_affinity_level(affinity)
        modifire = self.relationship_manager.get_affinity_modifier(affinity)

        return {
            "affinity": affinity,
            "level": level,
            "modifier": modifier
        }

    def get_all_afinities(self, player_id:str = "player")->Dict[str, Dict]:
        """
        获取所有的NPC的好感度信息
        :param player_id: 玩家ID
        :return:所有NPC的好感度信息
        """

        if not self.relationship_manager:
            return {}

        return self.relationship_manager.get_all_affinities(player_id=player_id)

    def set_npc_affinity(self, npc_name:str, affinity:float, player_id:str = "player"):
        """
        设置NPC对玩家的好感度
        :param npc_name:NPC名称
        :param affinity:好感度值(0-100)
        :param player_id:玩家ID
        """
        if not self.relationship_manager:
            print("❌ 好感度系统未初始化")
            return

        self.relationship_manager.set_affinaty(npc_name, affinity, player_id=player_id)
        level = self.relationship_manager.get_affinity_level(affinity)

        print(f"✅ 已设置{npc_name}对玩家的好感度: {affinity:.1f} ({level})")

# 全局单例
_npc_manager = None
def get_npc_manager()->NPCAgentManager:
    """获取NPC管理器单例"""
    global _npc_manager
    if _npc_manager is None:
        _npc_manager = NPCAgentManager()

    return _npc_manager