import apiconst
import apierror
import apiutil
import const
import datetime
import json
import falcon
import inspect
import numbers
import sqldb
import sys
import os

from apiutil import p1_serializer, validate_timestamp, clean_timestamp_str, list_filter_to_str, validate_timestamp_by_length
from sqldb import SqlDb1, SqlDb2, SqlDb3, SqlDb4, rtStatusDb, financieelDb, historyWeatherDB, configDB, currentWeatherDB, temperatureDB, WatermeterDB, PhaseDB,  powerProductionDB

from sys import exit
from logger import fileLogger,logging
from utilnetwork3 import getNicInfo

# INIT
prgname = 'P1Api'
e_db_serial             = SqlDb1()
e_db_history_sqldb2     = SqlDb2() # min
e_db_history_uur_sqldb3 = SqlDb3() # hour
e_db_history_uur_sqldb4 = SqlDb4() # day,month, year
rt_status_db            = rtStatusDb()
config_db               = configDB()
e_db_financieel         = financieelDb()
weer_history_db         = historyWeatherDB()
weer_db                 = currentWeatherDB()
temperature_db          = temperatureDB()
watermeter_db_uur       = WatermeterDB()
watermeter_db_dag       = WatermeterDB()
watermeter_db_maand     = WatermeterDB()
watermeter_db_jaar      = WatermeterDB()
fase_db                 = PhaseDB()
power_production_db     = powerProductionDB()

try:
    os.umask( 0o002 )
    flog = fileLogger( const.DIR_FILELOG + prgname + ".log", prgname )
    flog.setLevel( logging.INFO )
    flog.consoleOutputOn( True ) 
except Exception as e:
    print ("critical geen logging mogelijke, gestopt.:"+str(e.args[0]) )
    sys.exit(1)


flog.info("Start van programma.")

# Create the Falcon application object
app = falcon.API()
app.set_error_serializer( p1_serializer )

# open databases
# open van seriele database      
try:
     e_db_serial.init(const.FILE_DB_E_FILENAME ,const.DB_SERIAL_TAB)        
except Exception as e:
    flog.critical( str(__name__)  + " database niet te openen(1)."+const.FILE_DB_E_FILENAME+") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__)  + ": database tabel "+const.DB_SERIAL_TAB+" succesvol geopend." )

# open van power + gas history database (1 min interval)
try:
    e_db_history_sqldb2.init(const.FILE_DB_E_HISTORIE,const.DB_HISTORIE_MIN_TAB)    
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(2)." + const.FILE_DB_E_HISTORIE + ") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_HISTORIE_MIN_TAB + " (minuut) succesvol geopend." )

# open van history database (1 uur interval)
try:
    e_db_history_uur_sqldb3.init(const.FILE_DB_E_HISTORIE,const.DB_HISTORIE_UUR_TAB)    
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(3)." + const.FILE_DB_E_HISTORIE + ") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_HISTORIE_UUR_TAB + " succesvol geopend." )

# open van history database (dag , maand, year interval)
try:
    e_db_history_uur_sqldb4.init(const.FILE_DB_E_HISTORIE,const.DB_HISTORIE_DAG_TAB)    
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(4)." + const.FILE_DB_E_HISTORIE+") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_HISTORIE_DAG_TAB + " succesvol geopend." )

# open van status database      
try:    
    rt_status_db.init( const.FILE_DB_STATUS,const.DB_STATUS_TAB )
except Exception as e:
    flog.critical( str(__name__) +  ": Database niet te openen(5)."+const.FILE_DB_STATUS+") melding:"+str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_STATUS_TAB + " succesvol geopend." )

 # open van config database      
try:
    config_db.init( const.FILE_DB_CONFIG,const.DB_CONFIG_TAB )
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(6)."+const.FILE_DB_CONFIG+") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel "+const.DB_CONFIG_TAB+" succesvol geopend.")

# open van financieel database (
try:
    e_db_financieel.init( const.FILE_DB_FINANCIEEL , const.DB_FINANCIEEL_DAG_TAB )
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(7)." + const.FILE_DB_FINANCIEEL + ") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel "+const.DB_FINANCIEEL_DAG_TAB+" succesvol geopend." )

# open van weer database voor historische weer dag      
try:
    weer_history_db.init( const.FILE_DB_WEATHER_HISTORIE ,const.DB_WEATHER_DAG_TAB )
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(8)." + const.DB_WEATHER_DAG_TAB + ") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel "+const.DB_WEATHER_DAG_TAB + " succesvol geopend.")

# open van weer database voor huidige weer      
try:
    weer_db.init(const.FILE_DB_WEATHER ,const.DB_WEATHER_TAB)
except Exception as e:
    flog.critical( str(__name__) + ": database niet te openen(9)." + const.DB_WEATHER_TAB + ") melding:"+str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_WEATHER_TAB + " succesvol geopend." )

 # open van temperatuur database
try:    
    temperature_db.init(const.FILE_DB_TEMPERATUUR_FILENAME ,const.DB_TEMPERATUUR_TAB )
except Exception as e:
    flog.critical( str(__name__) + ": Database niet te openen(10)." + const.FILE_DB_TEMPERATUUR_FILENAME+") melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel "+const.DB_TEMPERATUUR_TAB  + " succesvol geopend." )

 # open van watermeter uur.
try:    
    watermeter_db_uur.init( const.FILE_DB_WATERMETER, const.DB_WATERMETER_UUR_TAB, flog )
except Exception as e:
    flog.critical( str(__name__) + ": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_WATERMETER_UUR_TAB + " succesvol geopend." )

try:    
    watermeter_db_dag.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_DAG_TAB , flog )
except Exception as e:
    flog.critical( str(__name__) + ": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_WATERMETER_DAG_TAB + " succesvol geopend." )

try:    
    watermeter_db_maand.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_MAAND_TAB ,flog )
except Exception as e:
    flog.critical( str(__name__) + ": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_WATERMETER_MAAND_TAB + " succesvol geopend." )

try:    
    watermeter_db_jaar.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_JAAR_TAB, flog )
