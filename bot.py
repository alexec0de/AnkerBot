import discord
from discord.ext import commands, tasks
from discord.utils import get
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
import contextlib
import io
import os
import logging
import aiohttp
import aeval
import sys
import time
import youtube_dl


import datetime
import requests
from db import DataBase
from Cybernator import Paginator
#import time
import asyncio
import random

PREFIX = '$'

client = commands.Bot(command_prefix = PREFIX)
client.remove_command('help')
hello = ['hello', 'hi', 'привет', 'хай', 'здарова', 'здравствуйте', 'ky', 'privet', 'ку']
goodbye = ['пока', 'bye']

db = DataBase()

 
def minify_text(txt):
    if len(txt) >= 1024:
        return f'''{str(txt)[:-900]}...
        ...и ещё {str(txt).replace(str(txt)[:-900], "")} символов...'''
    else:
        return str(txt)

@client.event
async def on_ready():
	await db.create_table()
	for guild in client.guilds:
	#	print(guild.members)
		for member in guild.members:
			#print(member)
			await db.insert_new_member(member)
	DiscordComponents(client)
	print('BOT ready')
	
	
	await client.change_presence(activity=discord.Streaming(name='команду {}help'.format(PREFIX), url="https://www.twitch.tv/qrushcsgo"))
	
	
@client.event
async def on_member_join(member):
	await db.insert_new_member(member)



@client.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.MissingPermissions):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Недостаточно прав!!')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)
	elif isinstance(error, commands.CommandNotFound):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Команда не найдена посмотрите {}help'.format(PREFIX))
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)
	print(error)
#	await ctx.send(error)

	
@client.event
async def on_message(message):
	await client.process_commands(message)
	msg = message.content.lower()
	
	if msg in hello:
		await message.channel.send('Привет, как дела')
	if msg in goodbye:
		await message.channel.send('Давай, пока скоро увидемся')

#clear message
@client.command(pass_context = True)
@commands.has_permissions(administrator = True)
async def clear(ctx, amount : int):
	await ctx.channel.purge(limit=amount)
	
#kick
@client.command(pass_context = True)
@commands.has_permissions(administrator = True)
async def kick(ctx, member: discord.Member, *, reason = None):
	await ctx.channel.purge(limit=1)
	await member.kick(reason=reason)
	await ctx.send(f'Я кикнул пользователя {member}')

#ban
@client.command(pass_context = True)
@commands.has_permissions(administrator = True)
async def ban(ctx, member: discord.Member, *, reason = None):
	await ctx.channel.purge(limit=1)
	await member.ban(reason=reason)
	await ctx.send(f'Я забанил пользователя {member}')

#help
@client.command(pass_context = True)
async def help(ctx):
	emd = discord.Embed(title = 'Модиративные команды', description = '{}clear - Отчистка чата\n{}kick - Удаление пользователя из сервера\n{}ban - Ограничение доступа к серверу пользователя\n{}mute - Ограничение доступа к чату серверa\n{}eval - Штука для разроботчика'.format(PREFIX, PREFIX, PREFIX, PREFIX, PREFIX))
	
	emd2 = discord.Embed(title = 'Основные команды', description = f'{PREFIX}time - Узнать время\n{PREFIX}server - Узнать инфу о сервере')
	emd3 = discord.Embed(title = 'Игры', description = f'{PREFIX}8ball - Игра про макический шарик\n{PREFIX}coin -Орёл и Решка')
	emd4 = discord.Embed(title= 'Экономика', description = f'{PREFIX}cash - Узнать свой баланс\n{PREFIX}award - Добавить пользователю баланс')
	emd5 = discord.Embed(title= 'Музыка', description = f'{PREFIX}join - Присоедится к каналу\n{PREFIX}leave - Выйти из канала\n{PREFIX}play - Сыграть музыку\n{PREFIX}pause - Остановить музыку\n{PREFIX}resume - Продолжить проигрование')
	emds = [emd, emd2, emd3, emd4, emd5]
	
	message = await ctx.send(embed = emd)
	page = Paginator(client, message, only=ctx.author, use_more = False, embeds = emds)
	await page.start()
	
	

