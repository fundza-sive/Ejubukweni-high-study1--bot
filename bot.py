import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import traceback

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Safety check for Environment Variables
if not TOKEN or not GEMINI_KEY:
    print("CRITICAL ERROR: Environment variables (TELEGRAM_TOKEN or GEMINI_API_KEY) are missing!")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'.\n"
    "Use **BOLD** for headers and be helpful for EGCSE students."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, "**Sawubona!** I am awake and ready. How can I help you study today?", parse_mode='Markdown')
    except Exception as e:
        print(f"Error in start command: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        print(f"Received message: {message.text}") # This will show in Render Logs
        response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        bot.reply_to(message, response.text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error handling message: {traceback.format_exc()}")
        # Fallback to plain text if Markdown fails
        try:
            bot.reply_to(message, "I encountered an error. Let me try answering without formatting:\n\n" + response.text)
        except:
            bot.reply_to(message, "Sorry, I'm having trouble connecting to my AI brain right now.")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    except Exception as e:
        print(f"Webhook Error: {e}")
        return "error", 500

@app.route("/")
def index():
    return f"<h1>Ejubukweni Bot Status: Online</h1><p>Token: {TOKEN[:5]}***</p>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

