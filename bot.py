import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


TOKEN = os.getenv("DISCORD_TOKEN")

DATA_FILE = "members.json"


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


======================
資料讀取 / 儲存
======================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


======================
計算紀念天數
======================
def calculate_days(date_string):

    leave_date = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    today = datetime.today()

    return (today - leave_date).days
  ======================
Bot 啟動
======================
@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"Remember Me 已上線：{bot.user}"
    )


======================
/goodbye 新增紀念人物
======================
@bot.tree.command(
    name="goodbye",
    description="新增一位需要紀念的人"
)
@app_commands.describe(
    name="名字",
    date="離開日期 YYYY-MM-DD",
    reason="離開原因（可不填）"
)
async def goodbye(
    interaction: discord.Interaction,
    name: str,
    date: str,
    reason: str = None
):

    data = load_data()

    data[name] = {
        "date": date,
        "reason": reason
    }

    save_data(data)

    await interaction.response.send_message(
        f"✅ 已記錄 {name}\n"
        f"📅 離開日期：{date}"
    )


======================
/remember 懷念
======================
@bot.tree.command(
    name="remember",
    description="查看懷念某人的第幾天"
)
@app_commands.describe(
    name="紀念人物名稱"
)
async def remember(
    interaction: discord.Interaction,
    name: str
):

    data = load_data()

    if name not in data:
        await interaction.response.send_message(
            "找不到這位紀念人物"
        )
        return

    days = calculate_days(
        data[name]["date"]
    )

    await interaction.response.send_message(
        f"🕊️ 懷念 {name} 的第 {days} 天"
    )
# ======================
# /reason 查看原因
# ======================

@bot.tree.command(
    name="reason",
    description="查看離開原因"
)
@app_commands.describe(
    name="紀念人物名稱"
)
async def reason(
    interaction: discord.Interaction,
    name: str
):

    data = load_data()

    if name not in data:
        await interaction.response.send_message(
            "找不到這位紀念人物"
        )
        return

    person_reason = data[name].get("reason")

    if not person_reason:
        await interaction.response.send_message(
            f"📝 {name} 沒有留下離開原因"
        )
        return

    await interaction.response.send_message(
        f"📝 {name} 的離開原因：\n{person_reason}"
    )


# ======================
# /list 查看名單
# ======================

@bot.tree.command(
    name="list",
    description="查看所有紀念人物"
)
async def list_members(
    interaction: discord.Interaction
):

    data = load_data()

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
# /ranking 排行榜
# ======================

@bot.tree.command(
    name="ranking",
    description="查看懷念排行榜"
)
async def ranking(
    interaction: discord.Interaction
):

    data = load_data()

    if not data:
        await interaction.response.send_message(
            "目前沒有紀念人物"
        )
        return

    ranking_list = []

    for name, info in data.items():

        days = calculate_days(
            info["date"]
        )

        ranking_list.append(
            (name, days)
        )


    ranking_list.sort(
        key=lambda x: x[1],
        reverse=True
    )


    message = "🏆 懷念排行榜\n\n"


    for index, item in enumerate(
        ranking_list[:10],
        start=1
    ):

        message += (
            f"{index}️⃣ {item[0]}\n"
            f"⏳ {item[1]} 天\n\n"
        )


    await interaction.response.send_message(
        message
    )
  # ======================
# /remove 刪除人物
# ======================

@bot.tree.command(
    name="remove",
    description="刪除紀念人物"
)
@app_commands.describe(
    name="紀念人物名稱"
)
async def remove(
    interaction: discord.Interaction,
    name: str
):

    data = load_data()

    if name not in data:
        await interaction.response.send_message(
            "找不到這位紀念人物"
        )
        return

    del data[name]

    save_data(data)

    await interaction.response.send_message(
        f"🗑️ 已刪除 {name}"
    )


# ======================
# /edit 修改資料
# ======================

@bot.tree.command(
    name="edit",
    description="修改紀念人物資料"
)
@app_commands.describe(
    name="原本名字",
    date="新的日期 YYYY-MM-DD（可不填）",
    reason="新的原因（可不填）"
)
async def edit(
    interaction: discord.Interaction,
    name: str,
    date: str = None,
    reason: str = None
):

    data = load_data()

    if name not in data:
        await interaction.response.send_message(
            "找不到這位紀念人物"
        )
        return


    if date:
        data[name]["date"] = date

    if reason:
        data[name]["reason"] = reason


    save_data(data)

    await interaction.response.send_message(
        f"✅ 已更新 {name} 的資料"
    )



# ======================
# /today 今日紀念
# ======================

@bot.tree.command(
    name="today",
    description="查看今日紀念人物"
)
async def today(
    interaction: discord.Interaction
):

    data = load_data()

    if not data:
        await interaction.response.send_message(
            "目前沒有紀念人物"
        )
        return


    message = "🌙 今日紀念\n\n"

    for name, info in data.items():

        days = calculate_days(
            info["date"]
        )

        message += (
            f"🕊️ {name}\n"
            f"第 {days} 天\n\n"
        )


    await interaction.response.send_message(
        message
    )



# ======================
# /help 使用說明
# ======================

@bot.tree.command(
    name="help",
    description="查看使用方式"
)
async def help_command(
    interaction: discord.Interaction
):

    message = """
🕊️ Remember Me 使用方式

/goodbye
新增紀念人物

/remember
查看懷念第幾天

/reason
查看離開原因

/list
查看所有人物

/ranking
查看排行榜

/edit
修改資料

/remove
刪除人物

/today
今日紀念
"""

    await interaction.response.send_message(
        message
    )
  # ======================
# remember 自動補全
# ======================

@remember.autocomplete("name")
async def remember_autocomplete(
    interaction: discord.Interaction,
    current: str
):

    data = load_data()

    choices = []

    for name in data.keys():

        if current.lower() in name.lower():

            choices.append(
                app_commands.Choice(
                    name=name,
                    value=name
                )
            )


    return choices[:25]



# ======================
# 啟動 Remember Me
# ======================

if TOKEN is None:

    print(
        "錯誤：沒有找到 DISCORD_TOKEN"
    )

else:

    bot.run(TOKEN)
