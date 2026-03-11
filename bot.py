import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import requests
import logging
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. SETUP & SECRETS
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Validate secrets
if not TOKEN or not GEMINI_KEY:
    logger.error("Missing environment variables!")
    exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = (
    "You are the Ejubukweni High School AI Tutor (Eswatini). "
    "Expertise: ONLY EGCSE Biology and Physical Science. "
    "STRICT RULES: "
    "1. Be extremely BRIEF. Use maximum 3-4 bullet points per answer. "
    "2. FORMATTING: Use <b>bold</b> for headers and • for lists. "
    "3. NEVER use hashtags (###) or asterisks (**). "
    "4. If asked about Maths, politely redirect to Science. "
    "5. Use local Eswatini examples when possible."
)

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 300,
    }
)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# 2. WEBHOOK SETUP
def set_webhook():
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if not hostname:
        logger.warning("No RENDER_EXTERNAL_HOSTNAME found")
        return
    
    webhook_url = f"https://{hostname}/{TOKEN}"
    logger.info(f"Setting webhook to: {webhook_url}")
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            json={"url": webhook_url},
            timeout=10
        )
        logger.info(f"Webhook response: {response.json()}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")

# Call webhook setup
set_webhook()

# 3. MESSAGE HANDLERS
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "<b>Sawubona!</b> I am your Ejubukweni Science Tutor. 🇸🇿\n\n"
        "Ask me about:\n"
        "• Biology\n"
        "• Physical Science (Physics & Chemistry)\n\n"
        "<i>I keep answers brief to save energy! ⚡</i>"
    )
    bot.send_message(
        chat_id=message.chat.id, 
        text=welcome_text, 
        parse_mode='HTML'
    )
    logger.info(f"Welcome sent to {message.from_user.username}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Log incoming message
        logger.info(f"Message from {message.from_user.username}: {message.text[:50]}...")
        
        # Show typing
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Prepare prompt with context
        user_input = message.text[:1000]  # Limit input length
        enhanced_prompt = (
            f"Student question about EGCSE Science: {user_input}\n\n"
            f"Remember: Be brief, use bullet points with •, and bold with <b> tags."
        )
        
        # Get Gemini response
        response = model.generate_content(enhanced_prompt)
        reply_text = response.text
        
        # Clean up any remaining markdown
        reply_text = reply_text.replace('**', '')  # Remove any stray asterisks
        
        # Send response
        try:
            bot.reply_to(message, reply_text, parse_mode='HTML')
            logger.info(f"Response sent successfully")
        except Exception as e:
            # If HTML fails, send plain text
            logger.warning(f"HTML parse failed: {e}")
            clean_text = re.sub(r'<[^>]+>', '', reply_text)
            bot.reply_to(message, clean_text)
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error: {error_str}")
        
        # Friendly error messages
        if "429" in error_str or "quota" in error_str.lower():
            bot.reply_to(message, 
                "📚 <b>Daily limit reached!</b>\n\n"
                "I've helped many students today! Please try again tomorrow morning. "
                "In the meantime, check your textbook chapter on this topic!")
        elif "500" in error_str:
            bot.reply_to(message, "🔄 API busy. Please try again in a moment!")
        else:
            bot.reply_to(message, 
                "❓ I couldn't process that. Please:\n"
                "• Ask a shorter question\n"
                "• Be specific about what you want to know\n"
                "• Try rephrasing")

# 4. FLASK ROUTES
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "error", 500

@app.route("/")
def index():
    return f"<h1>Ejubukweni Science Bot is Online 🚀</h1><p>{datetime.now()}</p>", 200

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/debug")
def debug():
    """Debug endpoint to check configuration"""
    return {
        "status": "online",
        "time": str(datetime.now()),
        "webhook_set": bool(os.environ.get('RENDER_EXTERNAL_HOSTNAME')),
        "bot_token_set": bool(TOKEN),
        "gemini_key_set": bool(GEMINI_KEY)
    }, 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port)
