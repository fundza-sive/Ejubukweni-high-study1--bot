import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import requests
import time

# 1. Get secrets from Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_KEY)

# Proper System Instructions setup for Gemini API
SYSTEM_INSTRUCTION = (
    "You are the Ejubukweni High School AI Tutor. "
    "Provide expert EGCSE Biology, Physical Science, and Mathematics notes, as well as JC Form 3 Additional Mathematics. "
    "Use BOLD for headers and • for lists. Be concise to ensure speed. Always be encouraging to the student in Eswatini."
)

# Initialize model WITH system instructions built-in
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)
print("Using Gemini model: gemini-2.5-flash")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Force set webhook on startup
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
    except Exception as e:
        print("Could not set webhook:", str(e))

set_webhook()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "*Sawubona!* I am awake and ready for revision. Ask me any Biology, Physical Science, or Math question!"
    bot.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        print(f"Got message: '{message.text}' from user {message.from_user.id}")
        bot.send_chat_action(message.chat.id, 'typing')
        
        reply_text = None
        
        # Retry up to 2 times for transient issues ONLY. No long sleeps!
        for attempt in range(2):
            try:
                # Just send the student's text, system instructions are already loaded!
                response = model.generate_content(message.text)
                
                # Check if Gemini blocked the response due to safety settings
                if not response.parts:
                    reply_text = "⚠️ Gemini blocked this request due to safety filters. Try rephrasing your question."
                    break

                reply_text = response.text
                break  # Success! Break the loop.
                
            except Exception as retry_err:
                err_str = str(retry_err).lower()
                print(f"Gemini attempt {attempt+1} failed: {err_str}")
                
                # Detect quota / rate limit exhaustion
                if any(word in err_str for word in ["quota", "exceeded", "limit", "429", "resourceexhausted"]):
                    reply_text = (
                        "⚠️ Sorry! I've used up all my free Google AI tokens for today.\n\n"
                        "Please try again tomorrow morning! I'm still learning too!"
                    )
                    break
                
                if attempt == 0:
                    time.sleep(2)  # Wait ONLY 2 seconds so Telegram doesn't timeout!
                else:
                    raise retry_err # Pass to the main error handler

        # Send the successful (or quota) reply
        if reply_text:
            # We use try/except here because sometimes Gemini outputs weird Markdown that Telegram hates
            try:
                bot.reply_to(message, reply_text, parse_mode='Markdown')
            except telebot.apihelper.ApiTelegramException:
                # If Markdown fails, send as plain text
                bot.reply_to(message, reply_text)

    except Exception as e:
        # THE FIX: Exposing the raw error to your Telegram chat without Markdown formatting!
        raw_error = str(e)
        print(f"CRASH ERROR: {raw_error}")
        
        error_msg = (
            "⚠️ SYSTEM ERROR! My brain crashed.\n\n"
            "Screenshot this and send it to Gemini:\n"
            "--------------------------\n"
            f"{raw_error}\n"
            "--------------------------"
        )
        # Notice NO parse_mode here. This guarantees the error delivers to your phone.
        bot.reply_to(message, error_msg)

# Webhook route
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        if update:
            bot.process_new_updates([update])
        return "ok", 200
    except Exception as e:
        print("Webhook error:", str(e))
        return "error", 500

@app.route("/")
def index():
    return "<h1>Ejubukweni Bot is running 🚀</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

