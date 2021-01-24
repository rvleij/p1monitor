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
prgname = 'P1Watermeter'

rt_status_db        = rtStatusDb()
config_db           = configDB()
watermeter_db_uur   = WatermeterDB()
watermeter_db_dag   = WatermeterDB()
watermeter_db_maand = WatermeterDB()
watermeter_db_jaar  = WatermeterDB()

gpioWatermeterPuls = gpioDigtalInput()
timestamp          = mkLocalTimeString() 

utc_timestamp_last_backup = 0 # warning used by multiprocessing
prg_is_active = True

def Main(argv): 
    global timestamp, utc_timestamp_last_backup

    flog.info("Start van programma.")

    DiskRestore()
    
     # open van config database      
    try:
        config_db.init(const.FILE_DB_CONFIG,const.DB_CONFIG_TAB)
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(3)."+const.FILE_DB_CONFIG+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel "+const.DB_CONFIG_TAB+" succesvol geopend.")

    # open van status database      
    try:    
        rt_status_db.init(const.FILE_DB_STATUS,const.DB_STATUS_TAB)
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)."+const.FILE_DB_STATUS+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel "+const.DB_STATUS_TAB+" succesvol geopend.")

    # open van watermeter databases
    try:    
        watermeter_db_uur.init( const.FILE_DB_WATERMETER, const.DB_WATERMETER_UUR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_UUR_TAB + " succesvol geopend." )

    try:    
        watermeter_db_dag.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_DAG_TAB , flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_DAG_TAB + " succesvol geopend." )

    try:    
        watermeter_db_maand.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_MAAND_TAB ,flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_MAAND_TAB + " succesvol geopend." )

    try:
        watermeter_db_jaar.init( const.FILE_DB_WATERMETER ,const.DB_WATERMETER_JAAR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_JAAR_TAB  + " succesvol geopend." )

    # database defrag 
    watermeter_db_uur.defrag()
    watermeter_db_dag.defrag()
    watermeter_db_maand.defrag()
    watermeter_db_jaar.defrag()

    # set proces gestart timestamp
    rt_status_db.timestamp( 98,flog )
    
    try:
        gpioWatermeterPuls.init( 97, config_db ,flog )
    except Exception as e:
        flog.warning( inspect.stack()[0][3] + ": GPIO pin voor watermeter niet te openen. " + str(e.args[0])  ) 

    # one time message for log
    if prgIsActive(flog) == False:
        flog.info(inspect.stack()[0][3]+": programma is niet als actief geconfigureerd , wordt niet uitgevoerd.")

    while True:

        while prgIsActive( flog ) == False: # sleep function in prgIsActive()
                continue
        
        #check if GPIO pin is set or else wait for a valid pin
        while gpioWatermeterPuls.gpio_pin == None:
            flog.debug( inspect.stack()[0][3] + ": GPIO pin wordt opnieuw geprobeerd.") 
            time.sleep(30) # wait to limit load
            try:
                gpioWatermeterPuls.init( 97, config_db ,flog )
            except:
                pass
           
        waitForPuls()


