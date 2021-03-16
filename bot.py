import discordCity as city
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import nacl
import random
import tenorpy
import asyncio
import time
import datetime
import math

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


client = discord.Client()
bot = commands.Bot(command_prefix='city ')
global nospeak
nospeak = False



@bot.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    
    #global nospeak
    #nospeak = False







#print(TOKEN)
class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot    


    @commands.command(name="create",help=": generates a city map from users in the server",pass_context=True)
    async def create_city(self, ctx):
        #x = city.do_City(20)
        async with ctx.channel.typing():
            time1 = datetime.datetime.now()
            y = ctx.guild.fetch_members()
            y = await y.flatten()
            #y = ctx.guild.members
            messages = []
            
            await ctx.message.add_reaction("<a:Typing:524609345585938444>")

            for channel in ctx.guild.channels:
                
                try:
                    print(channel)
                    channel = discord.utils.get(ctx.guild.text_channels, name=channel.name)
                    messages += await channel.history(limit=500).flatten()
                    #print(channel,x)
                except:
                    pass
            
            memberList = []
            for member in y:
                try:
                
                    mNum = 2*len(list(filter(lambda x: x.author == member, messages)))
                    memberList.append(self.Member(member, member == ctx.guild.owner, mNum))
                    #print(member.name,mNum)
                except:
                    print("pass")
                    pass
            
            #seconds_past = (datetime.datetime.now()-time1)
            time2 = datetime.datetime.now()
            await ctx.send("time elapsed for fetching messages: {0} seconds".format((time2-time1).seconds))
            city.do_City(memberList)
            time3 = datetime.datetime.now()
            await ctx.send("time elapsed for creating image: {0} seconds".format((time3-time2).seconds))
            await ctx.send(file=discord.File("test.png"))
            await ctx.send(file=discord.File("test.svg"))
            await ctx.message.remove_reaction("<a:Typing:524609345585938444>",self.bot.user)

    
            
        
    class Member:
        def __init__(self,member,owner,mCount):
            self.colour = member.colour.to_rgb()
            self.mention = member.name
            self.owner = owner
            self.messageCount = mCount
            self.joinDate = member.joined_at
            self.boosting = member.premium_since != None
            self.boostSince = member.premium_since
            self.administrator = member.guild_permissions.administrator


    
bot.add_cog(Main(bot))
#client.run(TOKEN)
bot.run(TOKEN)
