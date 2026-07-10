import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


TOKEN = os.getenv("DISCORD_TOKEN")

DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ======================
# 資料處理
# ======================

def get_file(guild_id):
    return f"{DATA_FOLDER}/{guild_id}.json"


def load_data(guild_id):

    file = get_file(guild_id)

    if not os.path.exists(file):
        return {}

    with open(file, "r", encoding="utf-8") as f:
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


def parse_date(date_text):

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                date_text,
                fmt
            )
        except:
            pass

    return None


# ======================
# 自動完成名字
# ======================

async def name_autocomplete(
    interaction: discord.Interaction,
    current: str
):

    data = load_data(
        interaction.guild.id
    )

    names = list(data.keys())

    result = []

    for name in names:

        if current.lower() in name.lower():

            result.append(
                app_commands.Choice(
                    name=name,
                    value=name
                )
            )

    return result[:25]


# ======================
# 啟動
# ======================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"登入成功：{bot.user}"
    )


# ======================
# goodbye
# ======================

@app_commands.command(
    name="goodbye",
    description="新增紀念人物"
)
@app_commands.describe(
    name="名字",
    date="日期 YYYY-MM-DD 或 YYYY/M/D",
    reason="原因"
)
async def goodbye(
    interaction: discord.Interaction,
    name: str,
    date: str,
    reason: str = None
):

    guild_id = interaction.guild.id

    data = load_data(guild_id)

    data[name] = {
        "date": date,
        "reason": reason
    }

    save_data(
        guild_id,
        data
    )


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

    data = load_data(
        interaction.guild.id
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
        datetime.today()
        -
        leave_date
    ).days


    await interaction.response.send_message(
        f"🕊️ 懷念 {name} 的第 {days} 天"
    )


# ======================
# reason
# ======================

@app_commands.command(
    name="reason",
    description="查看原因"
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
            "找不到"
        )

        return


    reason = data[name].get(
        "reason"
    )


    if not reason:
        reason = "沒有留下原因"


    await interaction.response.send_message(
        f"📝 {name}\n{reason}"
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

    for name in data:

        text += f"🕊️ {name}\n"


    await interaction.response.send_message(
        text
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

    result = []

    for name, info in data.items():

        date = parse_date(
            info["date"]
        )

        if date:

            days = (
                datetime.today()
                -
                date
            ).days

            result.append(
                (name, days)
            )


    result.sort(
        key=lambda x:x[1],
        reverse=True
    )


    msg = "🏆 排行榜\n\n"

    for i, item in enumerate(
        result[:10],
        1
    ):

        msg += (
            f"{i}. {item[0]} "
            f"{item[1]}天\n"
        )


    await interaction.response.send_message(
        msg
    )


# ======================
# help
# ======================

@app_commands.command(
    name="help",
    description="使用說明"
)
async def help_command(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        """
🕊️ Remember Me

/goodbye 新增紀念人物

/remember 查看第幾天

/reason 查看原因

/list 查看名單

/ranking 排行榜
"""
    )


bot.tree.add_command(goodbye)
bot.tree.add_command(remember)
bot.tree.add_command(reason)
bot.tree.add_command(list_people)
bot.tree.add_command(ranking)
bot.tree.add_command(help_command)


bot.run(TOKEN)
