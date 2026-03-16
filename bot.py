import os
import random
import re
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

import os
TOKEN = os.getenv("TOKEN")

# Google OAuth scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Google Sheet ID
SHEET_ID = "1lmB91KALnq--zl5m_Cunfh4OhUp5Gg5e7CzV_XCkksY"

# Drive folder ID
FOLDER_ID = "1oG_Xm8lCjzieuh3NsrbY5LxCu-3YQkf3"

# Conversation states
GENDER, AGE, DISTRICT, SENTENCE, EXPRESSION, VOICE = range(6)

SENTENCES = [
    "আপনি কি আজ বিকেলে আমার সাথে দেখা করতে পারবেন?",
    "বাহ! এই চমৎকার উপহারটির জন্য আপনাকে অনেক ধন্যবাদ।",
    "আমি বাজারে যাচ্ছি, আপনার জন্য কি কিছু আনতে হবে?",
    "ফাগুন, তুমি কি জানো আজ স্কুল কেন ছুটি দিয়েছে?",
    "উফ! আজকের গরমটা সত্যিই সহ্য করার মতো না।",
    "মা বললেন—সবসময় বড়দের সম্মান দিয়ে কথা বলতে হয়।",
    "তুমি কি চা খাবে, নাকি কফি খেতে পছন্দ করবে?",
    "শোনো! যাওয়ার সময় মনে করে দরজাটা ভালো করে আটকে দিও।",
    "তারা অনেকক্ষণ ধরে অপেক্ষা করছে, কিন্তু ট্রেনটি এখনো আসেনি।",
    "জীবনটা কত বিচিত্র, তাই না? মাঝে মাঝে ভাবলে অবাক লাগে।",
    "আরে! তুমি যে হঠাৎ এখানে আসবে, সেটা ভাবতেই পারিনি।",
    "আমাকে কাল সকাল সাতটার মধ্যে স্টেশনে পৌঁছাতে হবে।",
    "তোমার হাতের লেখা তো বেশ সুন্দর, কে শিখিয়েছে তোমাকে?",
    "আহা! বেচারা লোকটা সারা রাত একটুও ঘুমাতে পারেনি।",
    "বইপড়া মানুষের একটি মহৎ গুণ—এটি মনকে বিকশিত করে।",
    "ছি ছি! এমন কাজ তুমি করবে তা আমি বিশ্বাস করি না।",
    "হুররে! আমাদের ফুটবল দল আজকের ম্যাচে জিতে গিয়েছে।",
    "হায়! এখন আমি এই বিপদে কার সাহায্য পাব?",
    "ওহ! তোমার গান শুনে আমার মনটা শান্ত হয়ে গেল।",
    "ছি! মিথ্যা কথা বলা যে কত বড় পাপ, তা জানো?",
    "প্রিয় , আমি তোমাকে অনেক ভালবাসি।",
    "ইস! এই সুযোগটা হাতছাড়া হয়ে গেল, খুব খারাপ লাগছে।",
    "মাগো! তোমার হাতের রান্না খেয়ে প্রাণটা ভরে গেল।",
    "সাবাস! তুমি পরীক্ষায় প্রথম হয়ে আমাদের মুখ উজ্জ্বল করেছ।",
    "শান্ত হও, কান্নাকাটি করলে কোনো সমস্যার সমাধান হবে না।",
    "ঢাকা থেকে চট্টগ্রাম যেতে কতক্ষণ সময় লাগতে পারে?",
    "আপনি কি কখনো সুন্দরবনের গভীর জঙ্গলে ঘুরতে গিয়েছেন?",
    "এই মোবাইল ফোনের দাম কত, আর এর ওয়ারেন্টি কতদিনের?",
    "তুমি কি জানো আমাদের দেশের জাতীয় কবির নাম কী?",
    "আমাকে একটু বলবে, লাইব্রেরিটা ঠিক কোন দিকে অবস্থিত?",
    "কেন তুমি সেদিন অনুষ্ঠানে না এসে বাড়ি চলে গেলে?",
    "তুমি কি ভাত খাবে, নাকি তোমার জন্য রুটি বানাব?",
    "কার সাহায্য ছাড়াই কি তুমি এই কাজটি সম্পন্ন করেছ?",
    "আচ্ছা, মেঘনা নদী কি পদ্মা নদীর চেয়ে বেশি বড়?",
    "তোমার কি মনে হয় আজ রাতে বৃষ্টি হওয়ার সম্ভাবনা আছে?",
    "বাগানে লাল, নীল ও হলুদ রঙের অনেক ফুল ফুটেছে।",
    "পরিশ্রমী মানুষ সবসময় সফল হয়—এটাই জগতের চিরন্তন সত্য।",
    "শীতের সকালে গরম পিঠা খাওয়ার মজাই আলাদা হয়।",
    "নীল আকাশ আর সাদা মেঘের খেলা দেখতে ভালো লাগে।",
    "সে খুব ভালো ছবি আঁকে, বিশেষ করে প্রাকৃতিক দৃশ্য।",
    "সময়ের কাজ সময়ে করা উচিত, না হলে পস্তাতে হয়।",
    "আমাদের গ্রামে একটি ছোট নদী আছে, যার নাম ইছামতী।",
    "বই মানুষের প্রকৃত বন্ধু—এটি কখনো কাউকে ধোঁকা দেয় না।",
    "সত্য কথা সবসময় তেতো মনে হলেও তা বলা জরুরি।",
    "সূর্য পূর্ব দিকে ওঠে এবং পশ্চিম দিকে অস্ত যায়।",
    "তাড়াতাড়ি চলো, নাহলে আমরা সিনেমা শুরুর আগে পৌঁছাতে পারব না।",
    "বইগুলো টেবিলে রাখো, তারপর হাত-মুখ ধুয়ে খেতে এসো।",
    "মনোযোগ দিয়ে পড়াশোনা করো, কারণ সামনেই তোমার ফাইনাল পরীক্ষা।",
    "বাগান পরিষ্কার করো, গাছে পানি দাও এবং আগাছা তুলে ফেলো।",
    "চলো আজ বিকেলের দিকে গঙ্গার পাড়ে একটু হাঁটাচলা করি।",
    "সাবধানে রাস্তা পার হবে, কারণ আজকাল খুব দুর্ঘটনা ঘটছে।",
    "রিকশাওয়ালার সাথে বেশি দরদাম করা ঠিক হবে না ভাই।",
    "কলমটি পকেটে রাখো, হারানো গেলে খুব সমস্যা হয়ে যাবে।",
    "এই চিঠিটা পড়ে দেখ তো, এর মধ্যে কী লেখা আছে?",
    "জানালাগুলো বন্ধ করো, কারণ বাইরে খুব ধুলোবালি উড়ছে।",
    "রবীন্দ্রনাথ ঠাকুর বলেছিলেন—মানুষের অন্তর জয় করাই শ্রেষ্ঠ জয়।",
    "পৃথিবীটা খুব বড়; এখানে দেখার মতো অনেক কিছু রয়েছে।",
    "যে সহ সহ্য করতে পারে, সে একদিন বড় হবেই।",
    "শিক্ষা জাতির মেরুদণ্ড—একটি দেশ কখনো অশিক্ষিত হয়ে এগোয় না।",
    "আমরা সবাই রাজা আমাদের এই রাজার রাজত্বে, তাই নয় কি?",
    "জীবন মানেই যুদ্ধ; লড়ে যেতে হবে শেষ পর্যন্ত।",
    "মানুষ মরণশীল—এই চরম সত্যটি কেউ অস্বীকার করতে পারে না।",
    "যেখানে ভালোবাসা নেই, সেখানে মানুষের মনও টিকতে পারে না।",
    "বড় যদি হতে চাও, তবে ছোট হও প্রথমে।",
    "একতাই বল—বিপদ এলে সবাই মিলে এক হয়ে লড়তে হবে।",
    "আমি আজ অনেক সকালে ঘুম থেকে উঠে হাঁটতে গিয়েছিলাম।",
    "আমার বোন লিপি খুব ভালো গান গাইতে এবং নাচতে পারে।",
    "ল্যাপটপটি চার্জে দাও, না হলে মাঝপথে বন্ধ হয়ে যাবে।",
    "রাতে শোয়ার আগে অবশ্যই দাঁত ব্রাশ করা উচিত সবার।",
    "ডাল, ভাত আর মাছের ঝোল—এই আমার দুপুরের খাবার।",
    "আয়নায় নিজের মুখটি দেখে মুচকি একটু হাসল মেয়েটি।",
    "জানালার পাশে বসে বৃষ্টির শব্দ শুনতে আমার দারুণ লাগে।",
    "টিফিনে আমি আর আমার বন্ধুরা মিলে লুডু খেলি।",
    "আজ সারাদিন ইন্টারনেটের খুব সমস্যা হচ্ছে, কাজ করা যাচ্ছে না।",
    "চায়ে চিনি একটু কম দিও, বেশি মিষ্টি আমার সহ্য হয় না।",
    "ওহ হো! আজ আমার জরুরি মিটিং এর কথা মনেই ছিল না।",
    "চমৎকার! এই ছবিটা যে এত সুন্দর হবে, তা ভাবিনি।",
    "খোদা! আমাদের সকলকে এই মহামারি থেকে রক্ষা করো।",
    "সাবধান! সামনে একটি গর্ত আছে, দেখে পা ফেলুন।",
    "আহারে! ছোট ছেলেটা বৃষ্টির মধ্যে ভিজে কাঁপছে শীতে।",
    "কী দারুণ একটি গল্প শোনালে আজ, মন ভরে গেল।",
    "ইস! কলমটা ঠিক এই সময়েই কালি শেষ হয়ে গেল।",
    "থামো! আর একটিও কথা বলবে না আমার সামনে তুমি।",
    "চমৎকার দৃশ্য! পাহাড়ের চূড়া থেকে সূর্যোদয় দেখা যাচ্ছে।",
    "চুপ করো! ঘরে ছোট বাচ্চাটা এখন অকাতরে ঘুমাচ্ছে।",
    "বর্ষার দিনে কদম ফুলের ঘ্রাণ চারদিকে মৌ মৌ করে।",
    "আমাদের প্রিয় মাতৃভূমি বাংলাদেশ সবুজে ঘেরা একটি সুন্দর দেশ।",
    "নদীর কূলে নৌকাগুলো সারি সারি করে বাঁধা ছিল কাল।",
    "মাটির তৈরি এই পুতুলগুলো দেখতে সত্যিই খুব শৈল্পিক লাগে।",
    "আকাশটা আজ মেঘলা হয়ে আছে; বোধহয় বৃষ্টি নামবে এখনই।",
    "পাহাড়ের কোল ঘেঁষে বয়ে চলেছে একটি ছোট্ট ঝরনা ধারা।",
    "ছোটবেলার দিনগুলো কত আনন্দময় ছিল, তা বলে বোঝানো যাবে না।",
    "আমরা সবাই মিলে বনভোজনে গিয়ে অনেক আনন্দ করেছিলাম সেদিন।",
    "অন্ধকার রাতে জোনাকি পোকার আলো দেখে খুব ভালো লাগে।",
    "গাছের ছায়ায় বসে রাখাল তার বাঁশি বাজাচ্ছে মনের সুখে।",
    "প্রতিদিন সংবাদপত্র পড়া একটি ভালো অভ্যাস, এতে জ্ঞান বাড়ে।",
    "সে অনেক কষ্ট করে তার পড়াশোনার খরচ নিজে চালায়।",
    "এক গ্লাস ঠান্ডা পানি খেলে শরীরের ক্লান্তি অনেকটা কমে যায়।",
    "বিকেলের সোনালি রোদ যখন ঘাসের ওপর পড়ে, তখন অসাধারণ লাগে।",
    "শেষ পর্যন্ত কাজটি শেষ করে আমি একটি স্বস্তির নিঃশ্বাস ফেললাম।"
]

