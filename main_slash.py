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
]

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

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Beyblades spin | /commands"))

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

@bot.tree.command(name='translate', description='Translate text')
@app_commands.describe(lang='Language code (en, es, fr, de, etc)', text='Text to translate')
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

@bot.tree.command(name='commands', description='📖 All commands')
async def commands_list(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Command List", color=discord.Color.blue())
    embed.add_field(name="⚔️ BEYBLADE GAME", value="`/spawn` - Spawn random Beyblade\n`/catch` - Catch it\n`/collection` - View Beyblades\n`/battle` - Battle players\n`/stats` - View stats\n`/dex` - Pokedex", inline=False)
    embed.add_field(name="🎨 FUN", value="`/robux` - Fake robux\n`/verse` - Bible verse\n`/funfact` - Fun fact\n`/mc-get` - Minecraft\n`/translate` - Translate\n`/console` - Logs", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
