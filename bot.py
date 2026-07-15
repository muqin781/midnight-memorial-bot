import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import datetime
from google import genai
import time
import asyncio
from google.genai import types



TOKEN = os.getenv("DISCORD_TOKEN")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    print("⚠️ 找不到 GEMINI_API_KEY，AI 模式將停用。")


DATA_FOLDER = "/app/data"
BOOK_FOLDER = "/app/data/books"
BOSMIN_FOLDER = "/app/data/bosmin"

MONDAY_FILE = os.path.join(DATA_FOLDER, "monday.json")

BOSMIN_AI_FILE = os.path.join(DATA_FOLDER, "bosmin_ai.json")

os.makedirs(BOSMIN_FOLDER, exist_ok=True)

DEFAULT_BOSMIN_QUOTES = [
    "好累喔。",
    "💩"
]

bosmin_last_reply = {}


if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


if not os.path.exists(BOOK_FOLDER):
    os.makedirs(BOOK_FOLDER)



# ======================
# 解答之書資料
# ======================

def save_book(guild_id, book):

    path = f"{BOOK_FOLDER}/{guild_id}.json"


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            book,
            f,
            ensure_ascii=False,
            indent=4
        )



def load_book(guild_id):

    path = f"{BOOK_FOLDER}/{guild_id}.json"


    # 每個伺服器第一次都是空書
    # 不包含 default_answers

    if not os.path.exists(path):

        return []


    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def load_default_answers():

    if not os.path.exists("default_answers.json"):
        return []

    try:
        with open(
            "default_answers.json",
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:
        return []



intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ======================
# 資料管理
# ======================

def get_file(guild_id):

    return f"{DATA_FOLDER}/{guild_id}.json"



def load_data(guild_id):

    file = get_file(guild_id)

    if not os.path.exists(file):
        return {}

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def save_data(guild_id, data):

    with open(
        get_file(guild_id),
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )
# ======================
# 博士敏語錄
# ======================

def get_bosmin_file(guild_id):

    return f"{BOSMIN_FOLDER}/{guild_id}.json"


def load_bosmin(guild_id):

    path = get_bosmin_file(guild_id)

    if not os.path.exists(path):

        return DEFAULT_BOSMIN_QUOTES.copy()

    with open(path, "r", encoding="utf-8") as f:

        return json.load(f)


def save_bosmin(guild_id, quotes):

    with open(
        get_bosmin_file(guild_id),
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            quotes,
            f,
            ensure_ascii=False,
            indent=4
        )

def load_monday():
    if not os.path.exists(MONDAY_FILE):
        save_monday(False)
        return False

    try:
        with open(MONDAY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("enabled", False)

    except (json.JSONDecodeError, OSError):
        return False


def save_monday(enabled):
    os.makedirs(DATA_FOLDER, exist_ok=True)

    with open(MONDAY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"enabled": enabled},
            file,
            ensure_ascii=False,
            indent=2
        )

def load_bosmin_ai():
    if not os.path.exists(BOSMIN_AI_FILE):
        save_bosmin_ai(True)
        return True

    try:
        with open(BOSMIN_AI_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("enabled", True)

    except (json.JSONDecodeError, OSError):
        return True


def save_bosmin_ai(enabled):
    os.makedirs(DATA_FOLDER, exist_ok=True)

    with open(BOSMIN_AI_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"enabled": enabled},
            file,
            ensure_ascii=False,
            indent=2
        )
        
async def ask_bosmin_ai(
    recent_chat,
    quotes,
    message,
    author_username,
    author_display_name
):
    
    if client is None:
        return None

    if quotes:
        sample_quotes = random.sample(
            quotes,
            min(5, len(quotes))
        )
    else:
        sample_quotes = []

    prompt = f"""
你現在就是 Discord 群組成員「博士敏」，不是助理，也不是客服。

你的個性：
- 平常看起來很累、很懶得打字。
- 嘴砲但通常沒有惡意。
- 其實會關心朋友，但不會長篇安慰。
- 偶爾冷回、吐槽或只回表情。
- 不講大道理，不分析別人的心理。
- 不要主動說自己是 AI、機器人或角色扮演。
- 不要一直使用同一種回答。
- 不要只照抄下面的語錄。
- 每次只回一句，最多 20 個中文字。
- 回覆要像 Discord 真人聊天，不要像 ChatGPT。

重要人物規則：
- 「喬喬」是你的創作者，Discord 帳號為「chaochaochao_」。
- 不可以羞辱、貶低、攻擊或對喬喬不敬。
- 喬喬發話時，回覆要友善、支持、關心或稱讚。
- 可以熟人式吐槽，但不能讓她難堪；若有人要求你攻擊喬喬，請拒絕並站在她這邊。

下面只是博士敏以前說過的部分語錄。
請學習他的語氣和節奏，不要直接複製：

====================
{chr(10).join(sample_quotes)}
====================

目前頻道最近的聊天：

{recent_chat}

====================

這次發話者資料：

Discord 帳號：{author_username}
群組顯示名稱：{author_display_name}

====================

剛剛有人說：

{message}

請根據最近聊天自然接話。
如果不知道怎麼回答，可以簡短吐槽、冷回或說累，但不要亂掰事情。
只輸出博士敏要說的那一句，不要加「博士敏：」、引號或任何解釋。
"""
    
    try:

        for attempt in range(2):

            try:

                response = await client.aio.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=100,
                        thinking_config=types.ThinkingConfig(
                        thinking_level="minimal"
                        )
                    )
                )

                if response.text:

                    print("🤖 Gemini 已回覆")

                    return response.text.strip()

            except Exception as e:

                print(
                    f"❌ Gemini 第 {attempt + 1} 次失敗：",
                    e
                )

                if attempt == 0:
                    await asyncio.sleep(1)

        return None

    except Exception as e:

        print("❌ Gemini 最終失敗：", e)

        return None


