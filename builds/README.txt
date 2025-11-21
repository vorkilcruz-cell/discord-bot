Discord Bot - Beta v0.01
=========================

INSTALLATION:
1. Install Python 3.11 or higher
2. Install dependencies: pip install -r requirements.txt
3. Install FFmpeg on your system (required for music playback)

SETUP:
1. Create a Discord bot at https://discord.com/developers/applications
2. Enable these Privileged Gateway Intents in the bot settings:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
   - PRESENCE INTENT
3. Create a .env file and add your Discord token:
   DISCORD_TOKEN=your_token_here
4. Invite the bot to your server with these permissions:
   - Send Messages
   - Manage Messages
   - Moderate Members
   - Connect
   - Speak

RUNNING THE BOT:
python main_slash.py

FEATURES:
- Slash commands (use / to see all commands)
- Translation between any languages
- Fake robux generator (joke command)
- Auto-moderation (5-minute timeout for curse words)
- Daily Bible verses
- Music player with YouTube support
- Beyblade collection game (similar to Pokétwo)

COMMANDS:
/translate <lang_code> <text> - Translate text
/robux [amount] - Generate fake robux
/verse - Get random Bible verse
/play <url> - Play YouTube music
/loop - Toggle loop
/stop - Stop music
/leave - Leave voice channel
/spawn - Spawn a Beyblade
/catch <name> - Catch Beyblade
/collection - View collection
/battle @user - Battle another player
/stats [@user] - View battle stats
/commands - Show all commands

TROUBLESHOOTING:
- Make sure FFmpeg is installed for music playback
- Ensure bot has proper permissions in your Discord server
- Check that DISCORD_TOKEN is set correctly in .env file
- The bot needs "Moderate Members" permission to timeout users

For support, check the logs for error messages.
