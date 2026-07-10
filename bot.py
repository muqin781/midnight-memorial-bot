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

    file = get_file(guild_id)

    with open(file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


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
    description="新增離開紀念人物"
)
@app_commands.describe(
    name="名字",
    date="離開日期 YYYY-MM-DD",
    reason="原因（可選）"
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
# 懷念
# ======================

@app_commands.command(
    name="remember",
    description="查看懷念第幾天"
)
@app_commands.describe(
    name="名字"
)
async def remember(
    interaction: discord.Interaction,
    name: str
):

    guild_id = interaction.guild.id

    data = load_data(guild_id)


    if name not in data:

        await interaction.response.send_message(
            "找不到這位成員"
        )

        return


    leave_date = datetime.strptime(
        data[name]["date"],
        "%Y-%m-%d"
    )


    today = datetime.today()


    days = (
        today - leave_date
    ).days


    await interaction.response.send_message(
        f"🕊️ 懷念 {name} 的第 {days} 天"
    )


# ======================
# 查看原因
# ======================

@app_commands.command(
    name="reason",
    description="查看離開原因"
)
@app_commands.describe(
    name="名字"
)
async def reason(
    interaction: discord.Interaction,
    name: str
):

    guild_id = interaction.guild.id

    data = load_data(guild_id)


    if name not in data:

        await interaction.response.send_message(
            "找不到這位成員"
        )

        return


    r = data[name].get(
        "reason"
    )


    if not r:
        r = "沒有留下原因"


    await interaction.response.send_message(
        f"📝 {name}\n原因：{r}"
    )


# ======================
# 名單
# ======================

@app_commands.command(
    name="list",
    description="查看紀念名單"
)
async def list_people(
    interaction: discord.Interaction
):

    guild_id = interaction.guild.id

    data = load_data(guild_id)


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
# 排行榜
# ======================

@app_commands.command(
    name="ranking",
    description="查看紀念排行榜"
)
async def ranking(
    interaction: discord.Interaction
):

    guild_id = interaction.guild.id

    data = load_data(guild_id)


    today = datetime.today()


    ranking = []


    for name, info in data.items():

        date = datetime.strptime(
            info["date"],
            "%Y-%m-%d"
        )

        days = (
            today-date
        ).days


        ranking.append(
            (name, days)
        )


    ranking.sort(
        key=lambda x:x[1],
        reverse=True
    )


    msg = "🏆 紀念排行榜\n\n"


    for i, item in enumerate(
        ranking[:10],
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
    description="查看使用方法"
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
