import discord
from discord.ext import commands
import sys
import os
import json
import datetime
import asyncio
import concurrent.futures as cf

g_cache_dict = {}
g_is_inloop_check = False


def is_user_in_cache( today: str, userID: str, guildID: str, yesterday: str, guild: discord.Guild ) -> bool:
    global g_cache_dict
    if guildID not in g_cache_dict.keys():
        g_cache_dict[ guildID ] = {}
    if today not in g_cache_dict[ guildID ].keys():
        g_cache_dict[ guildID ][ today ] = []
        '''
        if yesterday in g_cache_dict[ guildID ].keys() and g_is_inloop_check is False:
            g_is_inloop_check = True
            del g_cache_dict[ guildID ][ yesterday ]
            executor = cf.ThreadPoolExecutor(max_workers=1)
            executor.submit( await loop_to_check( guild=guild, today=get_today_date_with_delta_str( 8 ) )  )
        '''
    if userID not in g_cache_dict[ guildID ][ today ]:
        g_cache_dict[ guildID ][ today ].append( userID )
        return False
    return True


async def loop_to_check( guild: discord.Guild, today: str ) -> bool:
    count = 0
    log_channel = guild.get_channel( {
        690548499233636362: 741666177050214430,
        741429518484635749: 742661957768970251
    }[ guild.id ] )
    for member in guild.members:
        count += 1
        await asyncio.sleep( 0.5 )
        manager = ManagerExperienceViaUser( userObj=member,
                                            storePathStr=get_user_json_path( guildID=guild.id, userID=member.id ),
                                            todayDateStr=today,
                                            thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=guild ) )
        await manager.check_activity()
        if count % 20 == 1:
            await log_channel.send(
                content=f"check on {member.mention} process {count*100/guild.member_count}%({count}/{guild.member_count})",
                delete_after=10 )
    print( 'finish' )
    await log_channel.send( content=f"process {100}%({count}/{guild.member_count})", delete_after=86400 )
    g_is_inloop_check = False


def load_level_roleObj_dict( guildObj: discord.Guild ) -> { int: discord.Role }:
    global g_cache_dict
    guildID = str( guildObj.id )
    if guildID not in g_cache_dict.keys():
        g_cache_dict[ guildID ] = {}
    if 'levelRoleDict' not in g_cache_dict[ guildID ].keys():
        path = f"{os.path.dirname( sys.argv[ 0 ] )}data/guild_{guildID}/0rules/levelRoleDict.json"
        if not os.path.exists( os.path.dirname( path ) ):
            os.makedirs( os.path.dirname( path ) )
        try:
            with open( path, 'r' ) as jsonFile:
                level_Role_Dict = json.load( jsonFile )
        except FileNotFoundError as e:
            print( f"{e} , return None" )
            return None
        except json.JSONDecodeError as e:
            print( f"file not right , return None , {e}" )
            return None
        else:
            g_cache_dict[ guildID ][ 'levelRoleDict' ] = ( lv_r_dict := {
                int( level ): guildObj.get_role( roleID )
                for level, roleID in level_Role_Dict.items()
            } )
            return lv_r_dict
    else:
        return g_cache_dict[ guildID ][ 'levelRoleDict' ]


