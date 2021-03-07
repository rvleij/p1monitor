#!/usr/bin/python3
import argparse
import sys
import glob
import zlib
import const
import inspect
import signal
import zipfile
import fnmatch
import datetime
import getopt
import json
import os
import pwd
import shutil
import subprocess
import semaphore3
import systemid
import time
import crypto3

from sqldb import configDB, SqlDb2, financieelDb, currentWeatherDB, historyWeatherDB, temperatureDB, WatermeterDB, PhaseDB, powerProductionDB, WatermeterDBV2
from logger import fileLogger,logging
from datetime import datetime, timedelta
from semaphore3 import writeSemaphoreFile
from os import umask
#from shutil import 

prgname = 'P1SqlImport'

config_db             = configDB()
e_db_history_min      = SqlDb2() 
e_db_financieel_dag   = financieelDb()
e_db_financieel_maand = financieelDb()
e_db_financieel_jaar  = financieelDb()
weer_db               = currentWeatherDB()
weer_history_db_uur   = historyWeatherDB()
temperature_db        = temperatureDB()
temperature_db        = temperatureDB()
#V1 of the watermeter database, we keep supporting this for older software versions that import data
watermeter_db_uur     = WatermeterDB()
watermeter_db_dag     = WatermeterDB()
watermeter_db_maand   = WatermeterDB()
watermeter_db_jaar    = WatermeterDB()
#V2 of the watermeter database
watermeter_db         = WatermeterDBV2()
fase_db               = PhaseDB()
power_production_db   = powerProductionDB()

statusdata = {
   'status_text'           : 'onbekend',
   'records_processed_ok'  :  0,
   'records_processed_nok' :  0,
   'records_total'         :  0,
   'export_timestamp'      :  0
}

#def updateRecordsProcessedOk(filename, cnt):
#    statusdata['records_processed_ok'] = cnt
#    writeStatusFile(filename)
#    #time.sleep(0.3) #debug
    
#def updateRecordsProcessedNok(filename, cnt):
#    statusdata['records_processed_nok'] = cnt
#    writeStatusFile(filename)
#    #time.sleep(0.3) #debug    


def updateStatusFile(filename, processed_ok, processed_nok, status_text , args):
   
    if args.rmstatus == True: # no status file requested, do noting
      return

    fo = open( filename, "w" )
    statusdata['records_processed_ok']  = processed_ok
    statusdata['records_processed_nok'] = processed_nok
    statusdata['status_text']           = status_text
    fo.write(json.dumps( statusdata ))
    fo.close()
    flog.debug (inspect.stack()[0][3]+": records_processed_ok = "+ str(statusdata['records_processed_ok']) )
    
