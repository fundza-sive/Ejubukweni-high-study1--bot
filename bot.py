import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
# Using the latest stable flash model for speed on mobile
model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__) # This MUST be named 'app' for Render/Gunicorn

# 2. THE EGCSE ESWATINI BRAIN
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'. You are an expert in the "
    "EGCSE Eswatini (ECESWA) syllabi for Biology (6884) and Physical Science (6888).\n\n"
    "When a student asks for a topic, follow this structure:\n"
    "1. QUICK NOTES: Provide clear, bullet-pointed notes suitable for Form 4/5.\n"
    "2. EXAM STYLE QUIZ: Offer to test them with a question from:\n"
    "   - Paper 1 (P1): Multiple choice / Short recall.\n"
    "   - Paper 2 (P2): Structured theory (Include $formulas$ if Science).\n"
    "   - Paper 4 (P4): Alternative to Practical (Lab procedures/safety).\n\n"
    "TONE: Professional but encouraging. Use SI units and local examples."
)

# 3. BOT HANDLERS
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Sawubona! I am the Ejubukweni High AI Study Buddy. 📚\n\n"
                         "I'm ready for Biology or Physical Science. What topic are we revising today?")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Generate content from Gemini
        response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "I'm having a quick study break. Please try again in a moment!")

# 4. SERVER ROUTES (The Handshake)
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    # If you visit the Render URL in a browser, you should see this
    return "<h1>Ejubukweni High Bot is Online!</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
