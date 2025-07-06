import asyncio
import json
import logging
import os
import random
import time
from threading import Thread
from typing import Optional
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from waitress import serve
from discord import TextChannel

command_locks = {}
COMMAND_COOLDOWN = 3  # seconds


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
    
# XP settings
MIN_XP = 15
MAX_XP = 25
XP_COOLDOWN = 60
cooldowns = {}

# Reset cooldowns
reset_cooldowns = {}
RESET_COOLDOWN_SECONDS = 86400  # 24 hours

# XP table
def generate_xp_table(max_level=100):
    xp_table = {}
    xp = 0
    for level in range(1, max_level + 1):
        xp += 500 if level == 1 else 499
        xp_table[level] = xp
    return xp_table

xp_table = generate_xp_table()

def get_level_from_xp(xp, xp_table):
    level = 0
    for lvl, required_xp in sorted(xp_table.items()):
        if xp >= required_xp:
            level = lvl
        else:
            break
    return level

# Role rewards
level_roles = {
    1: "Initiate",
    5: "Nightborne",
    10: "Veilbound"
}

level_messages = {
    1: "🪢 **Initiate — Level 1+**\nYou have stirred the Realm. You are awakened.\n_A knot just beginning to tie — the first connection, a loose bond forming. The Realm has noticed you, and your presence begins to twist into its fabric._",
    5: "🔗 **Nightborne — Level 5+**\nDusk knows your name. The path links you to the Realm.\n_A link forged — your presence is now a visible connection, stronger and more deliberate. You’re becoming part of the Realm’s chain, walking dusk-lit paths between shadow and light._",
    10: "🕸️ **Veilbound — Level 10+**\nThe Realm surrounds you and within it you are bound.\n_A web of fate — your spirit is now fully enmeshed. You’re not just part of the Realm; you are woven into its design and destiny._"
}

# Path system
path_roles = {
    "flame": {
        "role": "Flamebound",
        "symbol": "🔥",
        "message": "🔥 _You have chosen the Path of Flame._\nThe Realm stirs with heat. You are no longer a spark—you are the beginning of a blaze."
    },
    "ash": {
        "role": "Ashbound",
        "symbol": "🪶",
        "message": "🪶 _You have chosen the Path of Ash._\nThe Realm quiets. You are the stillness that follows, the breath held before the end."
    },
    "echo": {
        "role": "Echo-bound",
        "symbol": "🌀",
        "message": "🌀 _You have chosen the Path of Echoes._\nThe Realm ripples. You are the resonance of what was and what will be."
    }
}

path_lore = {
    "flame": {
        30: "🔥 _The fire no longer burns you. It obeys you._\nYou are no longer shaped by the Realm—you shape it in return.",
        40: "🔥 _You are the flame that devours the veil._\nThe Realm bends to your will, and the stars flicker in your wake.",
        50: "🔥 _The flame no longer consumes. It creates._\nYou forge new realities in the Realm’s crucible.",
        60: "🔥 _You are the forge and the fury._\nCreation and destruction are no longer opposites—they are your tools.",
        70: "🔥 _The Realm trembles at your heat._\nEven silence cannot withstand your presence.",
        80: "🔥 _You are the final ember and the first spark._\nTime itself ignites in your wake.",
        90: "🔥 _You are the flame that remembers._\nThe Realm burns with your memory."
    },
    "ash": {
        30: "🪶 _You are the silence after the storm._\nThe Realm no longer speaks to you—it listens.",
        40: "🪶 _You are the last ember in a world of dust._\nThe Realm remembers you not as a traveler, but as a witness.",
        50: "🪶 _You are the stillness that follows endings._\nThe Realm rests in your shadow, soothed by your silence.",
        60: "🪶 _You walk where even memory fades._\nWhat you carry is not forgotten—it is preserved.",
        70: "🪶 _Ash does not vanish. It settles._\nYou are the foundation of what will come.",
        80: "🪶 _You are the hush before the Realm dreams._\nEven the stars dim in reverence.",
        90: "🪶 _You are the dust of legends._\nThe Realm is built on your silence."
    },
    "echo": {
        30: "🌀 _You hear what was never said._\nThe Realm hums with truths that only you can perceive.",
        40: "🌀 _You are the echo that precedes the sound._\nThe Realm is no longer a place—it is your reflection.",
        50: "🌀 _You echo not what was, but what will be._\nThe Realm bends around your resonance.",
        60: "🌀 _You are the whisper in the void._\nEven silence carries your name.",
        70: "🌀 _You are the pattern beneath the chaos._\nThe Realm dances to your unseen rhythm.",
        80: "🌀 _You are the echo that shapes the source._\nReality follows where your voice has already been.",
        90: "🌀 _You are the resonance of the Realm itself._\nIts pulse is your own."
    }
}

