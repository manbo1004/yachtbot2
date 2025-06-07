import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# 데이터 불러오기
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 데이터 저장하기
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

# 자정 기준 출석 여부 확인
def has_checked_attendance(user_id):
    kst = datetime.utcnow() + timedelta(hours=9)
    today_str = kst.strftime("%Y-%m-%d")
    return data.get(str(user_id), {}).get("last_attendance") == today_str

# 포인트 조회
@bot.command()
async def 포인트(ctx):
    user_id = str(ctx.author.id)
    points = data.get(user_id, {}).get("points", 0)
    await ctx.send(f"{ctx.author.mention} 님의 포인트: {points}P")

# 출석
@bot.command()
async def 출석(ctx):
    user_id = str(ctx.author.id)
    kst = datetime.utcnow() + timedelta(hours=9)
    today_str = kst.strftime("%Y-%m-%d")

    if has_checked_attendance(user_id):
        await ctx.send(f"{ctx.author.mention} 이미 오늘 출석하셨습니다!")
        return

    if user_id not in data:
        data[user_id] = {"points": 0}

    data[user_id]["points"] = data[user_id].get("points", 0) + 100
    data[user_id]["last_attendance"] = today_str
    save_data(data)

    await ctx.send(f"{ctx.author.mention}님 출석 완료! +100P")

# 포인트 랭킹
@bot.command()
async def 랭킹(ctx):
    ranking = sorted(data.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:5]
    result = []
    for i, (user_id, info) in enumerate(ranking, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else "탈퇴자"
        result.append(f"{i}위 - {name}: {info.get('points', 0)}P")
    await ctx.send("🏆 포인트 랭킹 TOP 5 🏆\n" + "\n".join(result))

# 상점
@bot.command()
async def 상점(ctx):
    shop_items = [
        ("길드 명찰 (메이플랜드 실물)", 10000),
        ("치킨 기프티콘", 30000),
        ("500만 메소", 30000),
        ("피자 기프티콘", 45000),
        ("족발 기프티콘", 60000)
    ]
    shop_msg = "\n".join([f"{name}: {price}P" for name, price in shop_items])
    await ctx.send("🎁 현재 구매 가능한 보상 🎁\n" + shop_msg)

# 상품 구매
@bot.command()
async def 구매(ctx, *, item_name):
    user_id = str(ctx.author.id)
    shop = {
        "길드 명찰": 10000,
        "치킨": 30000,
        "500만 메소": 30000,
        "피자": 45000,
        "족발": 60000
    }

    matched = next((key for key in shop if key in item_name), None)
    if not matched:
        await ctx.send("존재하지 않는 상품입니다.")
        return

    price = shop[matched]
    if data.get(user_id, {}).get("points", 0) < price:
        await ctx.send("포인트가 부족합니다.")
        return

    data[user_id]["points"] -= price
    save_data(data)
    await ctx.send(f"{ctx.author.mention} {matched} 구매 완료! -{price}P")

# 관리자 지급
@bot.command()
@commands.has_permissions(administrator=True)
async def 지급(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    if user_id not in data:
        data[user_id] = {"points": 0}
    data[user_id]["points"] += amount
    save_data(data)
    await ctx.send(f"{member.display_name}님에게 {amount}P 지급 완료.")

# 슬롯
@bot.command()
async def 슬롯(ctx, amount: int):
    user_id = str(ctx.author.id)
    if data.get(user_id, {}).get("points", 0) < amount:
        await ctx.send("포인트가 부족합니다.")
        return

    icons = ["🍒", "🍋", "🔔", "⭐"]
    result = [random.choice(icons) for _ in range(3)]
    display = " | ".join(result)

    if result.count(result[0]) == 3:
        win = amount * 5
        msg = f"🎰 {display} - 대박! +{win}P"
    elif len(set(result)) == 2:
        win = amount * 2
        msg = f"🎰 {display} - 2개 일치! +{win}P"
    else:
        win = -amount
        msg = f"🎰 {display} - 꽝! -{amount}P"

    data[user_id]["points"] += win
    save_data(data)
    await ctx.send(msg)

# 주사위
@bot.command()
async def 주사위(ctx, number: int, amount: int):
    user_id = str(ctx.author.id)
    if number < 1 or number > 6:
        await ctx.send("1~6 사이 숫자를 선택하세요.")
        return
    if data.get(user_id, {}).get("points", 0) < amount:
        await ctx.send("포인트가 부족합니다.")
        return

    result = random.randint(1, 6)
    if result == number:
        win = amount * 6
        msg = f"🎲 결과: {result} - 정답! +{win}P"
    else:
        win = -amount
        msg = f"🎲 결과: {result} - 틀렸습니다. -{amount}P"

    data[user_id]["points"] += win
    save_data(data)
    await ctx.send(msg)

# 홀짝
@bot.command()
async def 홀짝(ctx, guess: str, amount: int):
    user_id = str(ctx.author.id)
    if guess not in ["홀", "짝"]:
        await ctx.send("홀 또는 짝 중 선택하세요.")
        return
    if data.get(user_id, {}).get("points", 0) < amount:
        await ctx.send("포인트가 부족합니다.")
        return

    number = random.randint(1, 100)
    result = "홀" if number % 2 == 1 else "짝"

    if guess == result:
        win = amount * 2
        msg = f"🎯 {number} - {result} 정답! +{win}P"
    else:
        win = -amount
        msg = f"🎯 {number} - {result} 틀림! -{amount}P"

    data[user_id]["points"] += win
    save_data(data)
    await ctx.send(msg)

# 경마
@bot.command()
async def 경마(ctx, horse: int, amount: int):
    user_id = str(ctx.author.id)
    if horse not in [1, 2, 3, 4]:
        await ctx.send("1~4번 말 중 선택하세요.")
        return
    if data.get(user_id, {}).get("points", 0) < amount:
        await ctx.send("포인트가 부족합니다.")
        return

    result = random.randint(1, 4)
    if result == horse:
        win = amount * 4
        msg = f"🏇 {result}번 말 우승! 정답 +{win}P"
    else:
        win = -amount
        msg = f"🏇 {result}번 말 우승! 틀림 -{amount}P"

    data[user_id]["points"] += win
    save_data(data)
    await ctx.send(msg)

# 봇 실행
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if token:
        bot.run(token)
    else:
        print("환경변수 TOKEN이 설정되지 않았습니다.")