def waitForPuls():
    global gpioWatermeterPuls

    #flog.debug(inspect.stack()[0][3]+": Start van verwerken van watermeter pulsen, verwerking is actief.")
    if gpioWatermeterPuls.gpioWaitRead() == True:
    #if pulsSimulator(probility = 0.99 ) == True:
    #if pulsSimulator( probility = 0.3 ) == True:
        rt_status_db.timestamp( 90, flog ) # set timestamp of puls detected
        timestamp = mkLocalTimeString()

        flog.debug( inspect.stack()[0][3]+": Watermeter puls gedetecteerd." )
        _id, puls_value_in_liters, _label = config_db.strget( 98, flog )
            
        ###################
        # hour processing #
        ###################
        timestamp_uur = timestamp[0:13]+":00:00"
        last_m3_hour_value = 0
        #first check if there are any previous records
        timestamp_uur_minus_one = str( datetime.strptime(timestamp_uur, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1 ) )
        rec_previous = watermeter_db_uur.select_previous_rec_with_values( timestamp_uur )
        if rec_previous != None: # there is an previous record
            flog.debug(inspect.stack()[0][3]+": een ouder record gevonden." + str(rec_previous ) )
            watermeter_db_uur.create_record_set_between_times( rec_previous[0], timestamp_uur_minus_one, rec_previous[3], 'hour' )
            last_m3_hour_value = float(rec_previous[3])
                
        rec = watermeter_db_uur.get_timestamp_record( timestamp_uur )    
        record_values = { \
            "timestamp":timestamp_uur, \
            "PULS_PER_TIMEUNIT":1, \
            "VERBR_PER_TIMEUNIT":puls_value_in_liters , \
             "VERBR_IN_M3_TOTAAL": format( (float(puls_value_in_liters)/1000) + last_m3_hour_value, '.4f' )\
         }

        if rec == None: # no record for this hour
            flog.debug(inspect.stack()[0][3]+": GEEN: uur record gevonden, nieuw record aanmaken.")
            watermeter_db_uur.replace_rec_with_values( record_values )
        else: # update current hour record
            flog.debug(inspect.stack()[0][3]+": WEL: uur record gevonden, bestaande record aanpassen.")
            record_values["PULS_PER_TIMEUNIT"]  = float(rec[1]) + 1
            record_values["VERBR_PER_TIMEUNIT"] = float(rec[2]) + float(puls_value_in_liters)
            record_values["VERBR_IN_M3_TOTAAL"] = format( ((float(rec[3]) + float(puls_value_in_liters)/1000)), '.4f' )
            watermeter_db_uur.replace_rec_with_values( record_values )
            

        ###################
        # day processing  #
         ###################
        timestamp_day = timestamp[0:11]+"00:00:00"
        last_m3_day_value = 0
         #first check if there are any previous records
        timestamp_dag_minus_one = str( datetime.strptime( timestamp_day, "%Y-%m-%d %H:%M:%S") - timedelta(days=1 ) )
        rec_previous = watermeter_db_dag.select_previous_rec_with_values( timestamp_day )
        if rec_previous != None: # there is an previous record
            flog.debug(inspect.stack()[0][3]+": een ouder dag record gevonden." + str(rec_previous ) )
            last_m3_day_value = float( rec_previous[3] )
            watermeter_db_dag.create_record_set_between_times( rec_previous[0], timestamp_dag_minus_one, last_m3_day_value, 'day' )
        else:
            last_m3_day_value = 0

        rec_day_total = watermeter_db_uur.get_totals_record( timestamp_day, 'day' )
        #print ( rec_day_total )
        record_values = { \
            "timestamp":          timestamp_day,    \
            "PULS_PER_TIMEUNIT":  rec_day_total[0], \
            "VERBR_PER_TIMEUNIT": rec_day_total[1], \
            "VERBR_IN_M3_TOTAAL": rec_day_total[2]  \
        }

        #print ( record_values )
        watermeter_db_dag.replace_rec_with_values( record_values )
            

        #####################
        # month processing  #
        #####################
        #timestamp_day = timestamp[0:11]+"00:00:00"
        timestamp_maand = timestamp[0:7]+"-01 00:00:00"
        last_m3_month_value = 0
        #print( timestamp_maand )

        #first check if there are any previous records
        timestamp_obj = utiltimestamp( timestamp_maand )
        timestamp_maand_minus_one = timestamp_obj.monthmodify(-1)
        #print ( timestamp_maand_minus_one )

        rec_previous = watermeter_db_maand.select_previous_rec_with_values( timestamp_maand  )

        if rec_previous != None: # there is an previous record
            flog.debug(inspect.stack()[0][3]+": een ouder maand record gevonden." + str(rec_previous ) )
            last_m3_month_value = float( rec_previous[3] )
            watermeter_db_maand.create_record_set_between_times( rec_previous[0], timestamp_maand_minus_one, last_m3_month_value, 'month' )
        else:
            last_m3_month_value = 0
           
        rec_month_total = watermeter_db_dag.get_totals_record( timestamp_day, 'month' )
        #print ( rec_month_total )
            
        record_values = { \
            "timestamp":          timestamp_maand,    \
            "PULS_PER_TIMEUNIT":  rec_month_total[0], \
            "VERBR_PER_TIMEUNIT": rec_month_total[1], \
            "VERBR_IN_M3_TOTAAL": rec_month_total[2]  \
        }

        #print ( record_values )
        watermeter_db_maand.replace_rec_with_values( record_values )    
            
        #####################
        # year processing  #
        #####################
        # we asume there will be no previous year to get data just update the year
        timestamp_jaar = timestamp[0:4]+"-01-01 00:00:00"
        #print( timestamp_jaar)
        rec_year_total = watermeter_db_maand.get_totals_record( timestamp_jaar, 'year' )
        #print ( rec_year_total )

        record_values = { \
            "timestamp":          timestamp_jaar,   \
            "PULS_PER_TIMEUNIT":  rec_year_total[0], \
            "VERBR_PER_TIMEUNIT": rec_year_total[1], \
            "VERBR_IN_M3_TOTAAL": rec_year_total[2]  \
        }

        #print ( record_values )
        watermeter_db_jaar.replace_rec_with_values( record_values )    
            
        #do db cleanup 
        try:
            sql_del_str = "delete from " + const.DB_WATERMETER_UUR_TAB + " where timestamp < '" +\
                 str( datetime.strptime( timestamp, "%Y-%m-%d %H:%M:%S") - timedelta(days=3670))+"'"
            flog.debug( inspect.stack()[0][3] + ": delete uren : sql=" + sql_del_str ) 
            watermeter_db_uur.del_rec( sql_del_str )     
        except Exception as e:
            flog.warning (inspect.stack()[0][3]+": watermeter deleten van oude uren records gefaald: " + str(e) )
    else:
        # warning, there puls must be off to update the gpio pin.
        gpioWatermeterPuls.check_pin_from_db()

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

        try:
            
            verbr_value = watermeter_db_uur.select_rec( sql )[0][0]

            if verbr_value != None:
                sql_2 = "update watermeter_history_dag SET VERBR_IN_M3_TOTAAL = " + \
                        format ( float( verbr_value ) , '.4f' ) + \
                        " WHERE timestamp = '" + timestamp_start + "';" 
                flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
                watermeter_db_dag.update_rec( sql_2  )
            
        except Exception:
                flog.warning( inspect.stack()[0][3]+": probleem met timestamp " + timestamp_start + \
                " bij het aanpassen van de watermetertellerstanden, tabel watermeter_history_dag" )
                return False
                
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

        try:
            verbr_value = watermeter_db_dag.select_rec( sql )[0][0]

            if verbr_value != None:
                sql_2 = "update watermeter_history_maand SET VERBR_IN_M3_TOTAAL = " + \
                        format ( float( verbr_value ) , '.4f' ) + \
                        " WHERE timestamp = '" + timestamp_start + "';" 
                flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
                watermeter_db_maand.update_rec( sql_2  )
            
        except Exception:
                flog.warning( inspect.stack()[0][3]+": probleem met timestamp " + timestamp_start + \
                " bij het aanpassen van de watermetertellerstanden, tabel watermeter_history_maand" )
                return False
                
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

        try:
            verbr_value = watermeter_db_maand.select_rec( sql )[0][0]

            if verbr_value != None:
                sql_2 = "update watermeter_history_jaar SET VERBR_IN_M3_TOTAAL = " + \
                        format ( float( verbr_value ) , '.4f' ) + \
                        " WHERE timestamp = '" + timestamp_start + "';" 
                flog.debug ( inspect.stack()[0][3] + ": " + sql_2 )
                watermeter_db_maand.update_rec( sql_2  )
            
        except Exception:
                flog.warning( inspect.stack()[0][3]+": probleem met timestamp " + timestamp_start + \
                " bij het aanpassen van de watermetertellerstanden, tabel watermeter_history_maand" )
                return False
                
        if timestamp_start == timestamp_stop:
            break
        timestamp_start = str( int(timestamp_start[0:4]) + 1 ) + timestamp_start[4:]

    return True