os.makedirs("voices", exist_ok=True)

# --- Load Google credentials from env ---
token_json_str = os.getenv("TOKEN_JSON")

if token_json_str:
    creds_data = json.loads(token_json_str)
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
else:
    # If not provided, fallback to oauth (first time login locally)
    oauth_json_str = os.getenv("OAUTH_JSON")
    oauth_creds_data = json.loads(oauth_json_str)
    with open("oauth_temp.json", "w") as f:
        json.dump(oauth_creds_data, f)

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file("oauth_temp.json", SCOPES)
    creds = flow.run_local_server(port=0)
    os.remove("oauth_temp.json")

# Initialize Google clients
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1
drive = build("drive", "v3", credentials=creds)



def get_next_number(gender):
    files = sheet.col_values(6)
    numbers = []

    for f in files:
        match = re.match(fr"{gender}_(\d+)", str(f))
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers) + 1 if numbers else 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("Male", callback_data="male"),
            InlineKeyboardButton("Female", callback_data="female")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select Gender:",
        reply_markup=reply_markup
    )

    return GENDER


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    selected_gender = query.data

    context.user_data["gender"] = selected_gender

    await query.edit_message_text(
        f"Gender selected: {selected_gender}"
    )

    await query.message.reply_text("Enter Age:")

    return AGE