except Exception as e:
    flog.critical( str(__name__) + ": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_WATERMETER_JAAR_TAB  + " succesvol geopend." )

# open van fase database      
try:
    fase_db.init( const.FILE_DB_PHASEINFORMATION ,const.DB_FASE_REALTIME_TAB )
    fase_db.defrag()
except Exception as e:
    flog.critical( str(__name__) + " database niet te openen(1)." + const.FILE_DB_PHASEINFORMATION + ") melding:"+str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_FASE_REALTIME_TAB + " succesvol geopend.")

# open van power production database
try:
    power_production_db.init( const.FILE_DB_POWERPRODUCTION , const.DB_POWERPRODUCTION_TAB, flog )
except Exception as e:
    flog.critical( inspect.stack()[0][3] + ": Database niet te openen(3)." + const.FILE_DB_POWERPRODUCTION + " melding:" + str(e.args[0]) )
    sys.exit(1)
flog.info( str(__name__) + ": database tabel " + const.DB_POWERPRODUCTION_TAB + " succesvol geopend." )


class Catalog( object ):
    
    def on_get(self, req, resp):
        """Handles all GET requests."""

        #print ( req.path )
        if req.path == apiconst.ROUTE_CATALOG_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_CATALOG_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_CATALOG_HELP  + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     

        try:
            # get IP adress
            ipadress = '<IP adres niet gevonden>'
            result = getNicInfo(nic='eth0')
            if result['result_ok'] == True and result['ip4'] != None: 
                ipadress = result['ip4']
            else:
                result = getNicInfo(nic='wlan0')
                if result['result_ok'] == True and result['ip4'] != None: 
                    ipadress = result['ip4']
        
            json_obj_data = [] 
            with open( const.DIR_SCRIPTS + 'apiconst.py' ) as search:
                for line in search:
                    line = line.rstrip()  # remove '\n' at end of line
                    if line.startswith('ROUTE_'):  # add ROUTE entries 
                        if '_HELP' in line or '{id}' in line: # remove HELP ROUTES & id's routes
                            continue
                        #route = line.split('=')[1].replace("'","").replace('{id}','1').strip()
                        route = line.split('=')[1].replace("'","").strip()
                        json_obj_data.append( ipadress + route )
                        json_obj_data.sort() #sort the routes

                        #json_obj_data.append( ipadress + route + '/help' )
                # adding help routes
                json_obj_data_routes = [] 
                for route in json_obj_data: 
                    json_obj_data_routes.append( route )
                    json_obj_data_routes.append( route + '/help')

            resp.body = json.dumps( json_obj_data_routes, ensure_ascii=False )   
            resp.status = falcon.HTTP_200  # This is the default status
        
        except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
        return     
        
catalog_resource = Catalog()
app.add_route( apiconst.ROUTE_CATALOG,      catalog_resource )
app.add_route( apiconst.ROUTE_CATALOG_HELP, catalog_resource )


class powerProductionS0( object ):

    sqlstr_base_regular = "select \
    TIMESTAMP,\
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    TIMEPERIOD_ID,\
    POWER_SOURCE_ID,\
    PRODUCTION_KWH_HIGH,\
    PRODUCTION_KWH_LOW,\
    PULS_PER_TIMEUNIT_HIGH,\
    PULS_PER_TIMEUNIT_LOW,\
    PRODUCTION_KWH_HIGH_TOTAL,\
    PRODUCTION_KWH_LOW_TOTAL,\
    PRODUCTION_KWH_TOTAL,\
    PRODUCTION_PSEUDO_KW from " + const.DB_POWERPRODUCTION_TAB

    sqlstr_base_round = "select \
    TIMESTAMP,\
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    TIMEPERIOD_ID,\
    POWER_SOURCE_ID,\
    ROUND( PRODUCTION_KWH_HIGH ),\
    ROUND( PRODUCTION_KWH_LOW ),\
    ROUND( PULS_PER_TIMEUNIT_HIGH ),\
    ROUND( PULS_PER_TIMEUNIT_LOW ),\
    ROUND( PRODUCTION_KWH_HIGH_TOTAL ),\
    ROUND( PRODUCTION_KWH_LOW_TOTAL ),\
    ROUND( PRODUCTION_KWH_TOTAL ),\
    ROUND( PRODUCTION_PSEUDO_KW ) from " + const.DB_POWERPRODUCTION_TAB

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL               : '',
            apiconst.JSON_TS_LCL_UTC           : 0,
            apiconst.JSON_API_PROD_PERIOD_ID   : 0,
            apiconst.JSON_API_PROD_PWR_SRC_ID  : 0,
            apiconst.JSON_API_PROD_KWH_H       : 0,
            apiconst.JSON_API_PROD_KWH_L       : 0,
            apiconst.JSON_API_PROD_PULS_CNT_H  : 0,
            apiconst.JSON_API_PROD_PULS_CNT_L  : 0,
            apiconst.JSON_API_PROD_KWH_TOTAL_H : 0,
            apiconst.JSON_API_PROD_KWH_TOTAL_L : 0,
            apiconst.JSON_API_PROD_KWH_TOTAL   : 0,
            apiconst.JSON_API_PROD_KW_PSEUDO   : 0
        }

        if  req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MIN_HELP   or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_HOUR_HELP  or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_DAY_HELP   or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MONTH_HELP or\
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_YEAR_HELP:
            
            flog.debug ( str( __name__ ) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_POWER_PRODUCTION_MIN_DAY_MONTH_YEAR_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str( __class__.__name__ ) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return

        # set period index 
        v_period_id = 0
        if req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MIN:
            v_period_id = " 11 "
        elif req.path == apiconst.ROUTE_POWERPRODUCTION_S0_HOUR:
            v_period_id = " 12 "
        elif req.path == apiconst.ROUTE_POWERPRODUCTION_S0_DAY:
            v_period_id = " 13 "
        elif req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MONTH:
            v_period_id = " 14 "
        elif req.path == apiconst.ROUTE_POWERPRODUCTION_S0_YEAR:
            v_period_id = " 15 "


        if  req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MIN   or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_HOUR  or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_DAY   or \
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_MONTH or\
            req.path == apiconst.ROUTE_POWERPRODUCTION_S0_YEAR :
            
            # default sql string
            sqlstr = self.sqlstr_base_regular

            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''

            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )

                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )

                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )

                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = self.sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )

                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " and TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = " and substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + " where TIMEPERIOD_ID = " + v_period_id + " and POWER_SOURCE_ID = 1 " + v_starttime + v_rangetimestamp + v_sort + str(v_limit)

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  =  power_production_db.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]               = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]           = a[1]
                        new_dict[ apiconst.JSON_API_PROD_PERIOD_ID ]   = a[2]
                        new_dict[ apiconst.JSON_API_PROD_PWR_SRC_ID ]  = a[3]
                        new_dict[ apiconst.JSON_API_PROD_KWH_H ]       = a[4]
                        new_dict[ apiconst.JSON_API_PROD_KWH_L ]       = a[5]
                        new_dict[ apiconst.JSON_API_PROD_PULS_CNT_H ]  = a[6]
                        new_dict[ apiconst.JSON_API_PROD_PULS_CNT_L ]  = a[7]
                        new_dict[ apiconst.JSON_API_PROD_KWH_TOTAL_H ] = a[8]
                        new_dict[ apiconst.JSON_API_PROD_KWH_TOTAL_L ] = a[9]
                        new_dict[ apiconst.JSON_API_PROD_KWH_TOTAL ]   = a[10]
                        new_dict[ apiconst.JSON_API_PROD_KW_PSEUDO ]   = a[11]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )

                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )

            resp.status = falcon.HTTP_200  # This is the default status

power_production_power_s0_resource  = powerProductionS0()

app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_MIN ,       power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_MIN_HELP,   power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_HOUR,       power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_HOUR_HELP,  power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_DAY,        power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_DAY_HELP,   power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_MONTH,      power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_MONTH_HELP, power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_YEAR,       power_production_power_s0_resource )
app.add_route( apiconst.ROUTE_POWERPRODUCTION_S0_YEAR_HELP,  power_production_power_s0_resource )


class IndoorTemperature( object ):
    
    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    RECORD_ID, \
    TEMPERATURE_1, \
    TEMPERATURE_1_MIN, \
    TEMPERATURE_1_AVG, \
    TEMPERATURE_1_MAX, \
    TEMPERATURE_2, \
    TEMPERATURE_2_MIN, \
    TEMPERATURE_2_AVG, \
    TEMPERATURE_2_MAX \
    from temperatuur where RECORD_ID = "

  
    sqlstr_base_round  = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    RECORD_ID, \
    ROUND( TEMPERATURE_1     ), \
    ROUND( TEMPERATURE_1_MIN ), \
    ROUND( TEMPERATURE_1_AVG ), \
    ROUND( TEMPERATURE_1_MAX ), \
    ROUND( TEMPERATURE_2     ), \
    ROUND( TEMPERATURE_2_MIN ), \
    ROUND( TEMPERATURE_2_AVG ), \
    ROUND( TEMPERATURE_2_MAX ) \
    from temperatuur where RECORD_ID = "


    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                : '',
            apiconst.JSON_TS_LCL_UTC            : 0,
            apiconst.JSON_API_RM_TMPRTR_RCRD_ID : 0,
            apiconst.JSON_API_RM_TMPRTR_IN      : 0,  
            apiconst.JSON_API_RM_TMPRTR_IN_L    : 0,
            apiconst.JSON_API_RM_TMPRTR_IN_A    : 0,
            apiconst.JSON_API_RM_TMPRTR_IN_H    : 0,
            apiconst.JSON_API_RM_TMPRTR_OUT     : 0,
            apiconst.JSON_API_RM_TMPRTR_OUT_L   : 0,
            apiconst.JSON_API_RM_TMPRTR_OUT_A   : 0,
            apiconst.JSON_API_RM_TMPRTR_OUT_H   : 0
        }

        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_HELP or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MIN_HELP  or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_HOUR_HELP or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_DAY_HELP  or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MONTH_HELP or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_YEAR_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_INDOOR_TEMPERATURE_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE:
            sqlstr_base_regular = self.sqlstr_base_regular + '10 '
            sqlstr_base_round   = self.sqlstr_base_round   + '10 '
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MIN:
            sqlstr_base_regular = self.sqlstr_base_regular + '11 '
            sqlstr_base_round   = self.sqlstr_base_round   + '11 '
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_HOUR:
            sqlstr_base_regular = self.sqlstr_base_regular + '12 '
            sqlstr_base_round   = self.sqlstr_base_round   + '12 '
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_DAY:
            sqlstr_base_regular = self.sqlstr_base_regular + '13 '
            sqlstr_base_round   = self.sqlstr_base_round   + '13 '    
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MONTH:
            sqlstr_base_regular = self.sqlstr_base_regular + '14 '
            sqlstr_base_round   = self.sqlstr_base_round   + '14 '
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_YEAR:
            sqlstr_base_regular = self.sqlstr_base_regular + '15 '
            sqlstr_base_round   = self.sqlstr_base_round   + '15 '

        # default sql string
        sqlstr  = sqlstr_base_regular
        
        if req.path == apiconst.ROUTE_INDOOR_TEMPERATURE or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MIN or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_HOUR or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_DAY or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_MONTH or \
            req.path == apiconst.ROUTE_INDOOR_TEMPERATURE_YEAR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
             # rangetimestamp 
            v_rangetimestamp = ''

            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                """
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = " and TIMESTAMP >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)
            """

                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " and TIMESTAMP >= '" + value + "' order by timestamp "
                        #v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = " and substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 


            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records =  temperature_db.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]            = a[1]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_RCRD_ID ] = a[2]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_IN ]      = a[3]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_IN_L ]    = a[4]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_IN_A ]    = a[5]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_IN_H ]    = a[6]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_OUT ]     = a[7]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_OUT_L ]   = a[8]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_OUT_A ]   = a[9]
                        new_dict[ apiconst.JSON_API_RM_TMPRTR_OUT_H ]   = a[10]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