#mute
@client.command()
@commands.has_permissions(administrator = True)
async def mute(ctx, member:discord.Member):
	mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
	await member.add_roles(mute_role)
	
	
#time
@client.command()
async def time(ctx):
	emb = discord.Embed(title = 'Время', colour = discord.Color.green())
	emb.set_author(name = client.user.name, icon_url = client.user.avatar_url)
	emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
	
	now_date = datetime.datetime.now()
	emb.add_field(name='Time', value = "Time:{}".format(now_date))
	
	await ctx.send(embed = emb)
	

#user info
#@client.command()
#async def user(ctx):
#	pass

#cash
@client.command()
async def cash(ctx, member: discord.Member = None):
	if member == None:
		await db.insert_new_member(ctx.author)
		cash = await db.get_data(ctx.author)
		await ctx.send(embed = discord.Embed(
			description = f"""Баланс пользователя **{ctx.author}** составляет **{cash['balance']}**"""
		))
	else:
		await db.insert_new_member(member)
		balance = await db.get_data(member)
		await ctx.send(embed = discord.Embed(
			description = f"""Баланс пользователя **{member}** составляет **{balance['balance']}**"""
		))



@client.command()
async def award(ctx, member: discord.Member, cash:int):
	if ctx.author.id == 707241794336718891:
		await db.update_member("UPDATE users SET balance = balance + ? WHERE member_id = ? AND guild_id = ?", [cash, member.id, ctx.guild.id])
		await ctx.message.add_reaction("💖")
	else:
		await ctx.send('Эта команда только для разраба')


#eval 
@client.command()
async def eval(ctx, *, ucode=None):
	if ctx.author.id != 707241794336718891:
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Эта команда только для разробочика!!')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		return await ctx.send(embed = emd)
	code = '\n'.join(ucode.split('\n')[1:])[:-3] if ucode.startswith('```') and ucode.endswith('```') else ucode
	libs = {
	'discord': discord,
	'commands': commands,
	'bot': client,
	'client': client,
	'ctx': ctx
	}
	try:
		reval = await aeval.aeval(code, libs, {})
		emb = discord.Embed(title=f'Успешно:',description=f'**Входные данные** - \n```py\n{code}\n```\n'
                        f'**Выходные данные** - \n```py\n{reval}\n```\n', color=discord.Color.green())
		await ctx.send(embed=emb)
	except Exception as exception:
		emb = discord.Embed(title=f'Ошибка:',
    	description='**Входные данные** - \n```py\n{code}\n```\n'
                        f'**Выходные данные** - \n```py\n{exception}\n```\n',
                        color=discord.Color.red())
		await ctx.send(embed=emb)

@client.command()
async def server(ctx):
    embed = discord.Embed(title = f"{ctx.guild.name}", description = "Информация о сервере", color = discord.Colour.blue())
    embed.add_field(name = '🆔Server ID', value = f"{ctx.guild.id}", inline = True)
    embed.add_field(name = '📆Created On', value = ctx.guild.created_at.strftime("%b %d %Y"), inline = True)
    embed.add_field(name = '👑Owner', value = f"{ctx.guild.owner}", inline = True)
    embed.add_field(name = '👥Members', value = f'{ctx.guild.member_count} Members', inline = True)
    embed.add_field(name = '💬Channels', value = f'{len(ctx.guild.text_channels)}Text | {len(ctx.guild.voice_channels)} Voice', inline = True)
    embed.add_field(name = '🌎Region', value = f'{ctx.guild.region}', inline = True)
    embed.set_thumbnail(url = ctx.guild.icon_url)
    embed.set_footer(text = "⭐ • Duo")
    embed.set_author(name = f'{ctx.author.name}', icon_url = ctx.message.author.avatar_url)
    await ctx.send(embed=embed)

#game
#8ball
@client.command(name = '8ball')
async def ball(ctx, ques=""):
	if ques=="":
		await ctx.send("Задай мне вопрс")
	else:
		choices = [
            'Надо подумать.', 'Может быть да а может быть нет', 'Хз.', 'Да - Конечно.', 'Спроси меня ещё-раз',
            'Я смотрю и вижу ответ - Да.', 'Нет.', 'Outlook good.', 'Да.'
            ]
		await ctx.send(f" {random.choice(choices)}")

