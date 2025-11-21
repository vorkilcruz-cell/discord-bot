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
        print("Slash commands synced!")

bot = MyBot()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required. Please set it in your environment or Replit Secrets.")

translator = Translator()

CURSE_WORDS = ['fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard', 'crap', 'hell']

BEYBLADE_FILE = 'beyblade_data.json'

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if data and 'entries' in data:
            data = data['entries'][0]

        if not data:
            raise Exception("Could not extract video data")
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -af loudnorm'
        }
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicPlayer:
    def __init__(self):
        self.queue = []
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
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if any(word in message.content.lower() for word in CURSE_WORDS):
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=5)
            await message.author.timeout(timeout_until, reason="Using inappropriate language")
            await message.channel.send(f'{message.author.mention} has been muted for 5 minutes for using inappropriate language.')
            await message.delete()
        except discord.Forbidden:
            await message.channel.send("I don't have permission to timeout members.")
        except Exception as e:
            print(f"Error timing out member: {e}")
            await message.channel.send(f"Failed to timeout user: {str(e)}")
    
    await bot.process_commands(message)

@bot.tree.command(name='translate', description='Translate text to any language')
@app_commands.describe(
    target_lang='Target language code (e.g., en, es, fr, de)',
    text='Text to translate'
)
async def translate(interaction: discord.Interaction, target_lang: str, text: str):
    try:
        translation = translator.translate(text, dest=target_lang)
        
        embed = discord.Embed(
            title="Translation",
            color=discord.Color.blue()
        )
        embed.add_field(name=f"Original ({translation.src})", value=text, inline=False)
        embed.add_field(name=f"Translation ({target_lang})", value=translation.text, inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(
            f"Translation error: {str(e)}\n\nUse language codes like: en (English), es (Spanish), fr (French), de (German), ja (Japanese), ko (Korean), zh-cn (Chinese)",
            ephemeral=True
        )

@bot.tree.command(name='robux', description='Generate fake robux as a joke!')
@app_commands.describe(amount='Amount of robux to generate (optional)')
async def robux(interaction: discord.Interaction, amount: int = None):
    if amount is None:
        amount = random.randint(1, 1000000)
    
    responses = [
        f"💰 Congratulations {interaction.user.mention}! You just earned {amount:,} ROBUX! (Just kidding, we're broke 😂)",
        f"🎉 JACKPOT! {amount:,} ROBUX added to your account! (In your dreams 💭)",
        f"⚡ SUPER RARE DROP! {amount:,} ROBUX! (Too bad it's not real 🤣)",
        f"🌟 WOW! The Robux gods have blessed you with {amount:,} ROBUX! (Psych! 😜)",
        f"🎊 LEGENDARY! You won {amount:,} ROBUX! (Now wake up ⏰)",
        f"💎 ULTRA RARE! {amount:,} ROBUX deposited! (In an alternate universe 🌌)",
    ]
    
    await interaction.response.send_message(random.choice(responses))

@bot.tree.command(name='verse', description='Get a random Bible verse')
async def verse(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        response = requests.get('https://labs.bible.org/api/?passage=random&type=json')
        if response.status_code == 200:
            verse_data = response.json()[0]
            
            embed = discord.Embed(
                title=f"{verse_data['bookname']} {verse_data['chapter']}:{verse_data['verse']}",
                description=verse_data['text'],
                color=discord.Color.gold()
            )
            embed.set_footer(text="Daily Bible Verse")
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Couldn't fetch a Bible verse right now. Please try again later.")
    except Exception as e:
        await interaction.followup.send(f"Error fetching Bible verse: {str(e)}")

@bot.tree.command(name='play', description='Play music from YouTube')
@app_commands.describe(url='YouTube URL to play')
async def play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to use this command!", ephemeral=True)
        return
    
    channel = interaction.user.voice.channel
    
    if interaction.guild.id not in music_players:
        music_players[interaction.guild.id] = MusicPlayer()
    
    player = music_players[interaction.guild.id]
    
    await interaction.response.defer()
    
    try:
        if player.voice_client is None:
            player.voice_client = await channel.connect()
        elif player.voice_client.channel != channel:
            await player.voice_client.move_to(channel)
        
        source = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        player.current = source
        
        if player.voice_client.is_playing():
            player.voice_client.stop()
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            if player.loop and player.current:
                player.voice_client.play(player.current, after=after_playing)
        
        player.voice_client.play(source, after=after_playing)
        
        await interaction.followup.send(f'🎵 Now playing: **{source.title}**')
    except Exception as e:
        await interaction.followup.send(f"Error playing audio: {str(e)}")

@bot.tree.command(name='loop', description='Toggle loop for the current song')
async def loop_command(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("No music is playing!", ephemeral=True)
        return
    
    player = music_players[interaction.guild.id]
    player.loop = not player.loop
    
    if player.loop:
        await interaction.response.send_message("🔁 Looping enabled!")
    else:
        await interaction.response.send_message("➡️ Looping disabled!")

@bot.tree.command(name='stop', description='Stop playing music')
async def stop(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("No music is playing!", ephemeral=True)
        return
    
    player = music_players[interaction.guild.id]
    
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.stop()
        player.loop = False
        player.current = None
        await interaction.response.send_message("⏹️ Stopped playing music!")
    else:
        await interaction.response.send_message("No music is currently playing!", ephemeral=True)

@bot.tree.command(name='leave', description='Leave the voice channel')
async def leave(interaction: discord.Interaction):
    if interaction.guild.id not in music_players:
        await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)
        return
    
    player = music_players[interaction.guild.id]
    
    if player.voice_client:
        await player.voice_client.disconnect()
        player.voice_client = None
        player.current = None
        player.loop = False
        await interaction.response.send_message("👋 Left the voice channel!")
    else:
        await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)

@bot.tree.command(name='spawn', description='Spawn a random Beyblade!')
async def spawn(interaction: discord.Interaction):
    rarity_roll = random.randint(1, 100)
    
    if rarity_roll <= 60:
        rarity = 'common'
    elif rarity_roll <= 90:
        rarity = 'rare'
    else:
        rarity = 'legendary'
    
    beyblade = random.choice(BEYBLADES[rarity])
    
    embed = discord.Embed(
        title="A wild Beyblade appeared!",
        description=f"A **{rarity.upper()}** Beyblade has spawned!\nType `/catch <name>` to catch it!",
        color=discord.Color.green() if rarity == 'common' else discord.Color.blue() if rarity == 'rare' else discord.Color.gold()
    )
    embed.add_field(name="Name", value=beyblade['name'], inline=False)
    embed.add_field(name="Stats", value=f"⚔️ Power: {beyblade['power']}\n🛡️ Defense: {beyblade['defense']}\n⏱️ Stamina: {beyblade['stamina']}", inline=False)
    
    await interaction.response.send_message(embed=embed)
    
    if not hasattr(bot, 'last_spawns'):
        bot.last_spawns = {}
    
    bot.last_spawns[interaction.channel.id] = {
        'beyblade': beyblade,
        'rarity': rarity,
        'channel': interaction.channel.id
    }

@bot.tree.command(name='catch', description='Catch the spawned Beyblade')
@app_commands.describe(name='Name of the Beyblade to catch')
async def catch(interaction: discord.Interaction, name: str):
    if not hasattr(bot, 'last_spawns') or interaction.channel.id not in bot.last_spawns:
        await interaction.response.send_message("There's no Beyblade to catch right now!", ephemeral=True)
        return
    
    spawn_data = bot.last_spawns[interaction.channel.id]
    beyblade = spawn_data['beyblade']
    
    if name.lower() != beyblade['name'].lower():
        await interaction.response.send_message(f"That's not the right name! Try again.", ephemeral=True)
        return
    
    data = load_beyblade_data()
    user_id = str(interaction.user.id)
    
    if user_id not in data:
        data[user_id] = {
            'beyblades': [],
            'wins': 0,
            'losses': 0
        }
    
    data[user_id]['beyblades'].append({
        **beyblade,
        'rarity': spawn_data['rarity'],
        'level': 1,
        'xp': 0
    })
    
    save_beyblade_data(data)
    
    await interaction.response.send_message(f"🎉 {interaction.user.mention} caught **{beyblade['name']}**!")
    del bot.last_spawns[interaction.channel.id]

@bot.tree.command(name='collection', description='View your Beyblade collection')
async def collection(interaction: discord.Interaction):
    data = load_beyblade_data()
    user_id = str(interaction.user.id)
    
    if user_id not in data or not data[user_id]['beyblades']:
        await interaction.response.send_message("You don't have any Beyblades yet! Use `/spawn` to find some.", ephemeral=True)
        return
    
    beyblades = data[user_id]['beyblades']
    
    embed = discord.Embed(
        title=f"{interaction.user.name}'s Beyblade Collection",
        description=f"Total Beyblades: {len(beyblades)}",
        color=discord.Color.purple()
    )
    
    for i, bey in enumerate(beyblades[:10], 1):
        embed.add_field(
            name=f"{i}. {bey['name']} (Level {bey['level']})",
            value=f"Rarity: {bey['rarity'].upper()}\n⚔️ {bey['power']} | 🛡️ {bey['defense']} | ⏱️ {bey['stamina']}",
            inline=False
        )
    
    if len(beyblades) > 10:
        embed.set_footer(text=f"Showing 10 of {len(beyblades)} Beyblades")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='battle', description='Challenge another player to a Beyblade battle!')
@app_commands.describe(opponent='The player to challenge')
async def battle(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot:
        await interaction.response.send_message("You can't battle a bot!", ephemeral=True)
        return
    
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("You can't battle yourself!", ephemeral=True)
        return
    
    data = load_beyblade_data()
    user_id = str(interaction.user.id)
    opp_id = str(opponent.id)
    
    if user_id not in data or not data[user_id]['beyblades']:
        await interaction.response.send_message("You don't have any Beyblades! Use `/spawn` to catch some.", ephemeral=True)
        return
    
    if opp_id not in data or not data[opp_id]['beyblades']:
        await interaction.response.send_message(f"{opponent.name} doesn't have any Beyblades!", ephemeral=True)
        return
    
    player_bey = data[user_id]['beyblades'][0]
    opponent_bey = data[opp_id]['beyblades'][0]
    
    player_total = player_bey['power'] + player_bey['defense'] + player_bey['stamina']
    opponent_total = opponent_bey['power'] + opponent_bey['defense'] + opponent_bey['stamina']
    
    player_total += random.randint(-10, 10)
    opponent_total += random.randint(-10, 10)
    
    embed = discord.Embed(title="⚔️ Beyblade Battle!", color=discord.Color.red())
    embed.add_field(
        name=f"{interaction.user.name}'s {player_bey['name']}",
        value=f"Power: {player_total}",
        inline=True
    )
    embed.add_field(
        name="VS",
        value="⚡",
        inline=True
    )
    embed.add_field(
        name=f"{opponent.name}'s {opponent_bey['name']}",
        value=f"Power: {opponent_total}",
        inline=True
    )
    
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(2)
    
    if player_total > opponent_total:
        winner_id = user_id
        loser_id = opp_id
        result_msg = f"🎊 {interaction.user.mention} wins the battle!"
    elif opponent_total > player_total:
        winner_id = opp_id
        loser_id = user_id
        result_msg = f"🎊 {opponent.mention} wins the battle!"
    else:
        result_msg = "🤝 It's a tie!"
        await interaction.followup.send(result_msg)
        return
    
    data[winner_id]['wins'] = data[winner_id].get('wins', 0) + 1
    data[loser_id]['losses'] = data[loser_id].get('losses', 0) + 1
    
    save_beyblade_data(data)
    
    await interaction.followup.send(result_msg)

@bot.tree.command(name='stats', description='View battle stats')
@app_commands.describe(member='The member to view stats for (optional)')
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_beyblade_data()
    user_id = str(member.id)
    
    if user_id not in data:
        await interaction.response.send_message(f"{member.name} hasn't started their Beyblade journey yet!", ephemeral=True)
        return
    
    user_data = data[user_id]
    wins = user_data.get('wins', 0)
    losses = user_data.get('losses', 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    embed = discord.Embed(
        title=f"{member.name}'s Battle Stats",
        color=discord.Color.green()
    )
    embed.add_field(name="Wins", value=str(wins), inline=True)
    embed.add_field(name="Losses", value=str(losses), inline=True)
    embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
    embed.add_field(name="Total Beyblades", value=str(len(user_data['beyblades'])), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='commands', description='Show all available commands')
async def commands_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Discord Bot Commands",
        description="Here are all the available slash commands:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🌍 Translation",
        value="`/translate <lang_code> <text>` - Translate text to any language",
        inline=False
    )
    
    embed.add_field(
        name="💰 Fun",
        value="`/robux [amount]` - Generate fake robux as a joke!",
        inline=False
    )
    
    embed.add_field(
        name="📖 Bible",
        value="`/verse` - Get a random Bible verse",
        inline=False
    )
    
    embed.add_field(
        name="🎵 Music Player",
        value="`/play <youtube_url>` - Play music from YouTube\n"
              "`/loop` - Toggle loop for current song\n"
              "`/stop` - Stop playing music\n"
              "`/leave` - Leave voice channel",
        inline=False
    )
    
    embed.add_field(
        name="⚔️ Beyblade Game",
        value="`/spawn` - Spawn a random Beyblade\n"
              "`/catch <name>` - Catch a spawned Beyblade\n"
              "`/collection` - View your collection\n"
              "`/battle @user` - Battle another player\n"
              "`/stats [@user]` - View battle stats",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Auto-Moderation",
        value="Automatically mutes members for 5 minutes when they use inappropriate language",
        inline=False
    )
    
    embed.set_footer(text="All commands use slash commands (/) | Have fun!")
    
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
