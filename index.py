import discord
from discord.ext import commands
import datetime
import youtube_dl
from requests import get
from discord.ext import tasks
from discord.ext.commands import CommandNotFound
import os

song1 = song2 = song3 = song4 = song5 = ""
playlist = []
index = 0
intents = discord.Intents.all()
intents.members = True

ydl_opts = {
    "playlistend": 30,
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }
    ],
}

ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}


def cmds(embed):
    embed.add_field(name="Join Bot", value="!join")
    embed.add_field(name="Leave Bot", value="!leave")
    embed.add_field(name="Play Music", value="!play [url]")
    embed.add_field(name="Stop Music", value="!stop")
    embed.add_field(name="Pause Music", value="!pause")
    embed.add_field(name="Resume Music", value="!resume")
    embed.add_field(name="Search YT", value="!search [words]")
    embed.add_field(name="Download", value="!dwl [url]")
    embed.add_field(name="Info Server", value="!info")
    return embed


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(
            description="Help DJpy",
            color=discord.Color.blue(),
        )
        embed = cmds(embed)
        await destination.send(embed=embed)


bot = commands.Bot(
    command_prefix="!", description="This is a helper bot.", intents=intents
)
bot.help_command = MyHelpCommand()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await info(ctx)
        return
    raise error


@bot.command()
async def set_channel_id(ctx, arg: str):
    global channel_id
    channel_id = arg
    await ctx.send("Configured Channel ID")


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title=f"{ctx.guild.name}",
        description="Gaming Server",
        timestamp=datetime.datetime.utcnow(),
        color=discord.Color.blue(),
    )
    embed.add_field(name="Server Created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    embed = cmds(embed)
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
            audiomp3 = [
                x
                for x in song_info["formats"]
                if (x["vcodec"] == "none") and (x["ext"] == "m4a")
            ]
            embed.description = f":headphones: [Descargar cancion]({audiomp3[0]['url']})."  # song_info['formats'][0]['url'])
            await ctx.send(embed=embed)

    except youtube_dl.utils.DownloadError:
        await ctx.send("This video is not available.")


@bot.command()
async def join(ctx):
    if ctx.voice_client is None:
        if not ctx.message.author.voice:
            await ctx.send(
                "{} is not connected to a voice channel".format(ctx.message.author.name)
            )
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()


@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()


@bot.command()
async def next_(ctx):
    await next_song(ctx)


def next_song(ctx):
    global playlist, index
    index += 1
    server = ctx.message.guild
    voice = server.voice_client
    if voice.is_playing():
        voice.pause()
    if len(playlist) == index + 1:
        voice.play(
            discord.FFmpegPCMAudio(
                playlist[index]["formats"][0]["url"], **ffmpeg_options
            )
        )
        return
    voice.play(
        discord.FFmpegPCMAudio(playlist[index]["formats"][0]["url"], **ffmpeg_options),
        after=lambda x: next_song(ctx),
    )


@bot.command()
async def play(ctx, url: str, dwl=True):
    await join(ctx)
    try:
        server = ctx.message.guild
        voice = server.voice_client
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            await ctx.send("Loading, wait for seconds...")
            song_info = ydl.extract_info(url, download=False)
            if len(song_info) == 1:
                if dwl is True:
                    embed = discord.Embed()
                    audiomp3 = [
                        x
                        for x in song_info["formats"]
                        if (x["vcodec"] == "none") and (x["ext"] == "m4a")
                    ]
                    embed.description = f":headphones: [Descargar cancion]({audiomp3[0]['url']})."  # song_info['formats'][0]['url'])
                    await ctx.send(embed=embed)

        if voice.is_playing():
            voice.pause()

        if "entries" not in song_info:
            voice.play(
                discord.FFmpegPCMAudio(song_info["formats"][0]["url"], **ffmpeg_options)
            )
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=song_info["title"]
                )
            )

        else:
            global playlist, index
            playlist = song_info["entries"]
            index = 0
            view = discord.ui.View()
            btn_next = discord.ui.Button(
                style=discord.ButtonStyle.green, label="Next", emoji="⏭️"
            )

            async def button_next(interaction):
                next_song(ctx)
                await interaction.response.edit_message()

            btn_next.callback = button_next
            voice.play(
                discord.FFmpegPCMAudio(
                    playlist[index]["formats"][0]["url"], **ffmpeg_options
                ),
                after=lambda x: next_song(ctx),
            )
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=playlist[0]["title"],
                )
            )

            view.add_item(item=btn_next)
            await ctx.send(view=view)

    except youtube_dl.utils.DownloadError:
        await ctx.send("This video is not available.")


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


