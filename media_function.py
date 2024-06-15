# media_functions.py

import re
import requests
from io import BytesIO
from moviepy.editor import VideoFileClip

def download_media(url):
    url = 'https://www.' + re.sub('(www\.)|(https?://)', '', url)
    if url[-1] == '/':
        url = url[:-1]

    response = requests.get(url, headers={'Accept': 'application/json'})
    content = re.sub('\s', '', response.text)
    cnt = int(re.findall('[0-9]+', re.findall('[0-9]+<.*>Media', content)[-1])[0]) + 20

    name = url.split('/')[-1]
    base_url = 'https://www.fapello.com/content/' + \
               name[0] + '/' + name[1] + '/' + name + \
               '/1000/' + name + '_'

    media = []
    for i in range(1, cnt + 1):
        media.append('%s%04d.jpg' % (base_url, i))
        media.append('%s%04d.mp4' % (base_url, i))

    return media

def split_video(video_bytes, max_size_mb=23):
    video_size_mb = len(video_bytes) / (1024 * 1024)
    if video_size_mb <= max_size_mb:
        return [video_bytes]

    video_clips = []
    video = VideoFileClip(BytesIO(video_bytes))
    duration = video.duration
    part_number = 0
    current_start = 0

    while current_start < duration:
        current_end = current_start + (max_size_mb * 1024 * 1024 / video_size_mb) * duration
        current_end = min(current_end, duration)
        subclip = video.subclip(current_start, current_end)
        subclip_bytes = BytesIO()
        subclip.write_videofile(subclip_bytes, codec='libx264', temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
        video_clips.append(subclip_bytes.getvalue())
        current_start = current_end
        part_number += 1

    return video_clips
