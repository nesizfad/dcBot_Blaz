import discord
from discord.ext import commands
import sys
import os
from collections import deque
import json
import datetime

g_users_cache = {}
g_xp_to_roles_dict = {
    1: 741691856890495046,
    2: 741691937299365919,
    3: 741691975626915921,
    4: 741692028689186856,
    5: 741692072729247874,
    6: 741692127410651189
}


def load_data( path: str, user: discord.Member ) -> dict:
    if not os.path.exists( os.path.dirname( path ) ):
        os.makedirs( os.path.dirname( path ) )
    try:
        with open( path, 'r' ) as fr:
            #print(fr)
            users_level_data = json.load( fr )
            #print( users_level_data )
    except FileNotFoundError as noFile:
        print( str( noFile ) + ' and created one' )
        open( path, 'w' ).close()
        users_level_data = {}
    except IOError as e:
        print( 'IOERROR : ' + str( e ) )
    if str( user.id ) not in users_level_data.keys():
        users_level_data[ str( user.id ) ] = {
            'lastDate': 'nodata',
            'nick': user.nick if user.nick is not None else user.name,
            'xpDeque': [ 7 ],
            'xpVaild': 7,
            'xpTotal': 7
        }
        print( 'created temp json' )

    return users_level_data


def is_user_in_cache( today: str, userID: str, guildID: str ) -> bool:
    global g_users_cache
    if today not in g_users_cache.keys():
        g_users_cache = {}
        g_users_cache[ today ] = {}
    if guildID not in g_users_cache[ today ].keys():
        g_users_cache[ today ][ guildID ] = []
    if userID not in g_users_cache[ today ][ guildID ]:
        g_users_cache[ today ][ guildID ].append( userID )
        return False
    return True


class UserDataManager():

    def __init__( self, usersLevelData: {}, user: discord.Member, today: str ):
        self.full_json_data = usersLevelData
        self.user = user
        self.user_id = user.id
        self.today_str = today
        self.last_date = usersLevelData[ str( self.user_id ) ][ 'lastDate' ]
        self.deque_xp = deque( usersLevelData[ str( self.user_id ) ][ 'xpDeque' ] )
        self.valid_xp = sum( self.deque_xp ) if usersLevelData[ str(
            self.user_id ) ][ 'xpVaild' ] == 0 else usersLevelData[ str( self.user_id ) ][ 'xpVaild' ]
        self.total_xp = sum( self.deque_xp ) if usersLevelData[ str( self.user_id ) ][ 'xpTotal' ] == 0 else self.valid_xp

    async def add_xp_daily( self ) -> ( bool, str ):
        try:
            if self.last_date == self.today_str:
                return ( False, 'have Done' )
            else:
                self.last_date = self.today_str
                self.deque_xp.append( 1 )
                if len( self.deque_xp ) > 45:
                    self.valid_xp -= self.deque_xp.popleft()
                self.valid_xp = min( self.valid_xp + 1, 45 )
                self.total_xp += 1
        except Exception as e:
            return ( False, e )
        else:
            #await self.check_upgrade()
            return ( True, 'succ' )

    async def add_xp_reward( self, xp: int = 0 ) -> ( bool, str ):
        try:
            if self.last_date != self.today_str:
                self.last_date = self.today_str
                xp += 1
                self.deque_xp.append( xp )
            else:
                self.deque_xp[ -1 ] += xp
            if len( self.deque_xp ) > 45:
                self.valid_xp -= self.deque_xp.popleft()
            self.valid_xp = min( self.valid_xp + xp, 45 )
            self.total_xp += xp
        except Exception as e:
            return ( False, e )
        else:
            #await self.check_upgrade()
            return ( True, 'succ' )

    def what_role_should_be( self ) -> int:
        level_reach = [ 1, 2, 5, 10, 20, 35, 60 ]
        for role_level, low, high in [ ( i + 1, level_reach[ i ], level_reach[ i + 1 ] )
                                       for i in range( len( level_reach ) - 1 ) ]:
            if self.valid_xp in range( low, high ):
                return role_level
        return 0

    async def check_upgrade( self ) -> bool:
        roles_is_levels = [ role for role in self.user.roles if role.id in g_xp_to_roles_dict.values() ]
        print( roles_is_levels )
        correct_role = self.user.guild.get_role( g_xp_to_roles_dict[ self.what_role_should_be() ] )
        if correct_role is None:
            print( 'no role can give' )
            return False
        if len( roles_is_levels ) > 1 or correct_role not in roles_is_levels:
            ex_roles = tuple( ex_role for ex_role in roles_is_levels if ex_role is not correct_role )
            if len( ex_roles ) != 0:
                await self.user.remove_roles( *ex_roles )
            if correct_role not in roles_is_levels:
                await self.user.add_roles( correct_role )
            return True
        else:
            print( 'nothing to change' )
            return True

    def data_dump( self, path: str ) -> ( bool, str ):
        self.full_json_data[ str( self.user_id ) ] = {
            'lastDate': self.today_str,
            'nick': self.user.nick if self.user.nick is not None else self.user.name,
            'xpDeque': list( self.deque_xp ),
            'xpVaild': self.valid_xp,
            'xpTotal': self.total_xp
        }

        print( path )
        if not os.path.exists( os.path.dirname( path ) ):
            os.makedirs( os.path.dirname( path ) )
        try:
            with open( path, 'w' ) as fw:
                json.dump( self.full_json_data, fw, indent=4, ensure_ascii=False )
        except IOError as e:
            return ( False, "IOError with " + e )
        else:
            return ( True, f"outputed{self.user_id}'s json" )


