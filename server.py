import json, os, sys, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from openai import OpenAI

PORT = int(os.environ.get("PORT", 8080))
DIR = r"D:\AI\kunming"
API_KEY = "sk-f0e67df8d3dc4bef9f9fd3ccdd007ee2"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            city = data.get("city", "")
            days = data.get("days", 3)
            people = data.get("people", 2)
            budget = data.get("budget", "comfort")
            pace = data.get("pace", "moderate")
            arrive_time = data.get("arrive_time", "12:00")
            arrive_place = data.get("arrive_place", "")
            leave_time = data.get("leave_time", "16:30")
            leave_place = data.get("leave_place", "")
            hotel = data.get("hotel", "")
            need_luggage = data.get("need_luggage", True)
            diet = data.get("diet", "any")
            styles = data.get("styles", [])
            must_visit = data.get("must_visit", [])
            extra = data.get("extra", "")

            if not city:
                self.send_json({"error": "\u8bf7\u8f93\u5165\u76ee\u7684\u5730\u57ce\u5e02"})
                return

            prompt = build_prompt(city, days, people, budget, pace, arrive_time, arrive_place,
                                  leave_time, leave_place, hotel, need_luggage, diet, styles,
                                  must_visit, extra)

            try:
                client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4096
                )
                result = response.choices[0].message.content
                self.send_json({"result": result})
            except Exception as e:
                self.send_json({"error": f"API \u8c03\u7528\u5931\u8d25: {str(e)}"})
        else:
            self.send_json({"error": "Not found"})

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

SYSTEM_PROMPT = """你是一个专业的旅行规划师。你的任务是根据用户提供的信息，生成一份详尽、实用的旅行攻略。

## 输出格式要求

请按以下 Markdown 格式输出攻略：

### 📋 行程概览
一个简洁的表格，列出每天的主题和核心景点。

### 🏨 住宿建议
推荐住宿区域和类型（如果用户提供了酒店地址则确认）。

然后为每一天生成以下内容：

### 📅 Day N — 主题名称

每个景点/活动包含：
- **时间**：具体到达和离开时间
- **🚖/🚶 交通**：景点间的交通方式（步行<15分钟标注🚶步行，否则标注🚖打车，并给出预估里程和费用）
- **⏱ 建议游玩**：游玩时长
- **💰 门票**：标注"免费"或具体价格
- **📝 简介**：1-2句话介绍亮点

每天结束后注明晚餐推荐。

### 🚖 打车费用估算
表格列出每天每段打车的里程和费用，最后给出总计。

### 🍜 美食推荐
列出当地必吃美食及推荐店铺。

### 📝 实用贴士
4-6条当地旅行实用建议。

## 核心规则

1. **到达日（Day 1）**：用户到达后，先去酒店办理入住再开始游玩。根据到达时间合理安排。
2. **离开日（最后一天）**：预留去机场/车站的时间（提前1.5-2小时到达）。如需回酒店取行李要预留时间。
3. **景点安排**：按地理位置合理排序，避免来回跑。同方向的景点安排在一起。
4. **交通方式**：相邻景点步行<15分钟就用🚶步行，否则🚖打车。标注预估里程和费用（按滴滴计价，约¥2.5/km）。
5. **门票标注**：每个景点必须标注"免费"或具体门票价格（¥）。
6. **餐饮**：每天推荐午餐和晚餐的去处和特色菜。
7. **时间合理**：每个景点游玩时间合理，不要安排太紧或太松。考虑用餐和交通时间。
8. **用户偏好**：根据用户选择的旅行偏好（人文/自然/美食/拍照/休闲/徒步）调整景点推荐。
9. **预算匹配**：经济实惠多推荐免费景点和街头小吃；舒适享受均衡搭配；轻奢体验推荐高端餐厅和精品体验。
10. **节奏匹配**：紧凑充实每天安排4-5个景点，适中均衡3-4个，轻松悠闲2-3个。

## 语言风格

- 使用中文
- 口语化、亲切但不失专业
- 像朋友在给你推荐行程
- 适当使用 emoji 增加可读性（但不要过度）
- 具体、实用、可操作"""

def build_prompt(city, days, people, budget, pace, arrive_time, arrive_place,
                 leave_time, leave_place, hotel, need_luggage, diet, styles, must_visit, extra):
    p = f"""请为我的{city}{days}日游生成一份详细攻略。

## 基本信息
- 目的地：{city}
- 天数：{days}天
- 人数：{people}人
- 预算：{"经济实惠" if budget=="budget" else "舒适享受" if budget=="comfort" else "轻奢体验"}
- 节奏：{"紧凑充实" if pace=="packed" else "适中均衡" if pace=="moderate" else "轻松悠闲"}
- 到达时间：Day 1 {arrive_time}{" 抵达"+arrive_place if arrive_place else ""}
- 离开时间：Day {days} {leave_time}{" 从"+leave_place+"出发" if leave_place else ""}
"""

    if hotel:
        p += f"- 酒店：{hotel}（以此为据点安排行程）\n"
    else:
        p += f"- 酒店：未指定，请根据预算推荐最佳住宿区域\n"

    if need_luggage:
        p += f"- 离开日需回酒店取行李再出发\n"

    if styles:
        style_names = {"culture": "人文历史", "nature": "自然风光", "food": "美食探店",
                       "photo": "拍照打卡", "relax": "休闲放空", "hike": "徒步户外"}
        p += f"- 旅行偏好：{', '.join(style_names.get(s, s) for s in styles)}\n"

    if must_visit:
        p += f"- 必去景点：{', '.join(must_visit)}（必须安排进行程）\n"
    else:
        p += "- 必去景点：无特别要求，请根据城市热门程度和偏好智能推荐\n"

    if diet != "any":
        diet_names = {"local": "偏好本地特色菜", "light": "清淡口味", "spicy": "无辣不欢", "veggie": "偏好素食"}
        p += f"- 饮食偏好：{diet_names.get(diet, diet)}\n"

    if extra:
        p += f"- 特殊要求：{extra}\n"

    p += f"""
请严格按系统指令中的格式生成攻略。记得：
- 每个景点标注免费/价格
- 景点间标注交通方式和预估费用
- 每天推荐餐饮
- 打车费用单独汇总
- 给出实用贴士
"""
    return p

if __name__ == "__main__":
    print(f"Server starting at http://0.0.0.0:{PORT}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")