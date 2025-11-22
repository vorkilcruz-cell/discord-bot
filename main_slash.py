import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import requests
from googletrans import Translator
import yt_dlp as youtube_dl
import os
from datetime import datetime, timedelta
import json
import subprocess
import logging
import sys
from io import StringIO

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)
        self.synced = False
        
    async def setup_hook(self):
        command_count = len(self.tree._get_all_commands())
        logger.info(f"📡 Syncing {command_count} slash commands with Discord...")
        
        try:
            # Try global sync first
            synced = await self.tree.sync()
            self.synced = True
            logger.info(f"✅ Successfully synced {len(synced)} commands globally!")
        except discord.errors.HTTPException as e:
            if e.code == 50240:
                # Entry Point command conflict - this is expected
                logger.warning(f"⚠️ Discord Entry Point conflict (Error 50240) - syncing to guilds instead...")
                logger.info(f"📝 Commands will sync to servers when bot connects - autocomplete should appear shortly")
                self.synced = False  # Will retry in on_ready
            else:
                logger.warning(f"⚠️ Discord sync error (Code {e.code}): {e}")
                logger.info(f"📝 Commands will still work - Discord cache will refresh automatically")

bot = MyBot()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DC_AGENT_WEBHOOK_URL = os.getenv('DC_AGENT_WEBHOOK_URL')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN required")

class WebhookHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            if DISCORD_WEBHOOK_URL:
                chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
                for chunk in chunks:
                    requests.post(DISCORD_WEBHOOK_URL, json={"content": f"```\n{chunk}\n```"}, timeout=5)
        except Exception as e:
            print(f"Webhook logging error: {e}")

def setup_logging():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if DISCORD_WEBHOOK_URL:
        webhook_handler = WebhookHandler()
        webhook_handler.setLevel(logging.INFO)
        webhook_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        webhook_handler.setFormatter(webhook_formatter)
        logger.addHandler(webhook_handler)
    
    return logger

def send_agent_webhook(indicator: str, content: str):
    """
    Send formatted messages to DC_AGENT_WEBHOOK_URL for comprehensive agent activity logging.
    Tracks: code edits, file reads, decisions, commands, actions, and completions.
    """
    if not DC_AGENT_WEBHOOK_URL:
        return False
    
    try:
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = f"[{timestamp}] **{indicator}**\n{content}"
        
        # Handle long messages by chunking
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        
        for chunk in chunks:
            response = requests.post(
                DC_AGENT_WEBHOOK_URL, 
                json={"content": chunk}, 
                timeout=5
            )
            if response.status_code not in [200, 204]:
                logger.debug(f"Webhook response code: {response.status_code}")
        
        return True
    except Exception as e:
        logger.debug(f"Failed to send agent webhook: {e}")
        return False

logger = setup_logging()
translator = Translator()
CURSE_WORDS = ['fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard', 'crap', 'hell']
BEYBLADE_FILE = 'beyblade_data.json'
CONFESSIONS_FILE = 'confessions.json'

CARDS = {
    'Churro Card': {'emoji': '🌮', 'rarity': 'rare', 'value': 500},
    'Ohio Card': {'emoji': '🗺️', 'rarity': 'legendary', 'value': 1000},
    'Vox Card': {'emoji': '🎤', 'rarity': 'legendary', 'value': 1500},
}

FUN_FACTS = [
    "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible!",
    "A group of flamingos is called a 'flamboyance'.",
    "Octopuses have three hearts - two pump blood to the gills, one pumps it to the rest of the body.",
    "Bananas are berries, but strawberries aren't!",
    "A single bolt of lightning contains enough energy to toast 100,000 slices of bread.",
    "The fingerprints of koalas are so similar to humans, they could confuse crime scene investigators!",
    "Dolphins have names for each other.",
    "A group of crows is called a 'murder'.",
    "Scotland's national animal is a unicorn.",
    "Wombat poop is cubic shaped to prevent it from rolling away.",
]

WEATHER_DATA = {
    'USA': {'temp': 72, 'condition': '☀️ Sunny', 'humidity': 65, 'wind': '10 mph'},
    'UK': {'temp': 59, 'condition': '🌧️ Rainy', 'humidity': 85, 'wind': '15 mph'},
    'Japan': {'temp': 68, 'condition': '⛅ Partly Cloudy', 'humidity': 70, 'wind': '8 mph'},
    'Australia': {'temp': 86, 'condition': '☀️ Hot & Sunny', 'humidity': 40, 'wind': '12 mph'},
    'Canada': {'temp': 50, 'condition': '❄️ Cold', 'humidity': 75, 'wind': '20 mph'},
    'Brazil': {'temp': 82, 'condition': '☀️ Sunny', 'humidity': 80, 'wind': '6 mph'},
    'Germany': {'temp': 55, 'condition': '⛅ Cloudy', 'humidity': 70, 'wind': '14 mph'},
    'France': {'temp': 61, 'condition': '🌧️ Rainy', 'humidity': 78, 'wind': '11 mph'},
    'India': {'temp': 88, 'condition': '☀️ Hot', 'humidity': 65, 'wind': '9 mph'},
    'Mexico': {'temp': 80, 'condition': '☀️ Sunny', 'humidity': 55, 'wind': '7 mph'},
}

