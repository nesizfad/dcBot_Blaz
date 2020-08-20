import datetime
import discord
from discord.ext import commands

g_saved_channels = { '管理專用研討區': 741450396874047570, '選擇身分組': 741709432660033577, 'blaz日誌': 742661957768970251 }
g_saved_roles_list_dict = {
    '佛心來著的藍披大佬': [ 741710669618872422 ],
    'beta': [ 741926764560908389 ],
    '四翼五翼六翼': [ 741692028689186856, 741692072729247874, 741692127410651189 ],
    '基礎十色': [
        741460995691643011, 741460789067644960, 741461567316558026, 741462100257275986, 741495203621240903, 741476747647909929,
        741462408471511220, 742056723291963473, 741455671001874493, 741476437718073444
    ]
}
g_saved_msgID_msg_dict = {}

g_saved_emojis_list_dict = { '1to10UniCodeEmoji': [ '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟' ] }

g_saved_user_last_time = {}

g_test_var = 743304144340910143


class ReactionInClassAction():
    '''bot reactionEvent emojis roles'''

    def __init__( self,
                  bot: commands.Bot,
                  rawReactionEventData: discord.RawReactionActionEvent,
                  reactionEmojisStrList=[],
                  giveRolesIDList=[] ):
        self.bot = bot
        self.guild = self.bot.get_guild( rawReactionEventData.guild_id )
        self.channel = self.guild.get_channel( rawReactionEventData.channel_id )
        self.user = self.guild.get_member( rawReactionEventData.user_id )
        self.raw_reaction_event_data = rawReactionEventData
        self.reaction_emojis_list = reactionEmojisStrList
        self.give_roles_list = giveRolesIDList
        self.emoji_role_dict = {}
        self.message = 'not get msg yet'
        try:
            self.emoji_role_dict = {
                reactionEmojisStrList[ index ]: giveRolesIDList[ index ]
                for index in range( len( reactionEmojisStrList ) )
            }
            self.role_emoji_dict = {
                giveRolesIDList[ index ]: reactionEmojisStrList[ index ]
                for index in range( len( reactionEmojisStrList ) )
            }
        except IndexError as e:
            print( 'something bad happend ' + e )

    async def send_to_channel( self, channelID: int = 0, contextStr: str = '' ):
        """send_to_channel(self,channelID : int = 0,contextStr : str = '')"""
        channel = self.guild.get_channel( channelID )
        await channel.send( contextStr )

    async def roles_pair_to_emoji( self, logSendToChannelID: int = 0, mode: str = '' ):
        if len( self.emoji_role_dict ) == 0:
            await self.send_to_channel( channelID=logSendToChannelID, contextStr='no data' )
        else:
            print( f"{self.raw_reaction_event_data.user_id} act {self.raw_reaction_event_data.emoji}" )
            role = self.guild.get_role( self.emoji_role_dict[ str( self.raw_reaction_event_data.emoji ) ] )
            if mode == 'add':
                excessive_roles = [ userRole for userRole in self.user.roles if userRole.id in self.give_roles_list ]
                await self.user.add_roles( role )
                if len( excessive_roles ) > 0:
                    if self.message == 'not get msg yet':
                        await self.get_message()
                    for excessive_role in excessive_roles:
                        await self.message.remove_reaction( self.role_emoji_dict[ excessive_role.id ], self.user )
                        print( f'excessive_role {excessive_role.mention}' )
            elif mode == 'remove':
                if role not in self.user.roles:
                    print( 'no this role , nothing happend' )
                    return
                await self.user.remove_roles( role )
            await self.send_to_channel( channelID=logSendToChannelID,
                                        contextStr=f"{self.user.mention} {mode} reaction and {mode} role {role.name}" )

    async def get_message( self ):
        if self.raw_reaction_event_data.message_id not in g_saved_msgID_msg_dict.keys():
            self.message = await self.channel.fetch_message( self.raw_reaction_event_data.message_id )
            g_saved_msgID_msg_dict[ self.raw_reaction_event_data.message_id ] = self.message
        else:
            self.message = g_saved_msgID_msg_dict[ self.raw_reaction_event_data.message_id ]

    async def remove_this_reaction( self ):
        if self.message == 'not get msg yet':
            await self.get_message()
        await self.message.remove_reaction( self.raw_reaction_event_data.emoji, self.user )