#coin
@client.command() 
async def coin(ctx):
    Coin = {
        0: "***Орел***",
        1: "***Решка***",
    }
    side_of_the_coin = random.randint(1, 1000)
    await ctx.send(f'{Coin[side_of_the_coin%2]}')

#music
#join
@client.command()
async def join(ctx):
    global voice
    try:
        if ctx.message.author.voice == None:
            await ctx.send(f'{ctx.message.author.mention}, может сначала ты на канал зайдешь?')
            return

        channel = ctx.author.voice.channel
        voice = await channel.connect()
    except:
        await ctx.send(f'Ну не кричи ты так, тут я, тут...')
        channel = ctx.author.voice.channel
        voice = await channel.connect()

#leave
@client.command()
async def leave(ctx):
    global voice
    try:
        #TrackQueue_1.clean()
        await ctx.voice_client.disconnect()
    except AttributeError:
        await ctx.send(f'Да ушел я уже, ушел, что ты такой злой?...')

#pause
@client.command()
async def pause(ctx):
	voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
	if voice.is_playing():
		voice.pause()
	else:
		await ctx.send('Вы не можите остановить музыку')
		
#resume
@client.command()
async def resume(ctx):
	voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
	if voice.is_paused():
		voice.resume()
	else:
		await ctx.send('Вы не можите включить музыку')

@client.command()
async def play(ctx, url: str):

    def check_queue():
        Queue_infile = os.path.isdir("./Queue")
        if Queue_infile is True:
            DIR = os.path.abspath(os.path.realpath("Queue"))
            length = len(os.listdir(DIR))
            still_q = length - 1
            try:
                first_file = os.listdir(DIR)[0]
            except:
                print("No more queded song(s)\n")
                queues.clear()
                return
            main_location = os.path.dirname(os.path.realpath(__file__))
            song_path = os.path.abspath(os.path.realpath("Queue") + "\\" + first_file)
            if length != 0:
                print("Song done, playing next queued\n")
                print(f"Songs still in queue: {still_q}")
                song_there = os.path.isfile("song.mp3")
                if song_there:
                    os.remove("song.mp3")
                shutil.move(song_path, main_location)
                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, 'song.mp3')
                voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.07
            else:
                queues.clear()
                return
        else:
            queues.clear()
            print("No songs were queued before the ending of the last song\n")
    previous_song = os.path.isfile("song.mp3")
    try:
        if previous_song:
            os.remove("song.mp3")
            queues.clear()
            print("Removed old song file")
    except PermissionError:
        print('Trying to delete song file, but it is playing')
        await ctx.send("Silly {0.display_name}, I am playing this song now".format(ctx.author))
        return
    
    Queue_infile = os.path.isdir("./Queue")

    try:
        Queue_folder = ("./Queue")
        if Queue_infile is True:
            print("Removed old queue folder")
            shutil.rmtree(Queue_folder)
    except:
        print("No old Queue folder")

    await ctx.send("Braum is on the job!") 

    voice = get(client.voice_clients, guild = ctx.guild)
    ydl_opts = {
         'format': 'bestaudio/best',
         'quiet': True,
         'postprocessors':[{
            'key':'FFmpegExtractAudio',
            'preferredcodec':'mp3',
            'preferredquality':'192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print('Downloading audio now\n')
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            name = file
            print(f"Renamed File: {file}\n")
            os.rename(file, "song.mp3")
    voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.07

    nname = name.rsplit("-", 2)
    await ctx.send(f"Playing: {nname}")
    print("Playing\n")

#error
@clear.error
async def clear_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Введите кол-во сообщений')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)
	
@ban.error
async def ban_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Введите пользователя которого хотите забанить')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)

@kick.error
async def kick_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Введите пользователя которого хотите кикнуть')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)


@mute.error
async def mute_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Введите пользователя которого хотите замьютить')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)


@award.error
async def award_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		emd = discord.Embed(title = '🛑Ошибка🛑', colour=discord.Color.red())
		emd.add_field(value=f'{ctx.author.name} совершил ошибку!!', name = 'Введите пользователя или сумму')
		emd.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = emd)
		

token = open('token.txt', 'r').readline()
client.run(token)