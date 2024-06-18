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
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',  # Setting to 320 kbps for higher quality
    }],
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -b:a 320k -af "volume=1.5, equalizer=f=1000:t=q:w=1.0:g=5"' 
}

# Bass boost filter (increase bass frequencies)
bass_boost_filter = "-af 'equalizer=f=40:width_type=o:width=2:g=10'"

# Low tunes filter (lower pitch)
low_tunes_filter = "-af 'asetrate=44100*0.9,atempo=1.1'"

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, filter=None, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        # Apply the filter if provided
        ffmpeg_opts = ffmpeg_options.copy()
        if filter:
            ffmpeg_opts['options'] += f' {filter}'

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data, volume=volume)

    def adjust_volume(self, volume):
        self.volume = volume / 100  # Discord.PCMVolumeTransformer expects volume in float (0.0 - 2.0)

    def get_duration(self):
            return self.duration

async def play_next(ctx):
    try:
        if ctx.voice_client and ctx.voice_client.is_connected():
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            if len(queue) > 0:
                url, filter = queue[0]  # Get the first item in queue without removing it
                player = await YTDLSource.from_url(url, loop=ctx.bot.loop, stream=True, filter=filter)
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
                await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
            elif loop:
                # Loop the current song if loop is enabled and there are no more songs in the queue
                if ctx.voice_client.is_playing():
                    player = ctx.voice_client.source
                    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), ctx.bot.loop))
                    await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
            else:
                await ctx.send("Queue is empty.")
        else:
            await ctx.send("Not connected to a voice channel.")
    except Exception as e:
        print(f'Error in play_next: {e}')
        await ctx.send('An error occurred while trying to play the next song.')