indoor_temperature_resource = IndoorTemperature()
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE,            indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_HELP,       indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_MIN,        indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_MIN_HELP,   indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_HOUR,       indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_HOUR_HELP,  indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_DAY,        indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_DAY_HELP,   indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_MONTH,      indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_MONTH_HELP, indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_YEAR,       indoor_temperature_resource )
app.add_route( apiconst.ROUTE_INDOOR_TEMPERATURE_YEAR_HELP,  indoor_temperature_resource )


class CurrentWeather( object ):
    
    sqlstr_base_regular =  "select \
    datetime( TIMESTAMP, 'unixepoch', 'localtime' ), \
    TIMESTAMP, \
    CITY_ID, \
    CITY, \
    TEMPERATURE, \
    DESCRIPTION, \
    WEATHER_ICON, \
    PRESSURE, \
    HUMIDITY, \
    WIND_SPEED, \
    WIND_DEGREE, \
    CLOUDS, \
    WEATHER_ID from "

    sqlstr_base_round =  "select \
    datetime( TIMESTAMP, 'unixepoch', 'localtime' ), \
    TIMESTAMP, \
    CITY_ID, \
    CITY, \
    ROUND( TEMPERATURE ), \
    DESCRIPTION, \
    WEATHER_ICON, \
    PRESSURE, \
    HUMIDITY, \
    ROUND( WIND_SPEED ), \
    WIND_DEGREE, \
    CLOUDS, \
    WEATHER_ID from "


    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL              : '',
            apiconst.JSON_TS_LCL_UTC          : 0,
            apiconst.JSON_API_CTY_ID          : 0,
            apiconst.JSON_API_CTY_NM          : '',
            apiconst.JSON_API_WTHR_TMPRTR     : 0,
            apiconst.JSON_API_WTHR_DSCRPTN    : 0,
            apiconst.JSON_API_WTHR_ICON       : '',
            apiconst.JSON_API_WTHR_PRSSR      : 0,
            apiconst.JSON_API_WTHR_HMDTY      : 0,
            apiconst.JSON_API_WTHR_WND_SPD    : 0,
            apiconst.JSON_API_WTHR_WND_DGRS   : 0,
            apiconst.JSON_API_WTHR_CLDS       : 0,
            apiconst.JSON_API_WTHR_WEATHER_ID : 0 
        }

        if req.path == apiconst.ROUTE_WEATHER_CURRENT_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_WEATHER_CURRENT_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_WEATHER_CURRENT_HELP  + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_WEATHER_CURRENT:
            sqlstr_base_regular = self.sqlstr_base_regular + 'weer '
            sqlstr_base_round   = self.sqlstr_base_round   + 'weer '
        
        # default sql string
        sqlstr  = sqlstr_base_regular

        if req.path == apiconst.ROUTE_WEATHER_CURRENT:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
        
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = " where datetime( TIMESTAMP, 'unixepoch', 'localtime' ) >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = weer_db.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]              = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]          = a[1]
                        new_dict[ apiconst.JSON_API_CTY_ID ]          = a[2] 
                        new_dict[ apiconst.JSON_API_CTY_NM ]          = a[3]
                        new_dict[ apiconst.JSON_API_WTHR_TMPRTR ]     = a[4]
                        new_dict[ apiconst.JSON_API_WTHR_DSCRPTN ]    = a[5]
                        new_dict[ apiconst.JSON_API_WTHR_ICON ]       = a[6]
                        new_dict[ apiconst.JSON_API_WTHR_PRSSR ]      = a[7]
                        new_dict[ apiconst.JSON_API_WTHR_HMDTY ]      = a[8]
                        new_dict[ apiconst.JSON_API_WTHR_WND_SPD ]    = a[9]
                        new_dict[ apiconst.JSON_API_WTHR_WND_DGRS ]   = a[10]
                        new_dict[ apiconst.JSON_API_WTHR_CLDS ]       = a[11]
                        new_dict[ apiconst.JSON_API_WTHR_WEATHER_ID ] = a[12]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

current_weather_resource  = CurrentWeather()
app.add_route( apiconst.ROUTE_WEATHER_CURRENT,      current_weather_resource )
app.add_route( apiconst.ROUTE_WEATHER_CURRENT_HELP, current_weather_resource )


