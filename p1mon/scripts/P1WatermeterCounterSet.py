#!/usr/bin/python3
import const
import inspect
import os
import shutil
import signal
import socket
import sys
import random
import time
import datetime

from datetime import datetime, timedelta
from logger import fileLogger,logging
from sqldb import configDB, rtStatusDb, WatermeterDB
from time import sleep
from util import fileExist,setFile2user,fileChanged, getUtcTime, mkLocalTimeString
from gpio import gpioDigtalInput
from random import randrange
from utiltimestamp import utiltimestamp

# programme name.
prgname = 'P1WatermeterCounterSet'

rt_status_db        = rtStatusDb()
config_db           = configDB()
watermeter_db_uur   = WatermeterDB()
watermeter_db_dag   = WatermeterDB()
watermeter_db_maand = WatermeterDB()
watermeter_db_jaar  = WatermeterDB()

gpioWatermeterPuls = gpioDigtalInput()
timestamp          = mkLocalTimeString() 

utc_timestamp_last_backup = 0 # warning used by multiprocessing

def Main(argv): 
    global timestamp, utc_timestamp_last_backup

    flog.info("Start van programma.")

    # open van config database      
    try:
        config_db.init(const.FILE_DB_CONFIG,const.DB_CONFIG_TAB)
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(3)."+const.FILE_DB_CONFIG+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel "+const.DB_CONFIG_TAB+" succesvol geopend.")

    # open van status database      
    try:    
        rt_status_db.init(const.FILE_DB_STATUS,const.DB_STATUS_TAB)
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)."+const.FILE_DB_STATUS+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel "+const.DB_STATUS_TAB+" succesvol geopend.")

    # open van watermeter databases
    try:    
        watermeter_db_uur.init( const.FILE_DB_WATERMETER, const.DB_WATERMETER_UUR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_UUR_TAB + " succesvol geopend." )

    try:    
        watermeter_db_dag.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_DAG_TAB , flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_DAG_TAB + " succesvol geopend." )

    try:    
        watermeter_db_maand.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_MAAND_TAB ,flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_MAAND_TAB + " succesvol geopend." )

    try:    
        watermeter_db_jaar.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_JAAR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.debug(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_JAAR_TAB  + " succesvol geopend." )

    #config_db.strset('1', 101, flog)
    #sys.exit(0)

     # watermeter reset
    try:
        _config_id, reset_watermeter_is_on, _text = config_db.strget( 101,flog )
        if reset_watermeter_is_on == "0":
            flog.info( inspect.stack()[0][3]+": watermeter reset is niet actief.")
        else:
            config_db.strset('0', 101, flog ) #reset de reset attempt.
            if resetWaterMeterStand() == False:
                flog.error("reset gefaald")
                rt_status_db.strset( 'verwerking gefaald.', 107, flog )
    except Exception:
        flog.error(inspect.stack()[0][3]+": reset flag error, gestopt. " )
        sys.exit( 1 )

    #resetWaterMeterStand()

    flog.info("Stop van programma.")
    rt_status_db.strset( 'aanpassing verwerkt', 107, flog )
    sys.exit( 0 )

def resetWaterMeterStand():

    flog.info( inspect.stack()[0][3] + ": watermeter reset wordt uitgevoerd (start)." )
    rt_status_db.strset( 'verwerking gestart', 107, flog )

    #sanity check
    try:
        _config_id, timestamp_reset, _text = config_db.strget( 100,flog )
        #timestamp_reset = '2019-11-29 08:00:00' 
        flog.info( inspect.stack()[0][3] + ": watermeter reset datum is " + str(timestamp_reset) )
        timestamp_obj  = utiltimestamp( timestamp_reset )
        timestamp_obj.santiycheck()
    except Exception:
        flog.error(inspect.stack()[0][3]+": watermeter reset fout, timestamp " + str( timestamp_reset ) + " is niet correct."  )
        return False

    try:
        _config_id, verbr_m3_reset_value, _text = config_db.strget( 99,flog )
        verbr_m3_reset_value = float( verbr_m3_reset_value )
        flog.info( inspect.stack()[0][3] + ": watermeter stand is " + str(verbr_m3_reset_value) )
    except Exception:
        flog.error(inspect.stack()[0][3]+": watermeter reset fout, meterstand  " + str( verbr_m3_reset_value ) + " is niet correct."  )
        return False
    
    try:
        rt_status_db.timestamp( 91, flog ) # set timestamp of reset.

        flog.info( inspect.stack()[0][3] + " Watermeterstanden aanpassen voor de uur tabel met de timestamp "  + timestamp_reset ) 
        watermeter_db_uur.update_m3_verbr_phase_1(   timestamp_reset, verbr_m3_reset_value, 'hour' )
        rt_status_db.strset( 'uren verwerkt', 107, flog )

        flog.info( inspect.stack()[0][3] + " Watermeterstanden aanpassen voor de dag tabel met de timestamp "  + timestamp_reset )
        updateTellerstandenDag( timestamp_reset )
        rt_status_db.strset( 'dagen verwerkt', 107, flog )
                
        flog.info( inspect.stack()[0][3] + " Watermeterstanden aanpassen voor de maand tabel met de timestamp " + timestamp_reset ) 
        updateTellerstandenMaand( timestamp_reset )
        rt_status_db.strset( 'maanden verwerkt', 107, flog )

        flog.info( inspect.stack()[0][3] + " Watermeterstanden aanpassen voor de jaar tabel met de timestamp " + timestamp_reset ) 
        updateTellerstandenJaar( timestamp_reset )
        rt_status_db.strset( 'jaren verwerkt', 107, flog )

        flog.info( inspect.stack()[0][3] + ": watermeterstand reset gereed. (stop)." )
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": watermeter reset fout ->" + str(e)  )
        return False
    
    return True


