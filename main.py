import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

haunted_users = {}
collected_whispers = {}
all_whispers = [
    "🩸 The shadows are softer tonight...",
    "🩸 I made you a friendship charm. It whispers.",
    "🩸 Blood tastes different under the moon.",
    "🩸 I dreamt of you last night. You fell. I caught you. Then dropped you again. 😌",
    "🩸 If you close your eyes, I’ll speak louder."
]

@bot.event
async def on_ready():
    print(f"🩸 BloodBun has awakened as {bot.user}!")

@bot.command(name="summonbun")
async def about_bloodbun(ctx):
    intro = (
        "🧸✨ **About BloodBun** ✨🩸\n"
        "Once a forgotten plush in Drac’s nest, BloodBun was stitched to life the moment The Realm awoke.\n"
        "He’s cute, he’s creepy, and he’s a little too aware of where you sleep.\n\n"
        "**Commands you can try:**\n"
        "`!hauntme` – opt into his creepy whispers.\n"
        "`!bloodwhisper` – hear what he's thinking.\n"
        "`!hauntstats` – check how many whispers you’ve unlocked.\n"
        "`!bloodstats` – see how often you’ve summoned him.\n"
        "`!unhauntme` – back out (for now...)\n"
        "`!snack`, `!cuddle`, `!hello` – because fluff is power!\n"
        "`!lore` to hear my secrets... if I'm awake.\n\n"
        "Collect all whispers and earn the 🐰Collector role.\n"
        "Be careful what you cuddle...\n\n"
        "*P.S. I only answer when I’m online. Otherwise? I vanish like socks in the laundry.*"
    )
    await ctx.send(intro)

import random

@bot.command(name='lore')
async def lore(ctx):
    lores = [
        "🌙 Vrykolia was born beneath a blood moon, wrapped in stormlight and lavender.",
        "🩸 The Realm isn’t a place… it’s a state of mind. And BloodBun guards its borders.",
        "🐰 BloodBun has his own room in Vry’s cottage. It’s full of bones. And snacks.",
        "🎻 On quiet nights, you can hear Vrykolia’s lullaby drifting from the forest... backward.",
        "💀 There is a secret room in The Realm where even Vry doesn’t go. BloodBun naps there.",
        "🕯️ Every time someone rage-quits a game, BloodBun gains power.",
        "🕸️ The Realm has layers. You’re only seeing what BloodBun *wants* you to see.",
        "🌲 The trees around Vry’s cottage sometimes whisper warnings. Other times, they gossip.",
        "🦴 BloodBun once stared into the void. It blinked first.",
        "👁️ There’s a glitch in The Realm that keeps respawning the same blackbird. BloodBun is watching it closely.",
        "🎮 BloodBun is canonically the final boss of Vry’s stream... if you pick the cursed ending.",
        "🩷 Drac once dared BloodBun to bite a celestial. That’s why stars twinkle nervously now.",
        "✨ The Realm pulls in dreamers, misfits, and those who hear static when the world goes quiet.",
        "🛏️ If you fall asleep in The Realm with your earbuds in, BloodBun might remix your dreams.",
        "📜 There are 13 rules in The Realm. BloodBun ignores 12 of them and *enforces* the last one with extreme prejudice.",

    ]
    response = random.choice(lores)
    await ctx.send(response)

@bot.command()
async def hello(ctx):
    await ctx.send("👋 BloodBun peeks out from the shadows... Hello, squishy.")

@bot.command()
async def snack(ctx):
    snacks = [
        "🩸 BloodBun is nibbling on a shadowberry tart...",
        "🧃 BloodBun sips suspiciously red juice from a juicebox.",
        "🍓 A bat-shaped fruit snack vanishes into fluff.",
        "🍪 He’s chewing something crunchy and it's definitely looking back."
    ]
    gif_url = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTh1N3k5bm5iMnNqNHptbGFrcmFub2h0Nm1yMHR2eDdocGt2Y3J5NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/DhKhBbHPlrTr9TFCZS/giphy.gif"

    chosen_snack = random.choice(snacks)
    await ctx.send(chosen_snack)

    if "juicebox" in chosen_snack:
        await ctx.send(gif_url)

