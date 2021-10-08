import discord
from discord import guild
from discord.ext import commands
import datetime
from urllib import parse, request
import re
import os
import pytube
from moviepy.editor import *

bot = commands.Bot(command_prefix="!", description="This is a helper bot.")


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def sum(ctx, a: int, b: int):
    await ctx.send(a + b)


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
    embed.set_thumbnail(
        url="https://w1.pngwing.com/pngs/199/577/png-transparent-python-logo-programming-language-computer-programming-python-tutorial-highlevel-programming-language-java-generalpurpose-programming-language-statement.png"
    )
    await ctx.send(embed=embed)


@bot.command()
async def yt(ctx, *, search):
    query_string = parse.urlencode({"search_query": search})
    html_content = request.urlopen("http://www.youtube.com/results?" + query_string)
    search_results = re.findall(
        'href="\\/watch\\?v=(.{11})', html_content.read().decode()
    )
    print(search_results)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Streaming(
            name="Tutorials", url="http://www.twitch.tv/accountname"
        )
    )
    print("My Bot is Ready")


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
    yt = pytube.YouTube(url)
    path_video = yt.streams.filter(mime_type="audio/mp4").get_audio_only().download()
    audio = AudioFileClip(path_video)
    audio.write_audiofile("song.mp3")
    os.remove(path_video)

    voice.play(discord.FFmpegPCMAudio("song.mp3"))


@bot.command()
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
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


bot.run(os.environ[DISCORD_TOKEN])
