#!/bin/bash

# Quick fix script to create media directories and sample images
# Run this on your server after deployment

MEDIA_PATH="/home/sunset/eventlinez/media"

echo "🖼️ Setting up media directories and sample images..."

# Create all necessary media directories
mkdir -p $MEDIA_PATH/event
mkdir -p $MEDIA_PATH/CACHE/images/event
mkdir -p $MEDIA_PATH/gallery
mkdir -p $MEDIA_PATH/partners

# Create a simple placeholder image using ImageMagick (if available) or download one
if command -v convert &> /dev/null; then
    # Create a simple placeholder image using ImageMagick
    convert -size 800x500 xc:lightblue -pointsize 48 -fill darkblue -gravity center -annotate +0+0 "Sample Event" $MEDIA_PATH/event/sample-event.jpg
    convert -size 1600x838 xc:lightgreen -pointsize 72 -fill darkgreen -gravity center -annotate +0+0 "Event Image" $MEDIA_PATH/event/sample-event-large.jpg
    echo "✅ Created sample images using ImageMagick"
elif command -v curl &> /dev/null; then
    # Download sample placeholder images from a public service
    curl -s "https://via.placeholder.com/800x500/4A90E2/FFFFFF?text=Sample+Event" -o $MEDIA_PATH/event/sample-event.jpg
    curl -s "https://via.placeholder.com/1600x838/4A90E2/FFFFFF?text=Event+Image" -o $MEDIA_PATH/event/sample-event-large.jpg
    echo "✅ Downloaded sample placeholder images"
else
    # Create empty files as fallback
    touch $MEDIA_PATH/event/sample-event.jpg
    touch $MEDIA_PATH/event/sample-event-large.jpg
    echo "⚠️ Created empty placeholder files (no ImageMagick or curl available)"
fi

# Set proper permissions
chown -R sunset:sunset $MEDIA_PATH 2>/dev/null || chown -R sunset:www-data $MEDIA_PATH
chmod -R 755 $MEDIA_PATH
find $MEDIA_PATH -type f -exec chmod 644 {} \;

echo "✅ Media directories and sample images set up successfully!"
echo "📁 Media structure:"
find $MEDIA_PATH -type d | head -10

echo ""
echo "🔧 Next steps:"
echo "1. Run your deploy script to apply the fixes"
echo "2. Or restart your Django application: sudo systemctl restart eventlinez.service"
echo "3. Check the website - images should now display properly"