import telebot
import requests
import time
from collections import defaultdict

# ================= CONFIG =================
API_TOKEN = '8539161053:AAHaZM5-W2q7CpuMnq6CsH74rV2SYq5f0wI' 
MY_CHAT_ID = '-1002384693828' 

bot = telebot.TeleBot(API_TOKEN)

GAME_RESULT_URL = "https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList"
# သင့်ရဲ့ Header Token ကို ဒီမှာ အသေထားထားပါမယ်
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY1Njg4MzYyIiwibmJmIjoiMTc2NTY4ODM2MiIsImV4cCI6IjE3NjU2OTAxNjIiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMi8xNC8yMDI1IDExOjU5OjIyIEFNIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiQWNjZXNzX1Rva2VuIiwiVXNlcklkIjoiNTg5MTkzIiwiVXNlck5hbWUiOiI5NTk5NjE3MzM4MyIsIlVzZXJQaG90byI6IjgiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR0tVMldJIiwiQW1vdW50IjoiMC4wMCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMTIvMTQvMjAyNSAxMToyOToyMiBBTSIsIkxvZ2luSVBBZGRyZXNzIjoiNjkuMTYwLjI0LjIwNyIsIkRiTnVtYmVyIjoiMCIsIklzdmFsaWRhdG9yIjoiMCIsIktleUNvZGUiOiI0MSIsIlRva2VuVHlwZSI6IkFjY2Vzc19Ub2tlbiIsIlBob25lVHlwZSI6IjEiLCJVc2VyVHlwZSI6IjAiLCJVc2VyTmFtZTIiOiIiLCJpc3MiOiJqd3RJc3N1ZXIiLCJhdWQiOiJsb3R0ZXJ5VGlja2V0In0.efVPTwsPwiwsuXfORcxpTO0RHS52NNRf2v9nUEAW9Bs"

# Global Variables
LAST_PREDICTED_ISSUE = None
LAST_PREDICTION = None

# ================= HELPERS =================
def get_big_or_small(num):
    try:
        n = int(num)
        return "SMALL" if n <= 4 else "BIG"
    except: return "N/A"

def fetch_and_get_data():
    try:
        payload = {
            "pageSize": 10, "pageNo": 1, "typeId": 1, "language": 7,
            "random": "0964ea21458141979d84ef05c6936dab",
            "signature": "84B341EF08510991724EAFE3C8140A8B",
            "timestamp": int(time.time())
        }
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": AUTH_TOKEN
        }
        r = requests.post(GAME_RESULT_URL, json=payload, headers=headers, timeout=10)
        data = r.json()
        lst = data.get("data", {}).get("list", [])
        return lst
    except: return []

def predict_next(results_list):
    sizes = [get_big_or_small(x["number"]) for x in results_list if get_big_or_small(x["number"]) != "N/A"][:12]
    if len(sizes) < 4: return "BIG", 60
    
    last3 = sizes[:3]
    if last3.count("BIG") >= 2: return "BIG", 75
    else: return "SMALL", 75

# ================= TELEGRAM MONITOR =================
def start_prediction():
    global LAST_PREDICTED_ISSUE, LAST_PREDICTION
    
    print("Bot is running... Monitoring Win/Lose...")
    
    while True:
        results = fetch_and_get_data()
        if not results:
            time.sleep(5)
            continue

        latest_issue = str(results[0]["issueNumber"])
        next_issue = str(int(latest_issue) + 1)

        # ၁။ Win/Lose စစ်ဆေးခြင်း (ပြီးခဲ့တဲ့ Period အတွက်)
        if LAST_PREDICTED_ISSUE == latest_issue:
            actual_num = results[0]["number"]
            actual_size = get_big_or_small(actual_num)
            
            is_win = (actual_size == LAST_PREDICTION)
            status_icon = "✅ WIN" if is_win else "❌ LOSE"
            
            result_msg = (
                f"📊 *RESULT FOR {latest_issue}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Number: `{actual_num}` ({actual_size})\n"
                f"Status: *{status_icon}*"
            )
            bot.send_message(MY_CHAT_ID, result_msg, parse_mode="Markdown")
            LAST_PREDICTED_ISSUE = None # Reset ပေးခြင်း

        # ၂။ ခန့်မှန်းချက်အသစ်ထုတ်ပြန်ခြင်း
        if LAST_PREDICTED_ISSUE is None or next_issue != LAST_PREDICTED_ISSUE:
            prediction, confidence = predict_next(results)
            
            predict_msg = (
                f"🎰 *BIGWIN PREDICTION*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📍 Period: `{next_issue}`\n"
                f"🎯 Predict: *{prediction}*\n"
                f"🔥 Confidence: {confidence}%\n\n"
                f"🔔 အချိန်မီ လောင်းထားကြပါ!"
            )
            
            bot.send_message(MY_CHAT_ID, predict_msg, parse_mode="Markdown")
            LAST_PREDICTED_ISSUE = next_issue
            LAST_PREDICTION = prediction
                
        time.sleep(10) # API ကို ဝန်မပိအောင် ၁၀ စက္ကန့်တစ်ခါ စစ်ပေးပါ

if __name__ == "__main__":
    start_prediction()