class ReactionAddAndRemoveProcess( commands.Cog, name='Calculation Commands' ):
    '''These are the deal with reaction'''

    def __init__( self, bot ):
        self.bot = bot

    async def cog_check( self, ctx ):
        '''
        The default check for this cog whenever a command is used. Returns True if the command is allowed.
        '''
        return True

    @commands.Cog.listener()
    async def on_raw_reaction_add( self, rawReactionEventData: discord.RawReactionActionEvent ):
        '''
        判斷標準順序
        1.判斷頻道
        2.判斷訊息
        3.判斷emoji
        4.判斷身分組
        5.執行
        '''
        print( 'on_raw_reaction_add is be called' )  # , {rawReactionEventData}')
        if rawReactionEventData.channel_id == g_saved_channels[ '選擇身分組' ]:  #🌌【選擇身分組】
            if rawReactionEventData.message_id == 741713982884413451:
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) == '<:goooood:741539091992018944>':  #:goooood:
                    if True:
                        dispenser = ReactionInClassAction( bot=self.bot,
                                                           rawReactionEventData=rawReactionEventData,
                                                           reactionEmojisStrList=[ '<:goooood:741539091992018944>' ],
                                                           giveRolesIDList=g_saved_roles_list_dict[ '佛心來著的藍披大佬' ] )
                        await dispenser.roles_pair_to_emoji( logSendToChannelID=g_saved_channels[ 'blaz日誌' ], mode='add' )
                    else:
                        pass
            elif rawReactionEventData.message_id == 741926673674534912:
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) == '🦋':  #:butterfly:
                    if True:
                        dispenser = ReactionInClassAction( bot=self.bot,
                                                           rawReactionEventData=rawReactionEventData,
                                                           reactionEmojisStrList=[ '🦋' ],
                                                           giveRolesIDList=g_saved_roles_list_dict[ 'beta' ] )
                        await dispenser.roles_pair_to_emoji( logSendToChannelID=g_saved_channels[ 'blaz日誌' ], mode='add' )
                    else:
                        pass
        # if rawReactionEventData.channel_id == 741862610642927697:
            '''el'''
            now = datetime.datetime.now()
            dispenser = ReactionInClassAction( bot=self.bot,
                                               rawReactionEventData=rawReactionEventData,
                                               reactionEmojisStrList=g_saved_emojis_list_dict[ '1to10UniCodeEmoji' ],
                                               giveRolesIDList=g_saved_roles_list_dict[ '基礎十色' ] )
            if rawReactionEventData.user_id not in g_saved_user_last_time.keys():
                g_saved_user_last_time[ rawReactionEventData.user_id ] = now
                #print('000001')
            elif g_saved_user_last_time[ rawReactionEventData.user_id ] + datetime.timedelta( seconds=2 ) > now:
                print( 'too fast' )
                await dispenser.remove_this_reaction()
                #print('000002')
                return
            else:
                g_saved_user_last_time[ rawReactionEventData.user_id ] = now
                #print('000003')
            if rawReactionEventData.message_id == g_test_var:  #msg
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) in g_saved_emojis_list_dict[ '1to10UniCodeEmoji' ]:  #emoji
                    if True in [
                            required_role in [ role.id for role in rawReactionEventData.member.roles ]
                            for required_role in g_saved_roles_list_dict[ '四翼五翼六翼' ]
                    ]:  #role 4 5 6
                        await dispenser.roles_pair_to_emoji( logSendToChannelID=g_saved_channels[ 'blaz日誌' ], mode='add' )
                    else:
                        # await dispenser.send_to_channel( channelID=g_saved_channels[ 'blaz日誌' ],
                        #                                  contextStr=f'{dispenser.user.mention} not have role' )
                        await dispenser.remove_this_reaction()

    @commands.command( name="add_reaction", aliases=[ 'ar' ] )
    @commands.has_permissions( administrator=True )
    async def add_reaction( self, ctx: commands.Context, msg: discord.Message, emojis="" ):
        for emoji in emojis.split():
            await msg.add_reaction( emoji )
        await ctx.send( 'reaction added!' )
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove( self, rawReactionEventData ):
        '''
        判斷標準順序
        1.判斷頻道
        2.判斷訊息
        3.判斷emoji
        4.判斷身分組
        5.執行
        '''
        print( 'on_raw_reaction_remove is be called' )  # , {rawReactionEventData}')
        if rawReactionEventData.channel_id == g_saved_channels[ '選擇身分組' ]:  #🌌【選擇身分組】
            if rawReactionEventData.message_id == 741713982884413451:
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) == '<:goooood:741539091992018944>':  #:goooood:
                    if True:
                        print( f"<@{rawReactionEventData.user_id}> remove reaction" )
                        guild = self.bot.get_guild( rawReactionEventData.guild_id )
                        user = guild.get_member( rawReactionEventData.user_id )
                        role = guild.get_role( g_saved_roles_list_dict[ '佛心來著的藍披大佬' ][ 0 ] )
                        await user.remove_roles( role )
                        channel = guild.get_channel( g_saved_channels[ 'blaz日誌' ] )
                        await channel.send(
                            content=f"<@{rawReactionEventData.user_id}> remove reaction and lost role 佛心來著的藍披大佬)" )
                    else:
                        pass
            elif rawReactionEventData.message_id == 741926673674534912:
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) == '🦋':  #:butterfly:
                    if True:
                        print( f"<@{rawReactionEventData.user_id}> remove reaction" )
                        guild = self.bot.get_guild( rawReactionEventData.guild_id )
                        user = guild.get_member( rawReactionEventData.user_id )
                        role = guild.get_role( g_saved_roles_list_dict[ 'beta' ][ 0 ] )
                        await user.remove_roles( role )
                        channel = guild.get_channel( g_saved_channels[ 'blaz日誌' ] )
                        await channel.send( content=f"<@{rawReactionEventData.user_id}> remove reaction and lost role beta" )
                    else:
                        pass
        #if rawReactionEventData.channel_id == 741862610642927697:
            elif rawReactionEventData.message_id == g_test_var:  #msg
                print( str( rawReactionEventData.emoji ) )
                if str( rawReactionEventData.emoji ) in g_saved_emojis_list_dict[ '1to10UniCodeEmoji' ]:  #emoji
                    dispenser = ReactionInClassAction( bot=self.bot,
                                                       rawReactionEventData=rawReactionEventData,
                                                       reactionEmojisStrList=g_saved_emojis_list_dict[ '1to10UniCodeEmoji' ],
                                                       giveRolesIDList=g_saved_roles_list_dict[ '基礎十色' ] )
                    await dispenser.roles_pair_to_emoji( logSendToChannelID=g_saved_channels[ 'blaz日誌' ], mode='remove' )


def setup( bot ):
    bot.add_cog( ReactionAddAndRemoveProcess( bot ) )
