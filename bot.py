import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import requests

# 1. Get secrets from Render (don't change these lines)
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

SYSTEM_INSTRUCTION = (
    "You are the Ejubukweni High School AI Tutor. Provide EGCSE Biology and Physical Science notes.\n"
    "Use **BOLD** for headers and • for lists. Be concise to ensure speed."
)

# Force set webhook every time the app starts (very important!)
def set_webhook():
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if not hostname:
        print("WARNING: Could not find RENDER_EXTERNAL_HOSTNAME")
        return
    
    webhook_url = f"https://{hostname}/{TOKEN}"
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        )
        print("Webhook set result:", response.text)
        
        # Also show current status
        info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
        print("Webhook info:", info.text)
    except Exception as e:
        print("Could not set webhook:", str(e))

set_webhook()   # Run it now

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "**Sawubona!** I am awake. Ask me any Biology or Physical Science question!"
    bot.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show in logs that we got a message
        print(f"Got message: '{message.text}' from user {message.from_user.id}")
        
        # Show typing animation
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Ask Gemini
        response = model.generate_content(
            f"{SYSTEM_INSTRUCTION}\n\nStudent: {message.text}"
        )
        
        reply_text = response.text if response.text else "Sorry, I couldn't create notes. Try asking differently?"
        
        # Safe way to send reply (this fixes your error)
        if hasattr(message, 'message_id') and message.message_id is not None:
            bot.send_message(
                chat_id=message.chat.id,
                text=reply_text,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id   # Makes it look like a reply
            )
        else:
            # If something is wrong with the message, just send normally
            print("Message had no message_id - sending normal message")
            bot.send_message(
                chat_id=message.chat.id,
                text=reply_text,
                parse_mode='Markdown'
            )

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        try:
            bot.send_message(
                message.chat.id,
                "Something went wrong... please try again in a few seconds. 😅"
            )
        except:
            pass  # Don't crash if we can't even send error message

# Webhook route - where Telegram sends messages
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        print("Webhook received:", json_string[:200])  # First 200 chars for debug
        update = telebot.types.Update.de_json(json_string)
        if update:
            bot.process_new_updates([update])
        return "ok", 200
    except Exception as e:
        print("Webhook error:", str(e))
        return "error", 500

# Simple status page (your cron can ping this)
@app.route("/")
def index():
    return "<h1>Bot is running 🚀</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
