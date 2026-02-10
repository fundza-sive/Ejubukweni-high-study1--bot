import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

# Using the most stable production name
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

SYSTEM_INSTRUCTION = (
    "You are the Ejubukweni High School AI Tutor. Provide EGCSE Biology and Physical Science notes.\n"
    "Use **BOLD** for headers and • for lists. Be concise to ensure speed."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "**Sawubona!** I am awake. Ask me any Biology or Science question!", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # 1. Show typing
        bot.send_chat_action(message.chat.id, 'typing')
        
        # 2. Simple generation (removed retry to prevent infinite typing)
        # We add safety_settings=None to prevent the AI from blocking school topics
        response = model.generate_content(
            f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}"
        )
        
        # 3. Reply
        if response.text:
            bot.reply_to(message, response.text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "I couldn't generate text. Please rephrase your question.")

    except Exception as e:
        print(f"Error: {e}")
        # If Markdown fails, send as plain text
        try:
            bot.send_message(message.chat.id, "Here are your notes (plain text):")
            bot.send_message(message.chat.id, response.text)
        except:
            bot.send_message(message.chat.id, "Connecting... please try again in a few seconds.")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Bot Status: Active</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

