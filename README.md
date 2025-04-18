# Photo Editor Bot

A Telegram bot that processes photos by adding text overlays, converting to 16:9 ratio with blurred background, and removing black/white borders. Also handles videos and GIFs by formatting captions.

## Features

- Adds "Search @Thrill_Zone" text overlays at top and bottom of photos
- Converts all photos to 16:9 aspect ratio
- Creates blurred background from the image itself for padding
- Automatically removes black and white borders from images
- Handles videos and GIFs by keeping them intact but formatting captions
- Extracts and formats TeraBox links in captions

## Deployment on Koyeb

### Prerequisites

1. Create a Telegram bot using BotFather and get your API token
2. Create a Koyeb account

### Deployment Steps

1. Fork or clone this repository
2. Create a new app on Koyeb
3. Connect your GitHub repository
4. Add your Telegram bot token as an environment variable:
   - Variable name: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from BotFather
5. Deploy the app

The deployment includes a simple HTTP server that responds to health checks on port 8000, which is required by Koyeb to verify that your service is running properly.

### Manual Deployment

```bash
# Clone the repository
git clone <repository-url>
cd photo-editor-bot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file to add your Telegram bot token

# Run the bot with web server for health checks
python web_server.py

# Alternatively, to run just the bot without the web server
# python photo_editor_bot.py
```

## Usage

1. Start a chat with your bot on Telegram
2. Send any photo to the bot
3. The bot will process it and send back the edited version
4. For videos and GIFs, send them with TeraBox links in the caption
5. The bot will format the caption according to the template

## License

MIT 