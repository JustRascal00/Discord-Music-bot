import asyncio
import random
import discord
from discord.ext import commands
from music import YTDLSource, play_next, bass_boost_filter, low_tunes_filter  # Import the filters here
from controls import PlaybackControls
from queue_manager import queue, loop, loop_queue
from config import GENIUS_API_TOKEN
from spotify import convert_spotify_url
import lyricsgenius

genius = lyricsgenius.Genius(GENIUS_API_TOKEN)

def setup_commands(bot):
    @bot.command(name='join', help='Tells the bot to join the voice channel')
    async def join(ctx):
        if not ctx.author.voice:
            await ctx.send(f"{ctx.author.name} is not connected to a voice channel")
            return
        channel = ctx.author.voice.channel
        await channel.connect()

    @bot.command(name='leave', help='Tells the bot to leave the voice channel')
    async def leave(ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @bot.command(name='play', help='Plays a song with optional effects. Usage: !play <url> [bass_boost|low_tunes]')
    async def play(ctx, url, effect=None):
        if not ctx.voice_client:
            if ctx.author.voice:
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

        async with ctx.typing():
            try:
                filter = None
                if effect == "bass_boost":
                    filter = bass_boost_filter
                elif effect == "low_tunes":
                    filter = low_tunes_filter

                if "spotify.com" in url:
                    queries = convert_spotify_url(url)
                    if isinstance(queries, list):
                        for query in queries:
                            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True, filter=filter)
                            player.title = query  # Assign the query as the title
                        if not ctx.voice_client.is_playing():
                            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                            await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
                        else:
                            queue.append((query, filter))
                            await ctx.send(f'Added to queue: {player.title}')
                    else:
                        player = await YTDLSource.from_url(queries, loop=bot.loop, stream=True, filter=filter)
                        player.title = queries  # Assign the query as the title
                        if not ctx.voice_client.is_playing():
                            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                            await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
                        else:
                            queue.append((queries, filter))
                            await ctx.send(f'Added to queue: {player.title}')
                else:
                    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True, filter=filter)
                    if not ctx.voice_client.is_playing():
                        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                        await ctx.send(f'Now playing: {player.title}', view=PlaybackControls())
                    else:
                        queue.append((url, filter))
                        await ctx.send(f'Added to queue: {player.title}')
            except discord.errors.ConnectionClosed as e:
                print(f'Disconnected with error: {e}')
                await ctx.send('An error occurred while trying to play the song.')
            except Exception as e:
                print(f'Error in play: {e}')
                await ctx.send('An error occurred while trying to play the song.')
           
    @bot.command(name='skip', help='Skips the current song')
    async def skip(ctx):
        ctx.voice_client.stop()

    @bot.command(name='queue', help='Shows the current queue')
    async def view_queue(ctx):
        if len(queue) == 0:
            await ctx.send("The queue is empty.")
        else:
            queue_str = '\n'.join([f"{i + 1}. {url}" for i, (url, filter) in enumerate(queue)])
            await ctx.send(f'Current queue:\n{queue_str}')

    @bot.command(name='remove', help='Removes a song from the queue')
    async def remove(ctx, index: int):
        if 0 < index <= len(queue):
            removed, _ = queue.pop(index - 1)
            await ctx.send(f'Removed {removed} from the queue.')
        else:
            await ctx.send("Invalid index.")

    @bot.command(name='clear', help='Clears the queue')
    async def clear(ctx):
        global queue
        queue = []
        await ctx.send("Cleared the queue.")

    @bot.command(name='move', help='Moves a song in the queue')
    async def move(ctx, from_index: int, to_index: int):
        if 0 < from_index <= len(queue) and 0 < to_index <= len(queue):
            queue.insert(to_index - 1, queue.pop(from_index - 1))
            await ctx.send(f'Moved song from position {from_index} to {to_index}.')
        else:
            await ctx.send("Invalid index.")

    @bot.command(name='volume', help='Changes the volume')
    async def volume(ctx, volume: int):
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f'Changed volume to {volume}%')

    @bot.command(name='loop', help='Loops the current song')
    async def loop_track(ctx):
        global loop
        loop = not loop
        await ctx.send(f'Looping is now {"enabled" if loop else "disabled"}.')

    @bot.command(name='loopqueue', help='Loops the entire queue')
    async def loop_queue_cmd(ctx):
        global loop_queue
        loop_queue = not loop_queue
        await ctx.send(f'Looping queue is now {"enabled" if loop_queue else "disabled"}.')

    @bot.command(name='shuffle', help='Shuffles the queue')
    async def shuffle(ctx):
        random.shuffle(queue)
        await ctx.send("Shuffled the queue.")

    @bot.command(name='lyrics', help='Fetches the lyrics for the current song')
    async def lyrics_command(ctx):
        if ctx.voice_client.is_playing():
            player = ctx.voice_client.source
            song_title = player.title.split('[')[0].strip()  # Remove additional tags for cleaner title

            # Check if the song is from Spotify
            if "spotify.com" in player.url:
                # Split the title to extract the song title and artist
                parts = song_title.split(" - ")
                if len(parts) == 2:
                    song_title, artist = parts
                    song = genius.search_song(song_title, artist)
                else:
                    song = genius.search_song(song_title)
            else:
                song = genius.search_song(song_title)

            if song:
                lyrics_truncated = song.lyrics[:4000]
                await ctx.send(f"Lyrics for {song.title} by {song.artist}:\n{lyrics_truncated}")
            else:
                await ctx.send(f"Could not find lyrics for {song_title}.")
        else:
            await ctx.send("Not playing any music right now.")

    @bot.command(name='info', help='Shows info about the current song')
    async def info(ctx):
        if ctx.voice_client.is_playing():
            player = ctx.voice_client.source
            await ctx.send(f'Currently playing: {player.title}')
        else:
            await ctx.send("Not playing any music right now.")
