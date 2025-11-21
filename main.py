import discord
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

bot = commands.Bot(command_prefix='m!', intents=intents)

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
    'source_address': '0.0.0.0'
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
        return cls(discord.FFmpegPCMAudio(filename, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn'), data=data)

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

@bot.command(name='translate')
async def translate(ctx, target_lang: str, *, text: str):
    """Translate text to any language. Usage: m!translate <language_code> <text>"""
    try:
        translation = translator.translate(text, dest=target_lang)
        
        embed = discord.Embed(
            title="Translation",
            color=discord.Color.blue()
        )
        embed.add_field(name=f"Original ({translation.src})", value=text, inline=False)
        embed.add_field(name=f"Translation ({target_lang})", value=translation.text, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Translation error: {str(e)}\n\nUse language codes like: en (English), es (Spanish), fr (French), de (German), ja (Japanese), ko (Korean), zh-cn (Chinese)")

@bot.command(name='robux')
async def robux(ctx, amount: int = None):
    """Generate fake robux as a joke!"""
    if amount is None:
        amount = random.randint(1, 1000000)
    
    responses = [
        f"💰 Congratulations {ctx.author.mention}! You just earned {amount:,} ROBUX! (Just kidding, we're broke 😂)",
        f"🎉 JACKPOT! {amount:,} ROBUX added to your account! (In your dreams 💭)",
        f"⚡ SUPER RARE DROP! {amount:,} ROBUX! (Too bad it's not real 🤣)",
        f"🌟 WOW! The Robux gods have blessed you with {amount:,} ROBUX! (Psych! 😜)",
        f"🎊 LEGENDARY! You won {amount:,} ROBUX! (Now wake up ⏰)",
        f"💎 ULTRA RARE! {amount:,} ROBUX deposited! (In an alternate universe 🌌)",
    ]
    
    await ctx.send(random.choice(responses))

@bot.command(name='verse')
async def verse(ctx):
    """Get a random Bible verse"""
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
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't fetch a Bible verse right now. Please try again later.")
    except Exception as e:
        await ctx.send(f"Error fetching Bible verse: {str(e)}")

@bot.command(name='play')
async def play(ctx, url: str):
    """Play music from YouTube. Usage: m!play <youtube_url>"""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command!")
        return
    
    channel = ctx.author.voice.channel
    
    if ctx.guild.id not in music_players:
        music_players[ctx.guild.id] = MusicPlayer()
    
    player = music_players[ctx.guild.id]
    
    if player.voice_client is None:
        player.voice_client = await channel.connect()
    elif player.voice_client.channel != channel:
        await player.voice_client.move_to(channel)
    
    async with ctx.typing():
        try:
            source = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            player.current = source
            
            if player.voice_client.is_playing():
                player.voice_client.stop()
            
            player.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop
            ))
            
            await ctx.send(f'🎵 Now playing: **{source.title}**')
        except Exception as e:
            await ctx.send(f"Error playing audio: {str(e)}")

async def play_next(ctx):
    if ctx.guild.id in music_players:
        player = music_players[ctx.guild.id]
        if player.loop and player.current:
            player.voice_client.play(player.current, after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop
            ))

@bot.command(name='loop')
async def loop(ctx):
    """Toggle loop for the current song"""
    if ctx.guild.id not in music_players:
        await ctx.send("No music is playing!")
        return
    
    player = music_players[ctx.guild.id]
    player.loop = not player.loop
    
    if player.loop:
        await ctx.send("🔁 Looping enabled!")
    else:
        await ctx.send("➡️ Looping disabled!")

@bot.command(name='stop')
async def stop(ctx):
    """Stop playing music"""
    if ctx.guild.id not in music_players:
        await ctx.send("No music is playing!")
        return
    
    player = music_players[ctx.guild.id]
    
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.stop()
        player.loop = False
        player.current = None
        await ctx.send("⏹️ Stopped playing music!")
    else:
        await ctx.send("No music is currently playing!")

@bot.command(name='leave')
async def leave(ctx):
    """Leave the voice channel"""
    if ctx.guild.id not in music_players:
        await ctx.send("I'm not in a voice channel!")
        return
    
    player = music_players[ctx.guild.id]
    
    if player.voice_client:
        await player.voice_client.disconnect()
        player.voice_client = None
        player.current = None
        player.loop = False
        await ctx.send("👋 Left the voice channel!")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command(name='spawn')
async def spawn(ctx):
    """Spawn a random Beyblade! (Similar to Pokétwo spawning)"""
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
        description=f"A **{rarity.upper()}** Beyblade has spawned!\nType `m!catch <name>` to catch it!",
        color=discord.Color.green() if rarity == 'common' else discord.Color.blue() if rarity == 'rare' else discord.Color.gold()
    )
    embed.add_field(name="Name", value=beyblade['name'], inline=False)
    embed.add_field(name="Stats", value=f"⚔️ Power: {beyblade['power']}\n🛡️ Defense: {beyblade['defense']}\n⏱️ Stamina: {beyblade['stamina']}", inline=False)
    
    await ctx.send(embed=embed)
    
    ctx.bot.last_spawn = {
        'beyblade': beyblade,
        'rarity': rarity,
        'channel': ctx.channel.id
    }