# MASSIVE BEYBLADE DATABASE
BEYBLADES = {
    'common': [
        {'id': 1, 'name': 'Storm Pegasus', 'type': 'Attack', 'power': 50, 'defense': 30, 'stamina': 40, 'special': 'Pegasus Spin'},
        {'id': 2, 'name': 'Rock Leone', 'type': 'Defense', 'power': 35, 'defense': 55, 'stamina': 30, 'special': 'Leone Shield'},
        {'id': 3, 'name': 'Flame Sagittario', 'type': 'Attack', 'power': 45, 'defense': 25, 'stamina': 50, 'special': 'Flame Arrow'},
        {'id': 4, 'name': 'Dark Wolf', 'type': 'Balance', 'power': 40, 'defense': 35, 'stamina': 45, 'special': 'Wolf Fang'},
        {'id': 5, 'name': 'Lightning Aquario', 'type': 'Balance', 'power': 42, 'defense': 38, 'stamina': 48, 'special': 'Water Stream'},
        {'id': 6, 'name': 'Cyber Pegasus', 'type': 'Attack', 'power': 48, 'defense': 32, 'stamina': 42, 'special': 'Cyber Attack'},
        {'id': 7, 'name': 'Metal Fusion', 'type': 'Defense', 'power': 38, 'defense': 50, 'stamina': 35, 'special': 'Metal Armor'},
        {'id': 8, 'name': 'Burn Phoenix', 'type': 'Balance', 'power': 44, 'defense': 40, 'stamina': 46, 'special': 'Phoenix Rise'},
    ],
    'rare': [
        {'id': 9, 'name': 'Lightning L-Drago', 'type': 'Attack', 'power': 70, 'defense': 40, 'stamina': 50, 'special': 'Drago Burst'},
        {'id': 10, 'name': 'Earth Eagle', 'type': 'Defense', 'power': 55, 'defense': 60, 'stamina': 55, 'special': 'Eagle Guard'},
        {'id': 11, 'name': 'Gravity Perseus', 'type': 'Balance', 'power': 65, 'defense': 50, 'stamina': 60, 'special': 'Gravity Field'},
        {'id': 12, 'name': 'Dark Bull', 'type': 'Defense', 'power': 52, 'defense': 65, 'stamina': 48, 'special': 'Bull Crash'},
        {'id': 13, 'name': 'Storm Aquario', 'type': 'Attack', 'power': 68, 'defense': 42, 'stamina': 55, 'special': 'Aqua Burst'},
        {'id': 14, 'name': 'Rock Giraffe', 'type': 'Defense', 'power': 48, 'defense': 70, 'stamina': 42, 'special': 'Giraffe Wall'},
        {'id': 15, 'name': 'Virgo', 'type': 'Balance', 'power': 62, 'defense': 58, 'stamina': 62, 'special': 'Virgo Force'},
        {'id': 16, 'name': 'Libra', 'type': 'Balance', 'power': 64, 'defense': 56, 'stamina': 64, 'special': 'Cosmic Balance'},
    ],
    'legendary': [
        {'id': 17, 'name': 'Big Bang Pegasus', 'type': 'Attack', 'power': 90, 'defense': 70, 'stamina': 85, 'special': 'Big Bang Impact'},
        {'id': 18, 'name': 'Meteo L-Drago', 'type': 'Attack', 'power': 95, 'defense': 65, 'stamina': 80, 'special': 'Meteo Burst'},
        {'id': 19, 'name': 'Phantom Orion', 'type': 'Balance', 'power': 75, 'defense': 80, 'stamina': 100, 'special': 'Phantom Domain'},
        {'id': 20, 'name': 'Cosmic Pegasus', 'type': 'Attack', 'power': 92, 'defense': 72, 'stamina': 88, 'special': 'Cosmic Flare'},
        {'id': 21, 'name': 'Ultimate Eagle', 'type': 'Defense', 'power': 78, 'defense': 95, 'stamina': 75, 'special': 'Ultimate Guard'},
        {'id': 22, 'name': 'Galaxy Pegasus', 'type': 'Attack', 'power': 96, 'defense': 70, 'stamina': 90, 'special': 'Galaxy Burst'},
        {'id': 23, 'name': 'Divine Phoenix', 'type': 'Balance', 'power': 85, 'defense': 85, 'stamina': 95, 'special': 'Phoenix Rebirth'},
        {'id': 24, 'name': 'Apocalypse L-Drago', 'type': 'Attack', 'power': 100, 'defense': 60, 'stamina': 75, 'special': 'Apocalypse'},
    ]
}

class MusicPlayer:
    def __init__(self):
        self.current = None
        self.loop = False
        self.voice_client = None

music_players = {}

def load_beyblade_data():
    if os.path.exists(BEYBLADE_FILE):
        with open(BEYBLADE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_beyblade_data(data):
    with open(BEYBLADE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def init_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            'beyblades': [],
            'level': 1,
            'gold': 0,
            'wins': 0,
            'losses': 0,
            'vorkteks': 1000,
            'cards': {},
            'last_daily': None
        }
    return data

def load_confessions():
    if os.path.exists(CONFESSIONS_FILE):
        with open(CONFESSIONS_FILE, 'r') as f:
            return json.load(f)
    return {'confessions': []}

def save_confessions(data):
    with open(CONFESSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_loans():
    if os.path.exists('loans.json'):
        with open('loans.json', 'r') as f:
            return json.load(f)
    return {'loans': []}

def save_loans(data):
    with open('loans.json', 'w') as f:
        json.dump(data, f, indent=2)

def load_channel_config():
    if os.path.exists('channel_config.json'):
        with open('channel_config.json', 'r') as f:
            return json.load(f)
    return {'alert_channel_id': None}

def save_channel_config(data):
    with open('channel_config.json', 'w') as f:
        json.dump(data, f, indent=2)

def log_command_result(command_name, user, status, details=""):
    """Log command execution results"""
    log_msg = f'✅ Command Success: /{command_name} by {user} ({user.id}) | {details}' if status == 'success' else f'❌ Command Failed: /{command_name} by {user} ({user.id}) | {details}'
    logger.info(log_msg)

@bot.event
async def on_ready():
    logger.info(f'✅ Bot connected! Logged in as {bot.user}')
    
    # If global sync failed, try guild-specific sync
    if not bot.synced:
        try:
            guild_count = 0
            for guild in bot.guilds:
                try:
                    await bot.tree.sync(guild=guild)
                    guild_count += 1
                except Exception as e:
                    logger.debug(f"Failed to sync commands in guild {guild.id}: {e}")
            
            if guild_count > 0:
                logger.info(f"✅ Successfully synced commands to {guild_count} guild(s)!")
                bot.synced = True
        except Exception as e:
            logger.warning(f"Guild sync fallback failed: {e}")
    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Beyblades spin | /commands"))
    logger.info(f'📊 Status updated to: Beyblades spin | /commands')
    
    config = load_channel_config()
    if config.get('alert_channel_id'):
        try:
            channel = bot.get_channel(config['alert_channel_id'])
            if channel:
                embed = discord.Embed(
                    title="🟢 BOT ONLINE",
                    description=f"**{bot.user}** is now online and ready!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Status", value="✅ Bot is running", inline=False)
                embed.add_field(name="Commands Available", value="Use `/commands` to see all commands", inline=False)
                embed.timestamp = discord.utils.utcnow()
                await channel.send(f"@everyone", embed=embed)
                logger.info(f'📢 Online alert sent to channel {config["alert_channel_id"]}')
        except Exception as e:
            logger.error(f'Failed to send online alert: {e}')

@bot.event
async def on_disconnect():
    logger.warning(f'⚠️ Bot disconnected!')
    config = load_channel_config()
    if config.get('alert_channel_id'):
        try:
            channel = bot.get_channel(config['alert_channel_id'])
            if channel:
                embed = discord.Embed(
                    title="🔴 BOT OFFLINE",
                    description=f"**{bot.user}** has gone offline.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Status", value="❌ Bot is offline", inline=False)
                embed.timestamp = discord.utils.utcnow()
                await channel.send(f"@everyone", embed=embed)
                logger.info(f'📢 Offline alert sent to channel {config["alert_channel_id"]}')
        except Exception as e:
            logger.error(f'Failed to send offline alert: {e}')

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f'❌ Command Error: {interaction.command.name} by {interaction.user} - {error}')
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ Error: {str(error)}", ephemeral=True)

async def command_callback(interaction: discord.Interaction) -> bool:
    command_name = interaction.command.name
    user = interaction.user
    logger.info(f'🔹 Command Invoked: /{command_name} by {user} ({user.id})')
    return True
    
bot.tree.interaction_check = command_callback

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if any(word in message.content.lower() for word in CURSE_WORDS):
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=5)
            await message.author.timeout(timeout_until, reason="Inappropriate language")
            await message.channel.send(f'{message.author.mention} muted for 5 minutes.')
            await message.delete()
        except:
            pass
    await bot.process_commands(message)

