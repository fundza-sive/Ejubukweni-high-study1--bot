import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. API CONFIGURATION
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini AI
genai.configure(api_key=GEMINI_KEY)
# Using the latest Gemini 3 model for best performance in 2026
model = genai.GenerativeModel("gemini-3-flash-preview")

# Initialize the Bot and the Web Server
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# 2. THE MASTER EGCSE SYSTEM PROMPT
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High EGCSE Study Buddy'. You are an expert tutor for "
    "Eswatini Biology (6884) and Physical Science (6888) syllabi for Form 4 and 5.\n\n"
    "When a student asks for a topic, follow this structure:\n"
    "1. BRIEF NOTES: Provide clear, point-form notes on the topic.\n"
    "2. EXAM STYLE QUIZ: Ask the student if they want questions from P1, P2, or P4.\n\n"
    "STRICT EXAM FORMATS:\n"
    "- P1: Short, 1-mark recall or multiple-choice questions.\n"
    "- P2: Structured questions with parts (a) and (b). Include science calculations.\n"
    "- P4: Alternative to Practical. Describe an experiment (like food tests or density measurements) "
    "and ask about variables, observations, or safety precautions.\n\n"
    "TONE: Use SI units, be encouraging, and use local Eswatini examples where possible."
)

# 3. BOT HANDLERS
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = (
        "Sawubona! I am the Ejubukweni High AI Study Buddy. 📚\n\n"
        "I'm ready for Biology, Physical Science, or Math.\n"
        "What topic are we revising today?"
    )
    bot.reply_to(message, welcome_msg)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        prompt = f"{SYSTEM_INSTRUCTION}\n\nStudent asks: {message.text}"
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "I'm having a quick brain-break. Please try again in a moment!")

# 4. SERVER & WEBHOOK LOGIC
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def webhook():
    return "<h1>Ejubukweni Bot is Running!</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
