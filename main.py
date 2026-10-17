import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("post_config.json")

DEFAULTS = {
    "poster_url": os.getenv("POSTER_URL", "").strip(),
    "channel_title": os.getenv("CHANNEL_TITLE", "MOVIE HUB").strip(),
    "post_title": os.getenv("POST_TITLE", "ALL YOUR ENTERTAINMENT IN ONE PLACE").strip(),
    "caption": os.getenv(
        "POST_CAPTION",
        "🎬 <b>{channel_title}</b>\n\n"
        "✨ <b>{post_title}</b>\n\n"
        "🍿 Browse movies and discover your next watch.\n"
        "📺 Check available video quality formats.\n"
        "👑 Explore premium membership plans.\n\n"
        "👇 Choose an option below."
    ).strip(),
    "buttons": {
        "movies": {"label": "🎬 Browse Movies", "url": os.getenv("MOVIE_URL", "").strip()},
        "quality": {"label": "📺 Video Quality", "url": os.getenv("QUALITY_URL", "").strip()},
        "premium": {"label": "👑 Premium Membership", "url": os.getenv("PREMIUM_URL", "").strip()},
        "start": {"label": "🚀 Get Started →", "url": os.getenv("START_BOT_URL", "").strip()},
    },
}

def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def parse_admin_ids() -> set[int]:
    try:
        return {int(x.strip()) for x in required_env("ADMIN_IDS").split(",") if x.strip()}
    except ValueError as exc:
        raise RuntimeError("ADMIN_IDS must contain numeric Telegram user IDs separated by commas.") from exc

BOT_TOKEN = required_env("BOT_TOKEN")
ADMIN_IDS = parse_admin_ids()
CHANNEL_ID = required_env("CHANNEL_ID")

def valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def load_config():
    config = json.loads(json.dumps(DEFAULTS))
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            config.update({k: v for k, v in saved.items() if k in ("poster_url", "channel_title", "post_title", "caption", "buttons")})
            # Preserve default button keys if new buttons were added in a future version.
            for key, default in DEFAULTS["buttons"].items():
                config["buttons"].setdefault(key, default)
        except Exception:
            logger.exception("Could not read saved config; using environment defaults.")
    return config

config = load_config()

