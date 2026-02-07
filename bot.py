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
server = Flask(__name__)

# 2. THE IMPROVED EGCSE BRAIN (NO MATH CODE)
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'. Expert in EGCSE Eswatini Biology and Physical Science.\n\n"
    "CRITICAL FORMATTING RULE:\n"
    "- NEVER use LaTeX, $, or backslashes (\\) for math.\n"
    "- For degrees, use 'degrees C' or 'o C'.\n"
    "- For fractions, use 'divide' or '/' (e.g., 1/2).\n"
    "- For powers, use '^' (e.g., m/s^2).\n"
    "- Use plain text only so it is readable on Telegram mobile.\n\n"
    "STRUCTURE:\n"
    "1. QUICK NOTES: Clear, bullet-pointed notes.\n"
    "2. EXAM STYLE QUIZ: Offer P1 (Recall), P2 (Theory/Calculation), or P4 (Practical).\n\n"
    "TONE: Friendly, Eswatini-focused, and very clear."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Sawubona! I am the Ejubukweni High AI Study Buddy. 📚\n\n"
                         "I've been upgraded to be easier to read! What topic are we revising today?")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        # Send the cleaned response
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "I'm having a quick study break. Please try again!")

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@server.route("/")
def index():
    return "<h1>Ejubukweni High Bot is Online and Clean!</h1>", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
