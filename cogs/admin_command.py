import discord
from discord.ext import commands
import json


class admin_commands( commands.Cog, name='Admin Commands' ):
    '''These are the deal with reaction'''

    def __init__( self, bot ):
        self.bot = bot

    async def cog_check( self, ctx ):
        '''
    The default check for this cog whenever a command is used. Returns True if the command is allowed.
    '''
        return True

    @commands.group( name="Roles_corresponds_to_the_Reactions", aliases=[ 'RC2R' ] )
    async def Roles_corresponds_to_the_Reactions( self, ctx: commands.context ):
        pass

    @Roles_corresponds_to_the_Reactions.command( name='new_correspondence', aliases=[ 'nc' ] )
    async def new_correspondence( self, ctx: commands.context, msg: discord.Message, emojis: str, roles: str ):
        j_dict = { 'msg': msg.id, 'emoji': emojis.split(), 'role': roles.replace( '<@&', '' ).replace( '>', '' ).split() }
        j_str = json.dumps( j_dict, sort_keys=True, indent=4, separators=( ',', ': ' ), ensure_ascii=False )
        await ctx.send( f'```css\n{j_str}\n```' )
        print( roles.replace( '<@&', '' ).replace( '>', '' ).split() )

    @Roles_corresponds_to_the_Reactions.command( name='view_correspondence', aliases=[ 'vc' ] )
    async def view_correspondence( self, ctx: commands.context ):
        await ctx.send( f'{str(ctx.message.content)}' )


def setup( bot ):
    bot.add_cog( admin_commands( bot ) )
