import chromadb
from chromadb.utils import embedding_functions
import datetime

# 定义中文 Embedding 函数
chinese_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5"
)

# 建立长期记忆物理存储
# PersistentClient 会将记忆数据保存在当前目录下的 "agent_memory" 文件夹中
client = chromadb.PersistentClient(path="./Memory/long_memory")

# 划分记忆脑区 (Collection)
# 你可以创建多个集合，比如 "daily_chat" 存日常对话，"code_snippets" 存代码片段
collection = client.get_or_create_collection(name="Long_memory", embedding_function=chinese_ef)


def AddMemory(memory, type="general", date=None, id=None, **kwargs):
    if id is None:
        id = f"mem_{len(collection.get()['ids']) + 1}"
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    collection.add(
        documents=[memory],
        metadatas=[{"type": type, "date": date, **kwargs}],
        ids=[id]  # 自动生成唯一 ID
    )
    return True

def SearchMemory(text, n_results=3, type=None, date=None, distance_threshold=0.5):
    """
    在长期记忆集合中搜索与文本最相似的记录。

    参数:
        text (str): 查询文本。
        n_results (int): 返回的最大结果数（过滤前）。
        type (str, optional): 按类型过滤（元数据字段）。
        date (str, optional): 按日期过滤（元数据字段）。
        distance_threshold (float, optional): 距离阈值，只返回距离 <= 该值的结果。

    返回:
        dict: 包含 ids, distances, metadatas, documents 的字典，结构与 ChromaDB 查询结果一致。
    """
    # 构建元数据过滤条件
    where_clause = {}
    if type is not None:
        where_clause["type"] = type
    if date is not None:
        where_clause["date"] = date
    where = where_clause if where_clause else None

    # 执行查询
    results = collection.query(
        query_texts=[text],
        n_results=n_results,
        where=where
    )

    # 如果设置了距离阈值，过滤结果
    if distance_threshold is not None and results['distances'] is not None:
        # 由于 query_texts 是单元素列表，取第一个结果集
        distances = results['distances'][0]
        ids = results['ids'][0]
        metadatas = results['metadatas'][0] if results['metadatas'] else None
        documents = results['documents'][0] if results['documents'] else None

        # 筛选符合条件的项
        filtered_ids = []
        filtered_distances = []
        filtered_metadatas = []
        filtered_documents = []

        for i, dist in enumerate(distances):
            if dist <= distance_threshold:
                filtered_ids.append(ids[i])
                filtered_distances.append(dist)
                if metadatas:
                    filtered_metadatas.append(metadatas[i])
                if documents:
                    filtered_documents.append(documents[i])

        # 重新组装结果字典（保持原有结构）
        results = {
            'ids': filtered_ids,
            'distances': filtered_distances,
            'metadatas': filtered_metadatas if filtered_metadatas else None,
            'documents': filtered_documents if filtered_documents else None
        }

    return results

def GetRecentMemory(limit=10, type="history"):
    """
    不进行语义搜索，直接获取最近的记录
    """
    # 使用 get 获取符合条件的数据（不计算向量距离）
    results = collection.get(
        where={"type": type},
        include=["metadatas", "documents"]
    )
    
    contexts = []
    if results and results.get('metadatas') and results.get('documents'):
        for metadata, document in zip(results['metadatas'], results['documents']):
            contexts.append({
                "title": document,
                "date": metadata.get('date', '未知日期'),
                "original_context": metadata.get('original_context', '无效内容')
            })
            
    # 在 Python 内存中按日期降序排序（最新的排前面）
    contexts = sorted(contexts, key=lambda x: x['date'], reverse=True)
    
    # 截取前 N 条
    return contexts[:limit]


if __name__ == "__main__":
    # all_data = collection.get(include=[])  # include=[] 表示只返回 ids
    # all_ids = all_data['ids']

    # if all_ids:
    #     collection.delete(ids=all_ids)
    #     print(f"已删除 {len(all_ids)} 条记录，集合现为空。")
    # else:
    #     print("集合本来就是空的。")

    # AddMemory("用户今天开始构思一个具有自主意识的本地 AI 助手架构。", type="general", date=None, id=None)
    # AddMemory("用户在处理 Python 依赖环境时遇到了版本冲突，花了半个小时解决。", type="bug_fix", date=None, id=None)
    # AddMemory("用户在配置 Docker 环境时，发现容器启动失败，检查了配置文件，发现端口映射错误。", type="bug_fix", date=None, id=None)
    # AddMemory("用户在使用本地 AI 助手时，发现它无法理解用户的指令，检查了代码，发现是因为没有正确处理用户输入。", type="bug_fix", date=None, id=None)

    print("后五条记忆：")
    all_data = collection.get(include=[])  # include=[] 表示只返回 ids
    all_ids = all_data['ids']

    # 2. 检查是否有数据
    if all_ids:
        # 3. 计算并获取最后五个 ID
        last_five_ids = all_ids[-5:]
        
        # 4. 用这些 ID 去获取完整的数据
        last_five_items = collection.get(
            ids=last_five_ids,
            include=["documents", "metadatas", "embeddings"] # 根据需要选择返回的字段
        )
        print(last_five_items)
    else:
        print("集合中没有数据。")

    results = SearchMemory("你周末有空教教我昨天的考试吗", n_results=3, type=None, date=None, distance_threshold=1.5)
    for index in range(len(results['ids'])):
        print(f"ID: {results['ids'][index]}")
        print(f"距离: {results['distances'][index]}")
        if results['metadatas']:
            print(f"元数据: {results['metadatas'][index]}")
        if results['documents']:
            print(f"文档: {results['documents'][index]}")
        print("-" * 40)

    # results = SearchMemory("用户在写代码", n_results=3, type=None, date=None, distance_threshold=0.5)
    # for index in range(len(results['ids'][0])):
    #     print(f"ID: {results['ids'][0][index]}")
    #     print(f"距离: {results['distances'][0][index]}")
    #     if results['metadatas']:
    #         print(f"元数据: {results['metadatas'][0][index]}")
    #     if results['documents']:
    #         print(f"文档: {results['documents'][0][index]}")
    #     print("-" * 40)

    # results = SearchMemory("用户在写代码", n_results=3, type=None, date=None, distance_threshold=0.5)
    # for index in range(len(results['ids'][0])):
    #     print(f"ID: {results['ids'][0][index]}")
    #     print(f"距离: {results['distances'][0][index]}")
    #     if results['metadatas']:
    #         print(f"元数据: {results['metadatas'][0][index]}")
    #     if results['documents']:
    #         print(f"文档: {results['documents'][0][index]}")
    #     print("-" * 40)

    
