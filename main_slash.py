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

FFMPEG_PATH = '/nix/store/15alrig3q4xjwfc3rbnsgj4bj29zn6ww-ffmpeg-7.1.1-bin/bin/ffmpeg'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synced!")

bot = MyBot()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN required")

translator = Translator()
CURSE_WORDS = ['fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard', 'crap', 'hell']
BEYBLADE_FILE = 'beyblade_data.json'

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
    "Cleopatra lived closer to the moon landing than to the building of the Great Pyramid.",
    "Sloths only defecate once a week.",
    "A group of pugs is called a 'grumble'.",
    "The smell of fresh-cut grass is actually a plant's distress call.",
    "Cats have a third eyelid called the nictitating membrane.",
    "A shrimp's heart is in its head.",
    "Squirrels can't taste sweetness.",
    "The Eiffel Tower grows about 6 inches taller in the summer due to thermal expansion.",
    "Penguins have knees - they're just hidden under their feathers!",
    "A group of jellyfish is called a 'bloom' or 'swarm'.",
]

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'socket_timeout': 15,
    'postprocessors': [{
        'key': 'FFmpegMetadata',
    }],
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            print(f"🎵 Extracting: {url}")
            data = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False)),
                timeout=20.0
            )
            
            if 'entries' in data:
                data = data['entries'][0]
                
            if not data or not data.get('url'):
                raise Exception("No audio stream found")
            
            print(f"✅ Got stream: {data.get('title', 'Unknown')}")
            
            ffmpeg_audio = discord.FFmpegPCMAudio(
                data['url'],
                executable=FFMPEG_PATH,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                options='-vn -bufsize 512k'
            )
            return cls(ffmpeg_audio, data=data)
        except asyncio.TimeoutError:
            raise Exception("⏱️ Extraction timeout - URL may be invalid")
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

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

BEYBLADES = {
    'common': [
        {'name': 'Storm Pegasus', 'power': 50, 'defense': 30, 'stamina': 40},
        {'name': 'Rock Leone', 'power': 35, 'defense': 55, 'stamina': 30},
        {'name': 'Flame Sagittario', 'power': 45, 'defense': 25, 'stamina': 50},
        {'name': 'Dark Wolf', 'power': 40, 'defense': 35, 'stamina': 45},
    ],
    'rare': [
        {'name': 'Lightning L-Drago', 'power': 70, 'defense': 40, 'stamina': 50},
        {'name': 'Earth Eagle', 'power': 55, 'defense': 60, 'stamina': 55},
        {'name': 'Gravity Perseus', 'power': 65, 'defense': 50, 'stamina': 60},
    ],
    'legendary': [
        {'name': 'Big Bang Pegasus', 'power': 90, 'defense': 70, 'stamina': 85},
        {'name': 'Meteo L-Drago', 'power': 95, 'defense': 65, 'stamina': 80},
        {'name': 'Phantom Orion', 'power': 75, 'defense': 80, 'stamina': 100},
    ]
}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/commands | Music ready"))

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

@bot.tree.command(name='play', description='Play YouTube audio')
@app_commands.describe(url='YouTube URL')
async def play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Join a voice channel first!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        channel = interaction.user.voice.channel
        if interaction.guild.id not in music_players:
            music_players[interaction.guild.id] = MusicPlayer()
        
        player = music_players[interaction.guild.id]
        
        if player.voice_client is None:
            print(f"🔗 Connecting to {channel.name}")
            player.voice_client = await channel.connect()
        elif player.voice_client.channel != channel:
            await player.voice_client.move_to(channel)
        
        print(f"▶️ Loading: {url}")
        source = await YTDLSource.from_url(url, loop=bot.loop)
        player.current = source
        
        if player.voice_client.is_playing():
            player.voice_client.stop()
        
        def after_play(error):
            if error:
                print(f"❌ Playback error: {error}")
            if player.loop and player.current:
                try:
                    player.voice_client.play(player.current, after=after_play)
                except:
                    pass
        
        player.voice_client.play(source, after=after_play)
        await interaction.followup.send(f'🎵 **{source.title}**')
        
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ Play error: {error_msg}")
        await interaction.followup.send(f"❌ Error: {error_msg}")

