import discord
from discord.ext import commands, tasks
from discord import app_commands
import wavelink
import random
import psutil
import platform
import asyncio
import time
from datetime import timedelta
import aiohttp


# Bot Setup
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
DISCORD_BOT_TOKEN = "your-bot-token-here"
support_server_link = "bot support server link"
bot_invite_link = f"bot_invite_link"


# Lavalink Configuration
LAVALINK_HOST = ""  # Replace with actual Lavalink server
LAVALINK_PORT = 
LAVALINK_PASSWORD = ""  # Replace with your Lavalink password

# Track previous songs
previous_track = None
bot.queues = {}
bot.vc_settings = {}  # Track 24/7 mode per guild
bot_start_time = time.time()
bot.repeat_count = {}

# Connect Lavalink Node
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
    node = wavelink.Node(uri=f"http://{LAVALINK_HOST}:{LAVALINK_PORT}", password=LAVALINK_PASSWORD)
    await wavelink.Pool.connect(client=bot, nodes=[node])
    bot.is_247 = {}  # Initialize the 24/7 mode dictionary
    bot.afk_timers = {}  # Initialize AFK timers dictionary
    activity = discord.Activity(type=discord.ActivityType.watching, name="Made By willsmith5314")
    await bot.change_presence(activity=activity)
    print("✅ Lavalink node connected!")


async def start_afk_timer(vc, guild_id):
    """ Waits 2 minutes before leaving if no song is playing and 24/7 mode is off. """
    await asyncio.sleep(120)  # Wait for 2 minutes
    if not vc.playing and not bot.is_247.get(guild_id, False):  # Check again before leaving
        await vc.disconnect()
        bot.afk_timers.pop(guild_id, None)
        channel = bot.get_channel(vc.channel.id)
        if channel:
            embed = discord.Embed(title="Disconnected", description="🚪 Disconnected due to inactivity. Enable `24/7` mode to stay in VC!", color=discord.Color.blue())
            await channel.send(embed=embed)




@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    global previous_track
    guild_id = payload.player.guild.id
    vc = payload.player

    # Check if repeat is enabled for this guild
    repeat = bot.repeat_count.get(guild_id)
    if repeat is not None:
        # If repeat is set to 0, repeat indefinitely; if positive, decrement until 0.
        if repeat == 0 or repeat > 0:
            if repeat > 0:
                bot.repeat_count[guild_id] -= 1  # Decrement repeat count
            # Replay the same track
            await vc.play(payload.track)
            print(f"🔁 Repeating track: {payload.track.title}")
            return

    # Store the last played track before proceeding
    previous_track = payload.track

    # If there is another track in the queue, play it
    if guild_id in bot.queues and bot.queues[guild_id]:
        next_track = bot.queues[guild_id].pop(0)
        await vc.play(next_track)
        print(f"🎵 Now playing: {next_track.title}")
    else:
        print("Queue is empty.")
        # If 24/7 mode is disabled, start the AFK timer to disconnect after inactivity.
        if not bot.is_247.get(guild_id, False):
            bot.afk_timers[guild_id] = asyncio.create_task(start_afk_timer(vc, guild_id))




