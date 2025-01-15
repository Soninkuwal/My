
import asyncio
import logging
import time
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, MONGODB_URL, LOG_CHANNEL_ID, START_IMAGE, JOIN_LINKS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Pyrogram Client
app = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize MongoDB
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.bot_database

# User data storage
user_state = {}
phone_code_hash = {}

# Start Button
start_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Join Group 1", url="your_group1_link"),
         InlineKeyboardButton("Join Group 2", url="your_group2_link")],
        [InlineKeyboardButton("Join Group 3", url="your_group3_link"),
         InlineKeyboardButton("Join Group 4", url="your_group4_link")],
    ]
)

# Function to add user to database
def add_user_to_db(user_id, username=None, first_name=None, last_name=None, language_code=None):
    users = db.users
    user_data = {"user_id": user_id, "username": username, "first_name": first_name, "last_name": last_name,
                 "language_code": language_code, "joined_at": time.time()}
    users.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

# 1. User Authentication (Login)
@app.on_message(filters.command(["login"]))
async def login_user(client, message):
    user_id = message.from_user.id
    if user_id in user_state and user_state[user_id] == "logging_in":
        await message.reply("You are already logging in, please wait for finishing login process.", quote=True)
        return
    await message.reply("Please provide your phone number with country code (e.g., +1234567890).", quote=True)
    user_state[user_id] = "waiting_for_phone"


@app.on_message(filters.text & ~filters.command(["start", "login", "logout", "join", "settings", "batch", "cancelbatch", "broadcast", "test"]))
async def handle_login_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_state:
       return
    if user_state[user_id] == "waiting_for_phone":
        phone_number = message.text
        try:
             sent_code = await app.send_code(phone_number)
             phone_code_hash[user_id] = sent_code.phone_code_hash
             user_state[user_id] = "waiting_for_code"
             await message.reply("Please provide the code you received.", quote=True)
        except Exception as e:
              logging.error(f"Error sending code: {e}")
              await message.reply("Something went wrong, please try again later or type /login again", quote=True)
              user_state.pop(user_id, None)
    elif user_state[user_id] == "waiting_for_code":
        code = message.text
        try:
           await app.sign_in(phone_number=phone_number, phone_code_hash=phone_code_hash[user_id], phone_code=code)
           await message.reply("You have successfully logged in", quote=True)
           user_state.pop(user_id, None)
           phone_code_hash.pop(user_id, None)
           add_user_to_db(message.from_user.id, message.from_user.username, message.from_user.first_name,
                           message.from_user.last_name, message.from_user.language_code)
        except PhoneCodeInvalid:
           await message.reply("Invalid code, please try again with /login command.", quote=True)
           user_state.pop(user_id, None)
           phone_code_hash.pop(user_id, None)
        except SessionPasswordNeeded:
          await message.reply("You have Two-Factor enabled, this bot not support login with Two-Factor. Please create application to login with it or disable it.", quote=True)
          user_state.pop(user_id, None)
          phone_code_hash.pop(user_id, None)
        except Exception as e:
          logging.error(f"Error signing in: {e}")
          await message.reply("Something went wrong, please try again later or type /login again.", quote=True)
          user_state.pop(user_id, None)
          phone_code_hash.pop(user_id, None)

# 2. Logout
@app.on_message(filters.command(["logout"]))
async def logout_user(client, message):
    user_id = message.from_user.id
    if user_id in user_state and user_state[user_id] == "logging_in":
        await message.reply("You are in process login.", quote=True)
        return
    if not app.is_connected:
       await message.reply("You are already logout", quote=True)
       return
    try:
        await app.disconnect()
        await message.reply("You are now logged out.", quote=True)
    except Exception as e:
        logging.error(f"Logout Error : {e}")
        await message.reply("Error during logout, try again.", quote=True)

# 3. Start Message
@app.on_message(filters.command(["start"]))
async def start(client, message):
    user = message.from_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name, user.language_code)
    await client.send_photo(message.chat.id, START_IMAGE, caption="Welcome! Please Join Our Groups:",
                           reply_markup=start_keyboard)

# 4. Link Management
@app.on_message(filters.command(["join"]))
async def join_links(client, message):
    try:
        join_tasks = [client.join_chat(link) for link in JOIN_LINKS]
        await asyncio.gather(*join_tasks)
        await message.reply("Joined links successfully", quote=True)
    except Exception as e:
        await message.reply(f"Error joining links : {e}", quote=True)


# 5. Settings Menu
@app.on_message(filters.command(["settings"]))
async def settings(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Change Thumbnail", callback_data="change_thumb")],
        [InlineKeyboardButton("Replace Word", callback_data="replace_word")],
        [InlineKeyboardButton("Delete Word", callback_data="delete_word")],
    ])
    await message.reply("Settings Menu:", reply_markup=keyboard, quote=True)


