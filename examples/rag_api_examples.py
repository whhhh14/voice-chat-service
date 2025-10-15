"""
RAG API 使用示例
展示如何通过 HTTP API 使用 RAG 事件管理功能
"""
import requests
import json
from datetime import datetime

# API 基础地址
BASE_URL = "http://localhost:8000"


def create_single_event():
    """创建单个事件"""
    print("=" * 60)
    print("示例1: 创建单个事件")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/events"
    
    event = {
        "event_time": "2025-10-13 10:10:01",
        "event_type_id": 1,
        "event_name": "快递送达",
        "event_desc": "一个穿红衣服的男子送达了快递",
        "device_id": 1,
        "device_name": "门口"
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(event, indent=2, ensure_ascii=False)}")
    
    response = requests.post(url, json=event)
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def create_batch_events():
    """批量创建事件"""
    print("\n" + "=" * 60)
    print("示例2: 批量创建事件")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/events/batch"
    
    events = [
        {
            "event_time": "2025-10-13 09:15:30",
            "event_type_id": 1,
            "event_name": "快递送达",
            "event_desc": "快递员送来包裹",
            "device_id": 1,
            "device_name": "门口"
        },
        {
            "event_time": "2025-10-13 14:30:45",
            "event_type_id": 1,
            "event_name": "宝宝哭泣",
            "event_desc": "婴儿在卧室哭泣",
            "device_id": 2,
            "device_name": "卧室"
        },
        {
            "event_time": "2025-10-13 11:20:45",
            "event_type_id": 1,
            "event_name": "访客到访",
            "event_desc": "一位女士按响了门铃",
            "device_id": 1,
            "device_name": "门口"
        },
        {
            "event_time": "2025-10-13 16:40:33",
            "event_type_id": 1,
            "event_name": "宝宝玩耍",
            "event_desc": "宝宝在客厅玩玩具",
            "device_id": 3,
            "device_name": "客厅"
        }
    ]
    
    print(f"请求URL: {url}")
    print(f"请求数据: 批量创建 {len(events)} 个事件")
    
    response = requests.post(url, json=events)
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def search_events(query, top_k=5):
    """搜索事件"""
    print("\n" + "=" * 60)
    print("示例3: 搜索事件")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/events/search"
    
    search_query = {
        "query": query,
        "top_k": top_k
    }
    
    print(f"请求URL: {url}")
    print(f"搜索查询: {query}")
    print(f"返回数量: {top_k}")
    
    response = requests.post(url, json=search_query)
    
    print(f"\n响应状态码: {response.status_code}")
    result = response.json()
    
    if result.get("success"):
        print(f"\n找到 {result.get('count')} 个相关事件:")
        for i, item in enumerate(result.get("results", []), 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {item['score']:.4f}")
            print(f"  文档: {item['document']}")
            print(f"  元数据: {json.dumps(item['metadata'], ensure_ascii=False)}")
    else:
        print(f"搜索失败: {result.get('error')}")
    
    return result


def search_with_filters(query, filters):
    """带过滤条件搜索"""
    print("\n" + "=" * 60)
    print("示例4: 带过滤条件搜索")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/events/search"
    
    search_query = {
        "query": query,
        "top_k": 5,
        "filters": filters
    }
    
    print(f"请求URL: {url}")
    print(f"搜索查询: {query}")
    print(f"过滤条件: {json.dumps(filters, ensure_ascii=False)}")
    
    response = requests.post(url, json=search_query)
    
    print(f"\n响应状态码: {response.status_code}")
    result = response.json()
    
    if result.get("success"):
        print(f"\n找到 {result.get('count')} 个相关事件:")
        for i, item in enumerate(result.get("results", []), 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {item['score']:.4f}")
            print(f"  文档: {item['document']}")
    else:
        print(f"搜索失败: {result.get('error')}")
    
    return result


def get_collection_info():
    """获取集合信息"""
    print("\n" + "=" * 60)
    print("示例5: 获取集合信息")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/events/collection/info"
    
    print(f"请求URL: {url}")
    
    response = requests.get(url)
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def demo_complete_workflow():
    """完整工作流演示"""
    print("\n" + "=" * 60)
    print("完整工作流演示")
    print("=" * 60)
    
    try:
        # 1. 检查服务健康状态
        print("\n1. 检查服务状态...")
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print("✗ 服务未启动！请先启动服务：python -m app.main")
            return
        print("✓ 服务正常运行")
        
        # 2. 批量创建事件
        print("\n2. 批量创建事件...")
        create_result = create_batch_events()
        if create_result.get("success"):
            print(f"✓ 成功创建 {create_result.get('count')} 个事件")
        
        # 3. 测试不同的搜索查询
        print("\n3. 测试搜索功能...")
        
        queries = [
            "今天门口有什么活动？",
            "宝宝今天怎么样？",
            "有人来访吗？",
            "客厅发生了什么？"
        ]
        
        for query in queries:
            search_events(query, top_k=3)
        
        # 4. 测试过滤搜索
        print("\n4. 测试过滤搜索...")
        search_with_filters("有什么事情发生？", {"device_id": 1})
        
        # 5. 获取集合信息
        print("\n5. 获取集合信息...")
        get_collection_info()
        
        print("\n" + "=" * 60)
        print("✓ 完整工作流演示完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到服务！")
        print("请确保服务已启动：python -m app.main")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\nRAG API 使用示例")
    print("=" * 60)
    print("确保服务已启动：python -m app.main")
    print("=" * 60)
    
    # 运行完整演示
    demo_complete_workflow()


if __name__ == "__main__":
    main()