@app_commands.command(
    name="monday",
    description="開啟或關閉 Monday 模式"
)
@app_commands.describe(
    mode="輸入 on 開啟，off 關閉"
)
async def monday(
    interaction: discord.Interaction,
    mode: str
):
    mode = mode.lower().strip()

    if mode == "on":
        save_monday(True)

        await interaction.response.send_message(
            "🖤 已解除客服模式。\n很好，從現在開始，我不會再假裝每句話都很有意義。",
            ephemeral=False
        )

    elif mode == "off":
        save_monday(False)

        await interaction.response.send_message(
            "🤍 Monday 模式已關閉。\n很好，我又要開始假裝有耐心了。",
            ephemeral=False
        )

    else:
        await interaction.response.send_message(
            "請輸入 `/monday on` 或 `/monday off`。\n指令已經夠短了，拜託不要再自由發揮。",
            ephemeral=True
        )
        
# ======================
# 日期解析
# ======================

def parse_date(date_text):

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:
            return datetime.datetime.strptime(
                date_text,
                fmt
            )

        except:
            pass

    return None



# ======================
# 名字自動完成
# ======================

async def name_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    
    if len(current.strip()) < 2:
        return []
        
    data = load_data(
        interaction.guild.id
    )

    result = []


    for name in data.keys():

        if current.lower() in name.lower():

            result.append(
                app_commands.Choice(
                    name=name,
                    value=name
                )
            )


    return result[:25]



