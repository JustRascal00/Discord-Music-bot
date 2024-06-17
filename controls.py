import discord

class PlaybackControls(discord.ui.View):
    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused the song.", ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.", ephemeral=True)

    @discord.ui.button(label="▶️ Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed the song.", ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not paused at the moment.", ephemeral=True)

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Stopped the song.", ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.gray)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Skipped to the next song.", ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not playing anything at the moment.", ephemeral=True)