class MusicControls(discord.ui.View):
    def __init__(self, vc):
        super().__init__()
        self.vc = vc
        self.bot = bot  # Store bot reference



    # Fix for Play/Pause Button
    @discord.ui.button(label="⏯ Play/Pause", style=discord.ButtonStyle.green)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.paused:
            # If the player is paused, resume playback.
            await self.vc.pause(False)
            embed = discord.Embed(title="▶ Resumed!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.vc.playing:
            # If the player is playing, pause it.
            await self.vc.pause(True)
            embed = discord.Embed(title="⏸ Paused!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Nothing is currently playing.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.playing:
            await self.vc.stop()
            embed = discord.Embed(title="⏭ Skipped!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)                  
    

    @discord.ui.button(label="🚪 Stop", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc:
            await self.vc.disconnect()
            embed = discord.Embed(title="🚪 Disconnected from the voice channel.", color=discord.Color.green())            
            await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="➕ Volume Up", style=discord.ButtonStyle.primary)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc:
            current_volume = self.vc.volume
            new_volume = min(current_volume + 10, 100)
            await self.vc.set_volume(new_volume)
            embed = discord.Embed(title=f"🔊 Volume increased to {new_volume}.", color=discord.Color.green())            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="➖ Volume Down", style=discord.ButtonStyle.primary)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc:
            current_volume = self.vc.volume
            new_volume = max(current_volume - 10, 1)
            await self.vc.set_volume(new_volume)
            embed = discord.Embed(title=f"🔉 Volume decreased to {new_volume}.", color=discord.Color.green())            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⏪ Play Previous", style=discord.ButtonStyle.secondary)
    async def play_previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        global previous_track
        await interaction.response.defer()
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            if not interaction.user.voice:
                embed = discord.Embed(title="You must be in a voice channel!", color=discord.Color.red())                
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            vc = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        if previous_track:
            await self.vc.play(previous_track)
            embed = discord.Embed(title=f"🔁 Playing previous: {previous_track.title}", color=discord.Color.green())            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="No previous track available.", color=discord.Color.red())            
            await interaction.followup.send(embed=embed, ephemeral=True)
            

    @discord.ui.button(label="🎶 Now Playing", style=discord.ButtonStyle.secondary)
    async def now_playing(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc and self.vc.current:
            embed = discord.Embed(title=f"🎶 Now playing: {self.vc.current.title}", color=discord.Color.green())            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="No song is currently playing.", color=discord.Color.red())            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🗑 Clear Queue", style=discord.ButtonStyle.danger)
    async def clear_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        if guild_id in self.bot.queues and self.bot.queues[guild_id]:  # Now it works!
            self.bot.queues[guild_id] = []
            embed = discord.Embed(title="✅ The queue has been cleared!", color=discord.Color.green())            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="🚫 The queue is already empty!", color=discord.Color.red())            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary)
    async def Queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild_id = interaction.guild.id
    
        if guild_id not in bot.queues or not bot.queues[guild_id]:
            embed = discord.Embed(title="🚫 The queue is empty.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
    
        queue_list = '\n'.join(f'**{idx+1}.** {track.title}' for idx, track in enumerate(bot.queues[guild_id]))
        embed = discord.Embed(title=f"🎶 **Current Queue:**\n{queue_list}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)



# Play command - auto joins voice channel if needed
@bot.tree.command(name='play', description='Play a song or playlist')
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    vc: wavelink.Player = interaction.guild.voice_client
    if not vc:
        if not interaction.user.voice:
            embed = discord.Embed(title="You must be in a voice channel!", color=discord.Color.red())            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        vc = await interaction.user.voice.channel.connect(cls=wavelink.Player)

    # Check if the query is a playlist
    is_playlist = "list=" in query
    
    # Search for the track(s)
    tracks = await wavelink.Playable.search(query)
    if not tracks:
        embed = discord.Embed(title="No results found.", color=discord.Color.red())        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    if guild_id not in bot.queues:
        bot.queues[guild_id] = []
    
    if is_playlist:
        for track in tracks:
            bot.queues[guild_id].append(track)
        if not vc.playing:
            # Start playback and attach controls if nothing is playing
            await vc.play(bot.queues[guild_id].pop(0))
            view = MusicControls(vc)
            embed = discord.Embed(title=f"🎶 Now playing: {vc.current.title}", color=discord.Color.green())
            await interaction.followup.send(embed=embed, view=view)
        else:
            # If already playing, just confirm the addition without buttons
            embed = discord.Embed(title=f"🎶 Added {len(tracks)} tracks from the playlist to the queue.", color=discord.Color.blue())
            await interaction.followup.send(embed=embed)
    else:
        track = tracks[0]
        bot.queues[guild_id].append(track)
        if not vc.playing:
            # Start playback and attach controls if nothing is playing
            await vc.play(bot.queues[guild_id].pop(0))
            view = MusicControls(vc)
            embed = discord.Embed(title=f"🎶 Now playing: {vc.current.title}", color=discord.Color.green())            
            await interaction.followup.send(embed=embed, view=view)
        else:
            embed = discord.Embed(title=f"🎶 Added to queue: {track.title}", color=discord.Color.green())            
            # Just confirm addition without buttons
            await interaction.followup.send(embed=embed)



@bot.tree.command(name='nowplaying', description='Show the currently playing track.')
async def nowplaying(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.current:
        embed = discord.Embed(title=f"🎶 Now playing: {vc.current.title}", color=discord.Color.green())        
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="No song is currently playing.", color=discord.Color.red())        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='clearqueue', description='Clear the song queue.')
async def clearqueue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in bot.queues:
        bot.queues[guild_id] = []
        embed = discord.Embed(title="✅ Queue cleared!", color=discord.Color.green())        
        await interaction.response.send_message("✅ Queue cleared!")
    else:
        embed = discord.Embed(title="Queue is already empty.", color=discord.Color.red())        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='volume', description='Set the volume level (1-100).')