@bot.tree.command(name='play', description='Music player (use external music bots)')
@app_commands.describe(url='YouTube URL or search term')
async def play(interaction: discord.Interaction, url: str):
    embed = discord.Embed(
        title="🎵 Music Feature",
        description="Due to platform limitations, this bot cannot play audio directly. Use a dedicated music bot instead!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Recommended Music Bots", value="Groovy • Hydra • Lavalink • MEE6 Pro • Suno", inline=False)
    embed.add_field(name="Find Music Bots", value="[top.gg](https://top.gg) or [discordbotlist.com](https://discordbotlist.com)", inline=False)
    embed.add_field(name="Your Bot Features", value="Beyblades • Translation • Bible Verses • Fun Facts • And More!", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='meet_again', description='🎵 Play "Meet Again" video in VC')
async def meet_again(interaction: discord.Interaction):
    user_voice = interaction.user.voice if hasattr(interaction.user, 'voice') else None
    if not user_voice:
        embed = discord.Embed(
            title="❌ Not in Voice Channel",
            description="You need to be in a voice channel to use this command!",
            color=discord.Color.red()
        )
        log_command_result('meet_again', interaction.user, 'error', 'User not in voice channel')
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎵 Meet Again - Video Link",
        description="Here's the video you requested!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Video", value="[Meet Again - YouTube](https://youtu.be/2a7_yCxMgZc)", inline=False)
    embed.add_field(name="Status", value="⚠️ Due to platform limitations, this bot cannot play audio in voice channels.\n\nUse a dedicated music bot (Groovy, Hydra, MEE6) to play this in your VC!", inline=False)
    embed.add_field(name="Quick Setup", value="1. Add a music bot to your server\n2. Use `/play` or the music bot's command\n3. Paste the video link or search", inline=False)
    embed.add_field(name="Recommended Bots", value="[Groovy](https://groovy.bot) • [Hydra](https://hydra.bot) • [MEE6](https://mee6.xyz)", inline=False)
    embed.set_thumbnail(url="https://img.youtube.com/vi/2a7_yCxMgZc/maxresdefault.jpg")
    
    log_command_result('meet_again', interaction.user, 'success', f'Shared "Meet Again" video')
    await interaction.response.send_message(embed=embed)

LANGUAGES = {
    'English': 'en', 'Spanish': 'es', 'French': 'fr', 'German': 'de', 'Italian': 'it',
    'Portuguese': 'pt', 'Russian': 'ru', 'Japanese': 'ja', 'Chinese': 'zh-CN', 'Korean': 'ko',
    'Arabic': 'ar', 'Hindi': 'hi', 'Turkish': 'tr', 'Vietnamese': 'vi', 'Thai': 'th',
    'Polish': 'pl', 'Dutch': 'nl', 'Swedish': 'sv', 'Greek': 'el', 'Hebrew': 'he'
}

LANGUAGE_CHOICES = [app_commands.Choice(name=lang, value=code) for lang, code in LANGUAGES.items()]

@bot.tree.command(name='translate', description='Translate text between languages')
@app_commands.describe(
    text='Text to translate',
    source='Select source language',
    target='Select target language'
)
@app_commands.choices(source=LANGUAGE_CHOICES, target=LANGUAGE_CHOICES)
async def translate(interaction: discord.Interaction, text: str, source: app_commands.Choice[str], target: app_commands.Choice[str]):
    try:
        if source.value == target.value:
            await interaction.response.send_message("❌ Source and target languages must be different!", ephemeral=True)
            return
        
        result = translator.translate(text, src_lang=source.value, dest_lang=target.value)
        embed = discord.Embed(title="🌐 Translation", color=discord.Color.blue())
        embed.add_field(name=f"📝 {source.name}", value=text, inline=False)
        embed.add_field(name=f"✨ {target.name}", value=result.text, inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name='robux', description='Fake robux generator')