def pulsSimulator(probility = 0.2 ):
    flog.warning( inspect.stack()[0][3] + " is actief."  ) 
    time.sleep(1)
    if random.randrange(100) < probility*100:
        return True
    else:
        return False

def prgIsActive( flog ):
    global prg_is_active

    _config_id, status, _text = config_db.strget( 96,flog )
    if status == "0":
        if  prg_is_active == True:
            flog.info(inspect.stack()[0][3]+": programma is niet als actief geconfigureerd, gepauzeerd.")
        prg_is_active = False
        flog.debug(inspect.stack()[0][3]+": programma is niet als actief geconfigureerd, pauzeer")
        sleep( 10 ) # wait 10 sec to try again
        return False
    else:
        if prg_is_active == False:
                flog.info(inspect.stack()[0][3]+": programma is geactiveerd.")
        prg_is_active = True
        return True

def backupData():
    flog.debug( inspect.stack()[0][3] + ": Gestart" )
    os.system("/p1mon/scripts/./P1DbCopy.py -all2disk --forcecopy")
      
def DiskRestore():
    # kopieren van bestaande database file van flash storage naar ramdisk
    # als deze nog niet al op de ramdisk staat
   os.system("/p1mon/scripts/P1DbCopy.py --allcopy2ram")
   
def saveExit(signum, frame):   
        signal.signal(signal.SIGINT, original_sigint)
        gpioWatermeterPuls.close()
        backupData()
        flog.info(inspect.stack()[0][3]+" SIGINT ontvangen, gestopt.")
        sys.exit(0)

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
    
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, saveExit)
    Main(sys.argv[1:])           
