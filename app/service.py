"""
语音聊天服务核心逻辑
整合各个模块，实现完整的语音对话流程
"""
import random
from typing import Dict, Any, Optional
from app.modules.audio_assembler import AudioAssembler
from app.modules.vad import VAD
from app.modules.asr import ASR
from app.modules.intent_understanding import IntentUnderstanding
from app.modules.rag import RAG
from app.modules.llm_generator import LLMGenerator
from app.modules.tts import TTS
from app.models import (
    IntentResult, RAGResult, 
    LLMResponse, TTSResult, ResultMessage, SkillType
)
from app.config import settings
import base64

import loguru

logger = loguru.logger


class VoiceChatService:
    """语音聊天服务"""
    
    def __init__(self):
        """初始化服务"""
        logger.info("初始化语音聊天服务...")
        
        # 初始化各个模块
        self.vad = VAD(
            sample_rate=settings.audio_sample_rate,
            threshold=settings.vad_threshold,
            min_speech_duration=settings.vad_min_speech_duration,
            max_speech_duration=settings.vad_max_speech_duration,
            min_silence_duration=settings.vad_min_silence_duration
        )
        
        self.asr = ASR(
            model_path=settings.asr_model,
            language=settings.asr_language
        )
        
        self.intent_understanding = IntentUnderstanding(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            system_prompt_path=settings.intent_system_prompt_path
        )
        
        self.rag = RAG(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.qdrant_collection_name,
            embedding_model_name=settings.rag_embedding_model,
            embedding_api_base_url=settings.embedding_api_base_url,
            embedding_api_key=settings.embedding_api_key,
            embedding_dim=settings.embedding_dim,
            top_k=settings.rag_top_k,
            similarity_threshold=settings.rag_similarity_threshold,
            use_memory=settings.qdrant_use_memory
        )
        
        self.llm_generator = LLMGenerator(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            system_prompt_path=settings.generator_system_prompt_path
        )
        
        self.tts = TTS(
            language=settings.tts_language,
            model_path=settings.tts_model_path,
            voice_name=settings.tts_voice_name
        )
        
        logger.info("语音聊天服务初始化完成")
    
    async def process_audio(
        self,
        audio_data: bytes,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ResultMessage]:
        """
        处理音频数据，返回结果
        
        Args:
            audio_data: PCM音频数据
            context: 上下文信息
            
        Returns:
            处理结果
        """
        try:
            logger.info("=" * 50)
            logger.info("开始处理音频")
            
            # 1. VAD：检测语音活动
            logger.info("步骤1: VAD语音活动检测")
            # has_speech, speech_data = self.vad.detect_speech(audio_data)
            
            # if not has_speech or not speech_data:
            #     logger.warning("未检测到语音活动")
            #     return None
            
            # 2. ASR：语音识别
            logger.info("步骤2: ASR语音识别")
            asr_result = await self.asr.recognize_async(audio_data)
            
            if not asr_result:
                logger.warning("ASR识别失败")
                return None
            
            logger.info(f"识别文本: {asr_result}")
            
            # 3. LLM语义理解
            logger.info("步骤3: LLM语义理解")
            intent_result: IntentResult = await self.intent_understanding.understand_async(
                asr_result,
                context
            )
            
            logger.info(f"意图识别: skill_id={intent_result.skill_id}, "
                       f"is_fixed_command={intent_result.is_fixed_command}")
            
            # 4. 根据是否命中固定指令，选择不同的处理路径
            if intent_result.is_fixed_command:
                # 命中固定指令：直接返回
                logger.info("步骤4: 命中固定指令，直接返回")
                if intent_result.skill_id == "baby_cry_detection":
                    resonpse_list = ["Okay, I’ll let you know right away if the baby cries."]
                else:
                    skill_id = intent_result.skill_id
                    if "call" in skill_id:
                        resonpse_list = ["OK"]
                    elif skill_id == "start_recording":
                        resonpse_list = ["OK, recording now", "Recording..."]
                    elif skill_id == "stop_recording":
                        resonpse_list = ["Recording stopped"]
                    else:
                        resonpse_list = ["Alright", "OK", "Sure", "No problem", "Got it"]

                response_text = random.choice(resonpse_list)


                # TODO: TTS合成(临时处理，后续不生成语音，或者调用缓存音频)
                logger.info("步骤4.1: TTS语音合成")
                tts_result: Optional[TTSResult] = await self.tts.synthesize_async(
                    response_text
                )
                
                # 将音频编码为Base64
                audio_base64 = None
                if tts_result and tts_result.audio:
                    audio_base64 = base64.b64encode(tts_result.audio).decode('utf-8')
                    logger.info(f"TTS合成完成: {len(tts_result.audio)} 字节")
                
                return ResultMessage(
                    skill_id=intent_result.skill_id,
                    text=response_text,
                    audio=audio_base64,
                    metadata={
                        "asr_text": asr_result,
                        "confidence": intent_result.confidence,
                        "is_fixed_command": True
                    }
                )
            else:
                # 未命中固定指令：RAG检索 -> LLM生成 -> TTS合成
                logger.info("步骤4: 未命中固定指令，进入RAG流程")
                
                # 4.1 RAG检索
                logger.info("步骤4.1: RAG检索")
                rag_result: RAGResult = await self.rag.retrieve_async(
                    asr_result,
                    context
                )
                
                logger.info(f"检索到 {len(rag_result.documents)} 个相关文档")
                
                # 4.2 LLM生成回复
                logger.info("步骤4.2: LLM生成回复")
                llm_response: LLMResponse = await self.llm_generator.generate_async(
                    query=asr_result,
                    intent=intent_result,
                    context=rag_result.documents,
                    history=context.get("history") if context else None
                )
                
                logger.info(f"生成回复: {llm_response.text}")
                
                # 4.3 TTS合成
                logger.info("步骤4.3: TTS语音合成")
                tts_result: Optional[TTSResult] = await self.tts.synthesize_async(
                    llm_response.text
                )
                
                # 将音频编码为Base64
                audio_base64 = None
                if tts_result and tts_result.audio:
                    audio_base64 = base64.b64encode(tts_result.audio).decode('utf-8')
                    logger.info(f"TTS合成完成: {len(tts_result.audio)} 字节")
                
                return ResultMessage(
                    skill_id=intent_result.skill_id,
                    text=llm_response.text,
                    audio=audio_base64,
                    metadata={
                        "asr_text": asr_result,
                        "confidence": intent_result.confidence,
                        "is_fixed_command": False,
                        "rag_documents": len(rag_result.documents),
                        "finish_reason": llm_response.finish_reason
                    }
                )
                
        except Exception as e:
            logger.error(f"处理音频时发生错误: {e}", exc_info=True)
            return None
        finally:
            logger.info("音频处理完成")
            logger.info("=" * 50)

