import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import time

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

# Using the full model path to fix the 404 error you saw in the logs
MODEL_NAME = "models/gemini-1.5-flash-latest" 
model = genai.GenerativeModel(MODEL_NAME)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'.\n"
    "Help students with EGCSE Biology and Physical Science.\n"
    "Use **BOLD** for headings and bullet points for lists."
)

def generate_with_retry(prompt, retries=5):
    """Exponential backoff for API calls"""
    for i in range(retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if i == retries - 1: raise e
            time.sleep(2**i) # Wait 1s, 2s, 4s...

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "**Sawubona!** I am your Ejubukweni High Study Buddy. 📚\n\n"
                         "How can I help you with Biology or Science today?", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show 'typing' status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = generate_with_retry(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        
        # Check if response has text
        if response and response.text:
            bot.reply_to(message, response.text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "I understood you, but I couldn't generate a text response. Please try again.")
            
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "I'm having a small brain-freeze. Please try asking again in a moment!")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Ejubukweni Bot: System Patched</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