class WeatherHistoryHourDayMonthYear( object ):
    
    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer),\
    CITY_ID, \
    CITY, \
    TEMPERATURE_MIN, \
    TEMPERATURE_AVG, \
    TEMPERATURE_MAX, \
    PRESSURE_MIN, \
    PRESSURE_AVG, \
    PRESSURE_MAX, \
    HUMIDITY_MIN, \
    HUMIDITY_AVG, \
    HUMIDITY_MAX, \
    WIND_SPEED_MIN, \
    WIND_SPEED_AVG, \
    WIND_SPEED_MAX, \
    WIND_DEGREE_MIN, \
    WIND_DEGREE_AVG,\
    WIND_DEGREE_MAX \
    from "


    sqlstr_base_round  = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer),\
    CITY_ID,\
    CITY, \
    ROUND( TEMPERATURE_MIN ), \
    ROUND( TEMPERATURE_AVG ), \
    ROUND( TEMPERATURE_MAX ), \
    PRESSURE_MIN, \
    PRESSURE_AVG, \
    PRESSURE_MAX, \
    HUMIDITY_MIN, \
    HUMIDITY_AVG, \
    HUMIDITY_MAX, \
    ROUND( WIND_SPEED_MIN ), \
    ROUND( WIND_SPEED_AVG ), \
    ROUND( WIND_SPEED_MAX ), \
    ROUND( WIND_DEGREE_MIN ) , \
    ROUND( WIND_DEGREE_AVG ) , \
    ROUND( WIND_DEGREE_MAX )  \
    from "


    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                 : '',
            apiconst.JSON_TS_LCL_UTC             : 0,
            apiconst.JSON_API_CTY_ID             : 0,
            apiconst.JSON_API_CTY_NM             : 0,
            apiconst.JSON_API_TMPRTR_L           : 0,
            apiconst.JSON_API_TMPRTR_A           : 0,
            apiconst.JSON_API_TMPRTR_H           : 0,
            apiconst.JSON_API_PRSSR_L            : 0,
            apiconst.JSON_API_PRSSR_A            : 0,
            apiconst.JSON_API_PRSSR_H            : 0,
            apiconst.JSON_API_HUMIDITY_L         : 0,
            apiconst.JSON_API_HUMIDITY_A         : 0,
            apiconst.JSON_API_HUMIDITY_H         : 0,
            apiconst.JSON_API_WND_SPD_L          : 0,
            apiconst.JSON_API_WND_SPD_A          : 0,
            apiconst.JSON_API_WND_SPD_H          : 0,
            apiconst.JSON_API_WND_DGRS_L         : 0,
            apiconst.JSON_API_WND_DGRS_A         : 0,
            apiconst.JSON_API_WND_DGRS_H         : 0
        }

        if req.path == apiconst.ROUTE_WEATHER_HOUR_HELP or \
            req.path == apiconst.ROUTE_WEATHER_DAY_HELP  or \
            req.path == apiconst.ROUTE_WEATHER_MONTH_HELP or \
            req.path == apiconst.ROUTE_WEATHER_YEAR_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_WEATHER_DAY_MONTH_YEAR_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_WEATHER_HOUR:
            sqlstr_base_regular = self.sqlstr_base_regular + 'weer_history_uur '
            sqlstr_base_round   = self.sqlstr_base_round   + 'weer_history_uur '
        if req.path == apiconst.ROUTE_WEATHER_DAY:
            sqlstr_base_regular = self.sqlstr_base_regular + 'weer_history_dag '
            sqlstr_base_round   = self.sqlstr_base_round   + 'weer_history_dag '
        if req.path == apiconst.ROUTE_WEATHER_MONTH:
            sqlstr_base_regular = self.sqlstr_base_regular + 'weer_history_maand '
            sqlstr_base_round   = self.sqlstr_base_round   + 'weer_history_maand '
        if req.path == apiconst.ROUTE_WEATHER_YEAR:
            sqlstr_base_regular = self.sqlstr_base_regular + 'weer_history_jaar '
            sqlstr_base_round   = self.sqlstr_base_round   + 'weer_history_jaar '

        # default sql string
        sqlstr  = sqlstr_base_regular
        

        if req.path == apiconst.ROUTE_WEATHER_HOUR or \
            req.path == apiconst.ROUTE_WEATHER_DAY or \
            req.path == apiconst.ROUTE_WEATHER_MONTH or \
            req.path == apiconst.ROUTE_WEATHER_YEAR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
        
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records = weer_history_db.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]         = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]     = a[1]
                        new_dict[ apiconst.JSON_API_CTY_ID ]     = a[2]
                        new_dict[ apiconst.JSON_API_CTY_NM ]     = a[3]
                        new_dict[ apiconst.JSON_API_TMPRTR_L ]   = a[4]
                        new_dict[ apiconst.JSON_API_TMPRTR_A ]   = a[5]
                        new_dict[ apiconst.JSON_API_TMPRTR_H ]   = a[6]
                        new_dict[ apiconst.JSON_API_PRSSR_L ]    = a[7]
                        new_dict[ apiconst.JSON_API_PRSSR_A ]    = a[8]
                        new_dict[ apiconst.JSON_API_PRSSR_H ]    = a[9]
                        new_dict[ apiconst.JSON_API_HUMIDITY_L ] = a[10]
                        new_dict[ apiconst.JSON_API_HUMIDITY_A ] = a[11]
                        new_dict[ apiconst.JSON_API_HUMIDITY_H ] = a[12]
                        new_dict[ apiconst.JSON_API_WND_SPD_L ]  = a[13]
                        new_dict[ apiconst.JSON_API_WND_SPD_A ]  = a[14]
                        new_dict[ apiconst.JSON_API_WND_SPD_H ]  = a[15]
                        new_dict[ apiconst.JSON_API_WND_DGRS_L ] = a[16]
                        new_dict[ apiconst.JSON_API_WND_DGRS_A ] = a[17]
                        new_dict[ apiconst.JSON_API_WND_DGRS_H ] = a[18]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

weather_history_hour_day_month_year_resource = WeatherHistoryHourDayMonthYear()
app.add_route( apiconst.ROUTE_WEATHER_HOUR,       weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_HOUR_HELP,  weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_DAY,        weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_DAY_HELP,   weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_MONTH,      weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_MONTH_HELP, weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_YEAR,       weather_history_hour_day_month_year_resource )
app.add_route( apiconst.ROUTE_WEATHER_YEAR_HELP,  weather_history_hour_day_month_year_resource )


class PowerGasHistoryDayMonthYear( object ):
    
    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    VERBR_KWH_181, \
    VERBR_KWH_182, \
    GELVR_KWH_281, \
    GELVR_KWH_282, \
    VERBR_KWH_X, \
    GELVR_KWH_X, \
    VERBR_GAS_2421, \
    VERBR_GAS_X from " 

    sqlstr_base_round = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    ROUND( VERBR_KWH_181 ), \
    ROUND( VERBR_KWH_182 ), \
    ROUND( GELVR_KWH_281 ), \
    ROUND( GELVR_KWH_282 ), \
    ROUND( VERBR_KWH_X ), \
    ROUND( GELVR_KWH_X ), \
    ROUND( VERBR_GAS_2421   ), \
    ROUND( VERBR_GAS_X      )  \
    from " 

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                 : '',
            apiconst.JSON_TS_LCL_UTC             : 0,
            apiconst.JSON_API_CNSMPTN_KWH_L      : 0,
            apiconst.JSON_API_CNSMPTN_KWH_H      : 0,
            apiconst.JSON_API_PRDCTN_KWH_L       : 0,
            apiconst.JSON_API_PRDCTN_KWH_H       : 0,
            apiconst.JSON_API_CNSMPTN_DLT_KWH    : 0,
            apiconst.JSON_API_PRDCTN_DLT_KWH     : 0,
            apiconst.JSON_API_CNSMPTN_GAS_M3     : 0,
            apiconst.JSON_API_CNSMPTN_GAS_DLT_M3 : 0
        }

        if req.path == apiconst.ROUTE_POWER_GAS_DAY_HELP or \
            req.path == apiconst.ROUTE_POWER_GAS_MONTH_HELP or \
            req.path == apiconst.ROUTE_POWER_GAS_YEAR_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_POWER_GAS_DAY_MONTH_YEAR_JSON , sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_POWER_GAS_DAY:
            sqlstr_base_regular = self.sqlstr_base_regular + 'e_history_dag '
            sqlstr_base_round   = self.sqlstr_base_round   + 'e_history_dag '
        if req.path == apiconst.ROUTE_POWER_GAS_MONTH:
            sqlstr_base_regular = self.sqlstr_base_regular + 'e_history_maand '
            sqlstr_base_round   = self.sqlstr_base_round   + 'e_history_maand '
        if req.path == apiconst.ROUTE_POWER_GAS_YEAR:
            sqlstr_base_regular = self.sqlstr_base_regular + 'e_history_jaar '
            sqlstr_base_round   = self.sqlstr_base_round   + 'e_history_jaar '

        # default sql string
        sqlstr  = sqlstr_base_regular
        

        if req.path == apiconst.ROUTE_POWER_GAS_DAY or \
            req.path == apiconst.ROUTE_POWER_GAS_MONTH or \
            req.path == apiconst.ROUTE_POWER_GAS_YEAR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''

            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = "where substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  =  e_db_history_uur_sqldb4.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                 = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]             = a[1]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_L ]      = a[2]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_H ]      = a[3]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_L ]       = a[4]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_H ]       = a[5]
                        new_dict[ apiconst.JSON_API_CNSMPTN_DLT_KWH ]    = a[6]
                        new_dict[ apiconst.JSON_API_PRDCTN_DLT_KWH ]     = a[7]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_M3 ]     = a[8]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_DLT_M3 ] = a[9]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

power_gas_history_day_month_year_resource  = PowerGasHistoryDayMonthYear()
app.add_route( apiconst.ROUTE_POWER_GAS_DAY,        power_gas_history_day_month_year_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_DAY_HELP,   power_gas_history_day_month_year_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_MONTH,      power_gas_history_day_month_year_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_MONTH_HELP, power_gas_history_day_month_year_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_YEAR,       power_gas_history_day_month_year_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_YEAR_HELP,  power_gas_history_day_month_year_resource )