@bot.command(name='catch')
async def catch(ctx, *, name: str):
    """Catch the spawned Beyblade"""
    if not hasattr(bot, 'last_spawn') or bot.last_spawn['channel'] != ctx.channel.id:
        await ctx.send("There's no Beyblade to catch right now!")
        return
    
    beyblade = bot.last_spawn['beyblade']
    
    if name.lower() != beyblade['name'].lower():
        await ctx.send(f"That's not the right name! Try again.")
        return
    
    data = load_beyblade_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data:
        data[user_id] = {
            'beyblades': [],
            'wins': 0,
            'losses': 0
        }
    
    data[user_id]['beyblades'].append({
        **beyblade,
        'rarity': bot.last_spawn['rarity'],
        'level': 1,
        'xp': 0
    })
    
    save_beyblade_data(data)
    
    await ctx.send(f"🎉 {ctx.author.mention} caught **{beyblade['name']}**!")
    del bot.last_spawn

@bot.command(name='collection')
async def collection(ctx):
    """View your Beyblade collection"""
    data = load_beyblade_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data or not data[user_id]['beyblades']:
        await ctx.send("You don't have any Beyblades yet! Use `m!spawn` to find some.")
        return
    
    beyblades = data[user_id]['beyblades']
    
    embed = discord.Embed(
        title=f"{ctx.author.name}'s Beyblade Collection",
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
    
    await ctx.send(embed=embed)

@bot.command(name='battle')
async def battle(ctx, opponent: discord.Member):
    """Challenge another player to a Beyblade battle!"""
    if opponent.bot:
        await ctx.send("You can't battle a bot!")
        return
    
    if opponent.id == ctx.author.id:
        await ctx.send("You can't battle yourself!")
        return
    
    data = load_beyblade_data()
    user_id = str(ctx.author.id)
    opp_id = str(opponent.id)
    
    if user_id not in data or not data[user_id]['beyblades']:
        await ctx.send("You don't have any Beyblades! Use `m!spawn` to catch some.")
        return
    
    if opp_id not in data or not data[opp_id]['beyblades']:
        await ctx.send(f"{opponent.name} doesn't have any Beyblades!")
        return
    
    player_bey = data[user_id]['beyblades'][0]
    opponent_bey = data[opp_id]['beyblades'][0]
    
    player_total = player_bey['power'] + player_bey['defense'] + player_bey['stamina']
    opponent_total = opponent_bey['power'] + opponent_bey['defense'] + opponent_bey['stamina']
    
    player_total += random.randint(-10, 10)
    opponent_total += random.randint(-10, 10)
    
    embed = discord.Embed(title="⚔️ Beyblade Battle!", color=discord.Color.red())
    embed.add_field(
        name=f"{ctx.author.name}'s {player_bey['name']}",
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
    
    await ctx.send(embed=embed)
    await asyncio.sleep(2)
    
    if player_total > opponent_total:
        winner = ctx.author
        winner_id = user_id
        loser_id = opp_id
        result_msg = f"🎊 {ctx.author.mention} wins the battle!"
    elif opponent_total > player_total:
        winner = opponent
        winner_id = opp_id
        loser_id = user_id
        result_msg = f"🎊 {opponent.mention} wins the battle!"
    else:
        result_msg = "🤝 It's a tie!"
        await ctx.send(result_msg)
        return
    
    data[winner_id]['wins'] = data[winner_id].get('wins', 0) + 1
    data[loser_id]['losses'] = data[loser_id].get('losses', 0) + 1
    
    save_beyblade_data(data)
    
    await ctx.send(result_msg)

@bot.command(name='stats')
async def stats(ctx, member: discord.Member = None):
    """View battle stats"""
    member = member or ctx.author
    data = load_beyblade_data()
    user_id = str(member.id)
    
    if user_id not in data:
        await ctx.send(f"{member.name} hasn't started their Beyblade journey yet!")
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
    
    await ctx.send(embed=embed)

@bot.command(name='commands')
async def commands_list(ctx):
    """Show all available commands"""
    embed = discord.Embed(
        title="🤖 Discord Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🌍 Translation",
        value="`m!translate <lang_code> <text>` - Translate text to any language",
        inline=False
    )
    
    embed.add_field(
        name="💰 Fun",
        value="`m!robux [amount]` - Generate fake robux as a joke!",
        inline=False
    )
    
    embed.add_field(
        name="📖 Bible",
        value="`m!verse` - Get a random Bible verse",
        inline=False
    )
    
    embed.add_field(
        name="🎵 Music Player",
        value="`m!play <youtube_url>` - Play music from YouTube\n"
              "`m!loop` - Toggle loop for current song\n"
              "`m!stop` - Stop playing music\n"
              "`m!leave` - Leave voice channel",
        inline=False
    )
    
    embed.add_field(
        name="⚔️ Beyblade Game",
        value="`m!spawn` - Spawn a random Beyblade\n"
              "`m!catch <name>` - Catch a spawned Beyblade\n"
              "`m!collection` - View your collection\n"
              "`m!battle @user` - Battle another player\n"
              "`m!stats [@user]` - View battle stats",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Auto-Moderation",
        value="Automatically mutes members for 5 minutes when they use inappropriate language",
        inline=False
    )
    
    embed.set_footer(text="Prefix: m! | Use m!commands to see this message again")
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
