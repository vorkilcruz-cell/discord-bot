# Changelog

## Beta v0.01 - November 21, 2025

### Added
- **Slash Commands**: All bot commands now use Discord's modern slash command system (/)
- **Improved Music Playback**: Enhanced FFmpeg configuration with loudness normalization and reconnection support
- **Build Package**: Created distributable beta_0.01.zip in builds folder with all necessary files

### Changed
- Converted all prefix commands (m!) to slash commands (/)
- Updated music player with better error handling and streaming capabilities
- Improved FFmpeg options for better audio quality
- Enhanced security by requiring DISCORD_TOKEN from environment variables

### Fixed
- Fixed auto-moderation timeout functionality using proper datetime objects
- Improved error messages and user feedback across all commands
- Better voice channel handling and connection management

### Security
- Removed hard-coded Discord token
- Required DISCORD_TOKEN to be set via environment variables or Replit Secrets
- Added .env.example file for secure configuration

### Features
- Translation between any languages
- Fake robux generator (joke command)
- Auto-moderation (5-minute timeout for inappropriate language)
- Random Bible verses
- Music player with YouTube support (play, loop, stop, leave)
- Beyblade collection game (spawn, catch, collection, battle, stats)

### Package Contents (builds/beta_0.01.zip)
- main_slash.py - Main bot file with slash commands
- requirements.txt - Python dependencies
- README.txt - Installation and usage instructions
- .env.example - Environment variable template
- .gitignore - Git ignore file for Python projects
