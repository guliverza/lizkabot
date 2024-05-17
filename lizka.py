import base64
import requests
import os
from io import BytesIO
from openai import OpenAI
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

openAiKey = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=openAiKey)
telegramBotToken = os.environ["TELEGRAM_TOKEN"]

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ("рисуй" in update.message.text or 'generate' in update.message.text or 'zīmē' in update.message.text):
        response = client.images.generate(model="dall-e-3", prompt=update.message.text, size="1024x1024", quality="standard", n=1)
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response.data[0].revised_prompt)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=(BytesIO(image_response.content)))
    else:
        messages = [{"role": 'user', "content": update.message.text}]
        response = client.chat.completions.create(model='gpt-4o', messages=messages, temperature=0)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response.choices[0].message.content)


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fileID = update.message.photo[-1].file_id
    file_info = await context.bot.get_file(fileID)
    file_data = await file_info.download_as_bytearray()
    downloaded_file = base64.b64encode(file_data).decode('utf-8')
    messages = [{"role": 'user', "content": [{"type": "text", "text": update.message.caption},
                                             {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{downloaded_file}"}}]}]
    response = client.chat.completions.create(model='gpt-4o', messages=messages, temperature=0)
    await context.bot.send_message(update.message.from_user.id, response.choices[0].message.content)

# if __name__ == '__main__':
application = ApplicationBuilder().token(telegramBotToken).build()
text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), text)
photo_handler = MessageHandler(filters.PHOTO & (~filters.COMMAND), photo)

application.add_handler(text_handler)
application.add_handler(photo_handler)

application.run_polling()
