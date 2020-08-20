import discord
from discord.ext import commands
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000


class ColorRecordRGB():
    '''save color's rgb in dec'''

    def __init__( self, r: int, g: int, b: int ):
        self.r = r
        self.g = g
        self.b = b

    def rgb_to_lab( self ):
        self.lab = convert_color( sRGBColor( self.r, self.g, self.b ), LabColor )
        return self.lab

    def compare_with_CIEDE2000( self, otherColor ):
        if not isinstance( otherColor, ColorRecordRGB ):
            return -1
        return delta_e_cie2000( self.rgb_to_lab(), otherColor.rgb_to_lab(), Kl=1, Kc=1, Kh=1 )


class CogReturnCalculation( commands.Cog, name='Calculation Commands' ):
    '''These are the Calculation commands'''

    def __init__( self, bot ):
        self.bot = bot

    async def cog_check( self, ctx ):
        '''
  The default check for this cog whenever a command is used. Returns True if the command is allowed.
  '''
        return True

    @commands.group( name="CIEDE2000", aliases=[ 'c2', 'c2000' ] )
    async def CIEDE2000( self, ctx: commands.Context ):
        pass

    @CIEDE2000.command( name='code&code', aliases=[ 'cc' ] )
    async def compare_code_and_code( self, ctx: commands.Context, code1: str = '#000000', code2: str = '#000000' ):
        dRGB_1 = int( code1.replace( '#', '' ), 16 )
        dRGB_2 = int( code2.replace( '#', '' ), 16 )
        if dRGB_1 >= 256**3 or dRGB_2 >= 256**3:
            await ctx.send( f"{'arg1' if dRGB_1 >= 256**3 else 'arg2'} is not right" )
            return
        color_1 = ColorRecordRGB( dRGB_1 // 65536, ( dRGB_1 % 65536 ) // 256, dRGB_1 % 256 )
        color_2 = ColorRecordRGB( dRGB_2 // 65536, ( dRGB_2 % 65536 ) // 256, dRGB_2 % 256 )
        await ctx.send( color_1.compare_with_CIEDE2000( color_2 ) )

    @CIEDE2000.command( name='code&role', aliases=[ 'cr' ] )
    async def compare_code_and_role( self, ctx: commands.Context, code: str, role: discord.Role ):
        dRGB_1 = int( code.replace( '#', '' ), 16 )
        if dRGB_1 >= 256**3:
            await ctx.send( f"{'arg1' if dRGB_1 >= 256**3 else 'arg2'} is not right" )
            return
        color_1 = ColorRecordRGB( dRGB_1 // 65536, ( dRGB_1 % 65536 ) // 256, dRGB_1 % 256 )
        color_2 = ColorRecordRGB( role.color.r, role.color.g, role.color.b )
        await ctx.send( color_1.compare_with_CIEDE2000( color_2 ) )

    @CIEDE2000.command( name='role&role', aliases=[ 'rr' ] )
    async def compare_role_and_role( self, ctx: commands.Context, role1: discord.Role, role2: discord.Role ):
        color_1 = ColorRecordRGB( role1.color.r, role1.color.g, role1.color.b )
        color_2 = ColorRecordRGB( role2.color.r, role2.color.g, role2.color.b )
        await ctx.send( color_1.compare_with_CIEDE2000( color_2 ) )


def setup( bot ):
    bot.add_cog( CogReturnCalculation( bot ) )
