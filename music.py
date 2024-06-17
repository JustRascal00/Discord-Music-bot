import discord
import yt_dlp as youtube_dl
import asyncio
from controls import PlaybackControls
from queue_manager import queue, loop, loop_queue

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def play_next(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return

    try:
        if len(queue) > 0:
            url = queue[0]
            if not loop_queue:
                queue.pop(0)

            player = await YTDLSource.from_url(url, loop=ctx.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
            await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
        elif loop and len(queue) > 0:
            url = queue[0]
            player = await YTDLSource.from_url(url, loop=ctx.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
            await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
        else:
            await ctx.send("Queue is empty.")
    except Exception as e:
        print(f'Error in play_next: {e}')
        await ctx.send('An error occurred while trying to play the next song.')