async def set_volume(interaction: discord.Interaction, volume: int):
    vc: wavelink.Player = interaction.guild.voice_client
    if not vc:
        embed = discord.Embed(title="🚫 I'm not connected to any voice channel.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    volume = max(1, min(100, volume))  # Ensure volume stays within 1-100
    await vc.set_volume(volume)  # Use set_volume() instead of setting vc.volume directly
    embed = discord.Embed(title=f"🔊 Volume set to {volume}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='skip', description='Skip the currently playing song.')
async def skip(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.playing:
        await vc.stop()
        embed = discord.Embed(title="⏭ Skipped!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="No song is currently playing.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='pause', description='Pause the currently playing song.')
async def pause(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.playing:
        await vc.pause(True)
        embed = discord.Embed(title="⏸ Paused!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="No song is currently playing.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='resume', description='Resume the paused song.')
async def resume(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.paused:
        await vc.pause(False)
        embed = discord.Embed(title="▶ Resumed!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="No song is paused.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='playprevious', description='Play the last played song')
async def playprevious(interaction: discord.Interaction):
    global previous_track
    await interaction.response.defer()
    
    vc: wavelink.Player = interaction.guild.voice_client
    if not vc:
        if not interaction.user.voice:
            embed = discord.Embed(title="You must be in a voice channel!", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        vc = await interaction.user.voice.channel.connect(cls=wavelink.Player)

    if previous_track:
        await vc.play(previous_track)
        embed = discord.Embed(title=f"🔁 Playing previous: {previous_track.title}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(title="No previous track available.", color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name='stop', description='Make the bot leave the voice channel.')
async def leave(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        embed = discord.Embed(title="🚪 Disconnected from the voice channel.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="I'm not connected to any voice channel.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)


# Queue command
@bot.tree.command(name='queue', description='View the queue')
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    
    if guild_id not in bot.queues or not bot.queues[guild_id]:
        embed = discord.Embed(title="🚫 The queue is empty.", color=discord.Color.red())
        await interaction.followup.send(embed=embed)
        return
    
    queue_list = '\n'.join(f'**{idx+1}.** {track.title}' for idx, track in enumerate(bot.queues[guild_id]))
    embed = discord.Embed(title=f"🎶 **Current Queue:**\n{queue_list}", color=discord.Color.green())
    await interaction.followup.send(embed=embed)

# Shuffle command - Shuffles the queue
@bot.tree.command(name='shuffle', description='Shuffle the queue')
async def shuffle(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id

    if guild_id in bot.queues and bot.queues[guild_id]:
        random.shuffle(bot.queues[guild_id])  # Shuffle the queue list
        embed = discord.Embed(title="🔀 Queue shuffled successfully!", color=discord.Color.green())
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(title="🚫 The queue is empty.", color=discord.Color.red())
        await interaction.followup.send(embed=embed)
        
@bot.tree.command(name="247", description="Enable or disable 24/7 mode for the bot.")
async def _247(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    await interaction.response.defer()  # Prevents the 3-second timeout issue

    guild_id = interaction.guild.id

    if not hasattr(bot, "is_247"):
        bot.is_247 = {}

    if guild_id in bot.is_247 and bot.is_247[guild_id]:  # If 24/7 is enabled, disable it
        bot.is_247[guild_id] = False
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
        embed = discord.Embed(title="✅ 24/7 mode disabled. The bot will now leave when inactive.", color=discord.Color.green())
        return await interaction.followup.send(embed=embed)

    if channel is None:
        embed = discord.Embed(title="❌ You must specify a voice channel!", color=discord.Color.red())
        return await interaction.followup.send(embed=embed, ephemeral=True)

    bot.is_247[guild_id] = True
    vc = interaction.guild.voice_client

    if not vc:
        vc = await channel.connect()
    else:
        await vc.move_to(channel)
    embed = discord.Embed(title=f"✅ 24/7 mode enabled in {channel.mention}. The bot will stay indefinitely.", color=discord.Color.green())
            
    await interaction.followup.send(embed=embed)
    
@bot.tree.command(name='loop', description='Loop the current song.')
async def loop(interaction: discord.Interaction):
    times = 3
    voice_client = interaction.guild.voice_client
    
    if not voice_client or not voice_client.playing:
        await interaction.response.send_message("No song is currently playing!", ephemeral=True)
        return
    
    if times < 0:
        await interaction.response.send_message("Please enter a valid number (0 for infinite, or any positive integer).", ephemeral=True)
        return
    
    # Store the repeat count in a dictionary or any persistent storage
    bot.repeat_count[interaction.guild.id] = times  # 0 means infinite repeat
    
    await interaction.response.send_message(f"Repeating the current song {'infinitely' if times == 0 else f'{times} times'}! 🔁")

    ########################################### UTLS ##################################################



@bot.tree.command(name="ping", description="Check the bot's latency with detailed statistics")
async def ping(interaction: discord.Interaction):
    """Displays bot latency, message latency, Lavalink latency, and API latency in an aesthetic format."""
    
    start_time = time.perf_counter()  # Start timing
    await interaction.response.send_message("🏓 Pinging...")  # Send initial message
    end_time = time.perf_counter()  # End timing
    
    message_latency = round((end_time - start_time) * 1000)  # Time taken for message response
    bot_latency = round(bot.latency * 1000)  # WebSocket latency in ms

    # ✅ Discord API Latency
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v10/gateway") as resp:
            header_latency = resp.headers.get("X-Response-Time", "0ms")
            api_latency = round(float(header_latency.replace("ms", "").strip())) if "ms" in header_latency else "N/A"

    # 🎨 Embed Response
    embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
    embed.add_field(name="🤖 Bot Latency", value=f"{bot_latency}ms", inline=True)
    embed.add_field(name="📩 Message Latency", value=f"{message_latency}ms", inline=True)
    embed.add_field(name="🛰 Discord API Latency", value=f"{api_latency}ms", inline=True)
    embed.set_footer(text="Made By willsmith5314 | Latency Checker")

    await interaction.edit_original_response(content=None, embed=embed)


@bot.tree.command(name="help", description="Get a list of all available commands")
async def help_command(interaction: discord.Interaction):
    """Displays a categorized list of bot commands in an elegant embed."""
    
    embed = discord.Embed(title="❓ Help Menu", description="Here are all the commands available:", color=discord.Color.blue())
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)

    # 🎵 Music Commands
    embed.add_field(
        name="🎵 Music Commands",
        value=(
            "**`/play [query]`** - Play a song from YouTube/Spotify\n"
            "**`/nowplaying`** - Show the currently playing track\n"
            "**`/queue`** - View the current queue\n"
            "**`/skip`** - Skip the current track\n"
            "**`/playprevious`** - Play the previously played song\n"
            "**`/pause`** - Pause the current song\n"
            "**`/resume`** - Resume paused music\n"
            "**`/stop`** - Stop playback and clear the queue\n"
            "**`/clearqueue`** - Remove all tracks from the queue\n"
            "**`/shuffle`** - Shuffle the queue\n"
            "**`/loop`** - Toggle loop \n"
            "**`/volume [0-100]`** - Adjust music volume\n"
            "**`/247 [on | off]`** - Enable or disable 24/7 mode\n"
        ),
        inline=False
    )

    # 🛠 Utility Commands
    embed.add_field(
        name="🛠 Utility Commands",
        value=(
            "**`/ping`** - Check bot latency & Lavalink ping\n"
            "**`/stats`** - View bot statistics\n"
            "**`/invite`** - Get the bot invite link\n"
            "**`/help`** - Display this help menu\n"
        ),
        inline=False
    )

    embed.set_footer(text="Made By willsmith5314 | Created with ❤️")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stats", description="Get bot statistics and system information")
async def stats(interaction: discord.Interaction):
    """Displays bot system statistics in an aesthetic embed."""
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_used = round(memory.used / (1024**3), 1)  # Convert to GB
    memory_total = round(memory.total / (1024**3), 1)  # Convert to GB
    
    # CPU usage
    cpu_usage = psutil.cpu_percent()
    cpu_model = platform.processor() or "Unknown CPU"
    
    # System architecture and platform
    arch = platform.architecture()[0]
    system_platform = platform.system().lower()
    
    # Uptime
    uptime_seconds = int(time.time() - bot_start_time)
    uptime_str = str(timedelta(seconds=uptime_seconds))  # Format uptime
    
    # Get bot statistics
    total_users = sum(guild.member_count for guild in bot.guilds)
    total_servers = len(bot.guilds)
    total_channels = sum(len(guild.channels) for guild in bot.guilds)
    
    # Bot Latency
    bot_latency = round(bot.latency * 1000)  # Convert to ms
    
    # Embed Setup
    embed = discord.Embed(title="📊 Bot Statistics", description="Made by **willsmith5314**", color=discord.Color.blue())
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.add_field(name="⏳ Memory Usage", value=f"{memory_used} GB / {memory_total} GB", inline=False)
    embed.add_field(name="⌚️ Uptime", value=uptime_str, inline=False)
    embed.add_field(name="📁 Users", value=f"{total_users}", inline=True)
    embed.add_field(name="📁 Servers", value=f"{total_servers}", inline=True)
    embed.add_field(name="📁 Channels", value=f"{total_channels}", inline=True)
    embed.add_field(name="👾 Discord.py", value=f"v{discord.__version__}", inline=True)
    embed.add_field(name="🏓 Ping", value=f"{bot_latency}ms", inline=True)
    embed.add_field(name="🤖 CPU Usage", value=f"{cpu_usage}%", inline=True)
    embed.add_field(name="🤖 Arch", value=f"{arch}", inline=True)
    embed.add_field(name="💻 Platform", value=f"{system_platform}", inline=True)
    embed.add_field(name="🤖 CPU", value=f"Ryzen 7 5700X 8-Core Processor   ", inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="invite", description="Get the invite link for the bot")
async def invite(interaction: discord.Interaction):
    """Sends an embed with the bot invite link and support server."""

    embed = discord.Embed(title="🔗 Invite Me!", description="Click the link below to invite me to your server!", color=discord.Color.blue())
    embed.add_field(name="🤖 Bot Invite Link", value=f"[Click Here to Invite]({bot_invite_link})", inline=False)
    embed.add_field(name="🌍 Support Server", value=f"[Join Support Server]({support_server_link})", inline=False)
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text="Made By willsmith5314 | Bringing Music to Your Server 🎶")

    await interaction.response.send_message(embed=embed)

bot.run("DISCORD_BOT_TOKEN")