def save_config():
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def is_admin(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id in ADMIN_IDS

async def deny(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("⛔ Admin only.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if is_admin(update):
        await update.effective_message.reply_text(
            "🎬 Movie post bot ready.\n\n"
            "/settings — current settings\n"
            "/preview — preview post\n"
            "/post — publish to channel\n"
            "/setposter URL — change poster image\n"
            "/setchanneltitle text — change brand heading\n"
            "/settitle text — change main title\n"
            "/setcaption text — change caption (use {channel_title} and {post_title})\n"
            "/setbutton movies|quality|premium|start | Button Label | https://link\n"
            "/id — show your Telegram ID\n\n"
            "Example: /setbutton movies | 🎬 Browse Movies | https://t.me/YourBot"
        )
    else:
        await update.effective_message.reply_text("This is a channel-posting bot. Contact the channel admin.")

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message and update.effective_user:
        await update.effective_message.reply_text(f"Your Telegram user ID: {update.effective_user.id}")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    button_lines = []
    for key, item in config["buttons"].items():
        button_lines.append(f"• {key}: {item.get('label','')} — {item.get('url') or '(link not set)'}")
    await update.effective_message.reply_text(
        "⚙️ Current post settings\n"
        f"Brand: {config['channel_title']}\n"
        f"Title: {config['post_title']}\n"
        f"Poster: {config['poster_url'] or '(not set)'}\n"
        "Buttons:\n" + "\n".join(button_lines) +
        "\n\nNote: settings are saved in the bot's local file; a Render restart/redeploy may reset them unless a persistent disk is configured."
    )

async def setposter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    value = " ".join(context.args).strip()
    if not valid_url(value):
        await update.effective_message.reply_text("Usage: /setposter https://direct-public-image-url.jpg")
        return
    config["poster_url"] = value
    save_config()
    await update.effective_message.reply_text("✅ Poster URL updated.")

async def setchanneltitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    value = " ".join(context.args).strip()
    if not value:
        await update.effective_message.reply_text("Usage: /setchanneltitle MOVIE HUB")
        return
    config["channel_title"] = value
    save_config()
    await update.effective_message.reply_text("✅ Brand heading updated.")

async def settitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    value = " ".join(context.args).strip()
    if not value:
        await update.effective_message.reply_text("Usage: /settitle ALL YOUR ENTERTAINMENT IN ONE PLACE")
        return
    config["post_title"] = value
    save_config()
    await update.effective_message.reply_text("✅ Post title updated.")

async def setcaption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    value = update.effective_message.text.partition(" ")[2].strip()
    if not value:
        await update.effective_message.reply_text("Usage: /setcaption Your caption text here")
        return
    config["caption"] = value
    save_config()
    await update.effective_message.reply_text("✅ Caption updated. Telegram-supported HTML can be used; keep it under 1024 characters after formatting.")

async def setbutton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    raw = update.effective_message.text.partition(" ")[2]
    parts = [p.strip() for p in raw.split("|", 2)]
    if len(parts) != 3:
        await update.effective_message.reply_text(
            "Usage: /setbutton movies | 🎬 Browse Movies | https://t.me/YourBot\n"
            "Keys: movies, quality, premium, start. To hide a button, use an empty URL."
        )
        return
    key, label, url = parts
    if key not in config["buttons"]:
        await update.effective_message.reply_text("Unknown key. Use: movies, quality, premium, start.")
        return
    if url and not valid_url(url):
        await update.effective_message.reply_text("Link must start with http:// or https://")
        return
    if not label:
        await update.effective_message.reply_text("Button label cannot be empty.")
        return
    config["buttons"][key] = {"label": label, "url": url}
    save_config()
    await update.effective_message.reply_text(f"✅ Button '{key}' updated.")

def make_keyboard():
    buttons = config["buttons"]
    rows = []
    # Screenshot-style structure: three feature rows, then a full-width Get Started row.
    for key in ("movies", "quality", "premium"):
        item = buttons.get(key, {})
        url = item.get("url", "").strip()
        if url:
            if not valid_url(url):
                raise RuntimeError(f"Invalid URL for button {key}")
            rows.append([InlineKeyboardButton(item["label"], url=url)])
    item = buttons.get("start", {})
    url = item.get("url", "").strip()
    if url:
        if not valid_url(url):
            raise RuntimeError("Invalid URL for Get Started button")
        rows.append([InlineKeyboardButton(item["label"], url=url)])
    return InlineKeyboardMarkup(rows) if rows else None

def make_caption():
    return config["caption"].replace("{channel_title}", config["channel_title"]).replace("{post_title}", config["post_title"])

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    if not config["poster_url"] or not valid_url(config["poster_url"]):
        await update.effective_message.reply_text("Poster not set. Use /setposter https://direct-image-url.jpg")
        return
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=config["poster_url"],
            caption=make_caption(),
            parse_mode="HTML",
            reply_markup=make_keyboard(),
        )
    except Exception as exc:
        logger.exception("Preview failed")
        await update.effective_message.reply_text(f"Preview failed. Check poster URL/caption. Error: {exc}")

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    if not is_admin(update):
        return await deny(update)
    if not config["poster_url"] or not valid_url(config["poster_url"]):
        await update.effective_message.reply_text("Poster not set. Use /setposter https://direct-image-url.jpg")
        return
    try:
        sent = await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=config["poster_url"],
            caption=make_caption(),
            parse_mode="HTML",
            reply_markup=make_keyboard(),
        )
        await update.effective_message.reply_text(f"✅ Post published in {CHANNEL_ID}. Message ID: {sent.message_id}")
    except Exception as exc:
        logger.exception("Channel post failed")
        await update.effective_message.reply_text(
            "❌ Posting failed. Check bot admin permission, CHANNEL_ID, poster URL and button links.\n"
            f"Error: {exc}"
        )
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Movie Posting Bot is running!", 200

@web_app.route("/health")
def health():
    return {"status": "ok"}, 200

def run_web():
    port = int(os.environ.get("PORT", "10000"))
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("setposter", setposter))
    app.add_handler(CommandHandler("setchanneltitle", setchanneltitle))
    app.add_handler(CommandHandler("settitle", settitle))
    app.add_handler(CommandHandler("setcaption", setcaption))
    app.add_handler(CommandHandler("setbutton", setbutton))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("post", post))
    logger.info("Movie posting bot is starting.")
Thread(target=run_web, daemon=True).start()
app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
