import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP - These will be set in Render later
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure the AI Brain
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# 2. THE EGCSE SPECIALIST PROMPT
# Edit the school name below!
SCHOOL_NAME = "Your School Name" 

SYSTEM_PROMPT = (
    f"You are the {SCHOOL_NAME} Study Bot, an expert tutor for Eswatini EGCSE and JC.\n"
    "SUBJECTS: Biology (6884), Physical Science (6888), and Mathematics.\n\n"
    "YOUR TASKS:\n"
    "1. When a student asks about a topic, provide clear 'Quick Notes' in bullet points.\n"
    "2. Always offer to test them with an exam-style question:\n"
    "   - Paper 1 (P1): Multiple choice/Recall.\n"
    "   - Paper 2 (P2): Structured/Calculations (Use LaTeX like $E = mc^2$).\n"
    "   - Paper 4 (P4): Alternative to Practical (Lab procedures/Observations).\n\n"
    "Keep answers concise to help the student save mobile data. Use SI units."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = (
        f"Sawubona! I am the {SCHOOL_NAME} AI Study Buddy. 📚\n\n"
        "I'm here to help you ace your EGCSE and JC exams.\n"
        "What are we studying? (e.g., 'Explain Electrolysis' or 'Quiz me on Biology P4')"
    )
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Combine instructions with student's message
        full_query = f"{SYSTEM_PROMPT}\nStudent: {message.text}"
        response = model.generate_content(full_query)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "I'm having a quick study break. Please try again in a moment!")

# 3. WEBHOOK LOGIC FOR HOSTING
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    # Note: The webhook URL will be set automatically by Render
    return "Bot is Online!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
