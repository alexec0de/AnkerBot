import discord
from discord.ext import commands, tasks
from discord.utils import get
#,from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
import contextlib
import io
import os
import logging
import aiohttp
import aeval
import sys
#import time
import youtube_dl


import requests
from db import DataBase
from Cybernator import Paginator
#import time
import asyncio
import random

PREFIX = '$'

client = commands.Bot(command_prefix = PREFIX, intents = discord.Intents.all())
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
	emd3 = discord.Embed(title = 'Игры', description = f'{PREFIX}8ball - Игра про макический шарик')
	emd4 = discord.Embed(title= 'Экономика', description = f'{PREFIX}cash - Узнать свой баланс\n{PREFIX}award - Добавить пользователю баланс\n{PREFIX}add-role- Добавить роль в магазин\n{PREFIX}rem-role - Удалить роль из магазина\n{PREFIX}buy - Купить роль\n{PREFIX}shop - Просмотреть доступные роли')

	emds = [emd, emd2, emd3, emd4]
	
	message = await ctx.send(embed = emd)
	page = Paginator(client, message, only=ctx.author, use_more = False, embeds = emds)
	await page.start()
	
	

#mute
@client.command()
@commands.has_permissions(administrator = True)
async def mute(ctx, member:discord.Member):
	mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
	await member.add_roles(mute_role)
	

	

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
@commands.has_permissions(manage_messages=True)
async def award(ctx, member: discord.Member, cash:int):
	await db.update_member("UPDATE users SET balance = balance + ? WHERE member_id = ? AND guild_id = ?", [cash, member.id, ctx.guild.id])
	await ctx.message.add_reaction("💖")



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
#soonz
#add-role
@client.command(name = 'add-role')
@commands.has_permissions(administrator = True)
async def add_role(ctx, role: discord.Role, cost: int=0):
	if cost < 0:
		await ctx.send("Сумма не должна быть меньше 0")
	else:
		await db.insert_new_role(role, cost) 
		await ctx.message.add_reaction("💖")

@client.command(name = 'rem-role')
@commands.has_permissions(administrator = True)
async def remove_role(ctx, role: discord.Role):
        if ctx.guild.get_role(role.id) is None:
            await ctx.send("Роли не существует")
        else:
            await db.delete_role_from_shop(role)
            await ctx.message.add_reaction("💖")
            
@client.command(name = 'buy')
async def buy_role(ctx, role: discord.Role):
        if ctx.guild.get_role(role.id) is None:
            await ctx.send("Роли не существует")
        elif role in ctx.author.roles:
            await ctx.send("У вас уже имеется такая роль")
        else:
            role_data = await db.get_shop_data(role)
            balance = await db.get_data(ctx.author)

            if balance["balance"] < role_data["cost"]:
                await ctx.send("Недостаточно средств")
            elif balance["balance"] <= 0:
                await ctx.send("Недостаточно средств")
            else:
                await db.update_member("UPDATE users SET balance = balance - ? WHERE member_id = ? AND guild_id = ?", [role_data["cost"], ctx.author.id, ctx.guild.id])

                await ctx.author.add_roles(role)
                await ctx.message.add_reaction("💖")
                
@client.command()
async def shop(ctx):
        embed = discord.Embed(title="Магазин ролей")

        data = await db.get_shop_data(ctx.guild.id, all_data=True)
        for row in data:
            if ctx.guild.get_role(row["role_id"]) is not None:
                embed.add_field(
                    name=f"Стоимость: {row['cost']}",
                    value=f"Роль: {ctx.guild.get_role(row['role_id']).mention}",
                    inline=False
                )

        await ctx.send(embed=embed)

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