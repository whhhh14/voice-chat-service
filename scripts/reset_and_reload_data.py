#!/usr/bin/env python3
"""
重置向量数据库并重新加载测试数据
删除旧集合，生成新的测试数据（3种场景）
"""
import json
import sys
import asyncio
from pathlib import Path
from typing import List
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models import Event
from app.modules.rag import RAG
from app.modules.vector_db import VectorDB
import loguru

logger = loguru.logger


def generate_new_test_events() -> List[dict]:
    """
    生成新的50条测试事件（基于3种场景）
    
    事件类型：
    - 宝宝哭声事件
    - 快递相关事件（送达、取走）
    - 访客来访事件
    """
    events = []
    base_time = datetime.now()
    
    # 生成最近10天的事件
    for day_offset in range(10):
        current_date = base_time - timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 每天生成5个事件
        # 事件1: 早上宝宝哭声
        events.append({
            "event_time": f"{date_str} 07:{30 + day_offset * 2}:00",
            "event_type_id": 1,
            "event_name": "宝宝哭声",
            "event_desc": "宝宝早上醒来哭泣",
            "device_id": 1002,
            "device_name": "卧室摄像头"
        })
        
        # 事件2: 上午快递送达
        couriers = ["顺丰", "京东", "中通", "圆通", "申通", "韵达", "邮政EMS", "天猫超市", "美团", "饿了么"]
        events.append({
            "event_time": f"{date_str} 09:{15 + day_offset * 3}:00",
            "event_type_id": 2,
            "event_name": "快递送达",
            "event_desc": f"{couriers[day_offset % len(couriers)]}快递员送来包裹",
            "device_id": 1001,
            "device_name": "门口摄像头"
        })
        
        # 事件3: 中午访客
        visitors = ["邻居来串门", "物业上门检查", "快递员按门铃", "朋友来访", "维修人员上门", "送水工", "外卖员", "家政服务人员"]
        events.append({
            "event_time": f"{date_str} 12:{20 + day_offset * 2}:00",
            "event_type_id": 3,
            "event_name": "访客来访",
            "event_desc": visitors[day_offset % len(visitors)],
            "device_id": 1001,
            "device_name": "门口摄像头"
        })
        
        # 事件4: 下午宝宝哭声
        events.append({
            "event_time": f"{date_str} 14:{10 + day_offset * 4}:00",
            "event_type_id": 1,
            "event_name": "宝宝哭声",
            "event_desc": "宝宝午睡醒来后哭泣",
            "device_id": 1002,
            "device_name": "卧室摄像头"
        })
        
        # 事件5: 傍晚快递取走
        events.append({
            "event_time": f"{date_str} 17:{30 + day_offset * 2}:00",
            "event_type_id": 2,
            "event_name": "快递取走",
            "event_desc": "主人取走门口的快递包裹",
            "device_id": 1001,
            "device_name": "门口摄像头"
        })
    
    return events


