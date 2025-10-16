"""
LLM语义理解模块
负责理解用户意图，判断是否命中固定指令
"""
from typing import Optional, Dict, Any, List
from app.models import IntentResult, SkillType
from app.modules.llm import LLM
import json
import re

import loguru

logger = loguru.logger


class IntentUnderstanding:
    """意图理解器"""
    
    def __init__(
        self,
        api_key: str = "EMPTY",
        base_url: str = "http://192.168.111.3:8093/v1",
        system_prompt_path: str = "conf/system_prompt_intent.txt"
    ):
        """
        初始化意图理解器
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            system_prompt_path: 系统提示词文件路径
        """
        self.llm = LLM(
            api_key=api_key,
            base_url=base_url,
            system_promt_path=system_prompt_path
        )
        
        logger.info(f"初始化意图理解器: base_url={base_url}")
    
    def understand(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        理解用户意图
        
        Args:
            text: 用户输入文本
            context: 上下文信息
            
        Returns:
            意图识别结果
        """
        try:
            logger.info(f"开始意图理解: {text}")
            
            # 调用LLM进行意图识别
            response = self.llm.generate(text)
            
            # 解析LLM返回的JSON结果
            intent_data = self._parse_intent_response(response)
            
            # 将场景类型转换为技能信息
            result = self._convert_to_intent_result(intent_data)
            
            logger.info(f"意图识别完成: skill_id={result.skill_id}, skill_type={result.skill_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"意图理解失败: {e}", exc_info=True)
            # 返回默认的聊天意图
            return IntentResult(
                skill_id="chat",
                skill_type=SkillType.CHAT,
                confidence=0.5,
                entities={},
                is_fixed_command=False
            )
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM返回的意图识别结果
        
        Args:
            response: LLM返回的文本
            
        Returns:
            解析后的意图数据字典
        """
        try:
            # 尝试提取JSON内容（可能包含在代码块中）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接提取花括号内容
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response
            
            # 解析JSON
            intent_data = json.loads(json_str)
            logger.info(f"解析意图数据: {intent_data}")
            return intent_data
            
        except Exception as e:
            logger.error(f"解析意图响应失败: {e}, response={response}")
            # 返回默认值
            return {
                "scene_type": 4,
                "scene_name": "其他场景",
                "confidence": 0.5
            }
    
    def _convert_to_intent_result(self, intent_data: Dict[str, Any]) -> IntentResult:
        """
        将LLM返回的场景数据转换为IntentResult
        
        Args:
            intent_data: 场景识别数据
            
        Returns:
            IntentResult对象
        """
        scene_type = intent_data.get("scene_type", 4)
        confidence = intent_data.get("confidence", 0.5)
        entities = {}
        
        # 场景一：Solo指令识别
        if scene_type == 1:
            instruction_type = intent_data.get("instruction_type", "")
            skill_id = self._map_instruction_to_skill(instruction_type)
            entities = {
                "instruction_type": instruction_type,
                "scene_name": intent_data.get("scene_name", "")
            }
            return IntentResult(
                skill_id=skill_id,
                skill_type=SkillType.COMMAND,
                confidence=confidence,
                entities=entities,
                is_fixed_command=True
            )
        
        # 场景二：事件提醒设置（设置通知和提醒）
        elif scene_type == 2:
            entities = {
                "detection_type": intent_data.get("detection_type", ""),
                "scene_name": intent_data.get("scene_name", "事件提醒设置")
            }
            return IntentResult(
                skill_id="event_reminder_setup",
                skill_type=SkillType.COMMAND,
                confidence=confidence,
                entities=entities,
                is_fixed_command=True
            )
        
        # 场景三：事件查询（包含历史记录查询、包裹问询等）
        elif scene_type == 3:
            entities = {
                "query_type": intent_data.get("query_type", "事件查询"),
                "scene_name": intent_data.get("scene_name", "事件查询")
            }
            return IntentResult(
                skill_id="event_query",
                skill_type=SkillType.QA,
                confidence=confidence,
                entities=entities,
                is_fixed_command=False
            )
        
        # 场景四：其他场景（聊天）
        else:
            return IntentResult(
                skill_id="chat",
                skill_type=SkillType.CHAT,
                confidence=confidence,
                entities={"scene_name": intent_data.get("scene_name", "其他场景")},
                is_fixed_command=False
            )
    
    def _map_instruction_to_skill(self, instruction_type: str) -> str:
        """
        将指令类型映射到技能ID
        
        Args:
            instruction_type: 指令类型
            
        Returns:
            技能ID
        """
        # 指令类型映射表
        instruction_map = {
            "关闭摄像机": "camera_off",
            "开启摄像机": "camera_on",
            "开启追踪": "tracking_on",
            "关闭追踪": "tracking_off",
            "打电话": "call",
            "call mom": "call_mom",
            "call husband": "call_husband",
            "call wife": "call_wife",
            "call dad": "call_dad",
            "call son": "call_son",
            "call daughter": "call_daughter",
            "结束通话": "hang_up",
            "拍照": "take_photo",
            "开启录像": "start_recording",
            "结束录像": "stop_recording"
        }
        
        return instruction_map.get(instruction_type, "unknown_command")
    
    async def understand_async(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        异步理解用户意图
        
        Args:
            text: 用户输入文本
            context: 上下文信息
            
        Returns:
            意图识别结果
        """
        # 实际应用中可以调用异步的LLM服务
        return self.understand(text, context)