final_role = "The Remembered"
final_message = (
    "🔮 **The Remembered — Level 100+**\n"
    "You are no longer part of the Realm. You are its memory.\n"
    "_Your presence echoes in the silence between stars. The Realm does not guide you—you are the path._"
)

# Data handling
def load_data():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.command(name="stats")
async def check_stats(ctx):
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("🌌 You haven't earned any XP yet. Start chatting to gain experience!")
        return

    user_data = data[user_id]
    xp = user_data["xp"]
    level = user_data["level"]

    next_level = level + 1
    next_level_xp = xp_table.get(next_level, "MAX")

    if next_level_xp == "MAX":
        xp_needed = "You've reached the maximum level!"
    else:
        xp_needed = f"{next_level_xp - xp} XP needed for level {next_level}"

    await ctx.send(f"🌟 **{ctx.author.display_name}'s Realm Stats**\n"
                   f"Level: {level}\n"
                   f"XP: {xp}\n"
                   f"Next: {xp_needed}")

@bot.command(name="choose")
async def choose_path(ctx, path: Optional[str] = None):
    if not path:
        await ctx.send("🌌 Choose your path: `!choose flame` 🔥  |  `!choose ash` 🪶  |  `!choose echo` 🌀")
        return

    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data or data[user_id]["level"] < 20:
        await ctx.send("🌌 You must reach level 20 before choosing a path.")
        return

    path = path.lower()
    if path not in path_roles:
        await ctx.send("🌌 Unknown path. Choose: `flame`, `ash`, or `echo`")
        return

    user_roles = [role.name for role in ctx.author.roles]
    for path_data in path_roles.values():
        if path_data["role"] in user_roles:
            await ctx.send("🌌 You have already chosen your path and cannot change it.")
            return

    path_info = path_roles[path]
    role = discord.utils.get(ctx.guild.roles, name=path_info["role"])
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(path_info["message"])
    else:
        await ctx.send(f"🌌 The {path_info['role']} role doesn't exist on this server.")

    @bot.command(name="leaderboard")
    async def leaderboard(ctx):
        now = time.time()
        user_id = str(ctx.author.id)

        # 🔐 Check if user is on cooldown
        if user_id in command_locks and now - command_locks[user_id] < COMMAND_COOLDOWN:
            return  # Ignore duplicate triggers

        # 🔓 Set new cooldown
        command_locks[user_id] = now

        data = load_data()
        if not data:
            await ctx.send("🌌 No one has earned XP yet!")
            return

        sorted_users = sorted(
            data.items(),
            key=lambda x: (-x[1]["level"], -x[1]["xp"])
        )[:10]
        
        print("🔍 Using level-first sorting")

        leaderboard_text = "🏆 **The Realm's Top Dwellers**\n"
        for i, (user_id, user_data) in enumerate(sorted_users, 1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"User {user_id}"
            leaderboard_text += f"{i}. {name} — Level {user_data['level']} ({user_data['xp']} XP)\n"

        await ctx.send(leaderboard_text)

@bot.command(name="realmpath")
async def realmpath(ctx):
    user_roles = [role.name for role in ctx.author.roles]
    current_path = None

    for path_key, path_data in path_roles.items():
        if path_data["role"] in user_roles:
            current_path = path_key
            break

    if not current_path:
        await ctx.send(f"{ctx.author.mention}, you have not chosen a path yet. Reach level 20 and use `!choose`.")
        return

    data = load_data()
    user_id = str(ctx.author.id)
    level = data.get(user_id, {}).get("level", 0)

    next_milestone = next((lvl for lvl in sorted(path_lore[current_path]) if lvl > level), None)
    if next_milestone:
        await ctx.send(f"{ctx.author.mention}, you walk the **Path of {path_roles[current_path]['role']}** {path_roles[current_path]['symbol']}\nNext revelation awaits at **Level {next_milestone}**.")
    else:
        await ctx.send(f"{ctx.author.mention}, you walk the **Path of {path_roles[current_path]['role']}** {path_roles[current_path]['symbol']}\nYou have received all known revelations. The Realm watches in silence...")

@bot.command(name="resetpath")
async def resetpath(ctx):
    user_id = str(ctx.author.id)
    now = time.time()

    if user_id in reset_cooldowns and now - reset_cooldowns[user_id] < RESET_COOLDOWN_SECONDS:
        remaining = int(RESET_COOLDOWN_SECONDS - (now - reset_cooldowns[user_id]))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await ctx.send(f"{ctx.author.mention}, you may only reset your path once every 24 hours.\nTry again in **{hours}h {minutes}m**.")
        return

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(f"{ctx.author.mention}, are you sure you want to abandon your path? Type `yes` to confirm.")

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        if msg.content.lower() == "yes":
            removed = False
            for path_data in path_roles.values():
                role = discord.utils.get(ctx.guild.roles, name=path_data["role"])
                if role in ctx.author.roles:
                    await ctx.author.remove_roles(role)
                    removed = True
            if removed:
                reset_cooldowns[user_id] = now
                await ctx.send(f"{ctx.author.mention}, your path has been severed. The Realm forgets... for now.")
            else:
                await ctx.send("You are not bound to any path.")
        else:
            await ctx.send("Path reset cancelled.")
    except asyncio.TimeoutError:
        await ctx.send("No response. Path reset cancelled.")

@bot.command(name="realmhelp")
async def realmhelp(ctx):
    embed = discord.Embed(
        title="📖 Realmbound Commands",
        description="The Realm whispers guidance to those who listen...",
        color=discord.Color.dark_purple()
    )
    embed.add_field(name="!stats", value="Check your level and XP.", inline=False)
    embed.add_field(name="!leaderboard", value="See the top Realmbound souls.", inline=False)
    embed.add_field(name="!choose [flame|ash|echo]", value="Choose your path at level 20.", inline=False)
    embed.add_field(name="!realmpath", value="View your current path and next lore milestone.", inline=False)
    embed.add_field(name="!resetpath", value="Abandon your current path (once every 24h).", inline=False)
    embed.set_footer(text="The Realm remembers those who remain.")
    await ctx.send(embed=embed)

haunted_users = {}
collected_whispers = {}
all_whispers = [
    "🩸 The shadows are softer tonight...",
    "🩸 I made you a friendship charm. It whispers.",
    "🩸 Blood tastes different under the moon.",
    "🩸 I dreamt of you last night. You fell. I caught you. Then dropped you again. 😌",
    "🩸 If you close your eyes, I'll speak louder."
]

@bot.command(name="hauntme")
async def hauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        haunted_users[user_id] = []
        try:
            await ctx.author.send("🩸 You've invited BloodBun into your DMs... Sweet dreams.")
        except discord.Forbidden:
            await ctx.send("🩸 Your DMs are locked... BloodBun will haunt you here instead.")
    else:
        try:
            await ctx.author.send("🩸 You are already haunted.")
        except discord.Forbidden:
            await ctx.send("🩸 You are already haunted.")

@bot.command(name="unhauntme")
async def unhauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id in haunted_users:
        del haunted_users[user_id]
        try:
            await ctx.author.send("🩸 You've pulled the covers up... for now.")
        except discord.Forbidden:
            await ctx.send("🩸 You've pulled the covers up... for now.")
    else:
        try:
            await ctx.author.send("🩸 You were never haunted to begin with. Curious.")
        except discord.Forbidden:
            await ctx.send("🩸 You were never haunted to begin with. Curious.")

@bot.command(name="bloodwhisper")
async def bloodwhisper(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        await ctx.send("🩸 You must use `!hauntme` to hear the whispers...")
        return

    available = [w for w in all_whispers if w not in haunted_users[user_id]]
    if not available:
        await ctx.send("🩸 You've heard all there is to hear... for now.")
        return

    whisper = random.choice(available)
    haunted_users[user_id].append(whisper)

    try:
        async with ctx.channel.typing():
            await ctx.author.send(whisper)
    except discord.Forbidden:
        await ctx.send(f"🩸 *whispers in the shadows:* {whisper}")

    if len(haunted_users[user_id]) == len(all_whispers):
        try:
            role = discord.utils.get(ctx.guild.roles, name="🐰Collector")
            if role:
                member = ctx.guild.get_member(ctx.author.id)
                if member:
                    await member.add_roles(role)
                    await ctx.send(f"✨🩸🐰 {ctx.author.mention} has unlocked all of BloodBun's whispers and become a 🐰Collector!")
        except Exception as e:
            print(f"Error awarding Collector role: {e}")

@bot.command(name="hauntstats")
async def hauntstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await ctx.send(f"🩸 You've collected {count}/{len(all_whispers)} whispers.")

@bot.command(name="bloodstats")
async def bloodstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await ctx.send(f"🩸 BloodBun has whispered to you {count} time(s).")

@bot.command()
async def hello(ctx):
    await ctx.send("👋 BloodBun peeks out from the shadows... Hello, squishy.")

@bot.command()
async def snack(ctx):
    snacks = [
        "🩸 BloodBun is nibbling on a shadowberry tart...",
        "🧃 BloodBun sips suspiciously red juice from a juicebox.",
        "🍓 A bat-shaped fruit snack vanishes into fluff.",
        "🍪 He's chewing something crunchy and it's definitely looking back."
    ]
    await ctx.send(random.choice(snacks))

@bot.command()
async def cuddle(ctx):
    cuddles = [
        "🧸 BloodBun flops into your lap. Accept the fluff.",
        "✨ A soft paw reaches for your hand. Trust it.",
        "🌑 You are now in a cuddle trap. Struggle only tightens it.",
        "🩸 A snuggle aura surrounds you. There's no escape."
    ]
    await ctx.send(random.choice(cuddles))

@bot.command(name="summonbun")
async def summonbun(ctx):
    intro = (
        "🧸✨ **About BloodBun** ✨🩸\n"
        "Once a forgotten plush in Drac's nest, BloodBun was stitched to life the moment The Realm awoke.\n"
        "He's cute, he's creepy, and he's a little too aware of where you sleep.\n\n"
        "**Commands you can try:**\n"
        "`!hauntme`, `!bloodwhisper`, `!hauntstats`, `!bloodstats`, `!unhauntme`\n"
        "`!snack`, `!cuddle`, `!hello`, `!lore`, `!summonbun`\n"
        "`!stats`, `!choose`, `!realmpath`, `!resetpath`, `!leaderboard`, `!realmhelp`\n\n"
        "Collect all whispers and earn the 🐰Collector role.\n"
        "*P.S. I only answer when I'm online. Otherwise? I vanish like socks in the laundry.*"
    )
    await ctx.send(intro)

@bot.command(name="lore")
async def lore(ctx):
    lores = [
        "🌙 Vrykolia was born beneath a blood moon, wrapped in stormlight and lavender.",
        "🩸 The Realm isn't a place… it's a state of mind. And BloodBun guards its borders.",
        "🐰 BloodBun has his own room in Vry's cottage. It's full of bones. And snacks.",
        "🎻 On quiet nights, you can hear Vrykolia's lullaby drifting from the forest... backward.",
        "💀 There is a secret room in The Realm where even Vry doesn't go. BloodBun naps there.",
        "🕯️ Every time someone rage-quits a game, BloodBun gains power.",
        "🕸️ The Realm has layers. You're only seeing what BloodBun *wants* you to see.",
        "🌲 The trees around Vry's cottage sometimes whisper warnings. Other times, they gossip.",
        "🦴 BloodBun once stared into the void. It blinked first.",
        "👁️ There's a glitch in The Realm that keeps respawning the same blackbird. BloodBun is watching it closely.",
        "🎮 BloodBun is canonically the final boss of Vry's stream... if you pick the cursed ending.",
        "🩷 Drac once dared BloodBun to bite a celestial. That's why stars twinkle nervously now.",
        "✨ The Realm pulls in dreamers, misfits, and those who hear static when the world goes quiet.",
        "🛏️ If you fall asleep in The Realm with your earbuds in, BloodBun might remix your dreams.",
        "📜 There are 13 rules in The Realm. BloodBun ignores 12 of them and *enforces* the last one with extreme prejudice.",
    ]
    await ctx.send(random.choice(lores))

# QOTD responses
bloodbun_qotd_responses = {
    "If BloodBun were a boss fight": "🐰 Phase 1: Cuddle trap. Phase 2: Emotional damage. Final phase: Disappears in a puff of static.",
    "What's one game you're bad at—but love anyway?": "🎮 All of them. I just press buttons until the controller cries.",
    "If The Realm was a video game": "🩸 Cozy horror survival with unpredictable fluff mechanics. And bugs. Intentional ones.",
    "If BloodBun whispered a creepy prophecy": "👁️ \"Your socks know too much. Burn the striped ones first.\"",
    "You've been marked by The Realm": "✨ Every mirror shows what you *almost* became. Also, your coffee is always slightly cold.",
    "Describe your soul in three emojis": "🧸🩸🔪",
    "What's your haunting style": "🕯️ Wisp. I drift through walls and whisper embarrassing memories.",
    "What book would you haunt": "📖 A cookbook. I like whispering bad substitutions during soufflés.",
    "You find a cursed journal": "✍️ \"Page intentionally left blank. The screaming starts on page 2.\"",
    "What snack would instantly restore your HP": "🍓 Shadowberry Pop-Tarts. Cursed but toasty.",
    "What's your comfort food when the shadows get too loud?": "🍲 Bone broth. No questions.",
    "What treat would you offer a ghost": "🍪 One (1) perfectly salted cookie. Still warm. Bribes matter."
}

# Stream detection and keyword triggers
realm_news_channel_id = 1377172856160649246
realm_nexus_channel_id = 1378882771061051442
carl_bot_id = 235148962103951360
quill_bot_id = 713586207119900693
last_stream_announcement = 0
stream_cooldown = 300

@bot.event

async def on_message(message):
    global last_stream_announcement

    if message.author == bot.user:
        return
   
    # Keyword triggers
    if not message.author.bot:
        lowered = message.content.lower()
        keyword_responses = {
            "vampire": [
                "🧛‍♂️ I once tried being a vampire. Too much cleanup.",
                "🦇 Fangs are cute. I prefer claws.",
                "🩸 Vampires bite. I nibble *psychically*."
            ],
            "blood": [
                "🩸 Is it yours? Asking for a ritual.",
                "🧃 Blood? Juice? Tomato soup? I don't ask anymore.",
                "🩸 The blood moon likes me. We're pen pals."
            ],
            "game": [
                "🎮 If you lose, I get your snacks.",
                "🧸 I'm unbeatable at hide-and-squeak.",
                "🎲 Want to play a game? It only ends when you scream."
            ],
            "snack": [
                "🍪 BloodBun drools slightly. It's fine.",
                "🩸 I accept offerings in cookie form.",
                "🥠 This one has a message: *RUN*."
            ],
            "cuddle": [
                "🧸 Snuggle activated. Resistance is... adorable.",
                "✨ Cuddles increase sanity by 2d4.",
                "🌙 Cuddle confirmed. Sleep in peace. Maybe."
            ],
            "fluff": [
                "🐰 Fluff is power. And static electricity.",
                "🩸 Fluffy things bite back.",
                "👁️ I'm made of 40% fluff, 60% secrets."
            ]
        }

        for keyword, responses in keyword_responses.items():
            if keyword in lowered:
                if random.randint(1, 6) == 1:
                    await message.channel.send(random.choice(responses))
                    break

    # Stream start detection
    if (
        message.channel.id == realm_news_channel_id
        and message.author.id == carl_bot_id
        and "has entered The Realm!" in message.content
    ):
        now = time.time()
        if now - last_stream_announcement >= stream_cooldown:
            stream_start_reactions = [
                "🩸 *BloodBun perks up.* Vry's back. The shadows are watching.",
                "👁️ The Realm opens... BloodBun sharpened his fluff for this.",
                "🧸 Twitching ears detected stream energy. *Cuddly chaos incoming.*",
                "🎮 Game on. Hope you're not afraid of static... or me.",
                '🌕 BloodBun whispers: "It begins again... bring snacks."'
            ]
            gif_url = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzFrYW5lOWdvcG1xc2g2MTl1aGwxa2Q5aHEzOWR6M3ZwNTU4M2I3ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/h8REz6z97lJpSKLYdX/giphy.gif"
            target_channel = bot.get_channel(realm_nexus_channel_id)
            if isinstance(target_channel, TextChannel):
                last_stream_announcement = now
                await target_channel.send(random.choice(stream_start_reactions))
                await target_channel.send(gif_url)


    # QOTD detection
    if message.channel.id == realm_nexus_channel_id and message.author.id == quill_bot_id:
        matched = False
        for key_phrase, response in bloodbun_qotd_responses.items():
            if key_phrase.lower() in message.content.lower():
                await message.channel.send(response)
                matched = True
                break
        if not matched:
            reactions = ["🩸", "👁️", "🧸", "🐰", "🐰"]
            for emoji in reactions:
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    pass  # Could log this if you want to track failed reactions
                    
        await bot.process_commands(message)
# Flask keep-alive server
app = Flask('')

@app.route('/')
def home():
    return "BloodBun is watching..."

def run():
    serve(app, host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Start the bot
logging.basicConfig(level=logging.INFO)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ DISCORD_TOKEN not found in environment!")
    exit(1)

if __name__ == "__main__":
    keep_alive()  # Starts the Flask server in a separate thread
    bot.run(TOKEN)  # Starts the Discord bot