@bot.tree.command(name='stop', description='Stop music')
async def stop(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("❌ Not playing", ephemeral=True)
        return
    player = music_players[interaction.guild.id]
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.stop()
        player.loop = False
        await interaction.response.send_message("⏹️ Stopped")
    else:
        await interaction.response.send_message("❌ Nothing playing", ephemeral=True)

@bot.tree.command(name='loop', description='Toggle loop')
async def loop_cmd(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("❌ Not playing", ephemeral=True)
        return
    player = music_players[interaction.guild.id]
    player.loop = not player.loop
    await interaction.response.send_message(f"{'🔁 Loop ON' if player.loop else '➡️ Loop OFF'}")

@bot.tree.command(name='leave', description='Leave voice')
async def leave(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("❌ Not in VC", ephemeral=True)
        return
    player = music_players[interaction.guild.id]
    if player.voice_client:
        await player.voice_client.disconnect()
        player.voice_client = None
        await interaction.response.send_message("👋 Left")
    else:
        await interaction.response.send_message("❌ Not in VC", ephemeral=True)

@bot.tree.command(name='translate', description='Translate text')
@app_commands.describe(lang='Language code', text='Text')
async def translate(interaction: discord.Interaction, lang: str, text: str):
    try:
        result = translator.translate(text, dest=lang)
        embed = discord.Embed(title="🌐 Translation", color=discord.Color.blue())
        embed.add_field(name=f"Original", value=text, inline=False)
        embed.add_field(name=f"{lang.upper()}", value=result.text, inline=False)
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
        result = subprocess.run(['tail', '-30', '/tmp/logs/Discord_Bot_20251121_094042_052.log'], capture_output=True, text=True, timeout=5)
        logs = result.stdout or "No logs"
        if len(logs) > 1900:
            logs = logs[-1900:]
        embed = discord.Embed(title="📋 Console", description=f"```\n{logs}\n```", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Error", ephemeral=True)

@bot.tree.command(name='spawn', description='Spawn Beyblade')
async def spawn(interaction: discord.Interaction):
    roll = random.randint(1, 100)
    rarity = 'common' if roll <= 60 else 'rare' if roll <= 90 else 'legendary'
    bey = random.choice(BEYBLADES[rarity])
    embed = discord.Embed(title="⚡ Beyblade Appeared!", description=f"**{rarity.upper()}** - Type `/catch {bey['name']}`", color=discord.Color.green())
    embed.add_field(name=bey['name'], value=f"⚔️ {bey['power']} | 🛡️ {bey['defense']} | ⏱️ {bey['stamina']}")
    await interaction.response.send_message(embed=embed)
    if not hasattr(bot, 'spawns'):
        bot.spawns = {}
    bot.spawns[interaction.channel.id] = {'bey': bey, 'rarity': rarity}

@bot.tree.command(name='catch', description='Catch Beyblade')
@app_commands.describe(name='Beyblade name')
async def catch(interaction: discord.Interaction, name: str):
    if not hasattr(bot, 'spawns') or interaction.channel.id not in bot.spawns:
        await interaction.response.send_message("❌ No spawn", ephemeral=True)
        return
    spawn = bot.spawns[interaction.channel.id]
    if name.lower() != spawn['bey']['name'].lower():
        await interaction.response.send_message(f"❌ Wrong! It was {spawn['bey']['name']}", ephemeral=True)
        return
    data = load_beyblade_data()
    uid = str(interaction.user.id)
    if uid not in data:
        data[uid] = {'beyblades': [], 'wins': 0, 'losses': 0}
    data[uid]['beyblades'].append({**spawn['bey'], 'rarity': spawn['rarity'], 'level': 1})
    save_beyblade_data(data)
    await interaction.response.send_message(f"🎉 Caught **{spawn['bey']['name']}**!")
    del bot.spawns[interaction.channel.id]

@bot.tree.command(name='collection', description='Your Beyblades')
async def collection(interaction: discord.Interaction):
    data = load_beyblade_data()
    uid = str(interaction.user.id)
    if uid not in data or not data[uid]['beyblades']:
        await interaction.response.send_message("❌ No Beyblades", ephemeral=True)
        return
    beys = data[uid]['beyblades']
    embed = discord.Embed(title=f"{interaction.user.name}'s Collection", description=f"Total: {len(beys)}", color=discord.Color.purple())
    for i, b in enumerate(beys[:10], 1):
        embed.add_field(name=f"{i}. {b['name']}", value=f"{b['rarity'].upper()} | ⚔️ {b['power']} | 🛡️ {b['defense']} | ⏱️ {b['stamina']}", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='battle', description='Battle someone')
@app_commands.describe(opponent='Player to battle')
async def battle(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot or opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ Invalid opponent", ephemeral=True)
        return
    data = load_beyblade_data()
    uid, oid = str(interaction.user.id), str(opponent.id)
    if uid not in data or not data[uid]['beyblades'] or oid not in data or not data[oid]['beyblades']:
        await interaction.response.send_message("❌ Both need Beyblades", ephemeral=True)
        return
    p, o = data[uid]['beyblades'][0], data[oid]['beyblades'][0]
    pt = p['power'] + p['defense'] + p['stamina'] + random.randint(-10, 10)
    ot = o['power'] + o['defense'] + o['stamina'] + random.randint(-10, 10)
    embed = discord.Embed(title="⚔️ Battle!", color=discord.Color.red())
    embed.add_field(name=f"{interaction.user.name}'s {p['name']}", value=f"Power: {pt}", inline=True)
    embed.add_field(name="VS", value="⚡", inline=True)
    embed.add_field(name=f"{opponent.name}'s {o['name']}", value=f"Power: {ot}", inline=True)
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(2)
    if pt > ot:
        winner, loser = uid, oid
        msg = f"🎊 {interaction.user.mention} wins!"
    elif ot > pt:
        winner, loser = oid, uid
        msg = f"🎊 {opponent.mention} wins!"
    else:
        await interaction.followup.send("🤝 Tie!")
        return
    data[winner]['wins'] = data[winner].get('wins', 0) + 1
    data[loser]['losses'] = data[loser].get('losses', 0) + 1
    save_beyblade_data(data)
    await interaction.followup.send(msg)

@bot.tree.command(name='stats', description='Battle stats')
@app_commands.describe(member='Player (optional)')
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_beyblade_data()
    uid = str(member.id)
    if uid not in data:
        await interaction.response.send_message(f"❌ No stats for {member.name}", ephemeral=True)
        return
    w, l = data[uid].get('wins', 0), data[uid].get('losses', 0)
    wr = (w / (w + l) * 100) if (w + l) > 0 else 0
    embed = discord.Embed(title=f"{member.name}'s Stats", color=discord.Color.green())
    embed.add_field(name="Wins", value=str(w), inline=True)
    embed.add_field(name="Losses", value=str(l), inline=True)
    embed.add_field(name="Rate", value=f"{wr:.1f}%", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='commands', description='All commands')
async def commands_list(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Commands", color=discord.Color.blue())
    embed.add_field(name="🎵 Music", value="`/play` `/loop` `/stop` `/leave`", inline=False)
    embed.add_field(name="⚔️ Beyblade", value="`/spawn` `/catch` `/collection` `/battle` `/stats`", inline=False)
    embed.add_field(name="Fun", value="`/robux` `/verse` `/funfact` `/mc-get` `/translate` `/console`", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