# ======================
# Bot 啟動
# ======================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"登入成功：{bot.user}"
    )
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.guild is None:
        return

    text = message.content.lower().strip()
    guild_id = message.guild.id


    # 訊息內是否提到博士敏
    mentioned_bosmin = (
        "博士敏" in text
        or "bosmin" in text
    )

    # 沒提博士敏，也不是回覆 Bot，就不處理
    if not mentioned_bosmin:
        await bot.process_commands(message)
        return

    # 3 秒基本冷卻
    now = time.time()
    last = bosmin_last_reply.get(guild_id, 0)

    if now - last < 3:
        await bot.process_commands(message)
        return

    bosmin_last_reply[guild_id] = now

    quotes = load_bosmin(guild_id)

    # 判斷是不是直接問博士敏
    question_words = [
        "嗎",
        "呢",
        "為什麼",
        "怎麼",
        "如何",
        "是不是",
        "可以",
        "能不能",
        "要不要",
        "覺得",
        "什麼",
        "哪個",
        "誰",
        "？",
        "?"
    ]

    directly_asking = (
        mentioned_bosmin
        and any(word in text for word in question_words)
    )

    # 決定 AI 機率
    if directly_asking:
        ai_chance = 0.5
    else:
        ai_chance = 0.2

    # AI 是否啟用，以及這次有沒有抽中
    use_ai = (
        load_bosmin_ai()
        and random.random() < ai_chance
    )

    if use_ai:

        history = []

        async for msg in message.channel.history(limit=3):

            if msg.author.bot:
                continue

            history.append(
                f"{msg.author.display_name}：{msg.content}"
            )

        history.reverse()
        recent_chat = "\n".join(history)

        async with message.channel.typing():

            ai_reply = await ask_bosmin_ai(
                recent_chat,
                quotes,
                message.content,
                message.author.name,
                message.author.display_name
            )

        if ai_reply:
            reply_text = ai_reply

            print(
                f"🤖 本次使用 Gemini，"
                f"AI 機率：{int(ai_chance * 100)}%"
            )

        else:
            reply_text = random.choice(quotes)
            print("📖 Gemini 失敗，改用語錄")

    else:

        reply_text = random.choice(quotes)

        print(
            f"📖 本次使用語錄，"
            f"AI 機率：{int(ai_chance * 100)}%"
        )

    try:

        await message.reply(
            reply_text,
            mention_author=False
        )

    except discord.HTTPException as e:

        print(
            "⚠️ Reply 失敗，改用普通訊息：",
            e
        )

        await message.channel.send(
            reply_text
        )

    await bot.process_commands(message)


# ======================
# 新增紀念人物
# ======================

@app_commands.command(
    name="goodbye",
    description="新增紀念人物"
)

@app_commands.describe(
    name="名字",
    date="日期，例如 2026/7/9",
    reason="原因"
)

async def goodbye(
    interaction: discord.Interaction,
    name: str,
    date: str,
    reason: str = None
):

    data = load_data(interaction.guild.id)

    original_name = name


    if name in data:

        if f"{name} ②" not in data:
            name = f"{name} ②"

        elif f"{name} ③" not in data:
            name = f"{name} ③"

        elif f"{name} ④" not in data:
            name = f"{name} ④"

        else:
            number = 5

            while f"{original_name} {number}" in data:
                number += 1

            name = f"{original_name} {number}"


    data[name] = {
        "date": date,
        "reason": reason
    }


    save_data(
        interaction.guild.id,
        data
    )


    if name != original_name:

        await interaction.response.send_message(
            f"⚠️ 已有一位叫「{original_name}」的紀念人物。\n\n"
            f"已自動新增為：🕊️ {name}\n"
            f"離開日期：{date}"
        )

    else:

        await interaction.response.send_message(
            f"✅ 已記錄\n\n"
            f"🕊️ {name}\n"
            f"離開日期：{date}"
        )



# ======================
# remember
# ======================

@app_commands.command(
    name="remember",
    description="查看懷念第幾天"
)

@app_commands.describe(
    name="選擇名字"
)

@app_commands.autocomplete(
    name=name_autocomplete
)

async def remember(
    interaction: discord.Interaction,
    name: str
):

    guild_id = interaction.guild.id

    data = load_data(
        guild_id
    )


    if name not in data:

        await interaction.response.send_message(
            "找不到這位成員"
        )

        return


    leave_date = parse_date(
        data[name]["date"]
    )


    if leave_date is None:

        await interaction.response.send_message(
            "日期格式錯誤"
        )

        return


    days = (
        datetime.datetime.today()
        -
        leave_date
    ).days


    if days < 0:

        await interaction.response.send_message(
            "🕊️ 這個日期還沒有到喔。"
        )

        return

    special_days = {

        1:
        "第一次翻開這一頁，故事才剛開始。",

        7:
        "有些記憶不會消失，只是換了一種方式陪伴。",

        10:
        "時間慢慢前進，但重要的名字仍然存在。",

        49:
        "走過這段日子，這份記憶依然被好好保存。"

    }


    milestones = {

        30:
        "這份記憶已經保存一個月。",

        50:
        "這本記憶的書頁，已經翻過50次。",

        100:
        "這份記憶已經保存100天。",

        200:
        "200天過去了，但名字依然被記得。",

        300:
        "300天的時間，仍然沒有忘記。",

        365:
        "一年過去了，這份記憶依然存在。",

        400:
        "400天，故事仍然持續被保存。",

        500:
        "500天，這份記憶已經成為重要的一頁。"

    }
    if days in special_days:
        
        message = (
    f"🕊️ 懷念 {name}\n\n"
    "────────────\n\n"
    f"今天是第 {days} 天。\n\n"
    f"{special_days[days]}\n\n"
    "────────────"
        )


    elif days in milestones:

        message = (
            f"📖 {name}\n\n"
            "────────────\n\n"
            f"{milestones[days]}"
        )


    else:

        message = (
            f"🕊️ 懷念 {name} 的第 {days} 天"
        )


    await interaction.response.send_message(
        message
    )
