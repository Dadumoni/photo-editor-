import os
import logging
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import io
import numpy as np

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PHOTO = 0

# User session storage
user_photos = {}

# Command handlers
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    update.message.reply_text(
        'Welcome to Photo Editor Bot! 📸\n\n'
        'Send me a photo and I will add "Search @Thrill_Zone" text overlays to the top and bottom.'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    update.message.reply_text(
        'How to use this bot:\n\n'
        '1. Send a photo to the bot\n'
        '2. The bot will add "Search @Thrill_Zone" text at the top and bottom\n'
        '3. The edited photo will be sent back to you\n\n'
        'You can also send videos or GIFs, and I will keep them as is but format the caption.\n\n'
        'Commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message'
    )

def crop_black_borders(image):
    """Remove black or white borders from an image if they exist."""
    # Convert to numpy array for easier processing
    img_array = np.array(image)
    
    # Check if image has 3 channels (RGB)
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        # Convert to grayscale for easier detection
        gray = np.mean(img_array, axis=2)
        
        # Find non-border rows and columns (neither black nor white)
        # For black borders: pixel values close to 0
        # For white borders: pixel values close to 255
        
        # We consider a row/column as border if all pixels are near-black or near-white
        # Find rows that contain actual content (not just borders)
        content_rows = []
        for i, row in enumerate(gray):
            # Check if row has pixels that are neither black nor white
            if np.any((row > 5) & (row < 250)):
                content_rows.append(i)
                
        # Find columns that contain actual content (not just borders)
        content_cols = []
        for i, col in enumerate(gray.T):  # Transpose to get columns
            # Check if column has pixels that are neither black nor white
            if np.any((col > 5) & (col < 250)):
                content_cols.append(i)
        
        # If we found content areas, crop to those boundaries
        if content_rows and content_cols:
            top, bottom = min(content_rows), max(content_rows)
            left, right = min(content_cols), max(content_cols)
            
            # Add a small margin (1 pixel) to ensure we don't cut too tightly
            top = max(0, top - 1)
            left = max(0, left - 1)
            bottom = min(img_array.shape[0] - 1, bottom + 1)
            right = min(img_array.shape[1] - 1, right + 1)
            
            # Only crop if there's actually a border to remove
            if top > 0 or bottom < img_array.shape[0] - 1 or left > 0 or right < img_array.shape[1] - 1:
                return image.crop((left, top, right + 1, bottom + 1))
    
    # Return original image if no borders found or image format incompatible
    return image

def add_text_to_image(image):
    """Add text overlay to the image by creating white bands at top and bottom, resize to 16:9 ratio, and add a border."""
    # First, remove any black borders that may exist
    image = crop_black_borders(image)
    
    # Convert to RGB if image has alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Get original dimensions
    orig_width, orig_height = image.size
    
    # Calculate target dimensions for 16:9 ratio
    target_ratio = 16 / 9
    current_ratio = orig_width / orig_height
    
    # Determine the new dimensions to make it 16:9 without cropping
    if current_ratio > target_ratio:
        # Image is wider than 16:9, use the width and add padding to height
        new_width = orig_width
        new_height = int(orig_width / target_ratio)
        # Calculate padding needed for top and bottom
        padding_y = (new_height - orig_height) // 2
        padding_x = 0
    else:
        # Image is taller than 16:9, use the height and add padding to width
        new_height = orig_height
        new_width = int(orig_height * target_ratio)
        # Calculate padding needed for left and right
        padding_x = (new_width - orig_width) // 2
        padding_y = 0
    
    # Create a blurred background by scaling up and blurring the original image
    background = image.copy()
    # Scale the background to be larger than needed
    scale_factor = max(new_width / orig_width, new_height / orig_height) * 1.5
    blur_width = int(orig_width * scale_factor)
    blur_height = int(orig_height * scale_factor)
    background = background.resize((blur_width, blur_height), Image.LANCZOS)
    # Apply blur effect
    background = background.filter(ImageFilter.GaussianBlur(radius=30))
    
    # Create canvas with the blurred background
    canvas = Image.new('RGB', (new_width, new_height), (0, 0, 0))
    # Calculate position to center the blurred background
    bg_x = (blur_width - new_width) // 2
    bg_y = (blur_height - new_height) // 2
    # Paste the blurred background
    canvas.paste(background, (-bg_x, -bg_y))
    
    # Paste the original image in the center of the canvas with padding
    paste_x = padding_x
    paste_y = padding_y
    canvas.paste(image, (paste_x, paste_y))
    
    # Get the final dimensions
    final_width, final_height = canvas.size
    
    # Calculate the height of the white bands (about 10% of image height)
    band_height = int(final_height * 0.10)
    
    # Create a new image with extra height for the bands
    final_canvas_height = final_height + (band_height * 2)
    new_image = Image.new('RGB', (final_width, final_canvas_height), color=(255, 255, 255))
    
    # Paste the image in the middle
    new_image.paste(canvas, (0, band_height))
    
    # Create a drawing object
    draw = ImageDraw.Draw(new_image)
    
    # Use fixed font size of 40 pixels
    font_size = 40
    
    # Try different fonts - prioritizing regular fonts
    font_options = ["arial.ttf", "times.ttf", "calibri.ttf", "tahoma.ttf", "verdana.ttf", "georgia.ttf"]
    font = None
    
    # Try to find a suitable font
    for font_name in font_options:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except IOError:
            continue
    
    # Fallback to default font if none found
    if font is None:
        font = ImageFont.load_default()
    
    text = "Search @Thrill_Zone"
    
    # Get text size
    try:
        text_width = draw.textlength(text, font=font)
    except AttributeError:
        # For older versions of PIL
        text_width, text_height = draw.textsize(text, font=font)
    
    # Calculate positions for centered text in bands
    # Top band - vertically center text in the band
    top_y = (band_height - font_size) // 2
    top_position = ((final_width - text_width) // 2, top_y)
    
    # Bottom band - vertically center text in the band
    bottom_y = final_canvas_height - band_height + (band_height - font_size) // 2
    bottom_position = ((final_width - text_width) // 2, bottom_y)
    
    # Draw text on the bands
    draw.text(top_position, text, fill=(0, 0, 0), font=font)
    draw.text(bottom_position, text, fill=(0, 0, 0), font=font)
    
    return new_image

def extract_terabox_links(text):
    """Extract unique TeraBox links from the text."""
    if not text:
        return []
    
    # Regex pattern to match TeraBox links from both domains
    pattern = r'(https?://(?:teraboxlink\.com|1024terabox\.com)/s/[a-zA-Z0-9_-]+)'
    
    # Find all links
    links = re.findall(pattern, text)
    
    # Remove duplicates while preserving order
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
    
    return unique_links

def format_caption(text):
    """Format caption to include only TeraBox links in the desired format."""
    links = extract_terabox_links(text)
    
    if not links:
        return None  # No TeraBox links found
    
    # Format the caption based on number of links
    formatted_caption = "📥 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐋𝐢𝐧𝐤𝐬/👀𝐖𝐚𝐭𝐜𝐡 𝐎𝐧𝐥𝐢𝐧𝐞\n\n"
    
    for i, link in enumerate(links):
        formatted_caption += f"Video {i+1}.👇\n{link}\n\n"
    
    formatted_caption += "#Thrill_Zone  #Viral_videos\nJoin For More @Thrill_Zone"
    
    return formatted_caption

def process_photo(update: Update, context: CallbackContext) -> None:
    """Process the photo sent by the user."""
    # Process the caption if present
    caption = None
    if update.message.caption:
        caption = format_caption(update.message.caption)
    
    # Get the photo with the highest resolution
    photo_file = update.message.photo[-1].get_file()
    
    # Download the photo
    photo_bytes = io.BytesIO()
    photo_file.download(out=photo_bytes)
    photo_bytes.seek(0)
    
    # Open the image using PIL
    image = Image.open(photo_bytes)
    
    # Add text overlay
    edited_image = add_text_to_image(image)
    
    # Save the edited image to a bytes buffer
    output = io.BytesIO()
    edited_image.save(output, format='JPEG')
    output.seek(0)
    
    # Send the edited photo back to the user with the formatted caption if available
    update.message.reply_photo(output, caption=caption)
    
    # Provide feedback
    update.message.reply_text('Your edited photo is ready! 🎉')

def process_video(update: Update, context: CallbackContext) -> None:
    """Process video or animation (GIF) sent by the user."""
    # Format the caption if present, otherwise use None
    caption = None
    if update.message.caption:
        caption = format_caption(update.message.caption)
    
    # Get the file ID
    if update.message.video:
        file_id = update.message.video.file_id
        # Reply with the same video but with the formatted caption
        update.message.reply_video(file_id, caption=caption)
    elif update.message.animation:
        file_id = update.message.animation.file_id
        # Reply with the same animation/GIF but with the formatted caption
        update.message.reply_animation(file_id, caption=caption)
    
    # Provide feedback
    update.message.reply_text('Your media is ready with the formatted caption! 🎉')

def main() -> None:
    """Start the bot."""
    # Get the API token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No token provided! Add your token to the .env file.")
        return

    # Create the Updater and pass it your bot's token
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Register message handlers
    dispatcher.add_handler(MessageHandler(Filters.photo, process_photo))
    dispatcher.add_handler(MessageHandler(Filters.video | Filters.animation, process_video))

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started. Press Ctrl+C to stop.")
    
    # Run the bot until the user presses Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main() 