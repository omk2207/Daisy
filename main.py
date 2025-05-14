import os
import logging
import telebot
from telebot import types
import pymongo
from datetime import datetime

# Import modules
from config import TOKEN, OWNER_ID, OWNER_USERNAME, MONGODB_URI
from handlers.admin_commands import register_admin_handlers
from handlers.user_commands import register_user_handlers
from handlers.fun_commands import register_fun_handlers
from handlers.welcome_leave import register_welcome_leave_handlers
from handlers.notes import register_notes_handlers
from utils.permissions import is_admin, is_owner, bot_has_admin_rights
from utils.filters import handle_filters
from utils.spam_flood import check_spam, check_flood
from database.db_handler import initialize_db, get_db

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Initialize database
db = initialize_db(MONGODB_URI)

# Store user data in memory for quick access (will be synced with DB)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    """Send a message when the command /start is issued."""
    user = message.from_user
    chat_id = message.chat.id
    
    welcome_message = (
        f"🌼 Welcome to DaisyBot, {user.first_name}! 🌼\n\n"
        f"I'm here to help manage your chat and make it bloom with fun and order. 🌺\n\n"
        f"🔧 Managed by: {OWNER_USERNAME}\n"
        f"🚀 Version: 1.0\n"
        f"💡 Use /help to see available commands\n\n"
        f"Let's make this chat a beautiful garden together! 🌻"
    )
    bot.send_message(chat_id, welcome_message)
    main_menu(message)

def main_menu(message):
    """Show the main menu."""
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    admin_btn = types.InlineKeyboardButton("👮 Admin Commands", callback_data='admin_commands')
    user_btn = types.InlineKeyboardButton("👥 User Commands", callback_data='user_commands')
    fun_btn = types.InlineKeyboardButton("🎉 Fun Commands", callback_data='fun_commands')
    settings_btn = types.InlineKeyboardButton("⚙️ Settings", callback_data='settings')
    notes_btn = types.InlineKeyboardButton("📝 Notes", callback_data='notes')
    
    markup.add(admin_btn, user_btn, fun_btn, settings_btn, notes_btn)
    
    bot.send_message(chat_id, 'Please choose a category:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle button presses."""
    if call.data == 'main_menu':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='Please choose a category:', reply_markup=get_main_menu_markup())
    elif call.data == 'admin_commands':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='Admin Commands:', reply_markup=get_admin_commands_markup())
    elif call.data == 'user_commands':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='User Commands:', reply_markup=get_user_commands_markup())
    elif call.data == 'fun_commands':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='Fun Commands:', reply_markup=get_fun_commands_markup())
    elif call.data == 'settings':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='Settings:', reply_markup=get_settings_markup())
    elif call.data == 'notes':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text='Notes Commands:', reply_markup=get_notes_markup())
    elif call.data in ['ban', 'unban', 'kick', 'mute', 'unmute', 'warn', 'unwarn', 'promote', 'demote', 'purge', 
                      'filter', 'stop', 'filterlist', 'gban', 'lockall', 'unlockall', 'dwarn', 'dmute']:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text=f"Use /{call.data} command to {call.data.replace('_', ' ')}.")
    elif call.data in ['info', 'id', 'rules', 'help']:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text=f"Use /{call.data} command to get {call.data.replace('_', ' ')}.")
    elif call.data in ['roll_dice', 'flip_coin', 'random_number', 'quote']:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text=f"Use /{call.data} command to {call.data.replace('_', ' ')}.")
    elif call.data in ['set_welcome', 'set_goodbye', 'set_rules', 'set_antispam', 'set_antiflood']:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text=f"Use /{call.data} command to set {call.data.replace('set_', '')}.")
    elif call.data in ['save', 'get', 'notes', 'clear']:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                             text=f"Use /{call.data} command to manage notes.")

