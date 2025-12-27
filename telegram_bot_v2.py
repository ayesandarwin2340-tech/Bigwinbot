import telebot
import requests
import time
import os
from threading import Thread
from flask import Flask
from collections import Counter

# ===== WEB SERVER =====
app = Flask('')
@app.route('/')
def home(): return "🔥 VIP Bot is Online!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ===== BOT CONFIG =====
API_TOKEN = '8539161053:AAHaZM5-W2q7CpuMnq6CsH74rV2SYq5f0wI'
MY_CHAT_ID = '-1002384693828'
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY1Njg4MzYyIiwibmJmIjoiMTc2NTY4ODM2MiIsImV4cCI6IjE3NjU2OTAxNjIiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMi8xNC8yMDI1IDExOjU5OjIyIEFNIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiQWNjZXNzX1Rva2VuIiwiVXNlcklkIjoiNTg5MTkzIiwiVXNlck5hbWUiOiI5NTk5NjE3MzM4MyIsIlVzZXJQaG90byI6IjgiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR0tVMldJIiwiQW1vdW50IjoiMC4wMCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMTIvMTQvMjAyNSAxMToyOToyMiBBTSIsIkxvZ2luSVBBZGRyZXNzIjoiNjkuMTYwLjI0LjIwNyIsIkRiTnVtYmVyIjoiMCIsIklzdmFsaWRhdG9yIjoiMCIsIktleUNvZGUiOiI0MSIsIlRva2VuVHlwZSI6IkFjY2Vzc19Ub2tlbiIsIlBob25lVHlwZSI6IjEiLCJVc2VyVHlwZSI6IjAiLCJVc2VyTmFtZTIiOiIiLCJpc3MiOiJqd3RJc3N1ZXIiLCJhdWQiOiJsb3R0ZXJ5VGlja2V0In0.efVPTwsPwiwsuXfORcxpTO0RHS52NNRf2v9nUEAW9Bs"
GAME_RESULT_URL = "https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList"

bot = telebot.TeleBot(API_TOKEN)

# Stats Memory
history_list = []
win_count = 0
lose_count = 0
win_streak = 0
lose_streak = 0
current_win_s = 0
current_lose_s = 0

# GLOBAL STATE
LAST_SENT_PREDICTION_PERIOD = None
PENDING_PREDICTION = None

# ================= HELPERS =================
def get_size(num):
    return "SMALL" if int(num) <= 4 else "BIG"

def get_most_frequent_digit(results, size):
    digits = [x["number"] for x in results if get_size(x["number"]) == size]
    if not digits: return "0"
    return Counter(digits).most_common(1)[0][0]

def fetch_data():
    try:
        payload = {"pageSize": 10, "pageNo": 1, "typeId": 1, "language": 7, "random": "0964ea21458141979d84ef05c6936dab", "signature": "84B341EF08510991724EAFE3C8140A8B", "timestamp": int(time.time())}
        headers = {"Content-Type": "application/json;charset=UTF-8", "Authorization": AUTH_TOKEN}
        r = requests.post(GAME_RESULT_URL, json=payload, headers=headers, timeout=10)
        return r.json().get("data", {}).get("list", [])
    except: return []

def pro_predict(results):
    short_seq = "".join(["B" if get_size(x["number"]) == "BIG" else "S" for x in results[:5][::-1]])
    patterns = {
        "BSBSB": "SMALL", "SBSBS": "BIG", "SSBBS": "SMALL", "BBSSB": "BIG",
        "SSSBB": "BIG", "BBBSS": "SMALL", "BSSBS": "SMALL", "SBBSB": "BIG",
        "BSSSB": "SMALL", "SBBBS": "BIG", "SBBSS": "BIG", "BSSBB": "SMALL",
        "BBSBB": "SMALL", "SSBSS": "BIG",
        "SBBBB": "BIG", "BSSSS": "SMALL",
        "SSSSB": "SMALL", "BBBBS": "SMALL",
         "SSSBS": "SMALL", "BBBSB": "BIG",
        "SBSSB": "SMALL", "BSBBS": "BIG",
        "SSSBB": "BIG","BBBBB": "BIG",
        "SSSSS": "SMALL","SBSSB": "BIG","BSBBS": "SMALL",
        "BSSSB": "BIG","SBBBS": "SMALL","SBBSS": "SMALL"
    }
    pred = patterns.get(short_seq)
    if pred: return pred, 99
    return get_size(results[0]["number"]), 50

