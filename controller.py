import sys
import os
import json
import datetime


def get_today_date_with_delta_str( hours: int = 0 ) -> str:
    return ( datetime.datetime.now() + datetime.timedelta( hours=hours ) ).date().strftime( '%y_%m_%d' )


def get_user_json_path( guildID: int, userID: int ) -> str:
    return f"{os.path.dirname( sys.argv[ 0 ] )}data/guild_{guildID}/usersLevelData/{userID}.json"


def return_ctr( guildID: int, userID: int ):

    return ManagerExperience( storePathStr=get_user_json_path( guildID=guildID, userID=userID ),
                              todayDateStr=get_today_date_with_delta_str( 8 ) )


class ManagerExperience():
    '''manager experience via user and store as json file with single user'''

    def __init__( self, storePathStr: str, todayDateStr: str ) -> None:
        self.data_path_str = storePathStr
        self.today_date_str = todayDateStr  # %y_%m_%d

        self._get_data()

    def _generate_new_user_xp_data( self ) -> dict:
        '''like func name'''
        return 'no data'

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

    def edit_total( self, total ) -> dict:
        if type( total ) is not int:
            print( f'type u input is {type(total)} there need int' )
        else:
            self.data[ 'xpTotal' ] = total
            print( 'changed' )
        return self.data

    def edit_eternal( self, eternal ) -> dict:
        if type( eternal ) is not float:
            print( f'type u input is {type(eternal)} there need float' )
        else:
            self.data[ 'eternal' ] = eternal
            print( 'changed' )
        return self.data

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
            print( f"outputed json" )
            return True