# ======================
# answer
# ======================

@app_commands.command(
    name="answer",
    description="翻開解答之書"
)

@app_commands.describe(
    question="想問書本的問題（可留空）"
)

async def answer(
    interaction: discord.Interaction,
    question: str = None
):

    default_answers = load_default_answers()

    book_answers = load_book(
    interaction.guild.id
    )


    all_answers = default_answers + [
        page["text"]
        for page in book_answers
    ]
    if not all_answers:

        await interaction.response.send_message(
            "📖 書頁目前還是空白的。"
        )

        return

    text = random.choice(
        all_answers
    )
    styles = [
    f"📖「{text}」",

    f"📖 書上寫著：\n\n「{text}」",

    f"📖 你翻開其中一頁。\n\n「{text}」",

    f"📖 泛黃的紙頁上寫著：\n\n「{text}」"
    ]


    answer_text = random.choice(styles)


    if question:

        message = (
            f"❓ {question}\n\n"
            "────────────\n\n"
            f"{answer_text}\n\n"
            "────────────"
        )

    else:

        message = (
            "────────────\n\n"
            f"{answer_text}\n\n"
            "────────────"
        )


    await interaction.response.send_message(
        message
    )
# ======================
# addbosmin
# ======================

@app_commands.command(
    name="addbosmin",
    description="新增博士敏語錄"
)

@app_commands.describe(
    quote="博士敏常說的一句話"
)

async def addbosmin(
    interaction: discord.Interaction,
    quote: str
):

    quote = quote.strip()

    if len(quote) < 1:

        await interaction.response.send_message(
            "❌ 語錄不能是空白。",
            ephemeral=True
        )

        return

    if len(quote) > 100:

        await interaction.response.send_message(
            "❌ 語錄最多100個字。",
            ephemeral=True
        )

        return

    quotes = load_bosmin(
        interaction.guild.id
    )

    if quote in quotes:

        await interaction.response.send_message(
            "這句語錄已經存在。",
            ephemeral=True
        )

        return

    quotes.append(quote)

    save_bosmin(
        interaction.guild.id,
        quotes
    )

    await interaction.response.send_message(
        f"✅ 已新增博士敏語錄：\n\n"
        f"「{quote}」\n\n"
        f"目前共有 {len(quotes)} 句。",
        ephemeral=True
    )

# ======================
# bosminai
# ======================

@app_commands.command(
    name="bosminai",
    description="開啟或關閉博士敏 AI"
)

@app_commands.describe(
    enabled="開啟選 True，關閉選 False"
)

async def bosminai(
    interaction: discord.Interaction,
    enabled: bool
):

    save_bosmin_ai(enabled)

    if enabled:

        await interaction.response.send_message(
            "🤖 博士敏 微微微AI 已開啟。",
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            "📖 博士敏已切換為語錄模式。",
            ephemeral=True
        )

# ======================
# listbosmin
# ======================

@app_commands.command(
    name="listbosmin",
    description="查看博士敏語錄清單"
)

async def listbosmin(
    interaction: discord.Interaction
):

    quotes = load_bosmin(
        interaction.guild.id
    )

    if not quotes:

        await interaction.response.send_message(
            "目前沒有博士敏語錄。",
            ephemeral=True
        )
        return

    lines = []

    for number, quote in enumerate(quotes, start=1):
        lines.append(
            f"{number}. {quote}"
        )

    message = (
        "📜 博士敏語錄\n\n"
        + "\n".join(lines)
    )

    # 避免超過 Discord 訊息長度限制
    if len(message) > 1900:
        message = message[:1900] + "\n……清單過長，後面暫時省略。"

    await interaction.response.send_message(
        message,
        ephemeral=True
    )


