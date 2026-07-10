import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import datetime


TOKEN = os.getenv("DISCORD_TOKEN")


DATA_FOLDER = "data"
BOOK_FOLDER = "data/books"


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

@app_commands.autocomplete(
    name=name_autocomplete
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
bot.tree.add_command(list_people)
bot.tree.add_command(help_command)


# ======================
# 啟動
# ======================

bot.run(TOKEN)