@bot.command()
async def cuddle(ctx):
    cuddles = [
        "🧸 BloodBun flops into your lap. Accept the fluff.",
        "✨ A soft paw reaches for your hand. Trust it.",
        "🌑 You are now in a cuddle trap. Struggle only tightens it.",
        "🩸 A snuggle aura surrounds you. There’s no escape."
    ]
    await ctx.send(random.choice(cuddles))

@bot.command(name="hauntme")
async def hauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        haunted_users[user_id] = []
        await ctx.author.send("🩸 You’ve invited BloodBun into your DMs... Sweet dreams.")
    else:
        await ctx.author.send("🩸 You are already haunted.")

@bot.command(name="unhauntme")
async def unhauntme(ctx):
    user_id = str(ctx.author.id)
    if user_id in haunted_users:
        del haunted_users[user_id]
        await ctx.author.send("🩸 You’ve pulled the covers up... for now.")
    else:
        await ctx.author.send("🩸 You were never haunted to begin with. Curious.")

@bot.command(name="bloodwhisper")
async def bloodwhisper(ctx):
    user_id = str(ctx.author.id)
    if user_id not in haunted_users:
        await ctx.send("🩸 You must use `!hauntme` to hear the whispers...")
        return

    available = [w for w in all_whispers if w not in haunted_users[user_id]]
    if not available:
        await ctx.send("🩸 You’ve heard all there is to hear... for now.")
        return

    whisper = random.choice(available)
    haunted_users[user_id].append(whisper)

    async with ctx.channel.typing():
        await ctx.author.send(whisper)


    if len(haunted_users[user_id]) == len(all_whispers):
        role = discord.utils.get(ctx.guild.roles, name="🐰Collector")
        if role:
            member = ctx.guild.get_member(ctx.author.id)
            if member:
                await member.add_roles(role)
                channel = discord.utils.get(ctx.guild.text_channels, name="🩸realm-nexus🩸")
                if channel:
                    await channel.send(f"✨🩸🐰 {ctx.author.mention} has unlocked all of BloodBun’s whispers and become a 🐰Collector!")

@bot.command(name="hauntstats")
async def hauntstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await ctx.send(f"🩸 You’ve collected {count}/{len(all_whispers)} whispers.")