class ExtensionBase( commands.Cog ):

    def __init__( self, bot, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.bot = bot

    async def cog_check( self, ctx ):
        '''
    The default check for this cog whenever a command is used. Returns True if the command is allowed.
    '''
        return True


class ManagerExperienceViaUser():
    '''manager experience via user and store as json file with single user'''

    def __init__( self, userObj: discord.Member, storePathStr: str, todayDateStr: str,
                  thisGuildLevelRoleDict: { int: discord.Role } ) -> None:
        self.user_obj = userObj
        self.lv_role_dict = thisGuildLevelRoleDict
        self.data_path_str = storePathStr
        self.today_date_str = todayDateStr  # %y_%m_%d

        self._get_data()

    def _auto_dump_and_check( func ):

        async def dump_and_check( self, *arg, **karg ) -> bool:
            if ( succ_tuple := await func( self, *arg, **karg ) )[ 0 ]:
                print( 'operated,try save' )
                self.data_dump()
                print( 'saved,try update' )
                await self._update_role()
            elif succ_tuple[ 1 ] == 'normal':
                print( 'no write and no update in SOP' )
            else:
                print( 'something wrong!' )
                return False
            return True

        return dump_and_check

    def _generate_new_user_xp_data( self ) -> dict:
        '''like func name'''
        return { 'nick': self.user_obj.display_name, 'lastDate': 'null', 'xpDeque': [], 'xpTotal': 0, 'eternal': 0 }

    def _get_data( self ) -> dict:
        '''get data from json file if not find generate one and return or save in data_dict'''
        if not os.path.exists( os.path.dirname( self.data_path_str ) ):
            os.makedirs( os.path.dirname( self.data_path_str ) )
        try:
            with open( self.data_path_str, 'r' ) as jsonFile:
                self.data = json.load( jsonFile )
        except FileNotFoundError as e:
            print( str( e ) + 'created temp json' )
            self.data = self._generate_new_user_xp_data()
        return self.data

    def _append_xp( self, xp: int ) -> bool:
        ( xpDQ := self.data[ 'xpDeque' ] ).append( xp )
        if len( xpDQ ) > 45:
            xpDQ.remove( xpDQ[ 0 ] )
        self.data[ 'xpTotal' ] += xp
        print( 'appended' )
        return True

    def _edit_today_xp_add_with( self, xp: int ) -> bool:
        if len( xpDQ := self.data[ 'xpDeque' ] ) < 1:
            print( f"get error at edit {self.user_obj.display_name} xp" )
            return False
        else:
            xpDQ[ -1 ] += xp
            if xp > 0:
                self.data[ 'xpTotal' ] += xp
            return True

    @_auto_dump_and_check
    async def add_sign_in_xp( self ) -> ( bool, str ):
        '''簽到'''
        is_succ_sign_in = True  # record if func not run correct
        print( f"{self.data[ 'lastDate' ]} =?= {self.today_date_str}" )
        if self.data[ 'lastDate' ] != self.today_date_str:
            print( 'date not match' )
            self.data[ 'lastDate' ] = self.today_date_str
            is_succ_sign_in = self._append_xp( 1 )
        elif self.data[ 'xpDeque' ][ -1 ] == 0:  #daily check
            is_succ_sign_in = self._edit_today_xp_add_with( 1 )
        else:
            print( f'{self.user_obj.display_name} was token' )
            return ( False, 'normal' )
        print( self.data )
        return ( is_succ_sign_in, 'optional' )

    @_auto_dump_and_check
    async def check_activity( self ) -> ( bool, str ):
        '''確認今日是否上線'''
        if self.data[ 'lastDate' ] != self.today_date_str:
            self.data[ 'lastDate' ] = self.today_date_str
            if self._append_xp( 0 ):
                print( f'{self.user_obj.display_name} check succ' )
                return ( True, 'normal' )
            else:
                print( '_append_xp fall' )
                return ( False, 'optional' )
        print( f'{self.user_obj.display_name} active today' )
        return ( False, 'normal' )

    @_auto_dump_and_check
    async def add_reward_xp( self, xp: int ) -> bool:
        '''給予獎勵'''
        is_succ_reward = True  # record if func not run correct
        if self.data[ 'lastDate' ] != self.today_date_str:
            self.data[ 'lastDate' ] = self.today_date_str
            is_succ_reward = self._append_xp( xp + 1 )
        else:
            is_succ_reward = self._edit_today_xp_add_with( xp )

        return ( is_succ_reward, 'optional' )

    @_auto_dump_and_check
    async def give_init_xp( self, xp: int ) -> bool:
        '''給予初始值'''
        self.data[ 'xpDeque' ].insert( 0, xp )
        self.data[ 'xpTotal' ] += xp
        print( self.data )
        return ( True, 'normal' )

    def trans_xp_to_external( self ) -> ( bool, str ):
        if ( realHaveXp := self._how_many_xp_have()[ 1 ] ) <= 45:
            return ( False, f'xp not enough ({realHaveXp}<=45)' )
        else:
            self.data[ 'eternal' ] += 1
            if self.data[ 'lastDate' ] != self.today_date_str:
                self.data[ 'lastDate' ] = self.today_date_str
                self._append_xp( -10 + 1 )
                return ( True, 'translated and sign in' )
            else:
                self._edit_today_xp_add_with( -10 )
                return ( True, 'translated' )

    def _how_many_xp_have( self ) -> ( int, int ):
        '''vaild and in limit'''
        return ( min( realHaveXp := ( sum( self.data[ 'xpDeque' ] ) ), 45 ), realHaveXp )

    def _what_role_should_be( self ) -> discord.Role:
        if self.lv_role_dict is None:
            print( 'rule is not load' )
            return None
        lvs_r = [ *( lvs := list( self.lv_role_dict.keys() ) ), lvs[ -1 ] * 2 ][ 1: ]
        vaild_xp = self._how_many_xp_have()[ 0 ]
        for low, h in [ ( lvs[ i ], lvs_r[ i ] ) for i in range( len( lvs ) ) ]:
            if vaild_xp in range( low, h ):
                return self.lv_role_dict[ low ]
        return None

    async def _update_role( self ) -> bool:
        if self.lv_role_dict is None:
            print( 'rule is not load' )
            return False
        cRole = self._what_role_should_be()
        if len( lruh := [ role for role in self.user_obj.roles
                          if role in self.lv_role_dict.values() ] ) != 1 or cRole not in lruh:  #level_roles_user_have
            if len( ex_roles := [ role for role in lruh if role is not cRole ] ) != 0:
                await self.user_obj.remove_roles( *ex_roles )
            if cRole not in lruh and cRole is not None:
                await self.user_obj.add_roles( cRole )
            print( 'role update' )
            return True
        else:
            print( 'no change' )
            return True

    def data_dump( self ) -> ( bool, str ):
        print( 'try to save' )
        if not os.path.exists( os.path.dirname( self.data_path_str ) ):
            os.makedirs( os.path.dirname( self.data_path_str ) )
        try:
            with open( self.data_path_str, 'w' ) as jsonFile:
                print( self.data )
                json.dump( self.data, jsonFile, indent=4, ensure_ascii=False )
        except IOError as e:
            print( "IOError with " + str( e ) )
            return False
        else:
            print( f"outputed{self.user_obj.display_name}({self.user_obj.id})'s json" )
            return True

    def return_data( self ) -> ( discord.Role, int, int, int, int, int, str ):
        '''role totalXp vaildXp realXp lastXp externalXp lastdate'''
        if self.data[ 'lastDate' ] == 'null':
            return ( None, 0, 0, 0, 0, 0, 'null' )
        last_date = ''
        for index in range( -1, ( len( self.data[ 'xpDeque' ] ) + 1 ) * -1, -1 ):
            if self.data[ 'xpDeque' ][ index ] != 0:
                last_date = get_today_date_with_delta_str( hours=24 * ( index + 1 ) )
                break
        return ( self._what_role_should_be(), ( data := self.data )[ 'xpTotal' ], ( haveXp := self._how_many_xp_have() )[ 0 ],
                 haveXp[ 1 ], data[ 'xpDeque' ][ -1 ], data[ 'eternal' ], last_date )


def get_today_date_with_delta_str( hours: int = 0 ) -> str:
    return ( datetime.datetime.now() + datetime.timedelta( hours=hours ) ).date().strftime( '%y_%m_%d' )


def get_user_json_path( guildID: int, userID: int ) -> str:
    return f"{os.path.dirname( sys.argv[ 0 ] )}data/guild_{guildID}/usersLevelData/{userID}.json"


class Levels( ExtensionBase, name='Levels parts' ):

    @commands.Cog.listener()
    async def on_message( self, msg: discord.Message ) -> bool:
        if msg.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return

        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8

        if is_user_in_cache( today=today_date_str,
                             guildID=msg.guild.id,
                             userID=msg.author.id,
                             yesterday=get_today_date_with_delta_str( hours=-24 ),
                             guild=msg.guild ):  #TODO:make this update check
            print( f"operation succ with (in cache){msg.author.display_name} on message" )
            return

        path = get_user_json_path( guildID=msg.guild.id, userID=msg.author.id )

        user_xp_manager = ManagerExperienceViaUser( userObj=msg.author,
                                                    storePathStr=path,
                                                    todayDateStr=today_date_str,
                                                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=msg.guild ) )

        flag = await user_xp_manager.add_sign_in_xp()
        if flag:
            print( f"operation succ with {msg.author.display_name} on message" )
        else:
            print( '\n\noperation failure\n\n' )
            return False

    @commands.Cog.listener()
    async def on_voice_state_update( self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState ):
        if member.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return

        #print()

        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8

        if is_user_in_cache( today=today_date_str,
                             guildID=member.guild.id,
                             userID=member.id,
                             yesterday=get_today_date_with_delta_str( hours=-24 ),
                             guild=member.guild ):  #TODO:make this update check
            print( f"operation succ with (in cache){member.display_name}'s voice channel changed !" )
            return

        path = get_user_json_path( guildID=member.guild.id, userID=member.id )

        user_xp_manager = ManagerExperienceViaUser( userObj=member,
                                                    storePathStr=path,
                                                    todayDateStr=today_date_str,
                                                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=member.guild ) )

        flag = await user_xp_manager.add_sign_in_xp()
        if flag:
            print( f"operation succ with {member.display_name}'s voice channel changed !" )
        else:
            print( '\n\noperation failure with voice channel changed\n\n' )
            return False

    @commands.group( name="Manage_XP_With_Command", aliases=[ 'xp' ] )
    async def Manage_XP_With_Command( self, ctx: commands.Context ):
        pass

    @Manage_XP_With_Command.command( name='reward', aliases=[ 'rd' ] )
    @commands.has_permissions( administrator=True )
    async def reward( self, ctx: commands.Context, member: discord.Member, xp: int = 0 ):
        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( 'not right guild' )
            return

        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8
        path = get_user_json_path( guildID=ctx.guild.id, userID=member.id )
        user_xp_manager = ManagerExperienceViaUser( userObj=member,
                                                    storePathStr=path,
                                                    todayDateStr=today_date_str,
                                                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=ctx.guild ) )

        flag = await user_xp_manager.add_reward_xp( xp=xp )
        if flag:
            await ctx.send( f'succ reward {xp} xp to {member.mention}' )

    @Manage_XP_With_Command.command( name='give_initial', aliases=[ 'init' ] )
    @commands.has_permissions( administrator=True )
    async def give_initial( self, ctx: commands.Context, member: discord.Member, xp: int = 0 ):

        ctx.send( content='this feature is not open', delete_after=360 )
        return

        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( 'not right guild' )
            return

        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8
        if xp == -71235:
            for key, value in {
                    "402394522824474624": "10",
                    "472087521560363008": "10",
                    "616609945441402916": "30",
                    "640197596450652160": "19",
                    "381453584463560704": "11",
                    "459279265343733762": "11",
                    "588038434120007727": "12",
                    "710854577121132636": "20",
                    "728550429033627740": "12",
                    "616981256768585758": "25",
                    "626717947536211969": "11",
                    "652909866658037790": "3",
                    "617164488453390336": "9",
                    "495876881623678976": "4",
                    "449493800113668096": "1",
                    "736859682379137036": "3",
                    "729536049931616347": "5",
                    "366257472899383308": "1",
                    "706097021362110525": "6",
                    "723461723004338204": "3",
                    "574575577063751684": "2",
                    "724757789188161609": "1",
                    "341201022859083777": "9",
                    "742693749880258561": "1",
                    "744133203429687397": "1",
                    "356457910986997780": "8",
                    "688249746808373260": "8",
                    "178785491011764224": "5",
                    "666760547135520768": "3",
                    "657978952522137650": "3",
                    "637196923287240714": "3",
                    "155553892606803968": "7",
                    "243994207163777025": "5",
                    "606149076693549076": "9",
                    "439105298481807360": "7",
                    "494069352308408322": "4",
                    "744211302519406593": "1",
                    "726417453151944745": "2",
                    "581857799621836823": "5",
                    "644946414987640852": "9",
                    "564378682429276180": "2",
                    "249808428816400384": "3",
                    "622725649899061258": "2",
                    "476731107887546369": "7",
                    "367687614834409472": "1",
                    "304255890452643841": "2",
                    "744359324427485316": "1",
                    "744461054939103292": "1",
                    "744886409885909112": "1"
            }.items():
                path = get_user_json_path( guildID=ctx.guild.id, userID=key )
                user_xp_manager = ManagerExperienceViaUser(
                    userObj=ctx.guild.get_member( int( key ) ),
                    storePathStr=path,
                    todayDateStr=today_date_str,
                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=ctx.guild ) )
                #flag = await user_xp_manager.give_init_xp( xp=int( value ) )
                if True:
                    await ctx.send( f'succ init {value} xp to <@{key}>' )
                await asyncio.sleep( 0.25 )
            await ctx.send( f'succ init xp to all members in json' )
            return
        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8
        path = get_user_json_path( guildID=ctx.guild.id, userID=member.id )
        user_xp_manager = ManagerExperienceViaUser( userObj=member,
                                                    storePathStr=path,
                                                    todayDateStr=today_date_str,
                                                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=ctx.guild ) )

        flag = await user_xp_manager.give_init_xp( xp=xp )
        if flag:
            await ctx.send( f'succ init {xp} xp to {member.mention}' )

    @Manage_XP_With_Command.command( name='check_whole_guild_member_activity', aliases=[ 'check_WGM_activity' ] )
    @commands.has_permissions( administrator=True )
    async def check_whole_guild_member_activity( self, ctx: commands.Context ):
        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( 'not right guild' )
            return

        print( '\n\nin process\n\n' )
        executor_in_command = cf.ThreadPoolExecutor( max_workers=1 )
        executor_in_command.submit( await loop_to_check( guild=ctx.guild, today=get_today_date_with_delta_str( 8 ) ) )

    @Manage_XP_With_Command.command( name='member_level_data', aliases=[ 'lv' ] )
    @commands.has_permissions( administrator=True )
    async def member_level_data( self, ctx: commands.Context, member: discord.Member ):
        if ctx.guild.id not in [ 690548499233636362, 741429518484635749 ]:
            print( ' not right guild' )
            return

        today_date_str = get_today_date_with_delta_str( hours=8 )  #UTC+8
        path = get_user_json_path( guildID=ctx.guild.id, userID=member.id )
        user_xp_manager = ManagerExperienceViaUser( userObj=member,
                                                    storePathStr=path,
                                                    todayDateStr=today_date_str,
                                                    thisGuildLevelRoleDict=load_level_roleObj_dict( guildObj=ctx.guild ) )
        lv_role_obj, t_x, v_x, r_x, l_x, e_x, last_date = user_xp_manager.return_data()

        if last_date == 'null':
            await ctx.send( content=f"尚無{member.mention}的經驗值資料，請他先在伺服器上留下足跡吧" )
            return

        embed = discord.Embed( title="XP Data",
                               description=f"{member.mention}的經驗值資料",
                               color=member.color,
                               timestamp=datetime.datetime.now() )
        embed.add_field( name="光翼數量", value='```html\n<0翼>\n```' if ( r := lv_role_obj ) is not None else r, inline=True )
        embed.add_field( name='曾擁有的光之子', value=mk_code_block( s=t_x, lang='py' ), inline=True )
        embed.add_field( name='還有效的光之子', value=mk_code_block( s=v_x, lang='fix' ), inline=True )
        embed.add_field( name='現擁有的光之子', value=mk_code_block( s=r_x, lang='md' ), inline=True )
        embed.add_field( name='今天拿的光之子', value=mk_code_block( s=l_x, lang='py' ), inline=True )
        embed.add_field( name='恆永久的光之子', value=mk_code_block( s=e_x, lang='fix' ), inline=True )
        embed.add_field( name='上次活躍日期', value=mk_str_c_w7_and_FS( s=last_date ), inline=True )
        embed.set_footer( text="blaz" )

        await ctx.send( content="請盡量不要太頻繁的調用此功能\n他可能導致一些伺服器延遲\n \n", embed=embed )


def mk_str_c_w7_and_FS( s ) -> str:
    return f'{s:^7}'.replace( ' ', '　' )


def mk_code_block( s: str, lang: str, mod: str = 'CFS', arg1: int = 7 ) -> str:
    return f"```{lang}\n{mk_str_c_w7_and_FS(s=s) if mod == 'CFS' else s}\n```"


def setup( bot ):
    bot.add_cog( Levels( bot ) )
