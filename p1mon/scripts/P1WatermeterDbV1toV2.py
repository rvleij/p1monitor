#!/usr/bin/python3
import const
import inspect
import os
import shutil
import signal
import sys
import time
import datetime
import sqldb

from datetime import datetime, timedelta, timezone
from logger import fileLogger,logging
from sqldb import WatermeterDB, WatermeterDBV2
from util import mkLocalTimeString

# programme name.
prgname = 'P1WatermeterDbV1toV2'

V2_watermeter_db = WatermeterDBV2()
V1_watermeter_db = WatermeterDB()

def Main(argv): 
    
    my_pid = os.getpid()
    flog.info("Start van programma met process id " + str(my_pid) )

    if os.path.isfile( const.FILE_DB_WATERMETER ):
        flog.info( inspect.stack()[0][3] + ": oude versie van database bestaat, start van verwerking." )
    else:
        flog.info( inspect.stack()[0][3] + ": oude versie van database bestand " +  const.FILE_DB_WATERMETER + " bestaat niet, niets te converteren. Gestopt!" )
        sys.exit(0)

     # open watermeter V1 databases
    try:    
        V1_watermeter_db.init( const.FILE_DB_WATERMETER, const.DB_WATERMETER_UUR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_UUR_TAB + " succesvol geopend." )

    # open watermeter V2 database 
    try:    
        V2_watermeter_db.init( const.FILE_DB_WATERMETERV2, const.DB_WATERMETERV2_TAB, flog )
    except Exception as e:
        flog.critical( inspect.stack()[0][3] + ": Database niet te openen(3)." + const.FILE_DB_WATERMETERV2 + " melding:" + str(e.args[0]) )
        sys.exit(1)
    flog.info( inspect.stack()[0][3] + ": database tabel " + const.DB_WATERMETERV2_TAB + " succesvol geopend." )

    flog.info( inspect.stack()[0][3] + ": wissen van records die verouderd zijn." )

    #do db cleanup 
    timestamp = mkLocalTimeString()
    try:
        del_timestamp =  str( datetime.strptime( timestamp, "%Y-%m-%d %H:%M:%S") - timedelta(days=3670))
        sql_del_str = "delete from " + const.DB_WATERMETER_UUR_TAB + " where timestamp < '" + del_timestamp + "'"
        flog.info( inspect.stack()[0][3] + ": uur records ouder dan " + del_timestamp + " worden gewist." ) 
        V1_watermeter_db.del_rec( sql_del_str )     
    except Exception as e:
        flog.warning (inspect.stack()[0][3]+": wissen van oude uren records gefaald: " + str(e) )


    total_records_processed = 0
   
    flog.info( inspect.stack()[0][3] + ": toevoegen van V1 database uur records naar V2 database." )
    records_processed = selectAndInsertRecord( const.DB_WATERMETER_UUR_TAB, sqldb.INDEX_HOUR)
    total_records_processed += records_processed
    flog.info( inspect.stack()[0][3] + ": " + str(records_processed) + " uur records toegevoegd." )

    flog.info( inspect.stack()[0][3] + ": toevoegen van V1 database dag records naar V2 database." )
    records_processed = selectAndInsertRecord( const.DB_WATERMETER_DAG_TAB, sqldb.INDEX_DAY )
    total_records_processed += records_processed
    flog.info( inspect.stack()[0][3] + ": " + str(records_processed) + " dag records toegevoegd." )

    flog.info( inspect.stack()[0][3] + ": toevoegen van V1 database maand records naar V2 database." )
    records_processed = selectAndInsertRecord( const.DB_WATERMETER_MAAND_TAB, sqldb.INDEX_MONTH )
    total_records_processed += records_processed
    flog.info( inspect.stack()[0][3] + ": " + str(records_processed) + " maand records toegevoegd." )

    flog.info( inspect.stack()[0][3] + ": toevoegen van V1 database jaar records naar V2 database." )
    records_processed = selectAndInsertRecord( const.DB_WATERMETER_JAAR_TAB, sqldb.INDEX_YEAR )
    total_records_processed += records_processed
    flog.info( inspect.stack()[0][3] + ": " + str(records_processed) + " jaar records toegevoegd." )

    flog.info( inspect.stack()[0][3] + ": " + str(total_records_processed) + " van V1 database records naar V2 database gekopierd." )

    renameV1Databases()

    sys.exit()


##############################################
# make a complete path to disk from ram path #
##############################################
def diskPathByFilename( filename ):
    _path,tail = os.path.split( filename )
    return const.DIR_FILEDISK + tail

def renameV1Databases():
    try:
        if os.path.isfile( const.FILE_DB_WATERMETER ):
            os.rename( const.FILE_DB_WATERMETER, const.FILE_DB_WATERMETER + ".imported" )
    except Exception as e:
        flog.warning( inspect.stack()[0][3] + ": " + const.FILE_DB_WATERMETER + " was niet te hernoemen -> " + str(e.args) )
    flog.info( inspect.stack()[0][3] + ": database bestand "  + const.FILE_DB_WATERMETER + " hernoemd naar " + const.FILE_DB_WATERMETER + ".imported" )

    filename =  diskPathByFilename(const.FILE_DB_WATERMETER) 
    try:
        if os.path.isfile( filename ):
            os.rename( filename, filename + ".imported" )
    except Exception as e:
        flog.warning( inspect.stack()[0][3] + ": " + filename + " was iet te hernoemen -> " + str(e.args) )
    flog.info( inspect.stack()[0][3] + ": database bestand "  + filename + " hernoemd naar " + filename + ".imported" )


def selectAndInsertRecord( tablename , timeperiod_id ):
    records_added = 0
    rec_values = sqldb.WATERMETER_REC
    try:
        sql = "select TIMESTAMP, PULS_PER_TIMEUNIT, VERBR_PER_TIMEUNIT, VERBR_IN_M3_TOTAAL from " + tablename
        records = V1_watermeter_db.select_rec( sql )
        for record in records:
            #print ( record[0] )
            rec_values['TIMESTAMP']             = record[0]
            rec_values['TIMEPERIOD_ID']         = timeperiod_id
            rec_values['PULS_PER_TIMEUNIT']     = record[1]
            rec_values['VERBR_PER_TIMEUNIT']    = record[2]
            rec_values['VERBR_IN_M3_TOTAAL']    = record[3]
            if V2_watermeter_db.insert_rec_with_values( rec_values, True ) == True:
                records_added += 1
    except Exception as _e:
        flog.warning (inspect.stack()[0][3]+": select gefaald: " + str(_e) )
    return records_added



def saveExit(signum, frame):
    flog.info(inspect.stack()[0][3]+" SIGINT ontvangen, gestopt.")
    signal.signal(signal.SIGINT, original_sigint)
    sys.exit(0)


########################################################
# init                                                 #
########################################################
if __name__ == "__main__":
    global process_bg 
    try:
        os.umask( 0o002 )
        flog = fileLogger( const.DIR_FILELOG + prgname + ".log" , prgname)    
        flog.setLevel( logging.DEBUG )
        flog.consoleOutputOn( True ) 
    except Exception as e:
        print ("critical geen logging mogelijke, gestopt.:"+str(e.args[0]))
        sys.exit(1)
    
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, saveExit)
    Main(sys.argv[1:])           