# ================= MONITORING =================
def start_monitoring():
    global LAST_SENT_PREDICTION_PERIOD, PENDING_PREDICTION, win_count, lose_count, win_streak, lose_streak, current_win_s, current_lose_s
    
    while True:
        data = fetch_data()
        if not data:
            time.sleep(5)
            continue
            
        latest_issue = str(data[0]["issueNumber"])
        
        # ၁။ Result စစ်ဆေးခြင်း (Predict ထားတဲ့ Period ထွက်လာရင်)
        if PENDING_PREDICTION and PENDING_PREDICTION['period'] == latest_issue:
            actual_num = data[0]["number"]
            actual_size = get_size(actual_num)
            is_win = (actual_size == PENDING_PREDICTION['side'])
            
            # Stats Update
            if is_win:
                win_count += 1
                current_win_s += 1
                current_lose_s = 0
                win_streak = max(win_streak, current_win_s)
            else:
                lose_count += 1
                current_lose_s += 1
                current_win_s = 0
                lose_streak = max(lose_streak, current_lose_s)

            history_list.append({"period": latest_issue, "pred": PENDING_PREDICTION['side'], "actual": actual_size, "win": is_win})
            
            # Result Message
            res_icon = "✅ [ WIN ]" if is_win else "❌ [ LOSE ]"
            result_msg = (
                f"📊 *PERIOD RESULT: {latest_issue}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎲 Number: `{actual_num}`\n"
                f"🔮 Result: *{actual_size}({actual_num})*\n\n"
                f"💰 Status: {res_icon}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(MY_CHAT_ID, result_msg, parse_mode="Markdown")
            PENDING_PREDICTION = None # Result ပြပြီးရင် ရှင်းမယ်

            # ၁၀ ပွဲပြည့်ရင် Summary ပြမယ်
            if len(history_list) % 10 == 0 and len(history_list) > 0:
                table_text = "📊 *GAME HISTORY (LAST 10)*\n"
                table_text += "`Period      Predict/Actual    Res`\n"
                for h in reversed(history_list[-10:]):
                    icon = "✅" if h["win"] else "❌"
                    table_text += f"`{h['period'][-5:]}       {h['pred'][:1]}/{h['actual'][:1]}             {icon}`\n"
                
                total = win_count + lose_count
                win_rate = (win_count / total * 100)
                
                summary = (
                    f"\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"💚 WIN•[{win_count}]  | ❤️ Lose•[{lose_count}]\n"
                    f"✅ Streak: {win_streak}     | ❌ Streak: {lose_streak}\n"
                    f"🔀 Total {total} | 📈 Win Rate: {win_rate:.1f}%\n\n"
                    f"======= DEVELOPED BY KELVIN ======="
                )
                bot.send_message(MY_CHAT_ID, table_text + summary, parse_mode="Markdown")

        # ၂။ Prediction အသစ်ထုတ်ခြင်း
        next_period = str(int(latest_issue) + 1)
        if LAST_SENT_PREDICTION_PERIOD != next_period:
            pred_side, conf = pro_predict(data)
            best_digit = get_most_frequent_digit(data, pred_side)
            
            p_icon = "🔴" if pred_side == "BIG" else "🔵"
            predict_msg = (
                f"💎 *BIGWIN VIP SIGNAL BY 𝗠𝗶𝗹𝗹𝗶𝗼𝗻𝗮𝗶𝗿𝗲 𝗧𝗲𝗮𝗺 *\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 Period: `{next_period}`\n"
                f"🎯 Prediction: {p_icon} *{pred_side}({best_digit})*\n"
                f"🔥 Confidence: `{conf}%` \n\n"
                f"⚠️ *Note:* 4ဇဆောင်ပီးမှ ဆော့ပါ။   🧠လူတောင်အမြဲမမှန်တာ BOTလည်းအမြဲမမှန်ပါ။\n\n"
                
                f"🚀Status: Waiting For Results...\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(MY_CHAT_ID, predict_msg, parse_mode="Markdown")
            
            LAST_SENT_PREDICTION_PERIOD = next_period
            PENDING_PREDICTION = {'period': next_period, 'side': pred_side}
            
        time.sleep(8) # ၈ စက္ကန့်တစ်ခါ data စစ်မယ်

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    start_monitoring()