def updateTellerstandenDag( timestamp ):

    timestamp = timestamp[0:9]+'-01 00:00:00' 
    #print ( "###1 = " + timestamp )

    timestamp_start = watermeter_db_dag.get_min_max_timestamp( timestamp, mode='min' )
    timestamp_stop  = watermeter_db_dag.get_min_max_timestamp( timestamp, mode='max' )
    rec_count       = watermeter_db_dag.get_record_count( timestamp )
    
    if timestamp_start == None or timestamp_stop == None or rec_count == None:
        flog.warning( inspect.stack()[0][3]+": probleem met inlezen van start, stop tijden of aantal records." )
        return False

    while True:

        sql = "select max(VERBR_IN_M3_TOTAAL) from watermeter_history_uur where substr(timestamp,1,10) = '" + \
        timestamp_start[0:10] + "';"
        flog.debug ( inspect.stack()[0][3] + ": " + sql )

        verbr_value = watermeter_db_uur.select_rec( sql )[0][0]

        if verbr_value != None:
            sql_2 = "update watermeter_history_dag SET VERBR_IN_M3_TOTAAL = " + \
                        format ( float( verbr_value ) , '.4f' ) + \
                        " WHERE timestamp = '" + timestamp_start + "';" 
            flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
            watermeter_db_dag.update_rec( sql_2  )
            
        if timestamp_start == timestamp_stop:
            break
        timestamp_start = str( datetime.strptime( timestamp_start, "%Y-%m-%d %H:%M:%S") + timedelta( days=1 ) )
    return True

def updateTellerstandenMaand( timestamp ):
    
    timestamp = timestamp[0:6]+'-01 00:00:00' 
    #print ( "###2 = " + timestamp )

    timestamp_start = watermeter_db_maand.get_min_max_timestamp( timestamp, mode='min' )
    timestamp_stop  = watermeter_db_maand.get_min_max_timestamp( timestamp, mode='max' )
    rec_count       = watermeter_db_maand.get_record_count( timestamp )
    
    if timestamp_start == None or timestamp_stop == None or rec_count == None:
        flog.warning( inspect.stack()[0][3]+": probleem met inlezen van start, stop tijden of aantal records." )
        return False

    while True:

        sql = "select max(VERBR_IN_M3_TOTAAL) from watermeter_history_dag where substr(timestamp,1,7) = '" + \
        timestamp_start[0:7] + "';"
        flog.debug ( inspect.stack()[0][3] + ": " + sql )

        verbr_value = watermeter_db_dag.select_rec( sql )[0][0]

        if verbr_value != None:
            sql_2 = "update watermeter_history_maand SET VERBR_IN_M3_TOTAAL = " + \
                format ( float( verbr_value ) , '.4f' ) + \
                " WHERE timestamp = '" + timestamp_start + "';" 
            flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
            watermeter_db_maand.update_rec( sql_2  )
            
        if timestamp_start == timestamp_stop:
            break
        timestamp_obj  = utiltimestamp( timestamp_start )
        timestamp_start = timestamp_obj.monthmodify(1)

    return True

def updateTellerstandenJaar( timestamp ):
    
    timestamp = timestamp[0:4]+'-01-01 00:00:00' 
    #print ( "###3 = " + timestamp )

    timestamp_start = watermeter_db_jaar.get_min_max_timestamp( timestamp, mode='min' )
    timestamp_stop  = watermeter_db_jaar.get_min_max_timestamp( timestamp, mode='max' )
    rec_count       = watermeter_db_jaar.get_record_count( timestamp )
    
    if timestamp_start == None or timestamp_stop == None or rec_count == None:
        flog.warning( inspect.stack()[0][3]+": probleem met inlezen van start, stop tijden of aantal records." )
        return False

    while True:

        sql = "select max(VERBR_IN_M3_TOTAAL) from watermeter_history_maand where substr(timestamp,1,4) = '" + \
        timestamp_start[0:4] + "';"
        flog.debug ( inspect.stack()[0][3] + ": " + sql )

        verbr_value = watermeter_db_maand.select_rec( sql )[0][0]

        if verbr_value != None:
            sql_2 = "update watermeter_history_jaar SET VERBR_IN_M3_TOTAAL = " + \
                format ( float( verbr_value ) , '.4f' ) + \
                " WHERE timestamp = '" + timestamp_start + "';" 
            flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
            watermeter_db_maand.update_rec( sql_2  )
             
        if timestamp_start == timestamp_stop:
            break
        timestamp_start = str( int(timestamp_start[0:4]) + 1 ) + timestamp_start[4:]

    return True


#-------------------------------
if __name__ == "__main__":

    try:
        os.umask( 0o002 )
        flog = fileLogger( const.DIR_FILELOG + prgname + ".log" , prgname)    
        #### aanpassen bij productie
        flog.setLevel( logging.INFO )
        flog.consoleOutputOn( True ) 
    except Exception as e:
        print ("critical geen logging mogelijke, gestopt.:"+str(e.args[0]))
        sys.exit(1)
    
    Main(sys.argv[1:])           
