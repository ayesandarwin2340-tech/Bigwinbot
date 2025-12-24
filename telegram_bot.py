import telebot
import requests
import time
import os
from threading import Thread
from flask import Flask

# ===== WEB SERVER FOR RENDER =====
app = Flask('')

@app.route('/')
def home():
    return "🔥 Bot is Online and Dominating!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ===== BOT CONFIG =====
API_TOKEN = '8539161053:AAHaZM5-W2q7CpuMnq6CsH74rV2SYq5f0wI'
MY_CHAT_ID = '-1002384693828'
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY1Njg4MzYyIiwibmJmIjoiMTc2NTY4ODM2MiIsImV4cCI6IjE3NjU2OTAxNjIiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMi8xNC8yMDI1IDExOjU5OjIyIEFNIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiQWNjZXNzX1Rva2VuIiwiVXNlcklkIjoiNTg5MTkzIiwiVXNlck5hbWUiOiI5NTk5NjE3MzM4MyIsIlVzZXJQaG90byI6IjgiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR0tVMldJIiwiQW1vdW50IjoiMC4wMCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMTIvMTQvMjAyNSAxMToyOToyMiBBTSIsIkxvZ2luSVBBZGRyZXNzIjoiNjkuMTYwLjI0LjIwNyIsIkRiTnVtYmVyIjoiMCIsIklzdmFsaWRhdG9yIjoiMCIsIktleUNvZGUiOiI0MSIsIlRva2VuVHlwZSI6IkFjY2Vzc19Ub2tlbiIsIlBob25lVHlwZSI6IjEiLCJVc2VyVHlwZSI6IjAiLCJVc2VyTmFtZTIiOiIiLCJpc3MiOiJqd3RJc3N1ZXIiLCJhdWQiOiJsb3R0ZXJ5VGlja2V0In0.efVPTwsPwiwsuXfORcxpTO0RHS52NNRf2v9nUEAW9Bs"
GAME_RESULT_URL = "https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList"

bot = telebot.TeleBot(API_TOKEN)
LAST_PREDICTED_ISSUE = None
LAST_PREDICTION = None

# ================= HELPERS =================
def get_size(num):
    return "SMALL" if int(num) <= 4 else "BIG"

def fetch_data():
    try:
        payload = {"pageSize": 10, "pageNo": 1, "typeId": 1, "language": 7, "random": "0964ea21458141979d84ef05c6936dab", "signature": "84B341EF08510991724EAFE3C8140A8B", "timestamp": int(time.time())}
        headers = {"Content-Type": "application/json;charset=UTF-8", "Authorization": AUTH_TOKEN}
        r = requests.post(GAME_RESULT_URL, json=payload, headers=headers, timeout=10)
        return r.json().get("data", {}).get("list", [])
    except: return []

# ================= PRO PREDICTION LOGIC =================
def pro_predict(results):
    sizes = [get_size(x["number"]) for x in results]
    
    # Trend Analysis (နောက်ဆုံး ၄ ကြိမ်က အတူတူပဲ ထွက်နေရင် လိုက်မယ်)
    if sizes[:4].count("BIG") == 4: return "BIG", 90
    if sizes[:4].count("SMALL") == 4: return "SMALL", 90
    
    # Pattern Analysis (BIG, SMALL, BIG ဆိုရင် SMALL လို့ ခန့်မှန်း)
    if sizes[0] != sizes[1] and sizes[1] != sizes[2]:
        return ("BIG" if sizes[0] == "SMALL" else "SMALL"), 85
    
    # Average Weighting
    big_count = sizes[:10].count("BIG")
    if big_count >= 6: return "BIG", 78
    return "SMALL", 78

# ================= MAIN MONITOR =================
def start_monitoring():
    global LAST_PREDICTED_ISSUE, LAST_PREDICTION
    
    while True:
        data = fetch_data()
        if not data:
            time.sleep(10)
            continue
            
        latest_issue = str(data[0]["issueNumber"])
        next_issue = str(int(latest_issue) + 1)
        
        # ၁။ WIN/LOSE RESULT အရင်ပြမယ်
        if LAST_PREDICTED_ISSUE == latest_issue:
            actual_num = data[0]["number"]
            actual_size = get_size(actual_num)
            win = (actual_size == LAST_PREDICTION)
            icon = "✅ [ WIN ]" if win else "❌ [ LOSE ]"
            
            result_text = (
                f"📊 *PERIOD RESULT: {latest_issue}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎲 Number: `{actual_num}`\n"
                f"🔮 Result: *{actual_size}*\n\n"
                f"💰 Status: {icon}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(MY_CHAT_ID, result_text, parse_mode="Markdown")
            LAST_PREDICTED_ISSUE = None

        # ၂။ နောက်တစ်ကြိမ်အတွက် ခန့်မှန်းချက်ထုတ်မယ်
        if LAST_PREDICTED_ISSUE is None or next_issue != LAST_PREDICTED_ISSUE:
            pred, conf = pro_predict(data)
            pred_icon = "🔴" if pred == "BIG" else "🔵"
            
            predict_text = (
                f"💎 *BIGWIN VIP SIGNAL*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 Period: `{next_issue}`\n"
                f"🎯 Prediction: {pred_icon} *{pred}*\n"
                f"🔥 Confidence: `{conf}%` \n\n"
                f"⚠️ *Note:* အမြဲတမ်း 3-Step သုံးပြီးကစားပါ\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(MY_CHAT_ID, predict_text, parse_mode="Markdown")
            LAST_PREDICTED_ISSUE = next_issue
            LAST_PREDICTION = pred
            
        time.sleep(10)

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    start_monitoring()
