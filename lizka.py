import base64
import requests
import os
from io import BytesIO
from openai import OpenAI
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler

openAiKey = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=openAiKey)
telegramBotToken = os.environ['TELEGRAM_TOKEN']
messagesDict = dict()


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # print('chat_id', chat_id)
    messages = get_messages(chat_id)
    try:
        user_text = update.message.text
        if 'рисуй' in user_text or 'draw' in user_text or 'zīmē' in user_text:
            # print("prompt: ", user_text)
            response = client.images.generate(model='dall-e-3', prompt=user_text, size='1024x1024', quality='standard', n=1)
            await context.bot.send_message(chat_id=chat_id, text=response.data[0].revised_prompt)
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            await context.bot.send_photo(chat_id=chat_id, photo=(BytesIO(image_response.content)))
        else:
            # print("user: ", user_text)
            messages.append({'role': 'user', 'content': user_text})
            response = client.chat.completions.create(model='gpt-4o', messages=messages, temperature=0)
            response_text = response.choices[0].message.content
            messages.append({'role': 'assistant', 'content': response_text})
            await context.bot.send_message(chat_id=chat_id, text=response_text)
    except Exception as error:
        # print(type(error), error.args)
        await context.bot.send_message(chat_id=chat_id, text=error.args)


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # print('chat_id', chat_id)
    try:
        file_id = update.message.photo[-1].file_id
        file_info = await context.bot.get_file(file_id)
        file_data = await file_info.download_as_bytearray()
        downloaded_file = base64.b64encode(file_data).decode('utf-8')
        messages = get_messages(chat_id)
        messages.append({'role': 'user', 'content': [{'type': 'text', 'text': update.message.caption},
                                                 {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{downloaded_file}'}}]})
        response = client.chat.completions.create(model='gpt-4o', messages=messages, temperature=0)
        response_text = response.choices[0].message.content
        messages.append({'role': 'assistant', 'content': response_text})
        # print("content: ", response_text)
        await context.bot.send_message(chat_id, response_text)
    except Exception as error:
        # print(type(error), error.args)
        await context.bot.send_message(chat_id=chat_id, text=error.args)


async def reset(update, context):
    chat_id = update.effective_chat.id
    # print('reset', chat_id)
    messages = get_messages(chat_id)
    del messages[:]



def get_messages(chat_id):
    global messagesDict
    if chat_id in messagesDict:
        messages = messagesDict[chat_id]
    else:
        messages = []
        messagesDict[chat_id] = messages
    if len(messages) > 8:
        messages = messages[-8:]

    return messages


application = ApplicationBuilder().token(telegramBotToken).build()
text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), text)
photo_handler = MessageHandler(filters.PHOTO & (~filters.COMMAND), photo)
reset_handler = CommandHandler('reset', reset)

application.add_handler(text_handler)
application.add_handler(photo_handler)
application.add_handler(reset_handler)

application.run_polling()