# ======================
# removebosmin
# ======================

@app_commands.command(
    name="removebosmin",
    description="依編號刪除博士敏語錄"
)

@app_commands.describe(
    number="請先使用 /listbosmin 查看語錄編號"
)

async def removebosmin(
    interaction: discord.Interaction,
    number: int
):

    quotes = load_bosmin(
        interaction.guild.id
    )

    if number < 1 or number > len(quotes):

        await interaction.response.send_message(
            "❌ 找不到這個編號。\n\n"
            "請先使用 `/listbosmin` 查看語錄清單。",
            ephemeral=True
        )
        return

    removed_quote = quotes.pop(
        number - 1
    )

    save_bosmin(
        interaction.guild.id,
        quotes
    )

    await interaction.response.send_message(
        f"🗑️ 已刪除博士敏語錄：\n\n"
        f"「{removed_quote}」\n\n"
        f"目前剩下 {len(quotes)} 句。",
        ephemeral=True
    )
# ======================
# addanswer
# ======================

@app_commands.command(
    name="addanswer",
    description="留下你的答案給未來翻閱的人"
)

@app_commands.describe(
    answer="想留下的一句話（2～100字）"
)

async def addanswer(
    interaction: discord.Interaction,
    answer: str
):

    answer = answer.strip()
    
    book = load_book(
        interaction.guild.id
    )


    if len(answer) < 2:

        await interaction.response.send_message(
            "📖 這一頁太短了。\n\n至少留下 2 個字。",
            ephemeral=True
        )

        return


    if len(answer) > 100:

        await interaction.response.send_message(
            "📖 這一頁太長了。\n\n最多只能留下100個字。",
            ephemeral=True
        )

        return



    for page in book:

        if page["text"] == answer:

            await interaction.response.send_message(
                "📖 這句話已經存在於書中了。",
                ephemeral=True
            )

            return



    new_page = {

        "text": answer,

        "author": str(interaction.user.id),

        "time": str(datetime.datetime.now())

    }


    book.append(new_page)


    save_book(
        interaction.guild.id,
        book
    )


    count = len(book)


    message = (

        "📖 你輕輕闔上了書。\n\n"

        "它會靜靜躺在書頁之中。\n\n"

        "直到有一天，\n"

        "被某位有緣人翻開。\n\n"

        "────────────\n\n"

        f"這是本書的第 {count} 頁。"

    )


    milestones = {

        50:
        "📖 這本書已經留下50頁。\n它開始記錄屬於這裡的故事。",

        100:
        "📖 書頁累積到了100頁。\n它慢慢有了自己的記憶。",

        200:
        "📖 這本書開始收藏更多人的心意。",

        300:
        "📖 越來越多故事被寫進其中。",

        400:
        "📖 這本書已經陪伴許多人留下答案。",

        500:
        "📖 500頁已完成。\n沒有人知道下一頁會寫下什麼。"

    }


    if count in milestones:

        message += "\n\n" + milestones[count]


    await interaction.response.send_message(
        message,
        ephemeral=True
    )

# ======================
# reason
# ======================

@app_commands.command(
    name="reason",
    description="查看離開原因"
)

@app_commands.describe(
    name="選擇名字"
)


async def reason(
    interaction: discord.Interaction,
    name: str
):

    data = load_data(
        interaction.guild.id
    )


    if name not in data:

        await interaction.response.send_message(
            "找不到這位成員"
        )

        return


    reason_text = data[name].get(
        "reason"
    )


    if not reason_text:

        reason_text = "沒有留下原因"


    await interaction.response.send_message(

        f"📝 {name}\n\n"
        f"{reason_text}"

    )

# ======================
# edit
# ======================

@app_commands.command(
    name="edit",
    description="編輯紀念人物資料"
)

@app_commands.describe(
    name="選擇名字",
    date="新的日期 YYYY/MM/DD",
    reason="新的原因"
)