@tasks.loop(seconds=1.0)
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            time = time + 1
            if voice.is_playing() and not voice.is_paused():
                time = 0
            if time == 50:
                await voice.disconnect()
            if not voice.is_connected():
                break


class song:
    def __init__(self, ctx, video):
        self.ctx = ctx
        self.video = video
        self.embed = discord.Embed(color=0x8934EB)
        self.view = discord.ui.View(timeout=240)
        self.embed.title = self.video["title"]
        self.embed.set_author(name=self.video["uploader"])
        self.embed.add_field(
            name="Duration",
            value=str(datetime.timedelta(seconds=int(self.video["duration"]))),
            inline=True,
        )
        self.embed.add_field(name="Views", value=self.video["view_count"], inline=True)
        self.embed.add_field(name="Likes", value=self.video["like_count"], inline=True)
        self.embed.add_field(
            name="Download:",
            value=f"[MP3]({self.video['formats'][0]['url']})",
            inline=True,
        )
        self.embed.set_thumbnail(url=f"{self.video['thumbnails'][0]['url']}")
        self.embed.set_footer(text="Link: " + self.video["webpage_url"])

        self.btn_play = discord.ui.Button(
            style=discord.ButtonStyle.green, label="Play", emoji="▶️"
        )
        self.btn_pause = discord.ui.Button(
            style=discord.ButtonStyle.grey, label="Pause", emoji="⏸️"
        )
        self.btn_stop = discord.ui.Button(
            style=discord.ButtonStyle.red, label="Stop", emoji="⏹️"
        )

        async def button_play(interaction):
            await play(self.ctx, self.video["webpage_url"], dwl=False)
            await interaction.response.edit_message()

        async def button_pause(interaction):
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice.is_playing():
                await pause(self.ctx)
            else:
                await resume(self.ctx)
            await interaction.response.edit_message()

        async def button_stop(interaction):
            await stop(self.ctx)
            await interaction.response.edit_message()

        self.btn_play.callback = button_play
        self.btn_pause.callback = button_pause
        self.btn_stop.callback = button_stop
        self.view.add_item(item=self.btn_play)
        self.view.add_item(item=self.btn_pause)
        self.view.add_item(item=self.btn_stop)

    async def send_embed(self):
        await self.ctx.send(embed=self.embed)

    async def send_view(self):
        await self.ctx.send(view=self.view)


@bot.command()
async def search(ctx, *, arg: str):
    global song1, song2, song3, song4, song5
    await join(ctx)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        await ctx.send("Searching...")
        try:
            get(arg)
        except:
            videolist = ydl.extract_info(f"ytsearch5:{arg}", download=False)["entries"]
        else:
            videolist = ydl.extract_info(arg, download=False)
    if len(videolist) == 5:
        song1 = song(ctx, videolist[0])
        song2 = song(ctx, videolist[1])
        song3 = song(ctx, videolist[2])
        song4 = song(ctx, videolist[3])
        song5 = song(ctx, videolist[4])

        await song1.send_embed()
        await song1.send_view()
        await song2.send_embed()
        await song2.send_view()
        await song3.send_embed()
        await song3.send_view()
        await song4.send_embed()
        await song4.send_view()
        await song5.send_embed()
        await song5.send_view()
    else:
        await ctx.send("ERROR.")


bot.run(os.environ["DISCORD_TOKEN"])