async def robux(interaction: discord.Interaction, amount: int = None):
    if amount is None:
        amount = random.randint(1, 1000000)
    msgs = [
        f"💰 {amount:,} ROBUX! (Just kidding 😂)",
        f"🎉 JACKPOT! {amount:,} ROBUX! (In your dreams)",
        f"⚡ {amount:,} ROBUX DROPPED! (Too bad it's fake 🤣)",
    ]
    await interaction.response.send_message(random.choice(msgs))

@bot.tree.command(name='verse', description='Random Bible verse')
async def verse(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        response = requests.get('https://labs.bible.org/api/?passage=random&type=json', timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            embed = discord.Embed(title=f"{data['bookname']} {data['chapter']}:{data['verse']}", description=data['text'], color=discord.Color.gold())
            await interaction.followup.send(embed=embed)
    except:
        await interaction.followup.send("❌ Error fetching verse")

@bot.tree.command(name='funfact', description='Random fun fact')
async def funfact(interaction: discord.Interaction):
    embed = discord.Embed(title="🎓 Fun Fact", description=random.choice(FUN_FACTS), color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='mc-get', description='Minecraft China Edition')
async def mc_get(interaction: discord.Interaction):
    embed = discord.Embed(title="⛏️ Minecraft: China Edition", color=discord.Color.green())
    embed.add_field(name="Download", value="[Get it here](https://news.4399.com/wdshijie/#search3-9e5f)", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='console', description='Bot logs')
async def console(interaction: discord.Interaction):
    try:
        result = subprocess.run(['tail', '-20', '/tmp/logs/Discord_Bot_20251121_094540_183.log'], capture_output=True, text=True, timeout=5)
        logs = result.stdout or "No logs"
        if len(logs) > 1900:
            logs = logs[-1900:]
        embed = discord.Embed(title="📋 Console", description=f"```\n{logs}\n```", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Error", ephemeral=True)

@bot.tree.command(name='spawn', description='🎰 Spawn a random Beyblade!')
async def spawn(interaction: discord.Interaction):
    roll = random.randint(1, 100)
    rarity = 'common' if roll <= 60 else 'rare' if roll <= 90 else 'legendary'
    bey = random.choice(BEYBLADES[rarity])
    
    color_map = {'common': discord.Color.greyple(), 'rare': discord.Color.blue(), 'legendary': discord.Color.gold()}
    embed = discord.Embed(title="⚡ A Wild Beyblade Appeared!", color=color_map[rarity])
    embed.add_field(name=f"🏷️ {bey['name']}", value=f"**Rarity:** {rarity.upper()}\n**Type:** {bey['type']}\n**Special:** {bey['special']}", inline=False)
    embed.add_field(name="Stats", value=f"⚔️ Attack: {bey['power']}\n🛡️ Defense: {bey['defense']}\n⏱️ Stamina: {bey['stamina']}", inline=False)
    embed.add_field(name="Catch", value=f"Use `/catch {bey['name']}`", inline=False)
    
    await interaction.response.send_message(embed=embed)
    if not hasattr(bot, 'spawns'):
        bot.spawns = {}
    bot.spawns[interaction.channel.id] = {'bey': bey, 'rarity': rarity}

@bot.tree.command(name='catch', description='🎯 Catch a Beyblade!')
@app_commands.describe(name='Exact Beyblade name')
async def catch(interaction: discord.Interaction, name: str):
    if not hasattr(bot, 'spawns') or interaction.channel.id not in bot.spawns:
        await interaction.response.send_message("❌ No Beyblade spawned! Use `/spawn` first.", ephemeral=True)
        return
    spawn = bot.spawns[interaction.channel.id]
    if name.lower() != spawn['bey']['name'].lower():
        await interaction.response.send_message(f"❌ Wrong name! The Beyblade was **{spawn['bey']['name']}**", ephemeral=True)
        return
    
    data = load_beyblade_data()
    uid = str(interaction.user.id)
    if uid not in data:
        data[uid] = {'beyblades': [], 'wins': 0, 'losses': 0, 'gold': 0, 'level': 1}
    
    caught_bey = {**spawn['bey'], 'rarity': spawn['rarity'], 'level': 1, 'xp': 0, 'battles': 0}
    data[uid]['beyblades'].append(caught_bey)
    data[uid]['gold'] += 10
    save_beyblade_data(data)
    
    embed = discord.Embed(title="🎉 Caught!", color=discord.Color.green())
    embed.add_field(name=f"Got **{spawn['bey']['name']}**!", value=f"Rarity: {spawn['rarity'].upper()}\n+10 Gold", inline=False)
    await interaction.response.send_message(embed=embed)
    del bot.spawns[interaction.channel.id]

@bot.tree.command(name='collection', description='📚 View your Beyblades')
async def collection(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_beyblade_data()
    uid = str(member.id)
    if uid not in data or not data[uid]['beyblades']:
        await interaction.response.send_message(f"❌ {member.name} has no Beyblades yet!", ephemeral=True)
        return
    
    beys = data[uid]['beyblades']
    embed = discord.Embed(title=f"📚 {member.name}'s Collection", description=f"Total: **{len(beys)}**  |  Level: **{data[uid].get('level', 1)}**  |  Gold: **{data[uid].get('gold', 0)}**", color=discord.Color.purple())
    
    for i, b in enumerate(beys[:12], 1):
        rarity_emoji = {'common': '⚪', 'rare': '🔵', 'legendary': '⭐'}
        embed.add_field(
            name=f"{i}. {rarity_emoji[b['rarity']]} {b['name']} (Lvl {b['level']})",
            value=f"**Type:** {b['type']} | **Special:** {b['special']}\n⚔️ {b['power']} | 🛡️ {b['defense']} | ⏱️ {b['stamina']}",
            inline=False
        )
    
    if len(beys) > 12:
        embed.set_footer(text=f"Showing 12 of {len(beys)} Beyblades")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='battle', description='⚔️ Battle another player!')
@app_commands.describe(opponent='Player to challenge')
async def battle(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot or opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ Invalid opponent", ephemeral=True)
        return
    
    data = load_beyblade_data()
    uid, oid = str(interaction.user.id), str(opponent.id)
    
    if uid not in data or not data[uid]['beyblades']:
        await interaction.response.send_message("❌ You have no Beyblades!", ephemeral=True)
        return
    if oid not in data or not data[oid]['beyblades']:
        await interaction.response.send_message(f"❌ {opponent.name} has no Beyblades!", ephemeral=True)
        return
    
    p_bey = data[uid]['beyblades'][0]
    o_bey = data[oid]['beyblades'][0]
    
    p_power = p_bey['power'] * (1 + p_bey['level'] * 0.1) + random.randint(-15, 15)
    o_power = o_bey['power'] * (1 + o_bey['level'] * 0.1) + random.randint(-15, 15)
    
    embed = discord.Embed(title="⚔️ BEYBLADE BATTLE!", color=discord.Color.red())
    embed.add_field(name=f"🔴 {interaction.user.name}", value=f"**{p_bey['name']}** (Lvl {p_bey['level']})\nPower: **{int(p_power)}**", inline=True)
    embed.add_field(name="VS", value="⚡", inline=True)
    embed.add_field(name=f"🔵 {opponent.name}", value=f"**{o_bey['name']}** (Lvl {o_bey['level']})\nPower: **{int(o_power)}**", inline=True)
    
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(3)
    
    if p_power > o_power:
        winner_id, loser_id = uid, oid
        msg = f"🎊 **{interaction.user.name}** wins!"
        gold_reward = 50
    elif o_power > p_power:
        winner_id, loser_id = oid, uid
        msg = f"🎊 **{opponent.name}** wins!"
        gold_reward = 50
    else:
        await interaction.followup.send("🤝 **It's a tie!**")
        return
    
    data[winner_id]['wins'] = data[winner_id].get('wins', 0) + 1
    data[winner_id]['gold'] = data[winner_id].get('gold', 0) + gold_reward
    data[loser_id]['losses'] = data[loser_id].get('losses', 0) + 1
    
    data[uid]['beyblades'][0]['battles'] = data[uid]['beyblades'][0].get('battles', 0) + 1
    data[uid]['beyblades'][0]['xp'] = data[uid]['beyblades'][0].get('xp', 0) + 25
    
    if data[uid]['beyblades'][0]['xp'] >= 100:
        data[uid]['beyblades'][0]['level'] += 1
        data[uid]['beyblades'][0]['xp'] = 0
        msg += f"\n✨ **{p_bey['name']}** leveled up to **Lvl {data[uid]['beyblades'][0]['level']}**!"
    
    save_beyblade_data(data)
    await interaction.followup.send(msg)

@bot.tree.command(name='stats', description='📊 Battle statistics')
@app_commands.describe(member='Player (optional)')
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_beyblade_data()
    uid = str(member.id)
    
    if uid not in data:
        await interaction.response.send_message(f"❌ No stats for {member.name}", ephemeral=True)
        return
    
    w = data[uid].get('wins', 0)
    l = data[uid].get('losses', 0)
    wr = (w / (w + l) * 100) if (w + l) > 0 else 0
    
    embed = discord.Embed(title=f"📊 {member.name}'s Stats", color=discord.Color.green())
    embed.add_field(name="🎖️ Battles", value=f"**Wins:** {w}\n**Losses:** {l}\n**Rate:** {wr:.1f}%", inline=False)
    embed.add_field(name="💰 Resources", value=f"**Gold:** {data[uid].get('gold', 0)}\n**Level:** {data[uid].get('level', 1)}\n**Beyblades:** {len(data[uid]['beyblades'])}", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='dex', description='🔍 Beyblade Pokedex')
@app_commands.describe(number='Beyblade ID (1-24)')
async def dex(interaction: discord.Interaction, number: int):
    if number < 1 or number > 24:
        await interaction.response.send_message("❌ ID must be 1-24", ephemeral=True)
        return
    
    for rarity, beys in BEYBLADES.items():
        for bey in beys:
            if bey['id'] == number:
                embed = discord.Embed(title=f"#{number} - {bey['name']}", color=discord.Color.blue())
                embed.add_field(name="Rarity", value=rarity.upper(), inline=False)
                embed.add_field(name="Type", value=bey['type'], inline=False)
                embed.add_field(name="Special Move", value=bey['special'], inline=False)
                embed.add_field(name="Stats", value=f"⚔️ Attack: {bey['power']}\n🛡️ Defense: {bey['defense']}\n⏱️ Stamina: {bey['stamina']}", inline=False)
                await interaction.response.send_message(embed=embed)
                return
    
    await interaction.response.send_message("❌ Beyblade not found", ephemeral=True)

@bot.tree.command(name='weather', description='🌤️ Check weather for any country')
@app_commands.describe(country='Country name (USA, UK, Japan, Australia, Canada, Brazil, Germany, France, India, Mexico)')
async def weather(interaction: discord.Interaction, country: str):
    country = country.title()
    
    if country not in WEATHER_DATA:
        available = ', '.join(WEATHER_DATA.keys())
        embed = discord.Embed(title="❌ Country Not Found", description=f"Available countries:\n{available}", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    data = WEATHER_DATA[country]
    embed = discord.Embed(title=f"🌤️ Weather in {country}", color=discord.Color.blue())
    embed.add_field(name="🌡️ Temperature", value=f"**{data['temp']}°F**", inline=True)
    embed.add_field(name="Condition", value=data['condition'], inline=True)
    embed.add_field(name="💨 Wind", value=data['wind'], inline=True)
    embed.add_field(name="💧 Humidity", value=f"**{data['humidity']}%**", inline=True)
    embed.set_footer(text="⚠️ Simulated Weather Data")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='youtube', description='📺 VorkilORCAL Channel')
async def youtube(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info('https://www.youtube.com/@VorkilORCAL', download=False)
            
            if 'entries' in info and len(info['entries']) > 0:
                latest = info['entries'][0]
                title = latest.get('title', 'Latest Video')
                video_url = f"https://www.youtube.com/watch?v={latest['id']}"
                channel_url = 'https://www.youtube.com/@VorkilORCAL'
                
                embed = discord.Embed(title="📺 VorkilORCAL Channel", color=discord.Color.red())
                embed.add_field(name="🎥 Latest Video", value=f"**{title}**\n[Watch Now]({video_url})", inline=False)
                embed.add_field(name="📢 Subscribe", value=f"[Visit Channel]({channel_url})", inline=False)
                embed.set_footer(text="YouTube Channel")
                
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(title="📺 VorkilORCAL Channel", description="[Visit Channel](https://www.youtube.com/@VorkilORCAL)", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
                
    except Exception as e:
        print(f'❌ YouTube Error: {e}')
        embed = discord.Embed(title="📺 VorkilORCAL Channel", description="[Visit Channel](https://www.youtube.com/@VorkilORCAL)", color=discord.Color.red())
        embed.add_field(name="Status", value="Latest video info unavailable, but you can visit the channel directly!", inline=False)
        await interaction.followup.send(embed=embed)

@bot.tree.command(name='balance', description='💰 Check VorkTek-Bucks and cards')
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_beyblade_data()
    data = init_user(data, member.id)
    save_beyblade_data(data)
    
    uid = str(member.id)
    vorkteks = data[uid].get('vorkteks', 1000)
    cards = data[uid].get('cards', {})
    
    embed = discord.Embed(title=f"💰 {member.name}'s Wallet", color=discord.Color.gold())
    embed.add_field(name="VorkTek-Bucks", value=f"**{vorkteks:,}** 💵", inline=False)
    
    if cards:
        card_list = '\n'.join([f"{CARDS[card]['emoji']} {card} x{count}" for card, count in cards.items()])
        embed.add_field(name="📦 Cards", value=card_list, inline=False)
    else:
        embed.add_field(name="📦 Cards", value="No cards yet!", inline=False)
    
    log_command_result('balance', interaction.user, 'success', f"Checked {member.name}'s balance: {vorkteks:,} VorkTek-Bucks")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='daily', description='📅 Collect daily VorkTek-Bucks bonus')
async def daily_bonus(interaction: discord.Interaction):
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    uid = str(interaction.user.id)
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_daily = data[uid].get('last_daily')
    
    if last_daily == today:
        await interaction.response.send_message("❌ You already claimed your daily bonus today! Come back tomorrow.", ephemeral=True)
        return
    
    bonus = 500
    data[uid]['vorkteks'] = data[uid].get('vorkteks', 1000) + bonus
    data[uid]['last_daily'] = today
    save_beyblade_data(data)
    
    embed = discord.Embed(title="📅 Daily Bonus Claimed!", description=f"You got **{bonus}** VorkTek-Bucks!", color=discord.Color.green())
    embed.add_field(name="Total", value=f"**{data[uid]['vorkteks']:,}** 💵", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='gamble', description='🎰 Gamble your VorkTek-Bucks')
@app_commands.describe(amount='Amount to gamble')
async def gamble(interaction: discord.Interaction, amount: int):
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    uid = str(interaction.user.id)
    
    if amount <= 0:
        await interaction.response.send_message("❌ Enter a positive amount!", ephemeral=True)
        return
    
    if data[uid].get('vorkteks', 0) < amount:
        await interaction.response.send_message("❌ Not enough VorkTek-Bucks!", ephemeral=True)
        return
    
    result = random.choice(['win', 'win', 'win', 'loss'])
    
    if result == 'win':
        data[uid]['vorkteks'] += amount
        msg = f"🎉 **YOU WIN!** +{amount:,} VorkTek-Bucks!\nTotal: **{data[uid]['vorkteks']:,}** 💵"
    else:
        data[uid]['vorkteks'] -= amount
        msg = f"😢 **YOU LOSE!** -{amount:,} VorkTek-Bucks!\nTotal: **{data[uid]['vorkteks']:,}** 💵"
    
    save_beyblade_data(data)
    embed = discord.Embed(title="🎰 Gamble Result", description=msg, color=discord.Color.green() if result == 'win' else discord.Color.red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='cards', description='📦 View collectible cards shop')
async def cards_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="📦 Collectible Cards", color=discord.Color.purple())
    for card_name, card_data in CARDS.items():
        embed.add_field(name=f"{card_data['emoji']} {card_name}", value=f"**{card_data['rarity'].upper()}**\nValue: {card_data['value']:,} VorkTek-Bucks\nUse: `/buy {card_name}`", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='buy', description='🛒 Buy a card')
@app_commands.describe(card='Card name (Churro Card, Ohio Card, Vox Card)')
async def buy_card(interaction: discord.Interaction, card: str):
    if card not in CARDS:
        await interaction.response.send_message(f"❌ Card not found. Available: {', '.join(CARDS.keys())}", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    uid = str(interaction.user.id)
    
    card_price = CARDS[card]['value']
    if data[uid].get('vorkteks', 0) < card_price:
        await interaction.response.send_message(f"❌ Need {card_price:,} VorkTek-Bucks, you have {data[uid].get('vorkteks', 0):,}!", ephemeral=True)
        return
    
    data[uid]['vorkteks'] -= card_price
    if card not in data[uid]['cards']:
        data[uid]['cards'][card] = 0
    data[uid]['cards'][card] += 1
    save_beyblade_data(data)
    
    embed = discord.Embed(title="✅ Card Purchased!", description=f"Bought **{card}** {CARDS[card]['emoji']}\nRemaining: **{data[uid]['vorkteks']:,}** VorkTek-Bucks", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='sell', description='💳 Sell a card')
@app_commands.describe(card='Card name (Churro Card, Ohio Card, Vox Card)')
async def sell_card(interaction: discord.Interaction, card: str):
    if card not in CARDS:
        await interaction.response.send_message(f"❌ Card not found!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    uid = str(interaction.user.id)
    
    if card not in data[uid]['cards'] or data[uid]['cards'][card] == 0:
        await interaction.response.send_message(f"❌ You don't have this card!", ephemeral=True)
        return
    
    card_value = CARDS[card]['value']
    sell_price = int(card_value * 0.8)
    
    data[uid]['vorkteks'] += sell_price
    data[uid]['cards'][card] -= 1
    save_beyblade_data(data)
    
    embed = discord.Embed(title="✅ Card Sold!", description=f"Sold **{card}** {CARDS[card]['emoji']}\nGot: **{sell_price:,}** VorkTek-Bucks\nTotal: **{data[uid]['vorkteks']:,}** VorkTek-Bucks", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='give', description='💸 Give VorkTek-Bucks to another user')
@app_commands.describe(user='User to give to', amount='Amount to give')
async def give_money(interaction: discord.Interaction, user: discord.User, amount: int):
    if amount <= 0:
        log_command_result('give', interaction.user, 'error', f"Invalid amount: {amount}")
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if user.id == interaction.user.id:
        log_command_result('give', interaction.user, 'error', f"Attempted self-transfer")
        await interaction.response.send_message("❌ You can't give money to yourself!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    data = init_user(data, user.id)
    
    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)
    
    if data[sender_id].get('vorkteks', 0) < amount:
        log_command_result('give', interaction.user, 'error', f"Insufficient funds: {data[sender_id].get('vorkteks', 0)} < {amount}")
        await interaction.response.send_message(f"❌ You only have {data[sender_id].get('vorkteks', 0):,} VorkTek-Bucks!", ephemeral=True)
        return
    
    data[sender_id]['vorkteks'] -= amount
    data[receiver_id]['vorkteks'] = data[receiver_id].get('vorkteks', 1000) + amount
    save_beyblade_data(data)
    
    log_command_result('give', interaction.user, 'success', f"Transferred {amount:,} to {user} | New balance: {data[sender_id]['vorkteks']:,}")
    embed = discord.Embed(title="✅ Money Transferred!", description=f"Gave **{amount:,}** VorkTek-Bucks to {user.mention}!\nYour balance: **{data[sender_id]['vorkteks']:,}** 💵", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='loan', description='💳 Request a loan from another user (10% interest)')
@app_commands.describe(user='User to loan from', amount='Amount to borrow')
async def request_loan(interaction: discord.Interaction, user: discord.User, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't loan from yourself!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, interaction.user.id)
    data = init_user(data, user.id)
    loans = load_loans()
    
    lender_id = str(user.id)
    borrower_id = str(interaction.user.id)
    
    if data[lender_id].get('vorkteks', 0) < amount:
        await interaction.response.send_message(f"❌ {user.mention} only has {data[lender_id].get('vorkteks', 0):,} VorkTek-Bucks!", ephemeral=True)
        return
    
    repay_amount = int(amount * 1.10)
    
    loan = {
        'id': len(loans['loans']) + 1,
        'lender': str(user.id),
        'borrower': borrower_id,
        'amount': amount,
        'repay_amount': repay_amount,
        'status': 'active',
        'timestamp': datetime.now().isoformat()
    }
    
    data[lender_id]['vorkteks'] -= amount
    data[borrower_id]['vorkteks'] = data[borrower_id].get('vorkteks', 1000) + amount
    loans['loans'].append(loan)
    
    save_beyblade_data(data)
    save_loans(loans)
    
    embed = discord.Embed(title="✅ Loan Approved!", description=f"**{amount:,}** VorkTek-Bucks borrowed from {user.mention}\nRepay amount (10% interest): **{repay_amount:,}** VorkTek-Bucks\nLoan ID: #{loan['id']}", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='repay', description='💳 Repay a loan')
@app_commands.describe(loan_id='Loan ID to repay')
async def repay_loan(interaction: discord.Interaction, loan_id: int):
    loans = load_loans()
    
    loan = None
    for l in loans['loans']:
        if l['id'] == loan_id:
            loan = l
            break
    
    if not loan:
        await interaction.response.send_message("❌ Loan not found!", ephemeral=True)
        return
    
    if loan['status'] != 'active':
        await interaction.response.send_message("❌ This loan is not active!", ephemeral=True)
        return
    
    if loan['borrower'] != str(interaction.user.id):
        await interaction.response.send_message("❌ This is not your loan!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, int(loan['lender']))
    data = init_user(data, int(loan['borrower']))
    
    borrower_id = loan['borrower']
    lender_id = loan['lender']
    repay_amount = loan['repay_amount']
    
    if data[borrower_id].get('vorkteks', 0) < repay_amount:
        await interaction.response.send_message(f"❌ You need {repay_amount:,} VorkTek-Bucks to repay, but you only have {data[borrower_id].get('vorkteks', 0):,}!", ephemeral=True)
        return
    
    data[borrower_id]['vorkteks'] -= repay_amount
    data[lender_id]['vorkteks'] = data[lender_id].get('vorkteks', 1000) + repay_amount
    
    loan['status'] = 'repaid'
    
    save_beyblade_data(data)
    save_loans(loans)
    
    lender = await bot.fetch_user(int(lender_id))
    embed = discord.Embed(title="✅ Loan Repaid!", description=f"Repaid **{repay_amount:,}** VorkTek-Bucks to {lender.mention}\nYour balance: **{data[borrower_id]['vorkteks']:,}** 💵", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='loans', description='💳 View your active loans')
async def view_loans(interaction: discord.Interaction):
    loans = load_loans()
    user_id = str(interaction.user.id)
    
    user_loans = [l for l in loans['loans'] if (l['borrower'] == user_id or l['lender'] == user_id) and l['status'] == 'active']
    
    if not user_loans:
        embed = discord.Embed(title="💳 Your Loans", description="You have no active loans!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    
    embed = discord.Embed(title="💳 Your Active Loans", color=discord.Color.gold())
    
    for loan in user_loans:
        if loan['borrower'] == user_id:
            role = "Borrowing"
            other_user = await bot.fetch_user(int(loan['lender']))
            embed.add_field(name=f"#{loan['id']} - {role}", value=f"From: {other_user.mention}\nAmount: **{loan['amount']:,}** VorkTek-Bucks\nRepay: **{loan['repay_amount']:,}** VorkTek-Bucks (10% interest)\nUse `/repay {loan['id']}` to repay", inline=False)
        else:
            role = "Lending"
            other_user = await bot.fetch_user(int(loan['borrower']))
            embed.add_field(name=f"#{loan['id']} - {role}", value=f"To: {other_user.mention}\nAmount: **{loan['amount']:,}** VorkTek-Bucks\nWill receive: **{loan['repay_amount']:,}** VorkTek-Bucks", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='admin-give', description='🔧 [ADMIN] Give VorkTek-Bucks')
@app_commands.describe(user='User to give to', amount='Amount')
async def admin_give(interaction: discord.Interaction, user: discord.User, amount: int):
    if not interaction.user.guild_permissions.administrator and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ Admin or server owner only!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, user.id)
    uid = str(user.id)
    
    data[uid]['vorkteks'] = data[uid].get('vorkteks', 1000) + amount
    save_beyblade_data(data)
    
    await interaction.response.send_message(f"✅ Gave {amount:,} VorkTek-Bucks to {user.mention}! Total: {data[uid]['vorkteks']:,}")

@bot.tree.command(name='admin-card', description='🔧 [ADMIN] Give card')
@app_commands.describe(user='User to give to', card='Card name')
async def admin_card(interaction: discord.Interaction, user: discord.User, card: str):
    if not interaction.user.guild_permissions.administrator and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ Admin or server owner only!", ephemeral=True)
        return
    
    if card not in CARDS:
        await interaction.response.send_message(f"❌ Card not found!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    data = init_user(data, user.id)
    uid = str(user.id)
    
    if card not in data[uid]['cards']:
        data[uid]['cards'][card] = 0
    data[uid]['cards'][card] += 1
    save_beyblade_data(data)
    
    await interaction.response.send_message(f"✅ Gave **{card}** {CARDS[card]['emoji']} to {user.mention}!")

@bot.tree.command(name='confess', description='🤐 Submit an anonymous confession')
@app_commands.describe(message='Your confession', penname='Optional pen name (leave blank for anonymous)')
async def confess(interaction: discord.Interaction, message: str, penname: str = None):
    confessions = load_confessions()
    
    confession = {
        'id': len(confessions['confessions']) + 1,
        'message': message,
        'penname': penname or 'Anonymous',
        'timestamp': datetime.now().isoformat()
    }
    
    confessions['confessions'].append(confession)
    save_confessions(confessions)
    
    embed = discord.Embed(title="✅ Confession Submitted!", description="Your confession has been posted anonymously.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='confessions', description='📖 View all confessions')
async def view_confessions(interaction: discord.Interaction):
    confessions = load_confessions()
    
    if not confessions['confessions']:
        embed = discord.Embed(title="📖 Confessions", description="No confessions yet. Be the first to confess!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    
    embed = discord.Embed(title="📖 All Confessions", color=discord.Color.purple())
    
    for conf in confessions['confessions'][-10:]:
        time_str = datetime.fromisoformat(conf['timestamp']).strftime('%m/%d %H:%M')
        embed.add_field(
            name=f"#{conf['id']} - {conf['penname']}",
            value=f"{conf['message']}\n*{time_str}*",
            inline=False
        )
    
    embed.set_footer(text=f"Showing latest 10 of {len(confessions['confessions'])} confessions")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='clear-confessions', description='🔧 [ADMIN] Delete all confessions')
async def clear_confessions(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ Admin or server owner only!", ephemeral=True)
        return
    
    confessions = {'confessions': []}
    save_confessions(confessions)
    
    await interaction.response.send_message("✅ All confessions have been cleared!")

@bot.tree.command(name='channel_set', description='🔧 [ADMIN] Set alert channel for online/offline notifications')
@app_commands.describe(channel_id='Channel ID for bot alerts')
async def channel_set(interaction: discord.Interaction, channel_id: int):
    if not interaction.user.guild_permissions.administrator and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ Admin or server owner only!", ephemeral=True)
        return
    
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message(f"❌ Channel with ID {channel_id} not found in this server!", ephemeral=True)
            return
        
        config = load_channel_config()
        config['alert_channel_id'] = channel_id
        save_channel_config(config)
        
        log_command_result('channel_set', interaction.user, 'success', f"Set alert channel to {channel.mention}")
        embed = discord.Embed(
            title="✅ Alert Channel Set!",
            description=f"Bot online/offline alerts will be sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=False)
        embed.add_field(name="What happens", value="When bot goes online: Gets alert with @everyone\nWhen bot goes offline: Gets alert with @everyone", inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        log_command_result('channel_set', interaction.user, 'error', f"Failed: {str(e)}")
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name='commands', description='📖 All commands')
async def commands_list(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Command List", color=discord.Color.blue())
    embed.add_field(name="⚔️ BEYBLADE GAME", value="`/spawn` - Spawn Beyblade\n`/catch` - Catch it\n`/collection` - View Beyblades\n`/battle` - Battle players\n`/stats` - View stats\n`/dex` - Pokedex", inline=False)
    embed.add_field(name="💰 VORKTEKS & CARDS", value="`/balance` - Check wallet\n`/daily` - Daily bonus\n`/gamble` - Gamble currency\n`/cards` - View cards\n`/buy` - Buy card\n`/sell` - Sell card", inline=False)
    embed.add_field(name="💸 MONEY TRANSFER & LOANS", value="`/give` - Give VorkTek-Bucks\n`/loan` - Borrow from someone\n`/repay` - Repay a loan\n`/loans` - View your loans", inline=False)
    embed.add_field(name="🤐 CONFESSIONS", value="`/confess` - Submit confession\n`/confessions` - View all confessions", inline=False)
    embed.add_field(name="🎵 MUSIC", value="`/meet_again` - Share \"Meet Again\" video\n`/play` - Music player info", inline=False)
    embed.add_field(name="🔧 ADMIN", value="`/channel_set` - Set alert channel\n`/admin-give` - Give VorkTek-Bucks\n`/admin-card` - Give card\n`/clear-confessions` - Clear all confessions", inline=False)
    embed.add_field(name="🎨 FUN & INFO", value="`/robux` - Fake robux\n`/verse` - Bible verse\n`/funfact` - Fun fact\n`/weather` - Weather\n`/youtube` - VorkilORCAL\n`/translate` - Translate\n`/console` - Logs", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
