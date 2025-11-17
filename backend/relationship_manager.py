"""NPC好感度管理系统"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from typing import Dict, Optional, Tuple
import json
import re

class RelationshioManager:
    """NPC好感度管理器
       功能:
       - 管理NPC与玩家的好感度 (0-100)
       - 使用LLM分析对话情感
       - 自动更新好感度
       - 提供好感度等级和修饰词
    """
    def __init__(self, llm:HelloAgentsLLM):
        """
        初始化好感度管理器
        :param llm: HelloAgentsLLM实例
        """

        self.llm = llm

        # 存储每个NPC与玩家的好感度
        # 格式: {npc_name: {player_id: affinity_score}}
        self.affinity_scores:Dict[str, Dict[str, float]] = {}

        # 创建好感度分析Agent
        self.analyzer_agent = SimpleAgent(
            name="AffinityAnalyzer",
            llm=llm,
            system_prompt=self._create_analyzer_prompt()
        )

        print("💖 好感度管理系统已初始化")

    def _create_analyzer_prompt(self)->str:
        """
        创建情感分析Agent的系统提示词
        :return :
         {
            "should_change": true/false,
            "change_amount": -15到+10之间的整数,
            "reason": "简短说明原因(10字以内)",
            "sentiment": "positive/neutral/negative"
        }
        """
        return """
        你是一个情感分析专家,负责分析对话中的情感倾向,判断是否应该改变NPC对玩家的好感度。

        【任务】
        分析玩家与NPC的对话,判断是否应该改变好感度,以及改变的幅度。

        【分析维度】
        1. **玩家态度**: 友好/中立/不友好
        2. **对话内容**: 积极/中立/消极
        3. **互动质量**: 深入/一般/敷衍
        4. **情感倾向**: 赞美/批评/中性

        【好感度变化规则】
        - 赞美、感谢、请教: +3 到 +8
        - 友好问候、正常交流: +1 到 +3
        - 普通闲聊、中性话题: 0
        - 批评、质疑、不耐烦: -3 到 -8
        - 侮辱、攻击、恶意: -8 到 -15

        【输出格式】(严格遵守JSON格式,不要添加任何其他文字)
        {
            "should_change": true/false,
            "change_amount": -15到+10之间的整数,
            "reason": "简短说明原因(10字以内)",
            "sentiment": "positive/neutral/negative"
        }

        【示例1】
        玩家: "你好,很高兴认识你!"
        NPC: "你好!我也很高兴认识你。"
        输出: {"should_change": true, "change_amount": 5, "reason": "友好问候", "sentiment": "positive"}

        【示例2】
        玩家: "你这个设计太丑了!"
        NPC: "抱歉,我会改进的..."
        输出: {"should_change": true, "change_amount": -8, "reason": "批评工作", "sentiment": "negative"}

        【示例3】
        玩家: "今天天气不错"
        NPC: "是啊,挺好的。"
        输出: {"should_change": false, "change_amount": 0, "reason": "普通闲聊", "sentiment": "neutral"}

        【示例4】
        玩家: "你的代码写得真棒!"
        NPC: "谢谢!我最近在研究新技术。"
        输出: {"should_change": true, "change_amount": 8, "reason": "赞美工作", "sentiment": "positive"}

        【示例5】
        玩家: "能教教我吗?"
        NPC: "当然可以!我很乐意分享。"
        输出: {"should_change": true, "change_amount": 6, "reason": "请教学习", "sentiment": "positive"}

        【重要】
        - 只输出JSON,不要添加任何解释或其他文字
        - change_amount必须是整数
        - reason必须简短(10字以内)
        - sentiment必须是positive/neutral/negative之一
        """

    def gete_affinity(self, npc_name:str, player_id:str = "player")->float:
        """
        获取好感度
        :param npc_name: NPC名称
        :param palyer_id: 玩家ID
        :return:好感度(0-100)
        """

        if npc_name not in self.affinity_scores:
            self.affinity_scores[npc_name] = {}

        if player_id not in self.affinity_scores[npc_name][player_id]:
            self.affinity_scores[npc_name][player_id] = 50.0 # 初始好感度为0

        return self.affinity_scores[npc_name][player_id]

    def set_affinaty(self, npc_name:str, affinaty:float, player_id:str = "player"):
        """
        设置好感度
        :param npc_name:NPC名称
        :param affinaty:好感度值
        :param player_id:玩家ID
        """

        if npc_name not in self.affinity_scores:
            self.affinity_scores[npc_name] = {}

        # 限制在0-100范围内
        affinaty = max(0.0, min(100.0, affinaty))
        self.affinity_scores[npc_name][player_id] = affinaty

    def analyze_and_update_affinaty(
            self,
            npc_name:str,
            player_message:str,
            npc_responce:str,
            player_id:str = "player"
    )->Dict[]:
        

