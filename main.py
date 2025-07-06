
import asyncio
import json
import logging
import os
import random
import time
from threading import Thread

import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from waitress import serve

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

# XP Commands
@bot.command(name="stats")
async def check_stats(ctx):
    """Check your XP and level stats"""
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data:
        await safe_send_message(ctx, "🌌 You haven't earned any XP yet. Start chatting to gain experience!")
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
    
    await safe_send_message(ctx, f"🌟 **{ctx.author.display_name}'s Realm Stats**\n"
                           f"Level: {level}\n"
                           f"XP: {xp}\n"
                           f"Next: {xp_needed}")

@bot.command(name="choose")
async def choose_path(ctx, path: str = None):
    """Choose your path at level 20"""
    if not path:
        await safe_send_message(ctx, "🌌 Choose your path: `!choose flame` 🔥  |  `!choose ash` 🪶  |  `!choose echo` 🌀")
        return
    
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data or data[user_id]["level"] < 20:
        await safe_send_message(ctx, "🌌 You must reach level 20 before choosing a path.")
        return
    
    path = path.lower()
    if path not in path_roles:
        await safe_send_message(ctx, "🌌 Unknown path. Choose: `flame`, `ash`, or `echo`")
        return
    
    # Check if user already has a path role
    user_roles = [role.name for role in ctx.author.roles]
    for path_data in path_roles.values():
        if path_data["role"] in user_roles:
            await safe_send_message(ctx, "🌌 You have already chosen your path and cannot change it.")
            return
    
    # Add the path role
    path_info = path_roles[path]
    role = discord.utils.get(ctx.guild.roles, name=path_info["role"])
    if role:
        if await safe_add_role(ctx.author, role):
            await safe_send_message(ctx, path_info["message"])
        else:
            await safe_send_message(ctx, "🌌 Something went wrong while choosing your path.")
    else:
        await safe_send_message(ctx, f"🌌 The {path_info['role']} role doesn't exist on this server.")

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Show the top 10 users by XP"""
    data = load_data()
    if not data:
        await safe_send_message(ctx, "🌌 No one has earned XP yet!")
        return
    
    # Sort users by XP
    sorted_users = sorted(data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    
    leaderboard_text = "🏆 **The Realm's Top Dwellers**\n"
    for i, (user_id, user_data) in enumerate(sorted_users, 1):
        try:
            user = bot.get_user(int(user_id))
            name = user.display_name if user else f"Unknown User"
        except:
            name = "Unknown User"
        
        leaderboard_text += f"{i}. {name} - Level {user_data['level']} ({user_data['xp']} XP)\n"
    
    await safe_send_message(ctx, leaderboard_text)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.error("DISCORD_TOKEN environment variable not found!")
    exit(1)

TOKEN = TOKEN.strip()  # Remove any whitespace
if len(TOKEN) < 50:
    logger.error("Discord token appears to be too short - please check your token")
    exit(1)

haunted_users = {}
collected_whispers = {}
all_whispers = [
    "🩸 The shadows are softer tonight...",
    "🩸 I made you a friendship charm. It whispers.",
    "🩸 Blood tastes different under the moon.",
    "🩸 I dreamt of you last night. You fell. I caught you. Then dropped you again. 😌",
    "🩸 If you close your eyes, I'll speak louder."
]

# Global config for stream detection
realm_news_channel_id = 1377172856160649246  # Carl's ping location
realm_nexus_channel_id = 1378882771061051442  # BloodBun's response location
carl_bot_id = 235148962103951360  # Carl-bot's user ID
quill_bot_id = 713586207119900693  # Quill's actual bot user ID

# Cooldown tracking
last_stream_announcement = 0
stream_cooldown = 300  # 5 minutes

# BloodBun QOTD Response Map
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

app = Flask('')

@app.route('/')
def home():
    return "BloodBun is lurking..."

def run():
    port = int(os.environ.get("PORT", 8080))
    serve(app, host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
async def safe_send_message(destination, content):
    """Safely send a message with error handling"""
    try:
        await destination.send(content)
        return True
    except discord.Forbidden:
        logger.warning(f"No permission to send message to {destination}")
        return False
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False

async def safe_add_role(member, role):
    """Safely add a role with error handling"""
    try:
        if role not in member.roles:
            await member.add_roles(role)
            return True
        return False
    except discord.Forbidden:
        logger.warning(f"No permission to add role {role.name} to {member.display_name}")
        return False
    except discord.HTTPException as e:
        logger.error(f"HTTP error adding role: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding role: {e}")
        return False

async def safe_add_reactions(message, reactions):
    """Safely add reactions with error handling"""
    try:
        for reaction in reactions:
            await message.add_reaction(reaction)
            await asyncio.sleep(0.25)  # Rate limit protection
    except discord.Forbidden:
        logger.warning("No permission to add reactions")
    except discord.HTTPException as e:
        logger.error(f"HTTP error adding reactions: {e}")
    except Exception as e:
        logger.error(f"Unexpected error adding reactions: {e}")

@bot.event
async def on_ready():
    print(f"🩸 BloodBun has awakened as {bot.user}!")
    logger.info(f"Bot connected as {bot.user}")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in event {event}: {args}, {kwargs}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingPermissions):
        await safe_send_message(ctx, "🩸 BloodBun lacks the power to perform that action...")
    elif isinstance(error, commands.BotMissingPermissions):
        await safe_send_message(ctx, "🩸 The shadows prevent me from doing that...")
    else:
        logger.error(f"Command error in {ctx.command}: {error}")
        await safe_send_message(ctx, "🩸 Something went wrong in the void...")

@bot.command(name="summonbun")
async def about_bloodbun(ctx):
    intro = (
        "🧸✨ **About BloodBun** ✨🩸\n"
        "Once a forgotten plush in Drac's nest, BloodBun was stitched to life the moment The Realm awoke.\n"
        "He's cute, he's creepy, and he's a little too aware of where you sleep.\n\n"
        "**Commands you can try:**\n"
        "`!hauntme` – opt into his creepy whispers.\n"
        "`!bloodwhisper` – hear what he's thinking.\n"
        "`!hauntstats` – check how many whispers you've unlocked.\n"
        "`!bloodstats` – see how often you've summoned him.\n"
        "`!unhauntme` – back out (for now...)\n"
        "`!snack`, `!cuddle`, `!hello` – because fluff is power!\n"
        "`!lore` to hear my secrets... if I'm awake.\n\n"
        "Collect all whispers and earn the 🐰Collector role.\n"
        "Be careful what you cuddle...\n\n"
        "*P.S. I only answer when I'm online. Otherwise? I vanish like socks in the laundry.*"
    )
    await safe_send_message(ctx, intro)

@bot.command(name='lore')
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
    response = random.choice(lores)
    await safe_send_message(ctx, response)

@bot.command()
async def hello(ctx):
    await safe_send_message(ctx, "👋 BloodBun peeks out from the shadows... Hello, squishy.")

@bot.command()
async def snack(ctx):
    snacks = [
        "🩸 BloodBun is nibbling on a shadowberry tart...",
        "🧃 BloodBun sips suspiciously red juice from a juicebox.",
        "🍓 A bat-shaped fruit snack vanishes into fluff.",
        "🍪 He's chewing something crunchy and it's definitely looking back."
    ]
    gif_url = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTh1N3k5bm5iMnNqNHptbGFrcmFub2h0Nm1yMHR2eDdocGt2Y3J5NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/DhKhBbHPlrTr9TFCZS/giphy.gif"

    chosen_snack = random.choice(snacks)
    await safe_send_message(ctx, chosen_snack)

    if "juicebox" in chosen_snack:
        await safe_send_message(ctx, gif_url)

@bot.command()
async def cuddle(ctx):
    cuddles = [
        "🧸 BloodBun flops into your lap. Accept the fluff.",
        "✨ A soft paw reaches for your hand. Trust it.",
        "🌑 You are now in a cuddle trap. Struggle only tightens it.",
        "🩸 A snuggle aura surrounds you. There's no escape."
    ]
    gif_url = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExdmN0eGk5ejcwcnR4dmJyODI4cXgzMGhhcGVoc2g5b2l5bDByZXN2ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/ugt20FJvA38QYS9RhC/giphy.gif"

    chosen_cuddle = random.choice(cuddles)
    await safe_send_message(ctx, chosen_cuddle)

    if "cuddle trap" in chosen_cuddle:
        await safe_send_message(ctx, gif_url)

@bot.command(name="hauntme")
async def hauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        haunted_users[user_id] = []
        try:
            await ctx.author.send("🩸 You've invited BloodBun into your DMs... Sweet dreams.")
        except discord.Forbidden:
            await safe_send_message(ctx, "🩸 Your DMs are locked... BloodBun will haunt you here instead.")
    else:
        try:
            await ctx.author.send("🩸 You are already haunted.")
        except discord.Forbidden:
            await safe_send_message(ctx, "🩸 You are already haunted.")

@bot.command(name="unhauntme")
async def unhauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id in haunted_users:
        del haunted_users[user_id]
        try:
            await ctx.author.send("🩸 You've pulled the covers up... for now.")
        except discord.Forbidden:
            await safe_send_message(ctx, "🩸 You've pulled the covers up... for now.")
    else:
        try:
            await ctx.author.send("🩸 You were never haunted to begin with. Curious.")
        except discord.Forbidden:
            await safe_send_message(ctx, "🩸 You were never haunted to begin with. Curious.")

@bot.command(name="bloodwhisper")
async def bloodwhisper(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        await safe_send_message(ctx, "🩸 You must use `!hauntme` to hear the whispers...")
        return

    available = [w for w in all_whispers if w not in haunted_users[user_id]]
    if not available:
        await safe_send_message(ctx, "🩸 You've heard all there is to hear... for now.")
        return

    whisper = random.choice(available)
    haunted_users[user_id].append(whisper)

    try:
        async with ctx.channel.typing():
            await ctx.author.send(whisper)
    except discord.Forbidden:
        await safe_send_message(ctx, f"🩸 *whispers in the shadows:* {whisper}")

    if len(haunted_users[user_id]) == len(all_whispers):
        try:
            role = discord.utils.get(ctx.guild.roles, name="🐰Collector")
            if role:
                member = ctx.guild.get_member(ctx.author.id)
                if member and await safe_add_role(member, role):
                    channel = discord.utils.get(ctx.guild.text_channels, name="🩸realm-nexus🩸")
                    if channel:
                        await safe_send_message(channel, f"✨🩸🐰 {ctx.author.mention} has unlocked all of BloodBun's whispers and become a 🐰Collector!")
        except Exception as e:
            logger.error(f"Error awarding Collector role: {e}")

@bot.command(name="hauntstats")
async def hauntstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await safe_send_message(ctx, f"🩸 You've collected {count}/{len(all_whispers)} whispers.")

@bot.command(name="bloodstats")
async def bloodstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await safe_send_message(ctx, f"🩸 BloodBun has whispered to you {count} time(s).")

@bot.event
async def on_message(message):
    global last_stream_announcement
    
    if message.author == bot.user:
        return

    try:
        # XP tracking for non-bot messages
        if not message.author.bot:
            user_id = str(message.author.id)
            now = time.time()

            if user_id not in cooldowns or now - cooldowns[user_id] >= XP_COOLDOWN:
                cooldowns[user_id] = now

                data = load_data()
                if user_id not in data:
                    data[user_id] = {"xp": 0, "level": 0}

                earned_xp = random.randint(MIN_XP, MAX_XP)
                data[user_id]["xp"] += earned_xp

                xp = data[user_id]["xp"]
                level = data[user_id]["level"]
                new_level = get_level_from_xp(xp, xp_table)

                if new_level > level:
                    data[user_id]["level"] = new_level
                    await safe_send_message(message.channel, f"{message.author.mention} leveled up to {new_level}! 🎉")

                    if new_level in level_roles:
                        role_name = level_roles[new_level]
                        role = discord.utils.get(message.guild.roles, name=role_name)
                        if role:
                            await safe_add_role(message.author, role)
                            msg = level_messages.get(new_level, "")
                            if msg:
                                await safe_send_message(message.channel, f"{message.author.mention} {msg}")

                    if new_level == 20:
                        await safe_send_message(message.channel,
                            f"{message.author.mention} 🌌 You have reached Level 20.\n"
                            "The Realm opens before you. Choose your path:\n"
                            "`!choose flame` 🔥  |  `!choose ash` 🪶  |  `!choose echo` 🌀"
                        )

                    if new_level in [30, 40, 50, 60, 70, 80, 90]:
                        user_roles = [role.name for role in message.author.roles]
                        for path_key, path_data in path_roles.items():
                            if path_data["role"] in user_roles:
                                lore_message = path_lore.get(path_key, {}).get(new_level, "")
                                if lore_message:
                                    await safe_send_message(message.channel, f"{message.author.mention} {lore_message}")
                                break

                    if new_level == 100:
                        role = discord.utils.get(message.guild.roles, name=final_role)
                        if role:
                            await safe_add_role(message.author, role)
                            await safe_send_message(message.channel, f"{message.author.mention} {final_message}")

                save_data(data)
        # Mention response
        if bot.user.mentioned_in(message):
            responses = [
                "🩸 BloodBun tilts his head... You're brave.",
                "🩸 Did someone say my name? I was napping in the cobwebs.",
                "🩸 You rang? I brought unsettling energy and a squeaky toy."
            ]

            if random.randint(1, 10) == 1:
                responses += [
                    "🩸 404: response.exe has vanished into the burrow.",
                    "🩸 [REDACTED] is not to be spoken of here.",
                    "🩸 I can see your soul's stitching from here.",
                    "🩸 You've been chosen. Do not resist the fluff.",
                    "🩸 *BloodBun unflops dramatically.* You rang?"
                ]

            if random.randint(1, 20) == 1:
                responses = ["🩸", "👁️🧸👁️", "🦴🩸", "🔪", "🪦", "🍥"]

            await safe_send_message(message.channel, random.choice(responses))

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
                    if random.randint(1, 6) == 1:  # ~16% chance
                        await safe_send_message(message.channel, random.choice(responses))
                        break

        # Stream Start Detection from Carl-bot
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
                if target_channel:
                    last_stream_announcement = now  # Update cooldown before sending
                    await safe_send_message(target_channel, random.choice(stream_start_reactions))
                    await safe_send_message(target_channel, gif_url)

        # Quill message check for QOTD responses
        if message.channel.id == realm_nexus_channel_id and message.author.id == quill_bot_id:
            matched = False
            for key_phrase, response in bloodbun_qotd_responses.items():
                if key_phrase.lower() in message.content.lower():
                    await safe_send_message(message.channel, response)
                    matched = True
                    break

            if not matched:
                reactions = ["🩸", "👁️", "🧸", "🐰"]
                await safe_add_reactions(message, reactions)

        # Secret DM whisper on QOTD response
        if message.channel.id == realm_nexus_channel_id:
            user_id = str(message.author.id)
            if user_id in haunted_users and not message.author.bot:
                available = [w for w in all_whispers if w not in haunted_users[user_id]]
                if available and random.randint(1, 3) == 1:  # 1 in 3 chance to trigger
                    whisper = random.choice(available)
                    haunted_users[user_id].append(whisper)

                    try:
                        await message.author.send(whisper)
                    except discord.Forbidden:
                        logger.info(f"Couldn't DM {message.author.display_name}.")
                    except Exception as e:
                        logger.error(f"Error sending DM to {message.author.display_name}: {e}")

                    # Check for Collector role reward
                    if len(haunted_users[user_id]) == len(all_whispers):
                        try:
                            role = discord.utils.get(message.guild.roles, name="🐰Collector")
                            if role:
                                member = message.guild.get_member(message.author.id)
                                if member and await safe_add_role(member, role):
                                    channel = discord.utils.get(message.guild.text_channels, name="🩸realm-nexus🩸")
                                    if channel:
                                        await safe_send_message(channel, f"✨🩸🐰 {message.author.mention} has unlocked all of BloodBun's whispers and become a 🐰Collector!")
                        except Exception as e:
                            logger.error(f"Error awarding Collector role: {e}")

        # Random chatter
        if not message.author.bot:
            if random.randint(1, 50) == 1:  # Adjust the number for frequency (lower = more often)
                random_chatter = [
                    "🩸 The air feels… thicker here.",
                    "👁️ I saw that. No, not you. The thing *behind* you.",
                    "🕯️ Sometimes I hum lullabies backwards. The forest sings along.",
                    "🐾 My paws are cold. That means something's coming.",
                    "🌑 Your shadow moved before you did.",
                    "🧸 I blinked. Reality didn't.",
                    "📣 BloodBun announces: snacks solve 98% of hauntings.",
                    "🎮 If you lose this round, I win... something.",
                    "🔮 BloodBun predicts: You'll misplace something important today. And it's already too late.",
                    "😌 I left a little something in your dreams. You'll see.",
                    "🍓 Shadowberries taste better when stolen."
                ]
                await safe_send_message(message.channel, random.choice(random_chatter))

    except Exception as e:
        logger.error(f"Error in on_message: {e}")

    await bot.process_commands(message)

keep_alive()
bot.run(TOKEN)