class PowerGasHistoryHour( object ):
    
    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    VERBR_KWH_181, \
    VERBR_KWH_182, \
    GELVR_KWH_281, \
    GELVR_KWH_282, \
    VERBR_KWH_X, \
    GELVR_KWH_X, \
    TARIEFCODE , \
    VERBR_GAS_2421, \
    VERBR_GAS_X from " 

    sqlstr_base_round = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    ROUND( VERBR_KWH_181 ), \
    ROUND( VERBR_KWH_182 ), \
    ROUND( GELVR_KWH_281 ), \
    ROUND( GELVR_KWH_282 ), \
    ROUND( VERBR_KWH_X ), \
    ROUND( GELVR_KWH_X ), \
    TARIEFCODE , \
    ROUND( VERBR_GAS_2421   ), \
    ROUND( VERBR_GAS_X      )  \
    from " 

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                 : '',
            apiconst.JSON_TS_LCL_UTC             : 0,
            apiconst.JSON_API_CNSMPTN_KWH_L      : 0,
            apiconst.JSON_API_CNSMPTN_KWH_H      : 0,
            apiconst.JSON_API_PRDCTN_KWH_L       : 0,
            apiconst.JSON_API_PRDCTN_KWH_H       : 0,
            apiconst.JSON_API_CNSMPTN_DLT_KWH    : 0,
            apiconst.JSON_API_PRDCTN_DLT_KWH     : 0,
            apiconst.JSON_API_TRFCD              : 0,
            apiconst.JSON_API_CNSMPTN_GAS_M3     : 0,
            apiconst.JSON_API_CNSMPTN_GAS_DLT_M3 : 0
        }

        if req.path == apiconst.ROUTE_POWER_GAS_HOUR_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_POWER_GAS_HOUR_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_POWER_GAS_HOUR_HELP  + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_POWER_GAS_HOUR:
            sqlstr_base_regular = self.sqlstr_base_regular + 'e_history_uur '
            sqlstr_base_round   = self.sqlstr_base_round   + 'e_history_uur '
        
        # default sql string
        sqlstr  = sqlstr_base_regular

        if req.path == apiconst.ROUTE_POWER_GAS_HOUR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''
        
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = "where substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = e_db_history_uur_sqldb3.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                 = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]             = a[1]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_L ]      = a[2]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_H ]      = a[3]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_L ]       = a[4]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_H ]       = a[5]
                        new_dict[ apiconst.JSON_API_CNSMPTN_DLT_KWH ]    = a[6]
                        new_dict[ apiconst.JSON_API_PRDCTN_DLT_KWH ]     = a[7]
                        new_dict[ apiconst.JSON_API_TRFCD ]              = a[8]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_M3 ]     = a[9]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_DLT_M3 ] = a[10]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

power_gas_history_hour_resource  = PowerGasHistoryHour()
app.add_route( apiconst.ROUTE_POWER_GAS_HOUR,        power_gas_history_hour_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_HOUR_HELP,   power_gas_history_hour_resource )


# range option done 2020-08-16
class PowerGasHistoryMin( object ):

    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    VERBR_KWH_181, \
    VERBR_KWH_182, \
    GELVR_KWH_281, \
    GELVR_KWH_282, \
    VERBR_KWH_X, \
    GELVR_KWH_X, \
    TARIEFCODE , \
    ACT_VERBR_KW_170, \
    ACT_GELVR_KW_270, \
    VERBR_GAS_2421 from " 


    sqlstr_base_round = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    ROUND( VERBR_KWH_181 ), \
    ROUND( VERBR_KWH_182 ), \
    ROUND( GELVR_KWH_281 ), \
    ROUND( GELVR_KWH_282 ), \
    ROUND( VERBR_KWH_X ), \
    ROUND( GELVR_KWH_X ), \
    TARIEFCODE , \
    ROUND( ACT_VERBR_KW_170 ), \
    ROUND( ACT_GELVR_KW_270 ), \
    ROUND( VERBR_GAS_2421   )  \
    from " 

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                : '',
            apiconst.JSON_TS_LCL_UTC            : 0,
            apiconst.JSON_API_CNSMPTN_KWH_L     : 0,
            apiconst.JSON_API_CNSMPTN_KWH_H     : 0,
            apiconst.JSON_API_PRDCTN_KWH_L      : 0,
            apiconst.JSON_API_PRDCTN_KWH_H      : 0,
            apiconst.JSON_API_CNSMPTN_DLT_KWH   : 0,
            apiconst.JSON_API_PRDCTN_DLT_KWH    : 0,
            apiconst.JSON_API_TRFCD             : 0,
            apiconst.JSON_API_CNSMPTN_KW        : 0,
            apiconst.JSON_API_PRDCTN_KW         : 0,
            apiconst.JSON_API_CNSMPTN_GAS_M3    : 0,
        }

        if req.path == apiconst.ROUTE_POWER_GAS_MIN_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_POWER_GAS_MIN_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_POWER_GAS_MIN_HELP + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_POWER_GAS_MIN:
            #sqlstr_base_regular = self.sqlstr_base_regular + 'e_history_min '
            #sqlstr_base_round   = self.sqlstr_base_round   + 'e_history_min '
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_HISTORIE_MIN_TAB + " "
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_HISTORIE_MIN_TAB + " "

        # default sql string
        sqlstr  = sqlstr_base_regular

        if req.path == apiconst.ROUTE_POWER_GAS_MIN:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''

            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = "where substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = e_db_history_sqldb2.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]            = a[1]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_L ]     = a[2]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_H ]     = a[3]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_L ]      = a[4]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_H ]      = a[5]
                        new_dict[ apiconst.JSON_API_CNSMPTN_DLT_KWH ]   = a[6]
                        new_dict[ apiconst.JSON_API_PRDCTN_DLT_KWH ]    = a[7]
                        new_dict[ apiconst.JSON_API_TRFCD ]             = a[8]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KW ]        = a[9]
                        new_dict[ apiconst.JSON_API_PRDCTN_KW ]         = a[10]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_M3 ]    = a[11]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

power_gas_history_min_resource = PowerGasHistoryMin()
app.add_route( apiconst.ROUTE_POWER_GAS_MIN,        power_gas_history_min_resource )
app.add_route( apiconst.ROUTE_POWER_GAS_MIN_HELP,   power_gas_history_min_resource )


class Financial( object ):

    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    VERBR_P, \
    VERBR_D, \
    GELVR_P, \
    GELVR_D, \
    GELVR_GAS, \
    VERBR_WATER from "

    sqlstr_base_round = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    ROUND( VERBR_P ), \
    ROUND( VERBR_D ), \
    ROUND( GELVR_P ), \
    ROUND( GELVR_D ), \
    ROUND( GELVR_GAS ) \
    ROUND( VERBR_WATER ) \
    from "

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                : '',
            apiconst.JSON_TS_LCL_UTC            : 0,
            apiconst.JSON_API_FNCL_CNSMPTN_E_H  : 0,
            apiconst.JSON_API_FNCL_CNSMPTN_E_L  : 0,
            apiconst.JSON_API_FNCL_PRDCTN_E_H   : 0,
            apiconst.JSON_API_FNCL_PRDCTN_E_L   : 0,
            apiconst.JSON_API_FNCL_CNSMPTN_GAS  : 0,
            apiconst.JSON_API_FNCL_CNSMPTN_WATER: 0
        }

        if req.path == apiconst.ROUTE_FINANCIAL_DAY_HELP or \
            req.path == apiconst.ROUTE_FINANCIAL_MONTH_HELP or \
                req.path == apiconst.ROUTE_FINANCIAL_YEAR_HELP:
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_FINANCIAL_DAY_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_FINANCIAL_DAY:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_FINANCIEEL_DAG_TAB # 'e_financieel_dag' 
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_FINANCIEEL_DAG_TAB # 'e_financieel_dag' 
        if req.path == apiconst.ROUTE_FINANCIAL_MONTH:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_FINANCIEEL_MAAND_TAB #e_financieel_maand'
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_FINANCIEEL_MAAND_TAB #e_financieel_maand'
        if req.path == apiconst.ROUTE_FINANCIAL_YEAR:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_FINANCIEEL_JAAR_TAB # 'e_financieel_jaar'
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_FINANCIEEL_JAAR_TAB # 'e_financieel_jaar'

        # default sql string
        sqlstr  = sqlstr_base_regular

        if req.path == apiconst.ROUTE_FINANCIAL_DAY or req.path == apiconst.ROUTE_FINANCIAL_MONTH or req.path == apiconst.ROUTE_FINANCIAL_YEAR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''
            
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                """"
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)
            """
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = " where substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = e_db_financieel.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                    = a[0]   
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]                = a[1] 
                        new_dict[ apiconst.JSON_API_FNCL_CNSMPTN_E_H ]      = a[2]
                        new_dict[ apiconst.JSON_API_FNCL_CNSMPTN_E_L ]      = a[3]
                        new_dict[ apiconst.JSON_API_FNCL_PRDCTN_E_H ]       = a[4]
                        new_dict[ apiconst.JSON_API_FNCL_PRDCTN_E_L ]       = a[5] 
                        new_dict[ apiconst.JSON_API_FNCL_CNSMPTN_GAS ]      = a[6]
                        new_dict[ apiconst.JSON_API_FNCL_CNSMPTN_WATER ]    = a[7] 
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status
            #resp.body = json.dumps( records, ensure_ascii=False )
            #resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True , indent=4)

