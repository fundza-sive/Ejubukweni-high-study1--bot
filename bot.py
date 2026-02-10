import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. SETUP
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
# Using 1.5-flash for maximum stability and speed
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# 2. THE TUTOR'S PERSONALITY
SYSTEM_INSTRUCTION = (
    "You are the 'Ejubukweni High School AI Tutor'. Your goal is to help EGCSE students in Eswatini.\n\n"
    "FORMATTING RULES:\n"
    "- ALWAYS use **BOLD TEXT** for headings. Do NOT use # or ###.\n"
    "- Use bullet points (•) for lists to make them easy to read on mobile.\n"
    "- For Chemistry: Write formulas simply (e.g., CO2, H2O, O2). Do not use ^ symbols.\n"
    "- Always encourage the student and use clear, simple English.\n\n"
    "SUBJECT FOCUS:\n"
    "- If a student asks for 'Biology' or uses /biology, focus on EGCSE Biology syllabus.\n"
    "- If a student asks for 'Science' or uses /science, focus on Physical Science (Physics/Chemistry)."
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "**Sawubona!** 📚\n\n"
        "I am the Ejubukweni High Study Buddy, optimized and ready to help!\n\n"
        "**Available Commands:**\n"
        "/biology - Get Biology notes\n"
        "/science - Get Physical Science notes\n"
        "/quiz - Test your knowledge\n\n"
        "What are we studying today?"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['biology'])
def bio_notes(message):
    prompt = f"{SYSTEM_INSTRUCTION}\n\nUser wants Biology notes. Give a friendly overview of the EGCSE Biology topics."
    response = model.generate_content(prompt)
    bot.reply_to(message, response.text, parse_mode='Markdown')

@bot.message_handler(commands=['science'])
def science_notes(message):
    prompt = f"{SYSTEM_INSTRUCTION}\n\nUser wants Physical Science notes. Give a friendly overview of the EGCSE Physical Science topics."
    response = model.generate_content(prompt)
    bot.reply_to(message, response.text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        # Generate content with the instruction and student's question
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nStudent asks: {message.text}"
        response = model.generate_content(full_prompt)
        
        # We try to send with Markdown first for the Bold text to work
        bot.reply_to(message, response.text, parse_mode='Markdown')
    except Exception:
        # If Markdown fails (e.g. if the AI sends a weird character), send as plain text
        bot.reply_to(message, response.text)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Ejubukweni Bot is Active & Awake!</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