async def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("重置向量数据库并重新加载测试数据")
    logger.info("=" * 70)
    
    # 配置
    QDRANT_HOST = "localhost"
    QDRANT_PORT = 6333
    COLLECTION_NAME = "events"
    EMBEDDING_MODEL = "Qwen3-Embedding-0.6B"
    EMBEDDING_API_URL = "http://localhost:8002/v1"
    EMBEDDING_API_KEY = "EMPTY"
    EMBEDDING_DIM = 1024
    
    logger.info(f"\n配置信息:")
    logger.info(f"  - Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    logger.info(f"  - Collection: {COLLECTION_NAME}")
    logger.info(f"  - Embedding Model: {EMBEDDING_MODEL} ({EMBEDDING_DIM}维)")
    
    try:
        # 步骤1: 删除旧集合
        logger.info(f"\n" + "=" * 70)
        logger.info("步骤 1/4: 删除旧集合")
        logger.info("=" * 70)
        
        vector_db = VectorDB(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            collection_name=COLLECTION_NAME,
            vector_dim=EMBEDDING_DIM,
            use_memory=False
        )
        
        # 检查集合是否存在
        try:
            info = vector_db.get_collection_info()
            old_count = info.get("points_count", 0)
            logger.info(f"找到旧集合，包含 {old_count} 个事件")
            
            # 删除集合
            vector_db.delete_collection()
            logger.info(f"✓ 成功删除集合 '{COLLECTION_NAME}'")
        except Exception as e:
            logger.info(f"集合不存在或已删除: {e}")
        
        # 步骤2: 生成新测试数据
        logger.info(f"\n" + "=" * 70)
        logger.info("步骤 2/4: 生成新测试数据（3种场景）")
        logger.info("=" * 70)
        
        events_data = generate_new_test_events()
        logger.info(f"✓ 生成了 {len(events_data)} 个新事件")
        
        # 统计事件类型
        event_types = {}
        for event_data in events_data:
            event_name = event_data["event_name"]
            event_types[event_name] = event_types.get(event_name, 0) + 1
        
        logger.info(f"\n事件类型统计:")
        for event_name, count in sorted(event_types.items()):
            logger.info(f"  - {event_name}: {count}个")
        
        # 保存到JSON文件
        output_file = project_root / "data" / "test_events.json"
        output_data = {
            "version": "3.0",
            "description": "基于3种场景的测试事件数据 - 包含50个事件",
            "generated_at": datetime.now().isoformat(),
            "event_types": {
                "1": "宝宝哭声",
                "2": "快递相关（送达/取走）",
                "3": "访客来访"
            },
            "events": events_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✓ 测试数据已保存到: {output_file}")
        
        # 步骤3: 重新初始化RAG（会自动创建新集合）
        logger.info(f"\n" + "=" * 70)
        logger.info("步骤 3/4: 重新初始化RAG模块")
        logger.info("=" * 70)
        
        rag = RAG(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            collection_name=COLLECTION_NAME,
            embedding_model_name=EMBEDDING_MODEL,
            embedding_api_base_url=EMBEDDING_API_URL,
            embedding_api_key=EMBEDDING_API_KEY,
            embedding_dim=EMBEDDING_DIM,
            top_k=5,
            similarity_threshold=0.3,
            use_memory=False
        )
        
        logger.info("✓ RAG模块初始化完成（新集合已创建）")
        
        # 步骤4: 批量导入新数据
        logger.info(f"\n" + "=" * 70)
        logger.info("步骤 4/4: 批量导入事件到向量数据库")
        logger.info("=" * 70)
        
        events = [Event(**event_data) for event_data in events_data]
        
        logger.info(f"开始异步批量导入 {len(events)} 个事件...")
        event_ids = await rag.add_events_batch(events)
        
        logger.info(f"✓ 成功导入 {len(event_ids)} 个事件")
        
        # 验证导入结果
        logger.info(f"\n验证导入结果...")
        collection_info = rag.get_collection_info()
        final_count = collection_info.get("points_count", 0)
        logger.info(f"✓ 集合中现在有 {final_count} 个事件")
        
        # 测试检索
        logger.info(f"\n" + "=" * 70)
        logger.info("测试 RAG 检索功能")
        logger.info("=" * 70)
        
        test_queries = [
            "昨天卧室宝宝有哭吗？",
            "今天门口有快递吗？",
            "最近有访客来过吗？",
        ]
        
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            result = await rag.retrieve_async(query, top_k=3)
            logger.info(f"找到 {len(result.documents)} 个相关事件:")
            for i, (doc, score, metadata) in enumerate(zip(result.documents, result.scores, result.metadata), 1):
                event_time = metadata.get("event_time", "")
                event_name = metadata.get("event_name", "")
                logger.info(f"  {i}. [相似度: {score:.4f}] {event_name} - {event_time}")
                logger.info(f"     {doc}")
        
        logger.info(f"\n" + "=" * 70)
        logger.info("✅ 数据重置和导入完成！")
        logger.info("=" * 70)
        logger.info(f"\n总结:")
        logger.info(f"  - 旧集合已删除")
        logger.info(f"  - 新集合已创建: {COLLECTION_NAME}")
        logger.info(f"  - 导入事件数量: {final_count}")
        logger.info(f"  - 事件类型: 宝宝哭声、快递相关、访客来访")
        logger.info(f"  - 时间跨度: 最近10天")
        
    except Exception as e:
        logger.error(f"操作失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