financial_resource = Financial()
app.add_route( apiconst.ROUTE_FINANCIAL_DAY,        financial_resource )
app.add_route( apiconst.ROUTE_FINANCIAL_DAY_HELP,   financial_resource )
app.add_route( apiconst.ROUTE_FINANCIAL_MONTH,      financial_resource )
app.add_route( apiconst.ROUTE_FINANCIAL_MONTH_HELP, financial_resource )
app.add_route( apiconst.ROUTE_FINANCIAL_YEAR,       financial_resource )
app.add_route( apiconst.ROUTE_FINANCIAL_YEAR_HELP,  financial_resource )


class Status( object ):

    sqlstr_base_regular = 'select ID,STATUS,LABEL,SECURITY from status '

    def on_get( self, req, resp, id = 'all' ):
        """Handles all GET requests."""

        #print ( str(__class__.__name__) )
        #print ( req.query_string )
        #print ( 'req.params=' + str( req.params ) )
        #print ( 'req.path='   + str( req.path ) )
        #print ( apiconst.ROUTE_STATUS )
        #print ( 'id='         +  id )

        json_data  = {
            apiconst.JSON_API_STTS_ID  : 0,
            apiconst.JSON_API_STTS     : '',
            apiconst.JSON_API_STTS_LBL : '',
            apiconst.JSON_API_SCRTY    : 0
        }

        id = id.lower()
        #print ( id )

        if req.path.endswith('/help'):
            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": help aanpassen wegens id en help in path." )
            id = 'help'

        if id == 'help':
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_STATUS_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
        elif id == 'all':
            sqlstr = self.sqlstr_base_regular + 'order by id'
        else:
            try:
                sqlstr = self.sqlstr_base_regular +' where id = '+ str( abs(int( id, 10 )) ) # no negative numbers.
                flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" + sqlstr )
            except Exception as _e:
                    err_str = 'id value not ok, value used is ' + str( id )
                    flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                    raise falcon.HTTPError( 
                        apierror.API_PARAMETER_ERROR['status'], 
                        apierror.API_PARAMETER_ERROR['title'], 
                        apierror.API_PARAMETER_ERROR['description'] + err_str, 
                        code=apierror.API_PARAMETER_ERROR['code'] 
                    )
    
        v_json_mode = ''
            
        for key, value in req.params.items():
            # this only gives the first parameter when more are put in
            value = list_filter_to_str( value )
            key = key.lower()
            #print ( key, value )
               
            if key == apiconst.API_PARAMETER_JSON_TYPE:     
                if value.lower() == 'object':
                    v_json_mode = 'object'
                    flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
               
        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

        try:
            # read datbase.
            records  = rt_status_db.select_rec( sqlstr )

            if v_json_mode ==  'object': 
                # process records for JSON opjects
                json_obj_data = [] 
                for a in records:
                    new_dict = json_data.copy()
                    new_dict[ apiconst.JSON_API_STTS_ID ]  = a[0] 
                    new_dict[ apiconst.JSON_API_STTS ]     = a[1] 
                    new_dict[ apiconst.JSON_API_STTS_LBL ] = a[2]
                    new_dict[ apiconst.JSON_API_SCRTY ]    = a[3]
                      
                    json_obj_data.append( new_dict )

                resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
            else:
                resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
        except Exception as _e:
            raise falcon.HTTPError( 
                apierror.API_DB_ERROR['status'], 
                apierror.API_DB_ERROR['title'], 
                apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                code=apierror.API_DB_ERROR['code'] 
                )
               
        resp.status = falcon.HTTP_200  # This is the default status
        #resp.body = json.dumps( records, ensure_ascii=False )
        #resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True , indent=4)

status_resource = Status()
app.add_route( apiconst.ROUTE_STATUS,         status_resource )
app.add_route( apiconst.ROUTE_STATUS_HELP,    status_resource )
app.add_route( apiconst.ROUTE_STATUS_ID,      status_resource )
app.add_route( apiconst.ROUTE_STATUS_ID_HELP, status_resource )


class Config( object ):
    
    sqlstr_base_regular = 'select ID,PARAMETER,LABEL from config '
   
    def on_get( self, req, resp, id = 'all' ):
        """Handles all GET requests."""

        #print ( str(__class__.__name__) )
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )
        #print ( apiconst.ROUTE_STATUS )

        json_data  = {
            apiconst.JSON_API_CNFG_ID    : 0,
            apiconst.JSON_API_CNFG_PRMTR : '',
            apiconst.JSON_API_CNFG_LABEL : ''
        }

        id = id.lower()
        #print ( id )

        if req.path.endswith('/help'):
            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": help aanpassen wegens id en help in path." )
            id = 'help'

        if id == 'help':
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_CONFIG_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
        elif id == 'all':
            sqlstr = self.sqlstr_base_regular + 'order by id'
        else:
            try:
                sqlstr = self.sqlstr_base_regular +' where id = '+ str( abs(int( id, 10 )) ) # no negative numbers.
                flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" + sqlstr )
            except Exception as _e:
                    err_str = 'id value not ok, value used is ' + str( id )
                    flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                    raise falcon.HTTPError( 
                        apierror.API_PARAMETER_ERROR['status'], 
                        apierror.API_PARAMETER_ERROR['title'], 
                        apierror.API_PARAMETER_ERROR['description'] + err_str, 
                        code=apierror.API_PARAMETER_ERROR['code'] 
                    )
    
        v_json_mode = ''
            
        for key, value in req.params.items():
            # this only gives the first parameter when more are put in
            value = list_filter_to_str( value )
            key = key.lower()
            #print ( key, value )
               
            if key == apiconst.API_PARAMETER_JSON_TYPE:     
                if value.lower() == 'object':
                    v_json_mode = 'object'
                    flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
               
        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

        try:
            # read datbase.
            records  = config_db.select_rec( sqlstr )

            if v_json_mode ==  'object': 
                # process records for JSON opjects
                json_obj_data = [] 
                for a in records:
                    new_dict = json_data.copy()
                    new_dict[ apiconst.JSON_API_CNFG_ID ]    = a[0] 
                    new_dict[ apiconst.JSON_API_CNFG_PRMTR ] = a[1] 
                    new_dict[ apiconst.JSON_API_CNFG_LABEL ] = a[2]
                      
                    json_obj_data.append( new_dict )

                resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
            else:
                resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
        except Exception as _e:
            raise falcon.HTTPError( 
                apierror.API_DB_ERROR['status'], 
                apierror.API_DB_ERROR['title'], 
                apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                code=apierror.API_DB_ERROR['code'] 
                )
               
        resp.status = falcon.HTTP_200  # This is the default status
        #resp.body = json.dumps( records, ensure_ascii=False )
        #resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True , indent=4)

config_resource = Config()
app.add_route( apiconst.ROUTE_CONFIG,         config_resource )
app.add_route( apiconst.ROUTE_CONFIG_HELP,    config_resource )
app.add_route( apiconst.ROUTE_CONFIG_ID,      config_resource )
app.add_route( apiconst.ROUTE_CONFIG_ID_HELP, config_resource )