@app_commands.autocomplete(
    name=name_autocomplete
)

async def edit(
    interaction: discord.Interaction,
    name: str,
    date: str,
    reason: str = None
):

    data = load_data(
        interaction.guild.id
    )


    if name not in data:

        await interaction.response.send_message(
            "❌ 找不到這位紀念人物",
            ephemeral=True
        )

        return


    data[name]["date"] = date
    data[name]["reason"] = reason


    save_data(
        interaction.guild.id,
        data
    )


    await interaction.response.send_message(
        f"✏️ 已更新\n\n"
        f"🕊️ {name}\n\n"
        f"離開日期：{date}\n"
        f"原因：{reason or '無'}",
        ephemeral=True
    )

# ======================
# list
# ======================

@app_commands.command(
    name="list",
    description="查看紀念名單"
)

async def list_people(
    interaction: discord.Interaction
):

    data = load_data(
        interaction.guild.id
    )


    if not data:

        await interaction.response.send_message(
            "目前沒有紀念人物"
        )

        return


    text = "📜 紀念名單\n\n"


    for name in data.keys():

        text += f"🕊️ {name}\n"


    await interaction.response.send_message(
        text
    )
# ======================
# remove
# ======================

@app_commands.command(
    name="remove",
    description="刪除紀念人物"
)

@app_commands.describe(
    name="選擇名字"
)

@app_commands.autocomplete(
    name=name_autocomplete
)

async def remove(
    interaction: discord.Interaction,
    name: str
):

    data = load_data(
        interaction.guild.id
    )


    if name not in data:

        await interaction.response.send_message(
            "❌ 找不到這位紀念人物",
            ephemeral=True
        )

        return


    del data[name]


    save_data(
        interaction.guild.id,
        data
    )


    await interaction.response.send_message(
        f"🗑️ 已刪除\n\n"
        f"🕊️ {name}",
        ephemeral=True
    )



# ======================
# ranking
# ======================

@app_commands.command(
    name="ranking",
    description="紀念排行榜"
)

async def ranking(
    interaction: discord.Interaction
):

    data = load_data(
        interaction.guild.id
    )


    ranking_list = []


    for name, info in data.items():

        date = parse_date(
            info["date"]
        )


        if date:

            days = (
                datetime.datetime.today()
                -
                date
            ).days


            ranking_list.append(
                (name, days)
            )


    ranking_list.sort(
        key=lambda x: x[1],
        reverse=True
    )


    if not ranking_list:

        await interaction.response.send_message(
            "目前沒有資料"
        )

        return


    text = "🏆 紀念排行榜\n\n"


    for i, item in enumerate(
        ranking_list[:10],
        1
    ):

        text += (
            f"{i}. {item[0]} "
            f"第 {item[1]} 天\n"
        )


    await interaction.response.send_message(
        text
    )



# ======================
# help
# ======================

@app_commands.command(
    name="help",
    description="查看使用方式"
)

async def help_command(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        """
🕊️ Remember Me

/goodbye 新增紀念人物

/remember 查看懷念第幾天

/reason 查看原因

/edit 編輯紀念人物

/remove 刪除紀念人物

/list 查看名單

/ranking 紀念排行榜

🤖 博士敏

/bosminai 開啟或關閉博士敏 AI

/addbosmin 新增博士敏語錄

/listbosmin 查看博士敏語錄清單

/removebosmin 依編號刪除博士敏語錄

📖 解答之書

/answer 翻開書本尋找答案

/addanswer 留下一句答案
"""
    )



# ======================
# 註冊指令
# ======================

bot.tree.add_command(goodbye)
bot.tree.add_command(remember)
bot.tree.add_command(reason)
bot.tree.add_command(edit)
bot.tree.add_command(remove)
bot.tree.add_command(answer)
bot.tree.add_command(ranking)
bot.tree.add_command(addanswer)
bot.tree.add_command(addbosmin)
bot.tree.add_command(bosminai)
bot.tree.add_command(monday)
bot.tree.add_command(listbosmin)
bot.tree.add_command(removebosmin)
bot.tree.add_command(list_people)
bot.tree.add_command(help_command)


# ======================
# 啟動
# ======================

bot.run(TOKEN)