@app.on_callback_query(filters.regex("^change_thumb$"))
async def change_thumb_callback(client, callback_query):
    await callback_query.answer("Please send me your new thumbnail")
    new_thumbnail = await client.listen(callback_query.message.chat.id, timeout=300)
    if new_thumbnail and new_thumbnail.photo:
        try:
            file_path = await client.download_media(new_thumbnail.photo)
            # logic to save the image and use it in start msg with another setting handler
            await callback_query.message.reply("Thumbnail has been updated", quote=True)
        except Exception as e:
            await callback_query.message.reply(f"Error: {e}", quote=True)


@app.on_callback_query(filters.regex("^replace_word$"))
async def replace_word_callback(client, callback_query):
    await callback_query.answer("Please send me the word you want to replace (old->new)")
    replacement_msg = await client.listen(callback_query.message.chat.id, timeout=300)
    if replacement_msg and replacement_msg.text and "->" in replacement_msg.text:
        old_word, new_word = replacement_msg.text.split("->", 1)
        # logic to handle the replacement
        await callback_query.message.reply(f"Replaced '{old_word}' with '{new_word}'.", quote=True)
    else:
        await callback_query.message.reply("Invalid format please use 'old->new' ", quote=True)


@app.on_callback_query(filters.regex("^delete_word$"))
async def delete_word_callback(client, callback_query):
    await callback_query.answer("Please send me the word you want to delete")
    delete_msg = await client.listen(callback_query.message.chat.id, timeout=300)
    if delete_msg and delete_msg.text:
        word_to_delete = delete_msg.text
        # logic to handle the delete
        await callback_query.message.reply(f"'{word_to_delete}' word removed", quote=True)
    else:
        await callback_query.message.reply("Invalid word", quote=True)


# 6. Batch Link Processing
@app.on_message(filters.command(["batch"]))
async def batch_join(client, message):
    await message.reply("Please provide links separated by spaces:", quote=True)
    response = await client.listen(message.chat.id, timeout=300)
    if response and response.text:
        links = response.text.split()
        if len(links) > 1000:
            await message.reply("You can only provide 1000 links in a batch", quote=True)
            return
        success_count = 0
        failed_count = 0
        for link in links:
            try:
                await client.join_chat(link)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logging.error(f"Error joining link {link}: {e}")
                continue
        await message.reply(
            f"Batch finished, {success_count} links joined successfully, {failed_count} failed.", quote=True)
    else:
        await message.reply("No links provided.", quote=True)


@app.on_message(filters.command(["cancelbatch"]))
async def cancel_batch(client, message):
    # logic to cancel current batch (you need to make it a persistent task with background tasks)
    await message.reply("Batch operation was canceled (not implemented)", quote=True)


# 7. Broadcast Message
@app.on_message(filters.command(["broadcast"]))
async def broadcast_message(client, message):
    await message.reply("Please provide the broadcast message.", quote=True)
    broadcast_msg = await client.listen(message.chat.id, timeout=300)
    if broadcast_msg and broadcast_msg.text:
        broadcast_text = broadcast_msg.text
        users = db.users.find()
        total_users = users.count()
        success_count = 0
        failed_count = 0
        for user in users:
            try:
                await client.send_message(user["user_id"], broadcast_text)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logging.error(f"Error sending message to {user['user_id']}: {e}")
        await message.reply(
            f"Message sent to {success_count} users with {failed_count} failed and total users {total_users}.",
            quote=True)
    else:
        await message.reply("Broadcast message was not provided", quote=True)

# 8. User Data Logging
@app.on_message(filters.new_chat_members)
async def new_member(client, message):
    for user in message.new_chat_members:
        add_user_to_db(user.id, user.username, user.first_name, user.last_name, user.language_code)
        try:
           user_info = await client.get_users(user.id)
           user_details = f"New Member: {user_info.first_name}, User ID: {user_info.id}, Username: @{user_info.username}"
           await client.send_message(LOG_CHANNEL_ID, user_details)
        except Exception as e:
           logging.error(f"Error getting user info: {e}")

@app.on_message()
async def get_user_message(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
       add_user_to_db(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name, message.from_user.language_code)
    elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        for user in message.entities:
            if user.type == "mention" :
                try:
                   user_info = await client.get_users(user.user.id)
                   add_user_to_db(user_info.id, user_info.username, user_info.first_name, user_info.last_name, user_info.language_code)
                   user_details = f"New Mention User: {user_info.first_name}, User ID: {user_info.id}, Username: @{user_info.username}"
                   await client.send_message(LOG_CHANNEL_ID, user_details)
                except Exception as e:
                     logging.error(f"Error getting user info: {e}")

# 9. Command Handling & Reaction Emoji
@app.on_message(filters.command(["test"]))
async def test_command(client, message):
    await message.reply("Command received!", quote=True)
    await message.react("👍")

# Run Bot
if __name__ == "__main__":
    print("Starting Bot...")
    app.run()