class SmartMeter( object ):

    sqlstr_base_regular = "select \
        TIMESTAMP, \
        cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
        RECORD_VERWERKT, \
        VERBR_KWH_181, \
        VERBR_KWH_182, \
        GELVR_KWH_281, \
        GELVR_KWH_282, \
        TARIEFCODE, \
        CAST( ACT_VERBR_KW_170 * 1000 AS INT), \
        CAST( ACT_GELVR_KW_270 * 1000 AS INT), \
        VERBR_GAS_2421 \
        from " + const.DB_SERIAL_TAB + " "
    
    sqlstr_base_round = "select \
        TIMESTAMP, \
        CAST(strftime('%s', TIMESTAMP, 'utc' ) AS INT), \
        RECORD_VERWERKT, \
        ROUND( VERBR_KWH_181 ), \
        ROUND( VERBR_KWH_182 ), \
        ROUND( GELVR_KWH_281 ), \
        ROUND( GELVR_KWH_282 ), \
        TARIEFCODE, \
        CAST(ACT_VERBR_KW_170 * 1000 AS INT), \
        CAST(ACT_GELVR_KW_270 * 1000 AS INT), \
        ROUND( VERBR_GAS_2421 ) \
        from " + const.DB_SERIAL_TAB + " "
    

    def on_get(self, req, resp):
        """Handles all GET requests."""

        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL             : '',
            apiconst.JSON_TS_LCL_UTC         : 0,
            apiconst.JSON_API_REC_PRCSSD     : 0,
            apiconst.JSON_API_CNSMPTN_KWH_L  : 0,
            apiconst.JSON_API_CNSMPTN_KWH_H  : 0,
            apiconst.JSON_API_PRDCTN_KWH_L   : 0,
            apiconst.JSON_API_PRDCTN_KWH_H   : 0,
            apiconst.JSON_API_TRFCD          : '',
            apiconst.JSON_API_CNSMPTN_W      : 0,
            apiconst.JSON_API_PRDCTN_W       : 0,
            apiconst.JSON_API_CNSMPTN_GAS_M3 : 0
        }

        if req.path == apiconst.ROUTE_SMARTMETER_HELP:
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_SMARTMETER_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_SMARTMETER_HELP  + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     

        # default sql string
        sqlstr = self.sqlstr_base_regular

        if req.path == apiconst.ROUTE_SMARTMETER:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
        
            
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = self.sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = "where TIMESTAMP >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = e_db_serial.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]             = a[0] 
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]         = a[1] 
                        new_dict[ apiconst.JSON_API_REC_PRCSSD ]     = a[2]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_L ]  = a[3]
                        new_dict[ apiconst.JSON_API_CNSMPTN_KWH_H ]  = a[4]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_L ]   = a[5]
                        new_dict[ apiconst.JSON_API_PRDCTN_KWH_H ]   = a[6]
                        new_dict[ apiconst.JSON_API_TRFCD ]          = a[7]
                        new_dict[ apiconst.JSON_API_CNSMPTN_W ]      = a[8]
                        new_dict[ apiconst.JSON_API_PRDCTN_W ]       = a[9]
                        new_dict[ apiconst.JSON_API_CNSMPTN_GAS_M3 ] = a[10]
                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status
            #resp.body = json.dumps( records, ensure_ascii=False )
            #resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True , indent=4)

smartmeter_resource = SmartMeter()
app.add_route( apiconst.ROUTE_SMARTMETER,      smartmeter_resource )
app.add_route( apiconst.ROUTE_SMARTMETER_HELP, smartmeter_resource )

class Watermeter( object ):

    sqlstr_base_regular = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    PULS_PER_TIMEUNIT, \
    VERBR_PER_TIMEUNIT, \
    VERBR_IN_M3_TOTAAL \
    from "

    sqlstr_base_round = "select \
    TIMESTAMP, \
    cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
    ROUND( PULS_PER_TIMEUNIT  ), \
    ROUND( VERBR_PER_TIMEUNIT ), \
    ROUND( VERBR_IN_M3_TOTAAL )\
    from " 

    def on_get(self, req, resp):
        """Handles all GET requests."""
        
        flog.debug ( str(__name__) + " route " + req.path + " selected.")
        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                  : '',
            apiconst.JSON_TS_LCL_UTC              : 0,
            apiconst.JSON_API_WM_PULS_CNT         : 0,
            apiconst.JSON_API_WM_CNSMPTN_LTR      : 0,
            apiconst.JSON_API_WM_CNSMPTN_LTR_M3   : 0
        }

        if req.path == apiconst.ROUTE_WATERMETER_HOUR_HELP or \
            req.path == apiconst.ROUTE_WATERMETER_DAY_HELP  or \
            req.path == apiconst.ROUTE_WATERMETER_MONTH_HELP or \
            req.path == apiconst.ROUTE_WATERMETER_YEAR_HELP:
            
            flog.debug ( str(__name__) + " help data selected.")
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_WATERMETER_HOUR_DAY_MONTH_YEAR_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     
            

        if req.path == apiconst.ROUTE_WATERMETER_HOUR:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_WATERMETER_UUR_TAB
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_WATERMETER_UUR_TAB
        if req.path == apiconst.ROUTE_WATERMETER_DAY:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_WATERMETER_DAG_TAB
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_WATERMETER_DAG_TAB
        if req.path == apiconst.ROUTE_WATERMETER_MONTH:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_WATERMETER_MAAND_TAB
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_WATERMETER_MAAND_TAB
        if req.path == apiconst.ROUTE_WATERMETER_YEAR:
            sqlstr_base_regular = self.sqlstr_base_regular + const.DB_WATERMETER_JAAR_TAB
            sqlstr_base_round   = self.sqlstr_base_round   + const.DB_WATERMETER_JAAR_TAB

        # default sql string
        sqlstr  = sqlstr_base_regular
        

        if req.path == apiconst.ROUTE_WATERMETER_HOUR or \
            req.path == apiconst.ROUTE_WATERMETER_DAY or \
            req.path == apiconst.ROUTE_WATERMETER_MONTH or \
            req.path == apiconst.ROUTE_WATERMETER_YEAR:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
            # rangetimestamp 
            v_rangetimestamp = ''


            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'], 
                            apierror.API_PARAMETER_ERROR['title'], 
                            apierror.API_PARAMETER_ERROR['description'] + err_str, 
                            code=apierror.API_PARAMETER_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_SORT:    
                    if value.lower() == 'asc':
                        v_sort = "ASC" 
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:     
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                    # clear range where clause, there can only be one.
                    v_rangetimestamp = '' 
                    # parse timestamp
                    if validate_timestamp_by_length( value ) == True:
                        v_starttime = " where TIMESTAMP >= '" + value + "' order by timestamp "
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )
                if key == apiconst.API_PARAMETER_RANGETIMESTAMP:
                    # clear starttime where clause, there can only be one.
                    v_starttime = ''
                    if validate_timestamp_by_length( value ) == True:
                        #print( "key=" + key + " value=" + value ) 
                        v_rangetimestamp = " where substr(timestamp,1," +  str(len(value)) + ") = '" + value + "' order by timestamp "
                    else:
                        raise falcon.HTTPError( 
                            apierror.API_TIMESTAMP_ERROR['status'], 
                            apierror.API_TIMESTAMP_ERROR['title'], 
                            apierror.API_TIMESTAMP_ERROR['description'] + str(value),
                            code=apierror.API_TIMESTAMP_ERROR['code'] 
                        )

            sqlstr = sqlstr + v_starttime + v_rangetimestamp + v_sort + str(v_limit)
            #print( "# sqlstr=" + sqlstr) 

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records = watermeter_db_uur.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                = a[0]
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]            = a[1]
                        new_dict[ apiconst.JSON_API_WM_PULS_CNT ]       = a[2]
                        new_dict[ apiconst.JSON_API_WM_CNSMPTN_LTR ]    = a[3]
                        new_dict[ apiconst.JSON_API_WM_CNSMPTN_LTR_M3 ] = a[4]

                        json_obj_data.append( new_dict )

                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status

watermeter_resource = Watermeter()
app.add_route( apiconst.ROUTE_WATERMETER_HOUR,       watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_HOUR_HELP,  watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_DAY,        watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_DAY_HELP,   watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_MONTH,      watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_MONTH_HELP, watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_YEAR,       watermeter_resource )
app.add_route( apiconst.ROUTE_WATERMETER_YEAR_HELP,  watermeter_resource )


