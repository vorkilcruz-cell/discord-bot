# Discord Bot with Multiple Features

A feature-rich Discord bot with translation, moderation, music playback, Bible verses, and a Beyblade collection game.

## Features

### 🌍 Translation
- **Command**: `m!translate <language_code> <text>`
- Translate text from any language to any language using Google Translate
- Auto-detects source language
- Supports all major languages (en, es, fr, de, ja, ko, zh-cn, etc.)

### 💰 Fake Robux Generator
- **Command**: `m!robux [amount]`
- Generates fake robux as a fun joke
- Random humorous responses
- Optional amount parameter

### 🛡️ Auto-Moderation
- Automatically detects and moderates inappropriate language
- Mutes users for 5 minutes when curse words are used
- Deletes the offending message
- Sends a notification to the channel

### 📖 Daily Bible Verse
- **Command**: `m!verse`
- Fetches random Bible verses from Bible.org API
- Beautiful embed formatting
- Shows book, chapter, verse, and text

### 🎵 Music Player
Play music from YouTube in voice channels:
- **`m!play <youtube_url>`** - Play a song from YouTube
- **`m!loop`** - Toggle loop for the current song
- **`m!stop`** - Stop playing music
- **`m!leave`** - Leave the voice channel

### ⚔️ Beyblade Collection Game
Similar to Pokétwo, collect and battle with Beyblades:
- **`m!spawn`** - Spawn a random Beyblade (Common, Rare, or Legendary)
- **`m!catch <name>`** - Catch the spawned Beyblade
- **`m!collection`** - View your Beyblade collection
- **`m!battle @user`** - Battle another player
- **`m!stats [@user]`** - View battle statistics

#### Beyblade Features:
- **Rarity System**: Common (60%), Rare (30%), Legendary (10%)
- **Stats**: Power, Defense, Stamina
- **Battles**: Turn-based combat with stat calculations
- **Progression**: Win/Loss tracking and statistics
- **Collection**: Persistent storage of caught Beyblades

### 📋 Help Command
- **Command**: `m!commands`
- Shows all available commands with descriptions

## Setup

### Prerequisites
- Python 3.11+
- Discord Bot Token
- FFmpeg (for music playback)

### Installation

1. The bot uses the Discord token provided in the code
2. All dependencies are pre-installed:
   - discord.py (with voice support)
   - yt-dlp
   - googletrans
   - PyNaCl
   - requests
   - python-dotenv

3. The bot will automatically start when you run the project

### Adding the Bot to Your Server

1. Go to the Discord Developer Portal
2. Select your bot application
3. Go to OAuth2 > URL Generator
4. Select scopes: `bot`
5. Select permissions:
   - Send Messages
   - Manage Messages
   - Connect
   - Speak
   - Moderate Members (for timeout)
6. Use the generated URL to invite the bot to your server

### Required Bot Permissions
- **Send Messages**: To respond to commands
- **Manage Messages**: To delete messages with curse words
- **Moderate Members**: To timeout users
- **Connect**: To join voice channels
- **Speak**: To play music

## Usage Examples

```
# Translation
m!translate es Hello, how are you?

# Fake Robux
m!robux 10000

# Bible Verse
m!verse

# Music
m!play https://www.youtube.com/watch?v=dQw4w9WgXcQ
m!loop
m!stop
m!leave

# Beyblade Game
m!spawn
m!catch Storm Pegasus
m!collection
m!battle @friend
m!stats
```

## Beyblade Game Details

### Available Beyblades

**Common Beyblades:**
- Storm Pegasus
- Rock Leone
- Flame Sagittario
- Dark Wolf

**Rare Beyblades:**
- Lightning L-Drago
- Earth Eagle
- Gravity Perseus

**Legendary Beyblades:**
- Big Bang Pegasus
- Meteo L-Drago
- Phantom Orion

### How to Play

1. Use `m!spawn` to spawn a random Beyblade
2. Quickly type `m!catch <name>` to catch it
3. Build your collection
4. Battle other players with `m!battle @user`
5. Track your progress with `m!stats`

## Data Storage

- Beyblade collection data is stored in `beyblade_data.json`
- Data persists between bot restarts
- Includes user collections, wins, and losses

## Moderation

The bot automatically moderates the following curse words:
- Common inappropriate language
- Users are timed out for 5 minutes
- Messages are deleted immediately

## Troubleshooting

### Music Not Playing
- Ensure the bot has proper permissions in the voice channel
- Check that FFmpeg is installed
- Verify the YouTube URL is valid

### Bot Not Responding
- Check that the bot has "Send Messages" permission
- Verify the command prefix is `m!`
- Ensure the bot is online

### Timeout Not Working
- The bot needs "Moderate Members" permission
- The bot's role must be higher than the user being moderated

## Technical Details

- **Framework**: discord.py
- **Music**: yt-dlp + FFmpeg
- **Translation**: Google Translate API
- **Bible Verses**: Bible.org API
- **Data Storage**: JSON file system

## Command Prefix

All commands use the prefix: `m!`

## Support

If you encounter any issues, check the console logs for error messages.
