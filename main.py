import discord
from discord.ext import commands
import random
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

def load_data():
    if not os.path.isfile(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

def get_user(ctx):
    return str(ctx.author.id)

def get_display_name(ctx):
    return ctx.author.display_name

@bot.event
async def on_ready():
    print(f"✅ 봇 실행됨 - {bot.user}")

@bot.command()
async def 출석(ctx):
    user = get_user(ctx)
    today = datetime.utcnow() + timedelta(hours=9)
    today_str = today.strftime("%Y-%m-%d")

    if user in data and data[user].get("last_checkin") == today_str:
        await ctx.send(f"{get_display_name(ctx)}님, 오늘은 이미 출석하셨습니다!")
        return

    if user not in data:
        data[user] = {"points": 0, "last_checkin": ""}

    data[user]["points"] += 100
    data[user]["last_checkin"] = today_str
    save_data(data)
    await ctx.send(f"🌞 {get_display_name(ctx)}님 출석 완료! 100포인트 적립되었습니다.")

@bot.command()
async def 포인트(ctx):
    user = get_user(ctx)
    points = data.get(user, {}).get("points", 0)
    await ctx.send(f"{get_display_name(ctx)}님의 현재 포인트: {points}P")

@bot.command()
async def 지급(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있어요.")
        return

    user = str(member.id)
    if user not in data:
        data[user] = {"points": 0, "last_checkin": ""}

    data[user]["points"] += amount
    save_data(data)
    await ctx.send(f"{member.display_name}님에게 {amount}포인트를 지급했습니다!")

@bot.command()
async def 랭킹(ctx):
    if not data:
        await ctx.send("아직 포인트 데이터가 없습니다.")
        return
    ranking = sorted(data.items(), key=lambda x: x[1].get("points", 0), reverse=True)
    message = "🏆 포인트 랭킹 (Top 10)\n"
    for i, (user_id, info) in enumerate(ranking[:10], start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else f"탈주자 ({user_id})"
        message += f"{i}. {name} - {info.get('points', 0)}P\n"
    await ctx.send(message)

@bot.command()
async def 상점(ctx):
    items = {
        "치킨": 30000,
        "500만메소": 30000,
        "피자": 45000,
        "족발": 60000,
        "길드명찰": 10000
    }
    message = "🛒 상점 목록:\n"
    for name, cost in items.items():
        message += f"{name} - {cost}P\n"
    await ctx.send(message)

@bot.command()
async def 구매(ctx, *, item_name):
    user = get_user(ctx)
    items = {
        "치킨": 30000,
        "500만메소": 30000,
        "피자": 45000,
        "족발": 60000,
        "길드명찰": 10000
    }

    if item_name not in items:
        await ctx.send("해당 아이템은 상점에 없습니다.")
        return

    cost = items[item_name]
    if data.get(user, {}).get("points", 0) < cost:
        await ctx.send("포인트가 부족합니다.")
        return

    data[user]["points"] -= cost
    save_data(data)
    await ctx.send(f"{item_name} 구매 완료! 포인트가 차감되었습니다.")

@bot.command()
async def 슬롯(ctx, amount: int):
    user = get_user(ctx)
    if data.get(user, {}).get("points", 0) < amount:
        await ctx.send("포인트가 부족합니다.")
        return

    emojis = ["🍒", "🍋", "🍊", "🍇", "⭐"]
    result = [random.choice(emojis) for _ in range(3)]
    data[user]["points"] -= amount

    if len(set(result)) == 1:
        winnings = amount * 5
        data[user]["points"] += winnings
        result_msg = "🎉 잭팟! 5배 당첨!"
    elif len(set(result)) == 2:
        winnings = amount * 2
        data[user]["points"] += winnings
        result_msg = "✨ 2배 당첨!"
    else:
        result_msg = "꽝입니다!"

    save_data(data)
    await ctx.send(f"{' | '.join(result)}\n{result_msg}")

@bot.command()
async def 주사위(ctx, 선택: int, 금액: int):
    if 선택 < 1 or 선택 > 6:
        await ctx.send("1~6 사이 숫자를 골라주세요.")
        return

    user = get_user(ctx)
    if data.get(user, {}).get("points", 0) < 금액:
        await ctx.send("포인트가 부족합니다.")
        return

    결과 = random.randint(1, 6)
    data[user]["points"] -= 금액

    if 결과 == 선택:
        data[user]["points"] += 금액 * 6
        message = f"🎲 {결과}! 6배 당첨!"
    else:
        message = f"🎲 {결과}! 꽝입니다."

    save_data(data)
    await ctx.send(message)

@bot.command()
async def 홀짝(ctx, 선택: str, 금액: int):
    if 선택 not in ["홀", "짝"]:
        await ctx.send("홀 또는 짝을 입력해주세요.")
        return

    user = get_user(ctx)
    if data.get(user, {}).get("points", 0) < 금액:
        await ctx.send("포인트가 부족합니다.")
        return

    결과 = random.choice(["홀", "짝"])
    data[user]["points"] -= 금액

    if 결과 == 선택:
        data[user]["points"] += 금액 * 2
        message = f"⚪ {결과}! 2배 당첨!"
    else:
        message = f"⚪ {결과}! 꽝입니다."

    save_data(data)
    await ctx.send(message)

@bot.command()
async def 경마(ctx, 말번호: int, 금액: int):
    if 말번호 < 1 or 말번호 > 4:
        await ctx.send("1~4번 말 중 하나를 선택해주세요.")
        return

    user = get_user(ctx)
    if data.get(user, {}).get("points", 0) < 금액:
        await ctx.send("포인트가 부족합니다.")
        return

    승리말 = random.randint(1, 4)
    data[user]["points"] -= 금액

    if 말번호 == 승리말:
        data[user]["points"] += 금액 * 4
        message = f"🐎 {승리말}번 말 우승! 4배 당첨!"
    else:
        message = f"🐎 {승리말}번 말 우승! 꽝입니다."

    save_data(data)
    await ctx.send(message)

bot.run(os.getenv("TOKEN"))
