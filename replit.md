# Overview

This is a feature-rich Discord bot that provides multiple entertainment and utility features including language translation, music playback from YouTube, Bible verse retrieval, auto-moderation, and a Beyblade collection game similar to Pokétwo. The bot uses modern Discord slash commands (`/`) exclusively for a better user experience with auto-completion and Discord's recommended approach.

## Latest Version
**Beta v0.02** - November 22, 2025
- VorkTek-Bucks currency system with daily bonuses, gambling (75% win rate), card trading
- Money transfer system (`/give` command)
- Loan system with 10% interest (`/loan`, `/repay`, `/loans` commands)
- Anonymous confessions system (`/confess`, `/confessions`, `/clear-confessions`)
- Bot online/offline alerts with configurable channel (`/channel_set`)
- Meet Again video link command (`/meet_again`)
- Comprehensive logging to Discord webhooks (DISCORD_WEBHOOK_URL)
- Agent activity monitoring via DC_AGENT_WEBHOOK_URL for tracking all code changes and interactions

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Technology**: Discord.py library with app_commands for slash command support
- **Command System**: Slash commands (`/`) only
- **Rationale**: Slash commands provide better user experience with auto-completion and are Discord's recommended approach
- **Primary Entry Point**: `main_slash.py` for production use
- **Legacy Support**: `main.py` contains prefix commands (deprecated, kept for reference)

## Event-Driven Architecture
- **Pattern**: Discord.py's event listener and command handler system
- **Intents Required**: 
  - Message content (for text processing and auto-moderation)
  - Members (for user interactions)
  - Voice states (for music playback)
  - Guilds (for slash command registration)
- **Rationale**: Intents ensure proper permission scoping and comply with Discord's privacy requirements

## Data Persistence
- **Solution**: File-based JSON storage (`beyblade_data.json`)
- **Purpose**: Stores Beyblade collection game data including user collections, battle statistics, and spawned Beyblades
- **Rationale**: Simple, lightweight solution suitable for small to medium-scale deployments without external database dependencies
- **Trade-offs**: 
  - Pros: No external services, easy to debug, portable
  - Cons: Limited scalability, potential race conditions with concurrent writes, no advanced querying

## Music Playback System
- **Technology**: yt-dlp (YouTube downloader) + FFmpeg for audio processing
- **Architecture**: 
  - YTDLSource class wraps Discord's PCMVolumeTransformer
  - Streams audio from YouTube URLs with reconnection support
  - In-memory audio source management
  - Loudness normalization for consistent volume
- **Dependencies**: FFmpeg must be installed on the host system
- **Features**: Play, stop, loop, and leave commands with voice channel integration
- **FFmpeg Options**: Reconnection support and loudness normalization (-af loudnorm)
- **Rationale**: yt-dlp is actively maintained (unlike deprecated youtube-dl) and provides robust YouTube extraction
- **Beta v0.01 Improvements**: Enhanced streaming with better error handling and audio quality

## Translation System
- **Library**: googletrans (unofficial Google Translate API wrapper)
- **Implementation**: Auto-detects source language and translates to target language
- **Rationale**: Free, simple API without requiring API keys
- **Trade-offs**: Relies on unofficial API which may have rate limits or stability issues

## Auto-Moderation
- **Approach**: Message content filtering with keyword matching
- **Action**: Automatic timeout (5 minutes) and message deletion
- **Word List**: Hardcoded list of prohibited terms
- **Rationale**: Simple pattern matching for common profanity; extensible for future ML-based solutions
- **Limitations**: Easily bypassed with character substitutions; consider more sophisticated NLP approaches for production

## Beyblade Collection Game
- **Game Mechanics**:
  - Rarity system (Common 60%, Rare 30%, Legendary 10%)
  - Stat-based combat (Power, Defense, Stamina)
  - Turn-based battle system
  - Collection and progression tracking
- **Data Model**: JSON structure storing user collections, stats, and active spawns per guild
- **Rationale**: Mimics successful Discord game bot patterns (Pokétwo) with simpler implementation

## Environment Configuration
- **Method**: Environment variables for sensitive data
- **Required Variables**: 
  - `DISCORD_TOKEN` - Bot authentication token
  - `DISCORD_WEBHOOK_URL` (optional) - Receives bot console logs and command activity
  - `DC_AGENT_WEBHOOK_URL` (optional) - Receives agent activity logs (code changes, interactions)
- **Data Storage Files**:
  - `beyblade_data.json` - Beyblades, currency, cards, stats per user
  - `confessions.json` - Anonymous confessions database
  - `loans.json` - Active and repaid loans
  - `channel_config.json` - Bot alert channel configuration
- **Rationale**: Prevents credential exposure in version control; compatible with deployment platforms like Replit

## Logging & Monitoring
- **Console Logging**: All bot activity logged to stdout with timestamps
- **Discord Webhook Logging**: Bot logs forwarded to DISCORD_WEBHOOK_URL for monitoring command execution and errors
- **Agent Webhook Logging**: Comprehensive agent activity forwarded to DC_AGENT_WEBHOOK_URL with formatted indicators:
  - `Agent Response >>` - Agent response messages
  - `User Input >>` - User requests and incoming data
  - `Code Edit >>` - Code file modifications and changes
  - `File Read >>` - File analysis and data access
  - `File Create >>` - New files being created
  - `Command >>` - Shell commands and tool execution
  - `Decision >>` - Reasoning, analysis, and decision points
  - `Action >>` - Current tasks and operations being performed
  - `Status >>` - System state, progress, and updates
  - `Completion >>` - Task completion and results
- **Rationale**: Real-time monitoring of bot health and comprehensive agent activity audit trail for debugging and auditing

# External Dependencies

## Discord API
- **Library**: discord.py v2.6.4+
- **Purpose**: Core bot functionality, event handling, and command processing
- **Voice Extension**: Required for music playback features

## YouTube Integration
- **Library**: yt-dlp v2025.11.12+
- **Purpose**: Extract and download audio from YouTube URLs
- **System Requirement**: FFmpeg binary for audio processing

## Translation Service
- **Library**: googletrans v4.0.0rc1
- **API**: Unofficial Google Translate API
- **Purpose**: Real-time text translation between languages
- **Note**: No API key required but may have undocumented rate limits

## Bible Verse API
- **Service**: Bible.org API
- **Purpose**: Fetch random Bible verses with formatting
- **Integration**: HTTP requests library for API calls

## Audio Processing
- **Library**: PyNaCl v1.5.0+
- **Purpose**: Voice encryption for Discord voice channels
- **System Requirement**: Native library compilation may be needed

## HTTP Client
- **Library**: requests v2.32.5+
- **Purpose**: API calls to external services (Bible.org, etc.)

## Environment Management
- **Library**: python-dotenv v1.2.1+
- **Purpose**: Load environment variables from .env files for local development
- **Deployment**: Replit Secrets or similar environment variable management in production

## Python Runtime
- **Required Version**: Python 3.11 or higher
- **Rationale**: Modern async/await syntax and type hinting support required by discord.py v2.x