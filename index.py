import discord
from discord.ext import commands
import datetime
import youtube_dl
import asyncio
import os


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description="")
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)


bot = commands.Bot(command_prefix="!", description="This is a helper bot.")
bot.help_command = MyHelpCommand()


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def info(ctx):

    embed = discord.Embed(
        title=f"{ctx.guild.name}",
        description="Lorem ipsum",
        timestamp=datetime.datetime.utcnow(),
        color=discord.Color.blue(),
    )
    embed.add_field(name="Server Created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="a song")
    )
    print("My Bot is Ready")


@bot.command()
async def dwl(ctx, url: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url, download=False)
            embed = discord.Embed()
            audiomp3 = [x for x in song_info['formats'] if (x['vcodec'] == 'none') and (x['ext'] == 'm4a')]
            embed.description = (f":headphones: [Descargar cancion]({audiomp3[0]['url']}).")
            await ctx.send(embed=embed)
    except youtube_dl.utils.DownloadError:
        await ctx.send("This video is not available.")


@bot.command()
async def play(ctx, url: str):
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name="General")
    try:
        await voiceChannel.connect()
    except:
        pass
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url, download=False)
            embed = discord.Embed()
            audiomp3 = [x for x in song_info['formats'] if (x['vcodec'] == 'none') and (x['ext'] == 'm4a')]
            embed.description = (f":headphones: [Descargar cancion]({audiomp3[0]['url']}).")     # song_info['formats'][0]['url'])
            await ctx.send(embed=embed)
        voice.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=song_info["title"]
            )
        )
    except youtube_dl.utils.DownloadError:
        await ctx.send("This video is not available.")


@bot.command()
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="a song"
            )
        )
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing.")


@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio is not paused.")


@bot.command()
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="a song")
    )


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing() and not voice.is_paused():
                time = 0
            if time == 600:
                await voice.disconnect()
            if not voice.is_connected():
                break

bot.run(os.environ['DISCORD_TOKEN'])
