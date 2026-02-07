import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
# Using 2.5 flash for the best instruction following
model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
server = app 

# 2. THE TELEGRAM-OPTIMIZED BRAIN
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'.\n\n"
    "TELEGRAM FORMATTING RULES:\n"
    "- Use **BOLD TEXT** for all main headings and subheadings.\n"
    "- NEVER use # or ### for headers.\n"
    "- For Chemical formulas: Use simple text like CO2, H2O, or C6H12O6 (No special code).\n"
    "- For Math: Use 'x' for multiply, '/' for divide, and '^' for powers (e.g., 10^2).\n"
    "- Keep paragraphs short and use bullet points (•) for lists.\n\n"
    "SUBJECT RULES:\n"
    "- If the user asks for 'Biology' or uses /biology, stay strictly on EGCSE Biology.\n"
    "- If the user asks for 'Science' or uses /science, stay strictly on EGCSE Physical Science (Physics/Chemistry).\n"
    "- Always offer a quick 'Check your understanding' question at the end."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "**Sawubona!** I am your Ejubukweni High Study Buddy. 📚\n\n"
                         "Use the menu or type a topic to start. I'm now optimized for clear reading!")

@bot.message_handler(commands=['biology'])
def bio_command(message):
    response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent wants BIOLOGY notes. Give an overview of the syllabus or ask for a topic.")
    bot.reply_to(message, response.text, parse_mode='Markdown')

@bot.message_handler(commands=['science'])
def science_command(message):
    response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent wants PHYSICAL SCIENCE notes. Give an overview of the syllabus or ask for a topic.")
    bot.reply_to(message, response.text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}")
        # We use parse_mode='Markdown' so that **Bold** actually works!
        bot.reply_to(message, response.text, parse_mode='Markdown')
    except Exception:
        # Fallback if Markdown fails (sometimes AI sends bad characters)
        bot.reply_to(message, response.text)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Ejubukweni Bot: Formatting Updated!</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