class Phase( object ):

    sqlstr_base_regular = "select \
        TIMESTAMP, \
        cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
        VERBR_L1_KW * 1000, \
        VERBR_L2_KW * 1000, \
        VERBR_L3_KW * 1000, \
        GELVR_L1_KW * 1000, \
        GELVR_L2_KW * 1000, \
        GELVR_L3_KW * 1000, \
        L1_V, \
        L2_V, \
        L3_V, \
        L1_A, \
        L2_A, \
        L3_A \
        FROM " + const.DB_FASE_REALTIME_TAB + " "

    
    sqlstr_base_round = "select \
        TIMESTAMP, \
        cast(strftime('%s', TIMESTAMP, 'utc' ) AS Integer), \
        ROUND( VERBR_L1_KW * 1000 ), \
        ROUND( VERBR_L2_KW * 1000 ), \
        ROUND( VERBR_L3_KW * 1000 ), \
        ROUND( GELVR_L1_KW * 1000 ), \
        ROUND( GELVR_L2_KW * 1000 ), \
        ROUND( GELVR_L3_KW * 1000 ), \
        ROUND( L1_V ), \
        ROUND( L2_V ), \
        ROUND( L3_V ), \
        ROUND( L1_A ), \
        ROUND( L2_A ), \
        ROUND( L3_A )  \
        FROM " + const.DB_FASE_REALTIME_TAB + " "
    
    def on_get(self, req, resp):
        """Handles all GET requests."""

        #print ( req.query_string )
        #print ( req.params )
        #print ( req.path )

        json_data  = {
            apiconst.JSON_TS_LCL                : '',
            apiconst.JSON_TS_LCL_UTC            : 0,
            apiconst.JSON_API_PHS_CNSMPTN_L1_W  : 0,
            apiconst.JSON_API_PHS_CNSMPTN_L2_W  : 0,
            apiconst.JSON_API_PHS_CNSMPTN_L3_W  : 0,
            apiconst.JSON_API_PHS_PRDCTN_L1_W   : 0,
            apiconst.JSON_API_PHS_PRDCTN_L2_W   : 0,
            apiconst.JSON_API_PHS_PRDCTN_L3_W   : 0,
            apiconst.JSON_API_PHS_L1_V          : 0,
            apiconst.JSON_API_PHS_L2_V          : 0,
            apiconst.JSON_API_PHS_L3_V          : 0,
            apiconst.JSON_API_PHS_L1_A          : 0,
            apiconst.JSON_API_PHS_L2_A          : 0,
            apiconst.JSON_API_PHS_L3_A          : 0
        }

        if req.path == apiconst.ROUTE_PHASE_HELP:
            try:
                resp.body = ( json.dumps( apiconst.HELP_ROUTE_PHASE_JSON, sort_keys=True , indent=2 ) )
            except Exception as _e:
                flog.error ( str(__class__.__name__) + ":" + inspect.stack()[0][3] + ": help request on " + \
                apiconst.ROUTE_PHASE_HELP  + " failed , reason:" + str(_e.args[0]))
                raise falcon.HTTPError( 
                    apierror.API_GENERAL_ERROR['status'], 
                    apierror.API_GENERAL_ERROR['title'], 
                    apierror.API_GENERAL_ERROR['description'] + str(_e.args[0]), 
                    code=apierror.API_GENERAL_ERROR['code'] 
                    )
            return     

        # default sql string
        sqlstr = self.sqlstr_base_regular

        if req.path == apiconst.ROUTE_PHASE:
            
            # PARAMETERS
            # limit (of records)  {default = all, >0 }
            v_limit = '' #means all records
            # sort (on timestamp) {default is desc, asc}
            v_sort = "DESC"
            # round ( default is off, on) whole number rounded up or down depending the fraction ammount. 
            # json {default is array, object}
            v_json_mode = ''
            # starttime  =
            v_starttime = ' order by timestamp '
        
            for key, value in req.params.items():
               # this only gives the first parameter when more are put in
                value = list_filter_to_str( value )
                
                key = key.lower()
                #print ( key, value )
                if key ==  apiconst.API_PARAMETER_LIMIT:
                    try:
                        v_limit = ' limit '+ str( abs(int( value, 10 )) ) # no negative numbers.
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query" +str(v_limit) )
                    except Exception as _e:
                        err_str = 'limit value not ok, value used is ' + str(value)
                        flog.error ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": " + err_str)
                        raise falcon.HTTPError( 
                            apierror.API_PARAMETER_ERROR['status'],
                            apierror.API_PARAMETER_ERROR['title'],
                            apierror.API_PARAMETER_ERROR['description'] + err_str,
                            code=apierror.API_PARAMETER_ERROR['code']
                        )
                if key == apiconst.API_PARAMETER_SORT:
                    if value.lower() == 'asc':
                        v_sort = "ASC"
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query sort naar asc gezet." )
                if key == apiconst.API_PARAMETER_JSON_TYPE:
                    if value.lower() == 'object':
                        v_json_mode = 'object'
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query json naar object type gezet." )
                if key == apiconst.API_PARAMETER_ROUND: # round to the nearst value
                    if value.lower() == 'on':
                        sqlstr = self.sqlstr_base_round
                        flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query round aangezet." )
                if key == apiconst.API_PARAMETER_STARTTIMESTAMP:
                        # parse timestamp
                        value =  clean_timestamp_str( value )
                        if validate_timestamp ( value ) == True:
                            v_starttime = "where TIMESTAMP >= '" + value + "' order by timestamp "
                            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": sql query starttime is " +str(value) )

            sqlstr = sqlstr +  v_starttime + v_sort + str(v_limit)

            flog.debug ( __class__.__name__ + ":" + inspect.stack()[0][3] + ": SQL = " + sqlstr )

            try:
                # read datbase.
                records  = fase_db.select_rec( sqlstr )

                if v_json_mode ==  'object': 
                    # process records for JSON opjects
                    json_obj_data = [] 
                    for a in records:
                        new_dict = json_data.copy()
                        new_dict[ apiconst.JSON_TS_LCL ]                = a[0] 
                        new_dict[ apiconst.JSON_TS_LCL_UTC ]            = a[1] 
                        new_dict[ apiconst.JSON_API_PHS_CNSMPTN_L1_W ]  = a[2]
                        new_dict[ apiconst.JSON_API_PHS_CNSMPTN_L2_W ]  = a[3]
                        new_dict[ apiconst.JSON_API_PHS_CNSMPTN_L3_W ]  = a[4]
                        new_dict[ apiconst.JSON_API_PHS_PRDCTN_L1_W ]   = a[5]
                        new_dict[ apiconst.JSON_API_PHS_PRDCTN_L2_W ]   = a[6]
                        new_dict[ apiconst.JSON_API_PHS_PRDCTN_L3_W ]   = a[7]
                        new_dict[ apiconst.JSON_API_PHS_L1_V ]          = a[8]
                        new_dict[ apiconst.JSON_API_PHS_L2_V ]          = a[9]
                        new_dict[ apiconst.JSON_API_PHS_L3_V ]          = a[10]
                        new_dict[ apiconst.JSON_API_PHS_L1_A ]          = a[11]
                        new_dict[ apiconst.JSON_API_PHS_L2_A ]          = a[12]
                        new_dict[ apiconst.JSON_API_PHS_L3_A ]          = a[13]
                        json_obj_data.append( new_dict )
                    resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True )
                else:
                    resp.body = json.dumps( records, ensure_ascii=False )
                
                #print ( records )
            except Exception as _e:
                raise falcon.HTTPError( 
                    apierror.API_DB_ERROR['status'], 
                    apierror.API_DB_ERROR['title'], 
                    apierror.API_DB_ERROR['description'] + str(_e.args[0] + " query used: " + sqlstr), 
                    code=apierror.API_DB_ERROR['code'] 
                    )
               
            resp.status = falcon.HTTP_200  # This is the default status
            #resp.body = json.dumps( records, ensure_ascii=False )
            #resp.body = json.dumps( json_obj_data , ensure_ascii=False , sort_keys=True , indent=4)

phase_resource = Phase()
app.add_route( apiconst.ROUTE_PHASE,       phase_resource )
app.add_route( apiconst.ROUTE_PHASE_HELP , phase_resource )
