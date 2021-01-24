#!/usr/bin/python3
import argparse
import const
import inspect
import grp
import os
import pwd
import stat
import sys
import shutil
import logger


from logger import logging,fileLogger
from shutil import copy2
from pwd    import getpwnam
from os     import umask, geteuid
from pwd    import getpwuid

prgname = 'P1DbCopy'

filelist = [
    const.FILE_DB_E_FILENAME , 
    const.FILE_DB_STATUS,
    const.FILE_DB_CONFIG,
    const.FILE_DB_E_HISTORIE,
    const.FILE_DB_FINANCIEEL,
    const.FILE_DB_WEATHER,
    const.FILE_DB_WEATHER_HISTORIE,
    const.FILE_DB_TEMPERATUUR_FILENAME,
    const.FILE_DB_WATERMETER,
    const.FILE_DB_PHASEINFORMATION,
    const.FILE_DB_POWERPRODUCTION
]
  
def Main(argv):
    flog.info( "Start van programma " + prgname + "." )
    flog.info(inspect.stack()[0][3]+": wordt uitgevoerd als user -> " + pwd.getpwuid( os.getuid() ).pw_name )

    parser = argparse.ArgumentParser(description='help informatie')
    parser.add_argument( '-sf',      '--sourcefile',           required=False )
    parser.add_argument( '-df',      '--destinationfolder',    required=False )
    parser.add_argument( '-fc',      '--forcecopy',            required=False, action="store_true" ) #copy always even if file exists
    parser.add_argument( '-s2disk',  '--serialcopy2disk',      required=False, action="store_true" )
    parser.add_argument( '-all2ram', '--allcopy2ram',          required=False, action="store_true" )
    parser.add_argument( '-all2disk','--allcopy2disk',         required=False, action="store_true" )
    parser.add_argument( '-t2disk',  '--temperature2disk',     required=False, action="store_true" )
    parser.add_argument( '-w2disk',  '--watermeter2disk',      required=False, action="store_true" )
    parser.add_argument( '-pp2disk', '--powerproduction2disk', required=False, action="store_true" )
    args = parser.parse_args()

    #print ( args )
    # single file copy 
    if args.sourcefile != None and args.destinationfolder != None:
        flog.debug(inspect.stack()[0][3]+": single file copy.")
        copyFile( args.sourcefile, args.destinationfolder , args.forcecopy)
        return

    #powerproduction to ram to disk copy
    if args.powerproduction2disk == True:
        flog.debug(inspect.stack()[0][3]+": kWh eigen levering bestand.")
        copyFile( const.FILE_DB_POWERPRODUCTION , const.DIR_FILEDISK, args.forcecopy )
        return

    #watermeter to ram to disk copy
    if args.temperature2disk == True:
        flog.debug(inspect.stack()[0][3]+": watermeter bestand.")
        copyFile( const.FILE_DB_WATERMETER , const.DIR_FILEDISK, args.forcecopy )
        return

     #temperature to ram to disk copy
    if args.temperature2disk == True:
        flog.debug(inspect.stack()[0][3]+": temperatuur bestand.")
        copyFile(const.FILE_DB_TEMPERATUUR_FILENAME , const.DIR_FILEDISK, args.forcecopy)
        return

    #serial to ram to disk copy
    if args.serialcopy2disk == True:
        flog.debug(inspect.stack()[0][3]+": serialcopy2disk.")
        #print ( 'serialcopy2disk' )
        #print ( const.FILE_DB_E_FILENAME )
        #print ( const.DIR_FILEDISK )
        copyFile(const.FILE_DB_E_FILENAME , const.DIR_FILEDISK, args.forcecopy)
        return

    #all to ram to disk copy
    if args.allcopy2ram == True:
        flog.debug(inspect.stack()[0][3]+": allcopy2ram")
        listCopy( const.DIR_FILEDISK, const.DIR_RAMDISK, filelist ,args.forcecopy)
        return

    #all to ram to disk copy
    if args.allcopy2disk == True:
        flog.debug(inspect.stack()[0][3]+": allcopy2disk")
        listCopy( const.DIR_RAMDISK, const.DIR_FILEDISK, filelist ,args.forcecopy)
        return

# functions
def listCopy(sourcefolder , destinationfolder, filelist, forcecopy):
    for filename in filelist:
        _path,tail = os.path.split( filename )
        copyFile( sourcefolder+tail, destinationfolder, forcecopy )

def copyFile(sourcefile, destinationfolder, forcecopy):
    
    _path, file = os.path.split( sourcefile )
    
    """
    print ( file )
    print ( _path )
    print ( sourcefile )
    print ( destinationfolder )
    print ( forcecopy )
    print ( fileExist(  destinationfolder + file) )
    """

    if forcecopy == False: # only copy when forced
        if fileExist( destinationfolder + file ):
            flog.debug(inspect.stack()[0][3]+": bestand "  + destinationfolder + file + " bestaat en niet gekopierd van " +  sourcefile ) 
            return
    try:
        if fileExist ( destinationfolder + file):
            setFile2user( destinationfolder + file )
        shutil.copy2( sourcefile, destinationfolder ) 
        setFile2user( destinationfolder + file )
        flog.debug(inspect.stack()[0][3]+": " + sourcefile + " naar " + destinationfolder + file + " gekopieerd.")
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": kopie " + sourcefile + " naar " + destinationfolder + " fout: " + str(e) )

def setFile2user( filename ):
    try:
        cmd = "sudo /bin/chown -f p1mon:p1mon " + filename
        if os.system( cmd ) != 0:
            raise ValueError('system chown command failed!')
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": setFile2user fout: " + str(e) + "voor file " + filename )
        return False
    return True

"""
def setFile2user( filename, username ):
    try :
        os.chmod(filename, stat.S_IREAD|stat.S_IWRITE|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH)
        fd = os.open(filename, os.O_RDONLY)
        os.fchown( fd, name2uid(username), name2gid(username) )
        os.close( fd )
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": setFile2user fout: " + str(e) + "voor file " + filename )
        return False
    return True
"""

def fileExist(filename):
    if os.path.isfile(filename):
        return True
    else:
        return False

def name2uid(name):
    return getpwnam(name).pw_uid
    
def name2gid(group):
    return grp.getgrnam(group).gr_gid

#-------------------------------
if __name__ == "__main__":
    try:
        os.umask( 0o002 )
        logfile = const.DIR_FILELOG+prgname+".log" 
        #setFile2user(logfile,'p1mon')
        flog = fileLogger(logfile,prgname)    
        #### aanpassen bij productie
        flog.setLevel( logging.INFO )
        flog.consoleOutputOn(True) 
    except Exception as e:
        print ( "critical geen logging mogelijke, gestopt.:" + str(e.args[0]) )
        sys.exit(1)

    Main( sys.argv[1:] )