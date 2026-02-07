import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
server = app # This ensures Render finds it whether it looks for 'app' or 'server'

# 2. THE CLEAN TEXT EGCSE BRAIN
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'. Expert in EGCSE Eswatini Biology and Physical Science.\n\n"
    "CRITICAL FORMATTING RULE FOR TELEGRAM:\n"
    "- NEVER use LaTeX, $, or backslashes (\\) for math.\n"
    "- Use 'degrees C' instead of the degree symbol with code.\n"
    "- Use '/' for fractions and '^' for powers.\n"
    "- Use simple text labels like 'Formula:' instead of complex math blocks.\n"
    "- Ensure every response is easy to read on a small mobile screen.\n\n"
    "STRUCTURE:\n"
    "1. QUICK NOTES: Clear, bullet-pointed notes.\n"
    "2. EXAM STYLE QUIZ: Offer P1 (Recall), P2 (Theory/Calculation), or P4 (Practical)."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Sawubona! I am the Ejubukweni High AI Study Buddy. 📚\n\n"
                         "I'm updated with cleaner text for Science and Math. What topic are we revising?")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "I'm taking a quick study break. Please try again!")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Ejubukweni High Bot is Online and Clean!</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
