import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import requests

# 1. SETUP & SECRETS
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_KEY)

# --- THE STRICT SYSTEM INSTRUCTION ---
# This "brain" setup ensures the bot is brief, stays on subject, and avoids messy symbols.
SYSTEM_INSTRUCTION = (
    "You are the Ejubukweni High School AI Tutor (Eswatini). "
    "Expertise: ONLY EGCSE Biology and Physical Science. "
    "STRICT RULES: "
    "1. Be extremely BRIEF. Use maximum 3-4 bullet points per answer to save tokens. "
    "2. FORMATTING: Use <b>bold</b> for headers and • for lists. "
    "3. NEVER use hashtags (###) or asterisks (**). "
    "4. If a student asks about Mathematics or Additional Maths, politely say you are focused on Science and Biology for now. "
    "5. Always use <b>HTML tags</b> for bolding. "
    "Be encouraging and concise."
)

# Using gemini-1.5-flash for speed and reliability on the free tier
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# 2. WEBHOOK SETUP (For Render)
def set_webhook():
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if not hostname: return
    webhook_url = f"https://{hostname}/{TOKEN}"
    # Using a timeout to prevent the script from hanging on startup
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}", timeout=10)
    except Exception as e:
        print(f"Webhook error: {e}")

set_webhook()

# 3. MESSAGE HANDLERS
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "<b>Sawubona!</b> I am your Ejubukweni Science Tutor. Ask me any Biology or Physical Science question! (I am keeping answers brief to save my daily energy! ⚡)"
    bot.send_message(
        chat_id=message.chat.id, 
        text=welcome_text, 
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show 'typing' status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Get response from Gemini
        response = model.generate_content(message.text)
        reply_text = response.text

        # Try to send as HTML (this fixes the bolding/symbols issue)
        try:
            bot.reply_to(message, reply_text, parse_mode='HTML')
        except Exception:
            # Fallback: If Gemini accidentally sends bad HTML, send as plain text
            bot.reply_to(message, reply_text)

    except Exception as e:
        # Handle the common "Daily Limit / Quota" error gracefully
        error_str = str(e)
        if "429" in error_str or "ResourceExhausted" in error_str:
            bot.reply_to(message, "⚠️ <b>Daily limit reached!</b> My brain is tired from helping so many students. Please try again tomorrow morning!")
        else:
            bot.reply_to(message, "⚠️ Something went wrong. Try asking a shorter question!")

# 4. FLASK ROUTES (For Render/Webhooks)
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "<h1>Ejubukweni Science Bot is Online 🚀</h1>", 200

if __name__ == "__main__":
    # Render provides the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)

