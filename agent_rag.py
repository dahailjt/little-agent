from openai import OpenAI
import json
import os
import requests
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ========== 初始化向量数据库 ==========
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="students",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
)

# 启动时加载数据
if collection.count() == 0:
    print("[INFO] 正在初始化向量数据库...")
    with open("students.txt", "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    documents, ids = [], []
    for i, line in enumerate(lines):
        documents.append(line)
        ids.append(f"stu{i}")
    collection.add(documents=documents, ids=ids)
    print(f"[OK] 向量数据库初始化完毕，已加载 {collection.count()} 条学生记录\n")
else:
    print(f"[OK] 向量数据库初始化完毕，已加载 {collection.count()} 条学生记录\n")


# ========== 五个工具函数 ==========

def get_weather(city):
    """从互联网实时查询天气"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        data = requests.get(url, timeout=5).json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = current["temp_C"]
        humidity = current["humidity"]
        wind = current["winddir16Point"]
        return f"{city}：{desc}，温度{temp}°C，湿度{humidity}%，风向{wind}"
    except:
        return f"查询{city}天气失败，请检查城市名是否正确"

def calculate(expression):
    """计算数学表达式"""
    try:
        return str(eval(expression))
    except:
        return "请输入正确的数学表达式"

def get_quote():
    """获取每日一言"""
    try:
        url = "https://v1.hitokoto.cn/"
        data = requests.get(url).json()
        return data["hitokoto"]
    except:
        return "查询每日一言失败"

def search_student_score(query):
    """向量搜索学生成绩——把自然语言转成语义匹配"""
    results = collection.query(query_texts=[query], n_results=3)
    lines = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        lines.append(f"[匹配度 {1-dist:.1%}] {doc}")
    return "\n".join(lines) if lines else "未找到相关学生数据"

def translate(word: str, src: str = "en", dst: str = "zh-CN") -> str:
    url = "https://api.mymemory.translated.net/get"
    r = requests.get(url, params={"q": word, "langpair": f"{src}|{dst}"}, timeout=8)
    data = r.json()
    if data.get("responseStatus") != 200:
        raise RuntimeError(data.get("responseDetails", "unknown error"))
    return data["responseData"]["translatedText"]
# ========== 工具定义（给模型看的说明书） ==========

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如广州"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 1+2*3"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_quote",
            "description": "获取一句随机名言或鸡汤",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_student_score",
            "description": "搜索学生成绩。当用户问谁某科最好/最差、某学生的某科成绩、排名等问题时调用。query用自然语言描述即可，如'数学成绩'、'谁语文最好'",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询，如'数学成绩'、'语文最高分'"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"translate",
            "description":"翻译英语单词，给出中文释义，当用户要查询英语单词意思的时候使用",
            "parameters":{
                "type":"object",
                "properties":{
                    "word":{"type":"string","description":"英语单词，如apple"}
                },
                "required":['word']
            }
        }
    }
]

# ========== 主循环 ==========
messages = [{"role": "system", "content": "你是一个有用的助手，可以查天气、算数学、获取名言、搜索学生成绩和查询英语单词。当用户问成绩相关问题时，务必先调用 search_student_score 搜索数据，再根据结果回答。"}]

while True:
    user_input = input("\n你: ")
    if user_input in ("quit", "exit"):
        print("再见！")
        break

    messages.append({"role": "user", "content": user_input})

    # 第一轮：模型决定是否调工具
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        # 模型要调工具
        messages.append(msg)
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if name == "get_weather":
                result = get_weather(args["city"])
            elif name == "calculate":
                result = calculate(args["expression"])
            elif name == "get_quote":
                result = get_quote()
            elif name == "search_student_score":
                result = search_student_score(args["query"])
            elif name == "translate":
                result =translate(args["word"])
            else:
                result = "未知工具"
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # 第二轮：模型根据工具结果生成最终回答
        response2 = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
        )
        reply = response2.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print("\nAI:", reply)
    else:
        # 直接回答
        content = msg.content or ""  # None 时兜底为空字符串
        messages.append({"role": "assistant", "content": content})
        print("\nAI:", msg.content)