async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Enter District:")
    return DISTRICT


async def district(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["district"] = update.message.text

    options = random.sample(SENTENCES, 5)

    context.user_data["sentence_options"] = options

    keyboard = []

    for i, sentence in enumerate(options):
        keyboard.append(
            [InlineKeyboardButton(sentence, callback_data=str(i))]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Choose a sentence:",
        reply_markup=reply_markup
    )

    return SENTENCE


async def sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    index = int(query.data)

    selected_sentence = context.user_data["sentence_options"][index]

    context.user_data["sentence"] = selected_sentence

    await query.edit_message_text(
        f"Selected sentence:\n\n{selected_sentence}"
    )

    # Expression buttons
    keyboard = [
        [
            InlineKeyboardButton("Happy", callback_data="happy"),
            InlineKeyboardButton("Sad", callback_data="sad")
        ],
        [
            InlineKeyboardButton("Romantic", callback_data="romantic"),
            InlineKeyboardButton("Surprise", callback_data="surprise")
        ],
        [
            InlineKeyboardButton("Angry", callback_data="angry"),
            InlineKeyboardButton("Neutral", callback_data="neutral")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Select Expression:",
        reply_markup=reply_markup
    )

    return EXPRESSION


async def expression(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    selected_expression = query.data

    context.user_data["expression"] = selected_expression

    await query.edit_message_text(
        f"Expression selected: {selected_expression}"
    )

    await query.message.reply_text("Send voice message.")

    return VOICE


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    voice_file = await update.message.voice.get_file()

    gender = context.user_data["gender"]
    age = context.user_data["age"]
    district = context.user_data["district"]
    sentence = context.user_data["sentence"]
    expression = context.user_data["expression"]

    number = get_next_number(gender)
    filename = f"{gender}_{number}_{district}.wav"
    local_path = f"voices/{filename}"

    await voice_file.download_to_drive(local_path)

    # Upload to Google Drive
    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }

    media = MediaFileUpload(local_path)

    file = None

    for i in range(3):  # retry 3 times
        try:
            file = drive.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            break
        except Exception as e:
            print("Drive upload failed, retrying...", e)
            time.sleep(2)

    if file is None:
        await update.message.reply_text("Upload failed. Please try again.")
        return ConversationHandler.END

    file_id = file.get("id")
    link = f"https://drive.google.com/file/d/{file_id}"

    # Save to Google Sheets
    sheet.append_row([
        gender,
        age,
        district,
        sentence,
        expression,
        filename,
        link
    ])

    os.remove(local_path)

    keyboard = [
        [InlineKeyboardButton("Record Another Voice", callback_data="restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✅ Voice saved successfully.\n\nDo you want to record another one?",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Male", callback_data="male"),
            InlineKeyboardButton("Female", callback_data="female")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Select Gender:",
        reply_markup=reply_markup
    )

    return GENDER
async def error_handler(update, context):
    print("Exception:", context.error)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [CallbackQueryHandler(gender)],
            AGE: [MessageHandler(filters.TEXT, age)],
            DISTRICT: [MessageHandler(filters.TEXT, district)],
            SENTENCE: [CallbackQueryHandler(sentence)],
            EXPRESSION: [CallbackQueryHandler(expression)],
            VOICE: [MessageHandler(filters.VOICE, voice)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_error_handler(error_handler)
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(restart, pattern="^restart$"))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()