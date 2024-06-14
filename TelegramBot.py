import logging
import os
import numpy as np
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler, Application
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Placeholder for the token
TOKEN_ID = "YOUR_NEW_TOKEN_ID_HERE"

# Update directory paths to relative paths
voice_dir = './voice/'
texts_dir = './texts/'
books_dir = './books/'

# Placeholder for the text file, update this to your actual text file
file_name = os.path.join(books_dir, 'your_text_file.txt')  # update txt file

try:
    with open(file_name, 'r', encoding='utf-8') as file:
        sentences = file.readlines()

    sentences = np.array(sentences)
except FileNotFoundError:
    logging.error(f"File '{file_name}' not found.")
    sentences = []

used_ids = []
users = {}

async def start(update, context):
    user_id = update.message.chat_id
    users[user_id] = {"gender": None, "voice_messages": [], "text_messages": []}  # dictionary
    keyboard = [[InlineKeyboardButton("Male", callback_data="male"),
                 InlineKeyboardButton("Female", callback_data="female"),
                 InlineKeyboardButton("Prefer not to say", callback_data="unk")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select your gender', reply_markup=reply_markup)

async def skip_text(update, context):
    text2voice = np.random.choice(sentences)
    chat_id = update.message.chat_id
    users[chat_id]["text_messages"] = text2voice
    await context.bot.send_message(chat_id=chat_id,
                                   text="Please read aloud the text below (use /skip if the text is problematic or too difficult):\n\n" + text2voice)  # send new text to user

async def button(update, context):
    query = update.callback_query
    user_id = query.message.chat_id
    users[user_id]["gender"] = query.data
    text2voice = np.random.choice(sentences)
    users[user_id]["text_messages"] = text2voice
    await query.edit_message_text(
        text="Attention! Send only one voice message per text. If you think there is a problem with the voice message you sent, there is no need to send an additional one. Move on to the next text.")
    await context.bot.send_message(chat_id=user_id,
                                   text="Please read aloud the text below (use /skip if the text is problematic or too difficult):\n\n" + text2voice)

async def handle_voice_message(update, context):
    chat_id = update.message.chat_id

    text = users[chat_id]["text_messages"]
    while True:
        flag = 0
        new_text = np.random.choice(sentences)
        for i in range(len(used_ids)):
            if new_text == used_ids[i]:
                flag = 1
        if flag == 0:
            break

    used_ids.append(new_text)

    await context.bot.send_message(chat_id=chat_id,
                                   text="Please read aloud the text below (use /skip if the text is problematic or too difficult):\n\n" + new_text)
    voice_file = await update.message.voice.get_file()
    file_name = f"user_{chat_id}_voice_{len(users[chat_id]['voice_messages']) + 1}.mp3"

    if users[chat_id]["gender"] == "female":
        text = "01||" + text
    elif users[chat_id]["gender"] == "male":
        text = "10||" + text
    else:
        text = "00||" + text

    if not os.path.exists(texts_dir):
        os.makedirs(texts_dir)

    txt = open(os.path.join(texts_dir, file_name.replace(".mp3", ".txt")), "w+")
    txt.write(text)
    txt.close()
    file_path = os.path.join(voice_dir, file_name)

    users[chat_id]["text_messages"] = new_text
    await voice_file.download_to_drive(file_path)
    users[chat_id]["voice_messages"].append(file_path)

def main():
    application = Application.builder().token(TOKEN_ID).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(CommandHandler("skip", skip_text))
    application.run_polling()
    application.idle()

if __name__ == '__main__':
    main()
