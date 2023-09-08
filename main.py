import telebot
import tensorflow as tf
import numpy as np
import sqlite3
import datetime
import os
bot_token = 'TOKEN'
bot = telebot.TeleBot(bot_token)
model = tf.keras.models.load_model('hotdog.h5')

with sqlite3.connect('user_data.db') as conn:
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TEXT)')
    conn.commit()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    joined_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with sqlite3.connect('user_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at) VALUES (?, ?, ?, ?, ?)', (user_id, username, first_name, last_name, joined_at))
        conn.commit()

    bot.send_message(message.chat.id, "Hi, thanks for using the bot. *lights cigarette* 'Special occasion!'")
    bot.send_message(message.chat.id, "You can send me pictures and I will predict what is drawn on them.")
    bot.send_sticker(message.chat.id, sticker ='CAACAgIAAxkBAAEKP7Rk-x7HXrMxYw6o0idbzE4y4KSjbAACIQADUiJEBlCJFVHAH2RRMAQ')

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        user_id = message.from_user.id
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path

        unique_filename = f"user_{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        downloaded_file = bot.download_file(file_path)

        with open(unique_filename, 'wb') as new_file:
            new_file.write(downloaded_file)

        img = tf.keras.preprocessing.image.load_img(unique_filename, target_size=(224, 224))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0

        prediction = model.predict(img_array)

        if prediction[0] >= 0.6:
            result = "Not Hotdog!"
        else:
            result = 'Hotdog!'

        with open(unique_filename, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=result)

        #Sending processed photos to a separate channel for statistics
        with open(unique_filename, 'rb') as photo:
            bot.send_photo('-1001793070847', photo)

        os.remove(unique_filename)

    except Exception as e:
        bot.reply_to(message, "An error has occurred. We want to make our product better than Hooli chat so write to us @horizondevelopment ")
bot.polling(non_stop=True)