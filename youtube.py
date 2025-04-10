import os
from googleapiclient.discovery import build

YOUTUBE_KEY = os.getenv('YOUTUBE_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_KEY')

youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)

# Function to get the latest 5 video URLs from a channel
def get_sub_count():
    response = youtube.channels().list(
        part='statistics',
        id=YOUTUBE_CHANNEL_ID
    ).execute()

    return int(response['items'][0]['statistics']['subscriberCount'])