@bot.command(name="bloodstats")
async def bloodstats(ctx):
    user_id = str(ctx.author.id)
    count = len(haunted_users.get(user_id, []))
    await ctx.send(f"🩸 BloodBun has whispered to you {count} time(s).")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Mention response
    if f"<@1389717350055411854>" in message.content:
        responses = [
            "🩸 BloodBun tilts his head... You're brave.",
            "🩸 Did someone say my name? I was napping in the cobwebs.",
            "🩸 You rang? I brought unsettling energy and a squeaky toy."
        ]

        if random.randint(1, 10) == 1:
            responses += [
                "🩸 404: response.exe has vanished into the burrow.",
                "🩸 [REDACTED] is not to be spoken of here.",
                "🩸 I can see your soul’s stitching from here.",
                "🩸 You’ve been chosen. Do not resist the fluff.",
                "🩸 *BloodBun unflops dramatically.* You rang?"
            ]

        if random.randint(1, 20) == 1:
            responses = ["🩸", "👁️🧸👁️", "🦴🩸", "🔪", "🪦", "🍥"]

        await message.channel.send(random.choice(responses))

    # 🧛 Keyword triggers
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
                "🧃 Blood? Juice? Tomato soup? I don’t ask anymore.",
                "🩸 The blood moon likes me. We're pen pals."
            ],
            "game": [
                "🎮 If you lose, I get your snacks.",
                "🧸 I’m unbeatable at hide-and-squeak.",
                "🎲 Want to play a game? It only ends when you scream."
            ],
            "snack": [
                "🍪 BloodBun drools slightly. It’s fine.",
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
                "👁️ I’m made of 40% fluff, 60% secrets."
            ]
        }

        for keyword, responses in keyword_responses.items():
            if keyword in lowered:
                if random.randint(1, 6) == 1:  # ~16% chance
                    await message.channel.send(random.choice(responses))
                    break

    await bot.process_commands(message)

    # Chance for BloodBun to randomly speak
    if not message.author.bot:
        if random.randint(1, 75) == 1:  # Adjust the number for frequency (lower = more often)
            random_chatter = [
                "🩸 The air feels… thicker here.",
                "👁️ I saw that. No, not you. The thing *behind* you.",
                "🕯️ Sometimes I hum lullabies backwards. The forest sings along.",
                "🐾 My paws are cold. That means something's coming.",
                "🌑 Your shadow moved before you did.",
                "🧸 I blinked. Reality didn’t.",
                "📣 BloodBun announces: snacks solve 98% of hauntings.",
                "🎮 If you lose this round, I win... something.",
                "🔮 BloodBun predicts: You’ll misplace something important today. And it’s already too late.",
                "😌 I left a little something in your dreams. You’ll see.",
                "🍓 Shadowberries taste better when stolen."
            ]
            await message.channel.send(random.choice(random_chatter))

    # 🎥 Stream Start Detection from Carl-bot
    import time
    import random

    # Global config
    realm_news_channel_id = 1377172856160649246  # Carl's ping location
    realm_nexus_channel_id = 1378882771061051442  # BloodBun's response location
    carl_bot_id = 235148962103951360  # Carl-bot’s user ID

    # Cooldown tracking
    last_stream_announcement = 0
    stream_cooldown = 300  # 5 minutes

    @bot.event
    async def on_message(message):
        global last_stream_announcement

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
                    await target_channel.send(random.choice(stream_start_reactions))

    # 📌 Config
    quill_bot_id = 713586207119900693  # Quill's actual bot user ID
    realm_nexus_channel_id = 1378882771061051442  # QOTD channel where Quill posts

    # 📖 BloodBun QOTD Response Map
    bloodbun_qotd_responses = {
        "If BloodBun were a boss fight": "🐰 Phase 1: Cuddle trap. Phase 2: Emotional damage. Final phase: Disappears in a puff of static.",
        "What’s one game you’re bad at—but love anyway?": "🎮 All of them. I just press buttons until the controller cries.",
        "If The Realm was a video game": "🩸 Cozy horror survival with unpredictable fluff mechanics. And bugs. Intentional ones.",
        "If BloodBun whispered a creepy prophecy": "👁️ “Your socks know too much. Burn the striped ones first.”",
        "You’ve been marked by The Realm": "✨ Every mirror shows what you *almost* became. Also, your coffee is always slightly cold.",
        "Describe your soul in three emojis": "🧸🩸🔪",
        "What’s your haunting style": "🕯️ Wisp. I drift through walls and whisper embarrassing memories.",
        "What book would you haunt": "📖 A cookbook. I like whispering bad substitutions during soufflés.",
        "You find a cursed journal": "✍️ \"Page intentionally left blank. The screaming starts on page 2.\"",
        "What snack would instantly restore your HP": "🍓 Shadowberry Pop-Tarts. Cursed but toasty.",
        "What’s your comfort food when the shadows get too loud?": "🍲 Bone broth. No questions.",
        "What treat would you offer a ghost": "🍪 One (1) perfectly salted cookie. Still warm. Bribes matter."
    }

    # 🪶 Quill message check
    if message.channel.id == realm_nexus_channel_id and message.author.id == quill_bot_id:
        matched = False
        for key_phrase, response in bloodbun_qotd_responses.items():
            if key_phrase.lower() in message.content.lower():
                await message.channel.send(response)
                matched = True
                break

        if not matched:
            try:
                await message.add_reaction("🩸")
                await message.add_reaction("👁️")
                await message.add_reaction("🧸")
                await message.add_reaction("🐰")
            except discord.Forbidden:
                print("BloodBun can't react — missing permissions.")

    # 🔮 Secret DM whisper on QOTD response (tracked like !bloodwhisper)
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
                    print(f"Couldn't DM {message.author.display_name}.")

                # 🐰 Check for Collector role reward
                if len(haunted_users[user_id]) == len(all_whispers):
                    role = discord.utils.get(message.guild.roles, name="🐰Collector")
                    if role:
                        member = message.guild.get_member(message.author.id)
                        if member and role not in member.roles:
                            await member.add_roles(role)
                            channel = discord.utils.get(message.guild.text_channels, name="🩸realm-nexus🩸")
                            if channel:
                                await channel.send(f"✨🩸🐰 {message.author.mention} has unlocked all of BloodBun’s whispers and become a 🐰Collector!")

    await bot.process_commands(message)

bot.run(TOKEN)