def Main(argv):             
    flog.info("Start van programma.")
    flog.info(inspect.stack()[0][3]+": wordt uitgevoerd als user -> "+pwd.getpwuid( os.getuid() ).pw_name)

    timestart = time.time()
    #timestamp = mkLocalTimestamp()

    importfile = ''
    global statusfile

    parser = argparse.ArgumentParser( description = prgname )
    parser.add_argument( '-i' , '--importfile', help="Naam van het export bestand om te importeren.",     required=True  ) 
    parser.add_argument( '-rm', '--rmstatus',   help="Maak geen status bestand aan", action='store_true', required=False ) 

    """
    try:
        opts, _args = getopt.getopt(argv,"hi:",["importfile="])
    except getopt.GetoptError:
        print ( prgname+'.py -i <importfile>' )
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ( prgname+'.py -i <importfile>' )
            sys.exit()
        elif opt in ("-i", "--importfile"):
            importfile = arg
    """
    args = parser.parse_args()
    if args.importfile != None:
        importfile = args.importfile

    if importfile == '':
        print ( prgname+'.py -i <importfile>' )
        flog.error("gestopt importfile ontbreekt.")
        sys.exit(2)

    #updateStatusFile( '/p1mon/mnt/ramdisk/test1.txt', 0, 0, 'bezig', args )
    #time.sleep(10)
    #sys.exit()

    #print 'importfile ', importfile
    #return
    flog.info(inspect.stack()[0][3]+": import bestand = "+importfile)

    _head,tail = os.path.split(importfile) 
   
    statusfile  = const.DIR_RAMDISK + tail + ".status"
    flog.info( inspect.stack()[0][3]+": status bestand = " + statusfile )

    updateStatusFile( statusfile, 0,0, 'bezig' , args )
    
    try:
        extension = os.path.splitext(importfile)[1]
        flog.info(inspect.stack()[0][3]+": ZIP file "+importfile+" gevonden ")
        if extension != '.zip':
            flog.warning(inspect.stack()[0][3]+": Geen passend ZIP file gevonden, gestopt.")  
            return
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": Geen passend ZIP file gevonden, gestopt -> "+str(e))
        return


    #statusdata['status_text'] = 'bezig'
    #writeStatusFile(statusfile)

    updateStatusFile(statusfile, 0,0, 'bezig' , args )
   
    #zipfilename = const.DIR_EXPORT + const.EXPORT_PREFIX + timestamp +".zip"
    #semafoorfile = const.DIR_RAMDISK + const.EXPORT_PREFIX + ".busy"
    #fo = open(semafoorfile, "w")
    #fo.write(semafoorfile)
    #fo.close()

    # open van config database
    try:
        config_db.init(const.FILE_DB_CONFIG,const.DB_CONFIG_TAB)
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(3)."+const.FILE_DB_CONFIG+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database "+const.DB_CONFIG+" succesvol geopend.")

    # open van history database (1 min interval)       
    try:
        e_db_history_min.init(const.FILE_DB_E_HISTORIE,const.DB_HISTORIE_MIN_TAB)    
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(4)."+const.FILE_DB_E_HISTORIE+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database "+const.DB_E_HISTORIE+" (minuut) succesvol geopend.")

    # open van financieel database (dag interval)
    try:
        e_db_financieel_dag.init(const.FILE_DB_FINANCIEEL ,const.DB_FINANCIEEL_DAG_TAB)    
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(9)."+const.FILE_DB_FINANCIEEL+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database "+const.DB_FINANCIEEL+" succesvol geopend.")

    # open van weer database 
    try:
        weer_db.init(const.FILE_DB_WEATHER ,const.DB_WEATHER_TAB)  
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(10)."+const.FILE_DB_WEATHER+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database "+const.DB_WEER+" succesvol geopend.")

    # open van weer history database 
    try:
        #weer_history_db_uur.init(const.FILE_DB_WEATHER_HISTORIE ,const.DB_HISTORIE_MIN_TAB)
        weer_history_db_uur.init(const.FILE_DB_WEATHER_HISTORIE ,const.DB_WEATHER_UUR_TAB) 
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": database niet te openen(10)."+const.FILE_DB_WEATHER_HISTORIE+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database "+const.DB_WEER_HISTORY+" succesvol geopend.")

    # open van temperatuur database
    try:
        temperature_db.init(const.FILE_DB_TEMPERATUUR_FILENAME ,const.DB_TEMPERATUUR_TAB )
        # fix the datbase structure from version 0.8.18 onwards, remove in the future
        temperature_db.change_table( flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)."+const.FILE_DB_TEMPERATUUR_FILENAME+") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel "+const.DB_TEMPERATUUR_TAB +" succesvol geopend.")

    # open van watermeter databases
    try:
        watermeter_db_uur.init( const.FILE_DB_WATERMETER, const.DB_WATERMETER_UUR_TAB, flog )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": Database niet te openen(1)." + const.FILE_DB_WATERMETER + ") melding:"+str(e.args[0]))
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel " + const.DB_WATERMETER_UUR_TAB + " succesvol geopend." )

    # open van watermeter V2 database 
    try:    
        watermeter_db.init( const.FILE_DB_WATERMETERV2, const.DB_WATERMETERV2_TAB, flog )
    except Exception as e:
        flog.critical( inspect.stack()[0][3] + ": Database niet te openen(20)." + const.FILE_DB_WATERMETERV2 + " melding:" + str(e.args[0]) )
        sys.exit(1)
    flog.info( inspect.stack()[0][3] + ": database tabel " + const.DB_WATERMETERV2_TAB + " succesvol geopend." )


    # open van fase database      
    try:
        fase_db.init( const.FILE_DB_PHASEINFORMATION ,const.DB_FASE_REALTIME_TAB )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+" database niet te openen(1)." + const.FILE_DB_PHASEINFORMATION + ") melding:"+str(e.args[0]) )
        sys.exit(1)
    flog.info(inspect.stack()[0][3]+": database tabel: " + const.DB_FASE_REALTIME_TAB + " succesvol geopend.")

    # open van power production database      
    try:    
        power_production_db.init( const.FILE_DB_POWERPRODUCTION , const.DB_POWERPRODUCTION_TAB, flog )
    except Exception as e:
        flog.critical( inspect.stack()[0][3] + ": Database niet te openen(1)." + const.FILE_DB_POWERPRODUCTION + " melding:" + str(e.args[0]) )
        sys.exit(1)
    flog.info( inspect.stack()[0][3] + ": database tabel " + const.DB_POWERPRODUCTION_TAB + " succesvol geopend." )


    try:
        zf = zipfile.ZipFile( importfile )
    except Exception as e:
        flog.critical(inspect.stack()[0][3]+": ZIP file " + importfile + " probleem =>" + str(e) )  
        sys.exit(1)

    try:
         for fname in zf.namelist():  #filter out the manifest file first
            if fname == const.FILE_EXPORT_MANIFEST[1:]:
                data = zf.read(const.FILE_EXPORT_MANIFEST[1:]).decode('utf-8')
                json_data = json.loads(data)
                statusdata['records_total']     = json_data['record_count']
                statusdata['export_timestamp']  = str(json_data['timestamp'])
                break
    except Exception as e:
        flog.warning(inspect.stack()[0][3]+": ZIP file verwerking ging mis tijdens manifest bestand verwerking "+str(e))

    # custom www folder
    try:
        for fname in zf.namelist():
            if fname[:len(const.FILE_PREFIX_CUSTOM_UI)-1] == const.FILE_PREFIX_CUSTOM_UI[1:]:
                zf.extract(fname,'/') # komt dan terecht in /p1mon/var/tmp
                 # via Watchdog wegens rechten op files.
                exportcode = fname[len(const.FILE_PREFIX_CUSTOM_UI)-1:-3]
                writeSemaphoreFile('custom_www_import' + exportcode,flog)
                #print fname

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": ZIP file verwerking ging mis tijdens custom www verwerking "+str(e))    

    records_ok_cnt  = 0
    records_nok_cnt = 0
   
    try:

        for fname in zf.namelist():
            
            _head,tail = os.path.split(fname)
            """
            print ( fname )
            print ( tail ) 
            print ( "configuratie="   +str( tail.startswith( 'configuratie' ) ) )
            print ( "financieel="      +str( tail.startswith( 'finacieel' ) ) )
            print ( "historie="       +str( tail.startswith( 'historie' ) ) )
            print ( "01_weer_historie="  +str( tail.startswith( '01_weer_historie' ) ) )
            print ( "weer="           +str( tail.startswith( 'weer' ) ) )
            print ( "manifest.json="  +str( tail.startswith( 'manifest.json' ) ) )
            print ( "02_temperatuur="  +str( tail.startswith( '02_temperatuur' ) ) )
            print ( "03_watermeter="  +str( tail.startswith( '03_watermeter' ) ) )
            """

            #if const.DB_WATERMETERV2  +"xxx" in fname:
            if tail.startswith( const.DB_WATERMETERV2  ):
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": " + const.DB_WATERMETERV2 + " tabel bevat " + str(len(content)) + " import records." )
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        # check if valid SQL
                        if fnmatch.fnmatch(sql,'replace into watermeter*'):
                            watermeter_db.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT WATERMETER = "+sql)       
                        updateStatusFile( statusfile, records_ok_cnt, records_nok_cnt, 'bezig' , args ) 

            #if const.DB_WATERMETER  +"xxx" in fname:
            elif tail.startswith( const.DB_WATERMETER  ):
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": " + const.DB_WATERMETER+ " tabel bevat " + str(len(content)) + " import records." )
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        # check if valid SQL
                        if fnmatch.fnmatch(sql,'replace into watermeter*'):
                            watermeter_db_uur.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT WATERMETER = "+sql)       
                        updateStatusFile( statusfile, records_ok_cnt, records_nok_cnt, 'bezig' , args ) 

            #if const.DB_TEMPERATURE +"xxx" in fname:
            elif tail.startswith( const.DB_TEMPERATURE  ):
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": " + const.DB_TEMPERATURE+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        # check if valid SQL
                        if fnmatch.fnmatch(sql,'replace into temperatuur*'):
                            temperature_db.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT TEMPERATUUR = "+sql)       
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig' ,args ) 
                #backupFile(const.FILE_DB_TEMPERATUUR_FILENAME)
                # fix the missing day and month records from versin 0.9.18 onwards. remove in the future.
                temperature_db.fix_missing_month_day(flog)
            
            #if const.DB_E_HISTORIE+"xxx" in fname:
            elif tail.startswith( const.DB_E_HISTORIE ):
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": "+const.DB_E_HISTORIE+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        # check if valid SQL
                        if fnmatch.fnmatch(sql,'replace into e_history*'):
                            e_db_history_min.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT HISTORIE= "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )

            #elif const.DB_FINANCIEEL in fname:
            # the or is fix from version 0.9.19 > to fix the typo in "finacieel" text
            elif tail.startswith( const.DB_FINANCIEEL ) or tail.startswith("finacieel"):
                #print const.DB_FINANCIEEL
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": "+const.DB_FINANCIEEL+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        # check if valid SQL
                        if fnmatch.fnmatch(sql,'replace into e_financieel*'):
                            e_db_financieel_dag.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT FINANCIEEL= "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args ) 
                

            #elif const.DB_CONFIG in fname:
            elif tail.startswith( const.DB_CONFIG ):
                #print const.DB_CONFIG
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": "+const.DB_CONFIG+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        if fnmatch.fnmatch(sql,'update config set PARAMETER=*'):         
                            config_db.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT CONFIGURATIE= "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )

            # elif const.DB_WEER_HISTORY in fname:
            elif tail.startswith( const.DB_WEER_HISTORY ):
                #print "WEER 2"
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": "+const.DB_WEER_HISTORY+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        if fnmatch.fnmatch(sql,'replace into weer_history*'):         
                            weer_history_db_uur.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                            records_nok_cnt = records_nok_cnt + 1
                            flog.warning(inspect.stack()[0][3]+": SQL STATEMENT WEER HISTORY= "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )
                

            #elif const.DB_WEER in fname:
            elif tail.startswith( const.DB_WEER ):
                #print "WEER"
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": "+const.DB_WEER+ " tabel bevat "+str(len(content))+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        if fnmatch.fnmatch(sql,'replace into weer*'):         
                            weer_db.insert_rec(sql)
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                           records_nok_cnt = records_nok_cnt + 1
                           flog.warning(inspect.stack()[0][3]+": SQL STATEMENT WEER = "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )
                
            
            #elif const.DB_PHASEINFORMATION in fname:
            elif tail.startswith( const.DB_PHASEINFORMATION ):
                #print ( "FASE INFO" )
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": " + const.DB_PHASEINFORMATION + " tabel bevat "+str( len(content) )+" import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        if fnmatch.fnmatch(sql,'replace into ' + const.DB_FASE_REALTIME_TAB + '*'):  #DB_FASE_REALTIME_TAB
                            fase_db.insert_rec(sql)
                            #print ( sql )
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                           records_nok_cnt = records_nok_cnt + 1
                           flog.warning(inspect.stack()[0][3]+": SQL STATEMENT FASE DATA = "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )

            elif tail.startswith( const.DB_POWERPRODUCTION ):
                #print ( "POWERPRODUCTION INFO" )
                data = zf.read(fname).decode('utf-8')
                content = data.split('\n')
                flog.info(inspect.stack()[0][3]+": " + const.DB_POWERPRODUCTION + " tabel bevat " + str( len(content) ) + " import records.")
                for sql in content:
                    if len( sql.strip() ) > 0: #clear empty string
                        if fnmatch.fnmatch(sql,'replace into ' + const.DB_POWERPRODUCTION_TAB + '*'):
                            power_production_db.excute( sql )
                            #print ( sql )
                            records_ok_cnt = records_ok_cnt + 1
                        else:
                           records_nok_cnt = records_nok_cnt + 1
                           flog.warning(inspect.stack()[0][3]+": SQL STATEMENT FASE DATA = "+sql)
                        updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'bezig', args )
                
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": ZIP file verwerking ging mis "+str(e))

    flog.info(inspect.stack()[0][3]+": alle input verwerkt.")
    zf.close 

    # waterbase V1 to V2 database conversion
    #os.system("/p1mon/scripts/P1WatermeterDbV1toV2.py > /dev/null 2>&1")
    os.system("/p1mon/scripts/P1WatermeterDbV1toV2.py")

    # lees systeem ID uit en zet deze in de config database. 
    # versleuteld om dat deze data in een back-up bestand terecht kan komen.
    try:  
        flog.info(inspect.stack()[0][3]+': System ID zetten in configuratie database: ' + str( systemid.getSystemId() ) )
        sysid_encrypted  = crypto3.p1Encrypt( systemid.getSystemId(),"sysid" ).encode('utf-8').decode('utf-8')
        config_db.strset( sysid_encrypted ,58, flog ) 
    except Exception as e:
        flog.warning(inspect.stack()[0][3]+": System ID zetten mislukt -> " + str(e.args[0]))

    #force update version nummer 
    flog.info(inspect.stack()[0][3]+": Update versie naar "+str(const.P1_VERSIE))
    config_db.insert_rec("replace into "+const.DB_CONFIG_TAB+\
    " values ('0','"+const.P1_VERSIE+"','Versie:')")

    if args.rmstatus == True: # no status file requested, do noting
        backgroundcommand = '(sleep 7200;rm ' + importfile + ' > /dev/null 2>&1)&' # failsave for import file.
    else:
        backgroundcommand = '(sleep 7200;rm '+importfile+' && rm '+statusfile+' > /dev/null 2>&1)&' # failsave for import file.
    flog.info(inspect.stack()[0][3]+": verwijderen van tijdelijke bestanden ->"+backgroundcommand )
    os.system(backgroundcommand)

    flog.info(inspect.stack()[0][3]+": wifi wordt aangepast")
    semaphore3.writeSemaphoreFile('wifi_aanpassen',flog) #make sure then wifi is updated.

    flog.info(inspect.stack()[0][3]+": cron wordt aangepast (backup)")
    semaphore3.writeSemaphoreFile('cron',flog) #make sure then crontab is updated.

    #make sure that all is copied to disk
    os.system("/p1mon/scripts/P1DbCopy.py --allcopy2disk --forcecopy")

    # reset watermeter to make sure the GPIO change is accepted.
    # writeSemaphoreFile( 'watermeter_import_data', flog ) not needed in new version

    timestop = time.time()
    flog.info( inspect.stack()[0][3] + ": Gereed verwerkings tijd is " + f"{timestop - timestart:0.2f} seconden." ) 
    updateStatusFile(statusfile, records_ok_cnt, records_nok_cnt, 'klaar', args ) 

    try:
        time.sleep(1) # allow file to be unlocked.
        os.remove(importfile) # remove uploaded file TODO REMOVE #
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": "+str(e))

    flog.info(inspect.stack()[0][3]+": Gereed.")

def fileChanged( src_file, dst_dir ):
    # geef secs verschil terug van bestand
    try :
        statinfo_src = os.stat(src_file)
        _head,tail = os.path.split(src_file)   
        statinfo_dst = os.stat(dst_dir+"/"+tail)
        return int(abs(statinfo_src.st_mtime - statinfo_dst.st_mtime))   
    except Exception as _e:
        return int(-1)


#-------------------------------
if __name__ == "__main__":
    try: 
        os.umask( 0o002 )
        flog = fileLogger( const.DIR_FILELOG + prgname + ".log", prgname)    
        #### aanpassen bij productie
        flog.setLevel( logging.INFO )
        flog.consoleOutputOn(True)
    except Exception as e:
        print ( "critical geen logging mogelijke, gestopt.:"+str(e.args[0]) )
        sys.exit(1)

    Main(sys.argv[1:])
