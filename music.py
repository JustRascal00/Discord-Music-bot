import asyncio
import discord
import yt_dlp as youtube_dl
from controls import PlaybackControls
from queue_manager import queue, loop, loop_queue
import time

# Initialize ytdl and ffmpeg options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto'
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5, filter=None):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.start_time = time.time()
        self.filter = filter

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, filter=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        ffmpeg_options['before_options'] = f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 {filter}" if filter else '-vn'

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, filter=filter)

    def adjust_volume(self, volume: int):
        self.volume = volume / 100

    def get_duration(self):
        return self.data.get('duration', 0)

bass_boost_filter = "equalizer=f=40:t=w:width_type=h:width=50:g=10"
low_tunes_filter = "asetrate=44100*0.8,aresample=44100"

async def play_next(ctx):
    print(f'play_next: Loop is {"enabled" if ctx.bot.loop_state else "disabled"}')
    print(f'play_next: Loop queue is {"enabled" if ctx.bot.loop_queue_state else "disabled"}')

    voice_client = ctx.voice_client

    if ctx.bot.loop_state:
        print('Looping current song...')
        current = voice_client.source
        new_source = await YTDLSource.from_url(current.webpage_url, loop=ctx.bot.loop, stream=True, filter=current.filter)
        new_source.start_time = time.time()  # Reset the start time
        voice_client.play(new_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
    elif queue:
        print(f'Queue before popping: {queue}')
        query, filter = queue.pop(0)
        print(f'Popped song: {query}')
        player = await YTDLSource.from_url(query, loop=ctx.bot.loop, stream=True, filter=filter)
        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
        await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())

        if ctx.bot.loop_queue_state:
            queue.append((query, filter))
            print(f'Appended {query} back to the queue due to loop queue state.')
        print(f'Queue after processing: {queue}')
    else:
        print('Queue is empty after popping.')
        await ctx.send("Queue is empty. Add more songs to keep the music going!")