class ExtensionBase( commands.Cog ):

    def __init__( self, bot, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.bot = bot

    async def cog_check( self, ctx ):
        '''
    The default check for this cog whenever a command is used. Returns True if the command is allowed.
    '''
        return True


class LevelsCog( ExtensionBase, name='Levels Cog' ):

    @commands.Cog.listener()
    async def on_message( self, msg: discord.Message ):
        if msg.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return

        today_date_str = ( datetime.datetime.now() + datetime.timedelta( hours=8 ) ).date().strftime( '%y_%m_%d' )  #UTC+8

        if is_user_in_cache( today=today_date_str, guildID=msg.guild.id, userID=msg.author.id ):
            return

        #path = os.path.dirname( sys.argv[ 0 ] ) + '/data/guild_' + str( msg.guild.id ) + '/usersLevelData.json'
        path = os.path.dirname( sys.argv[ 0 ] ) + 'data/guild_' + str( msg.guild.id ) + '/usersLevelData.json'
        #print( path )

        users_level_data = load_data( path=path, user=msg.author )

        if users_level_data[ str( msg.author.id ) ][ 'lastDate' ] == today_date_str:
            return

        user_xp_manager = UserDataManager( usersLevelData=users_level_data, user=msg.author, today=today_date_str )
        print( await user_xp_manager.add_xp_daily() )
        print( user_xp_manager.data_dump( path=path ) )

    @commands.group( name="Manage_XP_With_Command", aliases=[ 'xp' ] )
    async def Manage_XP_With_Command( self, ctx: commands.Context ):
        pass

    @Manage_XP_With_Command.command( name='reward', aliases=[ 'rd' ] )
    @commands.has_permissions( administrator=True )
    async def reward( self, ctx: commands.Context, member: discord.Member, xp: int = 0 ):
        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return

        today_date_str = ( datetime.datetime.now() + datetime.timedelta( hours=8 ) ).date().strftime( '%y_%m_%d' )  #UTC+8

        is_user_in_cache( today=today_date_str, guildID=ctx.guild.id, userID=member.id )

        path = os.path.dirname( sys.argv[ 0 ] ) + 'data/guild_' + str( ctx.guild.id ) + '/usersLevelData.json'
        #print( path )
        users_level_data = load_data( path=path, user=member )

        user_xp_manager = UserDataManager( usersLevelData=users_level_data, user=member, today=today_date_str )

        is_succ = await user_xp_manager.add_xp_reward( xp=xp )
        print( user_xp_manager.data_dump( path=path ) )
        if is_succ[ 0 ]:
            await ctx.send( f'succ reward {xp} xp to {member.mention}' )

    @Manage_XP_With_Command.command( name='member_level_data', aliases=[ 'lv' ] )
    @commands.has_permissions( administrator=True )
    async def member_level_data( self, ctx: commands.Context, member: discord.Member ):
        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return
        path = os.path.dirname( sys.argv[ 0 ] ) + 'data/guild_' + str( ctx.guild.id ) + '/usersLevelData.json'
        #print( path )
        user_level_data = load_data( path=path, user=member )[ str( member.id ) ]

        embed = discord.Embed( title="XP Data",
                               description=f"{member.mention}的經驗值資料",
                               color=member.color,
                               timestamp=datetime.datetime.now() )
        embed.add_field( name="光翼數量",
                         value='```html\n<0翼>\n```' if len(
                             kRoles := [ role for role in member.roles
                                         if role.id in g_xp_to_roles_dict.values() ] ) == 0 else kRoles[ -1 ].mention,
                         inline=True )
        embed.add_field( name="曾經擁有的　至今有效的　今天拿到的",
                         value=( f"```py\n{str(user_level_data['xpTotal']):^5} " + f"{str(user_level_data['xpVaild']):^5} " +
                                 f"{str(user_level_data['xpDeque'][-1]):^5}\n```" ).replace( ' ', '　' ),
                         inline=True )
        embed.set_footer( text="blaz" )

        await ctx.send( content="請盡量不要太頻繁的調用此功能\n他可能導致一些伺服器延遲\n \n", embed=embed )


def setup( bot ):
    bot.add_cog( LevelsCog( bot ) )