def get_main_menu_markup():
    """Get the main menu markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    admin_btn = types.InlineKeyboardButton("👮 Admin Commands", callback_data='admin_commands')
    user_btn = types.InlineKeyboardButton("👥 User Commands", callback_data='user_commands')
    fun_btn = types.InlineKeyboardButton("🎉 Fun Commands", callback_data='fun_commands')
    settings_btn = types.InlineKeyboardButton("⚙️ Settings", callback_data='settings')
    notes_btn = types.InlineKeyboardButton("📝 Notes", callback_data='notes')
    
    markup.add(admin_btn, user_btn, fun_btn, settings_btn, notes_btn)
    return markup

def get_admin_commands_markup():
    """Get the admin commands markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    ban_btn = types.InlineKeyboardButton("🚫 Ban", callback_data='ban')
    unban_btn = types.InlineKeyboardButton("✅ Unban", callback_data='unban')
    kick_btn = types.InlineKeyboardButton("👢 Kick", callback_data='kick')
    mute_btn = types.InlineKeyboardButton("🔇 Mute", callback_data='mute')
    unmute_btn = types.InlineKeyboardButton("🔊 Unmute", callback_data='unmute')
    warn_btn = types.InlineKeyboardButton("⚠️ Warn", callback_data='warn')
    unwarn_btn = types.InlineKeyboardButton("🔄 Unwarn", callback_data='unwarn')
    promote_btn = types.InlineKeyboardButton("🎖️ Promote", callback_data='promote')
    demote_btn = types.InlineKeyboardButton("⬇️ Demote", callback_data='demote')
    purge_btn = types.InlineKeyboardButton("🧹 Purge", callback_data='purge')
    filter_btn = types.InlineKeyboardButton("🔍 Filter", callback_data='filter')
    stop_btn = types.InlineKeyboardButton("🛑 Stop Filter", callback_data='stop')
    filterlist_btn = types.InlineKeyboardButton("📋 Filter List", callback_data='filterlist')
    gban_btn = types.InlineKeyboardButton("🌐🚫 Global Ban", callback_data='gban')
    lockall_btn = types.InlineKeyboardButton("🔒 Lock All", callback_data='lockall')
    unlockall_btn = types.InlineKeyboardButton("🔓 Unlock All", callback_data='unlockall')
    dwarn_btn = types.InlineKeyboardButton("🗑️⚠️ Delete & Warn", callback_data='dwarn')
    dmute_btn = types.InlineKeyboardButton("🗑️🔇 Delete & Mute", callback_data='dmute')
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')
    
    markup.add(ban_btn, unban_btn)
    markup.add(kick_btn, mute_btn)
    markup.add(unmute_btn, warn_btn)
    markup.add(unwarn_btn, promote_btn)
    markup.add(demote_btn, purge_btn)
    markup.add(filter_btn, stop_btn)
    markup.add(filterlist_btn, gban_btn)
    markup.add(lockall_btn, unlockall_btn)
    markup.add(dwarn_btn, dmute_btn)
    markup.add(back_btn)
    
    return markup

def get_user_commands_markup():
    """Get the user commands markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    info_btn = types.InlineKeyboardButton("ℹ️ Info", callback_data='info')
    id_btn = types.InlineKeyboardButton("🆔 IDs", callback_data='id')
    rules_btn = types.InlineKeyboardButton("📜 Rules", callback_data='rules')
    help_btn = types.InlineKeyboardButton("❓ Help", callback_data='help')
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')
    
    markup.add(info_btn, id_btn)
    markup.add(rules_btn, help_btn)
    markup.add(back_btn)
    
    return markup

def get_fun_commands_markup():
    """Get the fun commands markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    dice_btn = types.InlineKeyboardButton("🎲 Roll Dice", callback_data='roll_dice')
    coin_btn = types.InlineKeyboardButton("🪙 Flip Coin", callback_data='flip_coin')
    number_btn = types.InlineKeyboardButton("🔢 Random Number", callback_data='random_number')
    quote_btn = types.InlineKeyboardButton("💬 Quote", callback_data='quote')
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')
    
    markup.add(dice_btn, coin_btn)
    markup.add(number_btn, quote_btn)
    markup.add(back_btn)
    
    return markup

def get_settings_markup():
    """Get the settings markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    welcome_btn = types.InlineKeyboardButton("👋 Welcome Message", callback_data='set_welcome')
    goodbye_btn = types.InlineKeyboardButton("👋 Goodbye Message", callback_data='set_goodbye')
    rules_btn = types.InlineKeyboardButton("📜 Chat Rules", callback_data='set_rules')
    antispam_btn = types.InlineKeyboardButton("🛡️ Anti-Spam", callback_data='set_antispam')
    antiflood_btn = types.InlineKeyboardButton("🌊 Anti-Flood", callback_data='set_antiflood')
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')
    
    markup.add(welcome_btn, goodbye_btn)
    markup.add(rules_btn, antispam_btn)
    markup.add(antiflood_btn)
    markup.add(back_btn)
    
    return markup

def get_notes_markup():
    """Get the notes markup."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    save_btn = types.InlineKeyboardButton("💾 Save Note", callback_data='save')
    get_btn = types.InlineKeyboardButton("📝 Get Note", callback_data='get')
    notes_btn = types.InlineKeyboardButton("📋 List Notes", callback_data='notes')
    clear_btn = types.InlineKeyboardButton("🗑️ Clear Note", callback_data='clear')
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')
    
    markup.add(save_btn, get_btn)
    markup.add(notes_btn, clear_btn)
    markup.add(back_btn)
    
    return markup

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all messages that don't match other handlers."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check for spam and flood
    chat_settings = db.chat_settings.find_one({"chat_id": chat_id})
    if chat_settings:
        # Anti-spam check
        if "antispam" in chat_settings:
            antispam = chat_settings["antispam"]
            check_spam(bot, db, message, antispam["msg_limit"], antispam["time_frame"])
        
        # Anti-flood check
        if "antiflood" in chat_settings:
            antiflood = chat_settings["antiflood"]
            check_flood(bot, db, message, antiflood["msg_limit"], antiflood["time_frame"])
    
    # Handle filters
    handle_filters(bot, db, message)

def main():
    """Start the bot."""
    # Register all handlers
    register_admin_handlers(bot, db)
    register_user_handlers(bot, db)
    register_fun_handlers(bot, db)
    register_welcome_leave_handlers(bot, db)
    register_notes_handlers(bot, db)
    
    # Start the bot
    print(f"🌼 DaisyBot is starting up! Managed by {OWNER_USERNAME}")
    bot.infinity_polling()

if __name__ == '__main__':
    main()

console.log("Created main.py - The entry point for the DaisyBot")
