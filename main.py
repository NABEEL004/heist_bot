import logging
import os
import time
import cv2
import io

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, \
    CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler

from qreader import QReader

API = '' # add API key here

# Define states
ENTER_PASSWORD, VERIFY_PASSWORD = range(2)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# defining the function to run when starting the bot (upon receipt of /start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Hello {update.effective_user.first_name} \U0001F44B\U0001F3FC')
    time.sleep(2)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Welcome to the heist! Look for QR codes around the masjid, snap a picture of "
                                        "them and send them to me, and I can help you "
                                        "process them \U0001F50E")
    time.sleep(1)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="If you see anyone familiar walking around do also engage them and ask them any "
                                        "questions")
    time.sleep(1)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Let's crack this case together insyaAllah!!")


async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Here\'s a recap of what\'s going on :')
    time.sleep(2)
    await update.message.reply_text(f'A heist is planned to occur during the AFY Raya celebrations at Masjid Al-Falah, '
                                    f'utilizing the festive event as a cover.')
    time.sleep(4)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Investigation Goals: \n\n'
                                    '<b>What is Being Stolen:</b> Identify the item of immense value targeted in '
                                        'the heist.\n'
                                    '<b>How:</b> Determine the method the thief plans to use to execute the heist.\n'
                                    '<b>When:</b> Pinpoint the timing of the heist.\n'
                                    '<b>Why:</b> Understand the motives behind the theft.\n'
                                    '<b>Who:</b> Identify the mastermind behind the heist.',
                                   parse_mode=telegram.constants.ParseMode('HTML'))

    time.sleep(2)
    await update.message.reply_text('Tips: \n'
                                    '- Be highly observant and question everything.\n'
                                    '- Look for clues (QR Codes and AFY committee members) around the masjid to aid '
                                    'in solving these questions.\n'
                                    '- Maintain secrecy and work fast!\n'
                                    '- Report to the authorities as soon as a clear picture of the heist emerges.')


# defining the function to run when a photo is sent to the bot
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Processing image... \U0001F9D0')
    """Handles photo messages by trying to decode any QR codes."""
    chat_id = update.effective_user.id  # or use update.effective_user.id for user-specific folders
    folder_path = f'./photos/{chat_id}'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
    # print(type(photo_file))

    file_path = os.path.join(folder_path, 'qr_image.jpg')

    await photo_file.download_to_drive(custom_path=file_path)
    qr_result = await decode_qr_code(file_path)
    # qr_result = await decode_qr_code(update.message.photo[-1].file_id)
    if qr_result == 'fhiu':
        await start_qr_action(update=update, context=context)
    elif qr_result == 'a9d3':
        await send_pdf(update=update, context=context, pdf="floor_plan")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Looks like the suspect used the floor plan to plan out some sort of route. "
                                            "What could these markings mean... \U0001F914")
    elif qr_result == '532r':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Seems that these three receipts were thrown here in the trash. "
                                            "Perhaps one of them belongs to the suspect?")
        await send_image(update=update, context=context, image="Decathlon Receipt")
        await send_image(update=update, context=context, image="Outdoor Liife Receipt")
        await send_image(update=update, context=context, image="SKP Receipt")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Seems that these three receipts were thrown here in the trash. "
                                            "Perhaps one of them belongs to the suspect?")
    elif qr_result == 'g761':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Looks like there was an IG post that received alot of interaction "
                                            "around this area.")
        await send_image(update=update, context=context, image="IG_Post")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Could this have any significance in our case?")
    elif qr_result == '42q3':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Looks like you found an inventory list belonging to the masjid!")
        await send_image(update=update, context=context, image="Masjid Inventory")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Could one of these be the item that is being targeted? \U0001F3AF")
    elif qr_result == 'g2ii':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You found an invite to some sort of cohesion activity for the "
                                            "mosque's media team:")
        await send_image(update=update, context=context, image="cohesion")
    elif qr_result == '992f':
        await handle_cctv(update=update, context=context)
    elif qr_result == 'tt2w':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="There appears to be some sort of locality map with annotations \U0001F5FA")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Looks like there is some sort of route being planned. Perhaps the points "
                                            "being marked out can help us in our investigations!")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="And hmmm, seems rather odd that there's a grid system for such a simple "
                                            "map. Was the suspect using this for some other purpose?")
        await send_pdf(update=update, context=context, pdf="The Heist Map")

    elif qr_result:
        await update.message.reply_text("Wrong QR code detected, please try again.")
    else:
        await update.message.reply_text("No QR code detected. please try another image.")


