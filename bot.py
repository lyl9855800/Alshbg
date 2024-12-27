import discord
from discord.ext import commands
import asyncio
import json
import re

# إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ملف JSON لتخزين البيانات
DATA_FILE = "violations.json"

# الكلمات الممنوعة
BANNED_WORDS = ['badword1', 'badword2', 'badword3']

# قناة التقارير (ضع ID القناة هنا بعد تشغيل البوت)
REPORT_CHANNEL_ID = None

# تحميل البيانات من ملف JSON
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# حفظ البيانات إلى ملف JSON
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# عند تشغيل البوت
@bot.event
async def on_ready():
    global REPORT_CHANNEL_ID
    print(f'✅ البوت شغال: {bot.user}')
    print('------')
    # تحميل بيانات القناة من ملف JSON
    data = load_data()
    REPORT_CHANNEL_ID = data.get("report_channel_id")
    if REPORT_CHANNEL_ID:
        print(f"📝 التقارير سترسل إلى القناة ID: {REPORT_CHANNEL_ID}")

# مراقبة الرسائل (كلمات ممنوعة + منع الروابط)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # حذف الكلمات الممنوعة
    for word in BANNED_WORDS:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f'⚠️ {message.author.mention} الرسالة تحتوي على كلمات ممنوعة!')
            await send_report(f"🚨 كلمة ممنوعة من {message.author.mention} في القناة {message.channel.name}")
            return

    # منع الروابط
    if re.search(r"(http|www\.)", message.content):
        await message.delete()
        await message.channel.send(f'⚠️ {message.author.mention} يمنع نشر الروابط!')
        await send_report(f"🚨 محاولة نشر رابط من {message.author.mention} في القناة {message.channel.name}")
        return

    await bot.process_commands(message)

# إرسال التقارير إلى القناة المخصصة
async def send_report(content):
    if REPORT_CHANNEL_ID:
        channel = bot.get_channel(REPORT_CHANNEL_ID)
        if channel:
            await channel.send(content)

# إعداد قناة التقارير
@bot.command()
@commands.has_permissions(administrator=True)
async def set_report_channel(ctx, channel: discord.TextChannel):
    global REPORT_CHANNEL_ID
    REPORT_CHANNEL_ID = channel.id
    data = load_data()
    data["report_channel_id"] = REPORT_CHANNEL_ID
    save_data(data)
    await ctx.send(f"✅ تم تعيين قناة التقارير إلى {channel.mention}.")

# كتم الصوت
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    if reason is None:
        reason = "بدون سبب"

    guild = ctx.guild
    mute_role = discord.utils.get(guild.roles, name="Muted")
    if not mute_role:
        mute_role = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)

    await member.add_roles(mute_role)
    await ctx.send(f'✅ {member.mention} تم كتمه لمدة {duration} دقيقة بسبب: {reason}')
    await send_report(f"🚨 {member.mention} تم كتمه بواسطة {ctx.author.mention} لمدة {duration} دقيقة بسبب: {reason}")

    # فك الكتم بعد انتهاء المدة
    await asyncio.sleep(duration * 60)
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(f'✅ {member.mention} تم فك الكتم عنه.')

# طرد مستخدم
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "بدون سبب"
    await member.kick(reason=reason)
    await ctx.send(f'✅ {member.mention} تم طرده بسبب: {reason}')
    await send_report(f"🚨 {member.mention} تم طرده بواسطة {ctx.author.mention} بسبب: {reason}")

# حظر مستخدم
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "بدون سبب"
    await member.ban(reason=reason)
    await ctx.send(f'✅ {member.mention} تم حظره بسبب: {reason}')
    await send_report(f"🚨 {member.mention} تم حظره بواسطة {ctx.author.mention} بسبب: {reason}")

# فك الحظر
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f'✅ {user.mention} تم فك الحظر عنه.')
            await send_report(f"✅ {user.mention} تم فك الحظر عنه بواسطة {ctx.author.mention}")
            return
    await ctx.send(f'⚠️ لم يتم العثور على مستخدم بهذا الاسم.')

# عرض السجل من ملف JSON
@bot.command()
async def violations(ctx):
    data = load_data()
    report_channel_id = data.get("report_channel_id", "غير محدد")
    await ctx.send(f"📋 سجل المخالفات:\nقناة التقارير: {report_channel_id}")

# تشغيل البوت
bot.run('51ff65d66bce5426fd5249c7e08d2fcf0a3d1bffdecba2742d4b4e960f7bd4c5')
