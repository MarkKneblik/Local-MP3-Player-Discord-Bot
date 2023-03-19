import discord # import discord api
from discord.ext import commands #for user commands
from asyncio import Event
import queue # for song queue
import os # for searching for audio files in user's 'Music' directory

TOKEN = 'NzQ4NTg3ODI0NzUxNzA2MTc2.GqyBZX.iRWago6kMjWBvszfhrfhhNZIHLdlo1iif0hBG0'

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = commands.Bot(command_prefix='/', intents=intents) # initialize client with command prefix '/'

skipped = Event()
generalText = None # initialize general text channel to null
generalVoice = None # initialize general voice channel to null
voiceClient = None # initialize voice client to null
song_queue = queue.Queue(maxsize=0) # initialize song queue to hold any amount of songs
exec = "C:/VSCode Projects/Local MP3 Bot/ffmpeg-2023-03-05-git-912ac82a3c-full_build/bin/ffmpeg" 

@client.event
async def on_ready():   # called when bot has connected to server
     global generalText
     generalText = discord.utils.get(client.get_all_channels(), name='general') # search all channels for 'general' text channel
     await generalText.send('Local MP3 Player has arrived! Type "/commands" to view commands.')

@client.command(name='join')
async def join(ctx):
    global generalVoice
    voice_state = ctx.message.author.voice
    if voice_state is None: # check if message author is in a voice channel
        await generalText.send('You must be connected to a voice channel to invite the player.')
    elif generalVoice is not None: # check if player is already connected to a voice channel
        await generalText.send('Player is already connected to a voice channel.')
    else:
        generalVoice = ctx.author.voice.channel
        await generalVoice.connect() # connect to voice channel

@client.command(name='disconnect')
async def disconnect(ctx): 
    global generalVoice
    if generalVoice is None: # if player is not connected to a voice channel
        await generalText.send('Cannot disconnect if player is not in a voice channel.')
    else:
        voiceClient = ctx.author.guild.voice_client
        generalVoice = None # reset general voice channel to null
        voiceClient.stop() # stop voice client
        while not song_queue.empty(): # clear queue before disconnecting
            song_queue.get()
        await voiceClient.disconnect()
        

def checkQueue():
    if(not song_queue.empty()): # if queue is not empty 
        src = song_queue.get() # pop off front of queue
        voiceClient.play(discord.FFmpegPCMAudio(executable=exec, source=src), after=lambda x=None: checkQueue()) # play song from front of queue and call checkQueue recursively to check if there is anything in the queue

@client.command(name='play')
async def play(ctx, *arg):
    global generalVoice
    global voiceClient
    voiceClient = ctx.author.guild.voice_client # get voiceClient of guild

    if generalVoice is None:
        await generalText.send('Cannot play song, player is not in a voice channel.')

    else: # if there is a voice client
        song_arg = " ".join(arg) # form song name from tuple
        music_directory = "C:/Users/Mark/Music/" # root directory for searching for songs
        song_to_find = song_arg
        song_name = None # initialize song name to null

        for relative_path, dirs, files in os.walk(music_directory): # traverse files and subdirectories
            if (song_to_find  + '.mp3') in files: # if song name entered is an mp3 and is found
                song_name = os.path.join(music_directory, relative_path, (song_to_find  + '.mp3')) # form song name
            elif (song_to_find  + '.m4a') in files: # if song name entered is an m4a and is found
                song_name = os.path.join(music_directory, relative_path, (song_to_find  + '.m4a')) # form song name

        if song_name is None: # if song was not found
            await generalText.send('Cannot play song, please enter a valid song name.')
        else:
            song_queue.put(song_name) # put song name at end of queue
            if song_queue.qsize() > 0 and (voiceClient.is_playing() or voiceClient.is_paused()): # ensures that 'song added to queue' message is not sent if it is the first song added to queue
                await generalText.send('Song added to queue.')
            if(not voiceClient.is_playing() and not voiceClient.is_paused()): # if a song is not playing or paused
                src = song_queue.get() # pop off the front of queue
                voiceClient.play(discord.FFmpegPCMAudio(executable=exec, source=src), after=lambda x=None: checkQueue()) # play song at front of queue. after song finishes, check the queue to see if there are more songs to be played

@client.command(name='pause')
async def pause(ctx):
    global generalVoice
    if generalVoice is None:
        await generalText.send('Cannot pause, player is not in a voice channel.')
    elif voiceClient.is_paused():
        await generalText.send('Song is already paused.')
    elif not voiceClient.is_playing():
        await generalText.send('Cannot pause, player has already been stopped.')
    else: # if player is playing, pause
        voiceClient.pause()

@client.command(name='resume')
async def resume(ctx):
    global generalVoice
    if generalVoice is None:
        await generalText.send('Cannot resume, player is not in a voice channel.')
    elif voiceClient.is_paused(): # if player is paused, resume
        voiceClient.resume()
    else:
        await generalText.send("Cannot resume if a song isn't paused.")

@client.command(name='skip')
async def skip(ctx):
    global generalVoice
    if generalVoice is None:
        await generalText.send('Cannot skip, player is not in a voice channel.')
    elif ((voiceClient is None) or (not voiceClient.is_playing()) and (not voiceClient.is_paused())):
        await generalText.send('Cannot skip if a song is not playing or paused.')
    else:
        voiceClient.stop() # stop the player. checkQueue() continues running in another thread, so it will enter its 'if' statement after this stops

@client.command(name='stop')
async def stop(ctx):
    global generalVoice
    if generalVoice is None:
        await generalText.send('Cannot stop, player is not in a voice channel.')
    elif voiceClient is None:
        await generalText.send('No song is playing or paused.')
    else: # if player is playing or is paused, stop player
        voiceClient.stop()
        if not song_queue.empty(): # clear queue after stopping player
            song_queue.get()

@client.command(name='commands')
async def commands(ctx):
    commands_message = """
    **/join** - connects player to voice channel of user that issued the command.
    **/play** - plays a song if queue is empty. If queue is not empty, adds song to queue.
    **/pause** - pauses song if a song is playing.
    **/resume** - resumes song if a song is paused.
    **/skip** - skips to the next song in queue.
    **/stop** - stops player and clears queue.
    **/disconnect** - disconnects player from its voice channel."""
    await generalText.send(commands_message)

client.run(TOKEN)