# defining the function to read and return the content of the QR code
async def decode_qr_code(image_path):
    """Decode the QR code from the given image file."""
    qreader = QReader()
    # image_url = f'https://api.telegram.org/file/bot{API}/photos/{image_path}'
    # print(image_url)
    # image = io.imread(image_url)
    image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
    decoded_text = qreader.detect_and_decode(image=image, return_detections=False)

    if decoded_text:
        return decoded_text[0]
    return None


# defining the function to start the password checking conversation
async def start_qr_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.message.reply_text('Accessing messages...')
    # Let's assume this function is called when QR code requires further action
    context.user_data['start_password_flow'] = True
    await update.message.reply_text("Hmm it seems that I am able to access some suspicious messages that were sent "
                                    "from this area. ")
    await update.message.reply_text("However, it looks like the messages are password-protected and I need a 6-digit "
                                    "password. \U0001F510")
    await update.message.reply_text("Type 'yes' to proceed to type a password attempt or 'no' to try again later.")


# defining the function that checks each text input to the chat, to see if the password checking conversation should be
# started
async def check_password_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('start_password_flow', False):
        if update.message.text.lower() == "yes":
            del context.user_data['start_password_flow']
            await update.message.reply_text("Please enter the 6-digit password:")
            return VERIFY_PASSWORD
        else:
            await update.message.reply_text("Ok will not proceed to check the messages now. "
                                            "You can scan the code and try again later!")
    return ConversationHandler.END  # If no flag set, end any non-existing conversation


# defining the function to verify the password during the password conversation
async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_password = update.message.text
    if len(user_password) < 6:
        await update.message.reply_text("Password is too short! Please try again or /cancel to exit.")
        return VERIFY_PASSWORD
    elif len(user_password) > 6:
        await update.message.reply_text("Password is too long! Please try again or /cancel to exit.")
        return VERIFY_PASSWORD
    if user_password.upper() == "D1C2B2":
        await update.message.reply_text("Password is correct, good job!")
        await update.message.reply_text("Here are the messages...")
        await send_image(update=update, context=context, image="messages")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="It appears to be some texts exchanged between the suspect and a hacker. "
                                            "The CCTVs being down seems like a good thing to happen for a heist...")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Incorrect password, try again or /cancel to exit.")
        return VERIFY_PASSWORD


# # defining the code to send the messages screenshot
# async def send_messages(update:Update, context: ContextTypes.DEFAULT_TYPE):
#     with open('./clues/messages.png', 'rb') as photo:
#         await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)


# defining the function to run when exiting the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ok will not check the messages now. "
                                    "You can scan the code and try again later!")
    return ConversationHandler.END


# template for sending images to the chat based on declared file path
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    # Function to send an image file
    with open(f'./clues/{image}.png', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)


# template for sending images to the chat based on declared file path
async def send_image_jpeg(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    # Function to send an image file
    with open(f'./clues/{image}.jpeg', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)


# template for sending images to the chat based on declared file path
async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE, pdf):
    # Function to send an image file
    with open(f'./clues/{pdf}.pdf', 'rb') as pdf:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf)


# placeholder for sending receipt images
async def send_receipts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Function to send an image file
    # with open('test_clue.png', 'rb') as photo:
    #     await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
    await update.message.reply_text("Pictures of receipts")


# function for prompting user for which day's CCTV images should be checked
async def handle_cctv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Seems like we can access some CCTV images taken with this camera.")
    question = "There are images from several days. Which day do you want to check?"
    options = ["01/05/24", "02/05/24", "03/05/24"]  # Define your options here

    # Create a list of InlineKeyboardButton objects
    keyboard = [[InlineKeyboardButton(option, callback_data=option) for option in options]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    await update.message.reply_text(question, reply_markup=reply_markup)


#
async def send_cctv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    choice = query.data
    await query.answer()

    # Respond based on the choice
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have selected {choice}")

    if choice == "01/05/24":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Here's the image from 1st May! Could this person be the suspect?")
        await send_image_jpeg(update=update, context=context, image="1may")
    elif choice == "02/05/24":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Here's the image from 2nd May! Could this person be the suspect?")
        await send_image_jpeg(update=update, context=context, image="2may")
    elif choice == "03/05/24":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Here's the image from 3rd May! Could this person be the suspect?")
        await send_image_jpeg(update=update, context=context, image="3may")
    else:
        await update.message.reply_text("Wrong input detected, please try again.")

    # Function to send an image file
    # with open('test_clue.png', 'rb') as photo:
    #     await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)

    # await update.message.reply_text("CCTV pictures")



if __name__ == '__main__':
    application = ApplicationBuilder().token(API).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT, check_password_init)],  # No direct entry points like /start
        states={
            # ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
            VERIFY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('recap', intro))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(send_cctv))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))


    application.run_polling()
