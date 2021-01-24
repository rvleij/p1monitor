#!/bin/bash

## Fill in name of program here.
PROG="p1mon"
PRG_PATH="/p1mon/scripts/"
PID_PATH="/p1mon/mnt/ramdisk/"
LOG_PATH="/var/log/p1monitor/"
LOCK_PATH="/var/lock/"
WWW_DOWLOAD_PATH="/p1mon/www/download"
EXPORT_PATH="/p1mon/export/"
RAMDISK="/p1mon/mnt/ramdisk/"
DATADISK="/p1mon/data/"
DBX_ROOT="/p1mon/mnt/ramdisk/dbx/"
DBX_DATA="/data" 
DBX_BACKUP="/backup"
STATUS_FILE="p1mon*status"
USB_LOCK="LCK*ttyUSB0"
PRG1="P1SerReader.py"
PRG2="P1Db.py"
PRG3="P1Watchdog.py"
PRG4="*.log*"
PRG5="P1Weather.py"
PRG6="P1UdpDaemon.py"
PRG7="P1DropBoxDeamon.py"
PRG8="P1UdpBroadcaster.py"
PRG9="gunicorn"
PRG9_PATH="/home/p1mon/.local/bin/"
PRG9_ALIAS="P1Api"
PRG9_PARAMETERS=" --timeout 900 --bind localhost:10721 --worker-tmp-dir /p1mon/mnt/ramdisk --workers 2 P1Api:app --log-level warning"
PRG10="P1UpgradeAssist.py --restore"
PRG11="logspacecleaner.sh"
PRG12="P1Watermeter.py"
PRG13="P1MQTT.py"
PRG14="P1GPIO.py"
PRG15="P1PowerProductionS0.py"
P1FILE="p1msg.txt"


## reset rechten wegens dev werk en kopie acties.
#sudo /bin/chmod 775  $PRG_PATH$PRG8 $PRG_PATH$PRG1 $PRG_PATH$PRG2 $PRG_PATH$PRG3 $PRG_PATH$PRG5 $PRG_PATH$PRG6 $LOG_PATH$PRG4 $PID_PATH$P1FILE  &>/dev/null
#sudo /bin/chown p1mon:p1mon $PRG_PATH$PRG8 $PRG_PATH$PRG1 $PRG_PATH$PRG2 $PRG_PATH$PRG3 $PRG_PATH$PRG5 $PRG_PATH$PRG6 $LOG_PATH$PRG4 $PID_PATH$P1FILE &>/dev/null
cd /p1mon/scripts
sudo chmod 754 P1*.py*;sudo chown p1mon:p1mon P1*.py
sudo chmod 754 *.sh;sudo chown p1mon:p1mon *.sh 

 # make p1monitor log folder (new from june 2019)
sudo mkdir -p p1monitor $LOG_PATH
sudo /bin/chown p1mon:p1mon $LOG_PATH $WWW_DOWLOAD_PATH $EXPORT_PATH $RAMDISK
sudo /bin/chmod 775 $LOG_PATH 
sudo /bin/chmod 770 $WWW_DOWLOAD_PATH $EXPORT_PATH

# clean log files on any action, also done by the watchdog
# script clean when gets full. Should never happen ;)
sudo $PRG_PATH$PRG11

start() {

    # disable power save van de wifi.
    echo "Wifi power save wordt uitgezet"
    sudo /sbin/iw dev wlan0 set power_save off
    /sbin/iw wlan0 get power_save

    #upgrade assist start
    echo "Upgrade assist wordt gestart."
    $PRG_PATH$PRG10
    # note the watchdog does the import from /p1mon/data 

    #check if upgrade assist gereed is.
    #if [ $( ps -ef| grep "$PRG10" | grep -v grep | wc -l ) -gt 0 ]
    #then
    #    echo " $PRG10 loopt nog, wacht 2 minuten"
    #    sleep 120 
    #else
    #    echo " $PRG10 is gereed, geen pauze gebruikt."
    #fi  
    
    # Serial interface start
    if [ -e "$PID_PATH$PRG1.pid" ]; then
        echo "$PRG1 al actief!"
        return
    else
        # set sticky bit for C program to run als p1mon 
        sudo /bin/chmod +s /p1mon/scripts/p1monExec
        # remove status file als dat bestaat
        sudo /bin/rm $RAMDISK$STATUS_FILE &>/dev/null 
        #sudo nice --adjustment=-15 su -c p1mon $PRG_PATH$PRG1 &>/dev/null &
        sudo nice --adjustment=-15 sudo -i -u p1mon $PRG_PATH$PRG1 &>/dev/null &
        echo "$PRG1.started"
        touch "$PID_PATH$PRG1.pid"
    sudo chmod a+rw "$PID_PATH$PRG1.pid" &>/dev/null
    echo "5 seconden wachttijd"
    # tijd zodat de serial db bij het starten gedefragmenteerd kan worden
	sleep 5
    fi
   
    # DB start
    if [ -e "$PID_PATH$PRG2.pid" ]; then
        echo "$PRG2 al actief!"
        return
    else
        $PRG_PATH$PRG2 &>/dev/null &
	echo "$PRG2.started"
        touch "$PID_PATH$PRG2.pid"
	sudo chmod a+rw "$PID_PATH$PRG2.pid" &>/dev/null
    echo "5 seconden wachttijd"
	sleep 5
    fi

    # DropBoxDaemon start
    # make folders if not available (thank you -p switch)
    # folder are also made by program.
    sudo /bin/mkdir -p $DBX_ROOT $DBX_ROOT$DBX_DATA $DBX_ROOT$DBX_BACKUP
    sudo find  $DBX_ROOT -type d -exec chmod 774 {} +
    sudo /bin/chmod 774 $DBX_ROOT
    sudo /bin/chown p1mon:p1mon $DBX_ROOT $DBX_ROOT$DBX_DATA $DBX_ROOT$DBX_BACKUP
    if [ -e "$PID_PATH$PRG7.pid" ]; then
        echo "$PRG7 al actief!"
        return
    else
        $PRG_PATH$PRG7 &>/dev/null &
        echo "$PRG7.started"
        touch "$PID_PATH$PRG7.pid"
        sudo chmod a+rw "$PID_PATH$PRG7.pid" 2>&1 >/dev/null
    fi

    # Watchdog start
    if [ -e "$PID_PATH$PRG3.pid" ]; then
        echo "$PRG3 al actief!"
        return
    else
        $PRG_PATH$PRG3 2>&1 >/dev/null &
        echo "$PRG3.started"
        touch "$PID_PATH$PRG3.pid"
        sudo chmod a+rw "$PID_PATH$PRG3.pid" 2>&1 >/dev/null
    fi

    # run weather once to make sure we have the weather database, fixes import issues.
    $PRG_PATH$PRG5 2>&1 >/dev/null & 

    # UDP deamon start
    if [ -e "$PID_PATH$PRG6.pid" ]; then
        echo "$PRG6 al actief!"
        return
    else
        $PRG_PATH$PRG6 &>/dev/null &
        echo "$PRG6.started"
        touch "$PID_PATH$PRG6.pid"
        sudo chmod a+rw "$PID_PATH$PRG6.pid" 2>&1 >/dev/null
    fi

    # UDP broadcast start
    if [ -e "$PID_PATH$PRG8.pid" ]; then
        echo "$PRG8 al actief!"
        return
    else
        $PRG_PATH$PRG8 &>/dev/null &
        echo "$PRG8.started"
        touch "$PID_PATH$PRG8.pid"
        sudo chmod a+rw "$PID_PATH$PRG8.pid" 2>&1 >/dev/null
    fi

    # API start
    if [ -e "$PID_PATH$PRG9_ALIAS.pid" ]; then
        echo "$PRG9_ALIAS al actief!"
        return
    else
        $PRG9_PATH$PRG9$PRG9_PARAMETERS 2>&1 >/dev/null &
        echo "$PRG9_ALIAS.started"
        touch "$PID_PATH$PRG9_ALIAS.pid"
        sudo chmod a+rw "$PID_PATH$PRG9_ALIAS.pid" 2>&1 >/dev/null
    fi

    # Watermeter start
    if [ -e "$PID_PATH$PRG12.pid" ]; then
        echo "$PRG12 al actief!"
        return
    else
        $PRG_PATH$PRG12 &>/dev/null &
	echo "$PRG12.started"
        touch "$PID_PATH$PRG12.pid"
	sudo chmod a+rw "$PID_PATH$PRG12.pid" &>/dev/null
    fi

    # MQTT start
    if [ -e "$PID_PATH$PRG13.pid" ]; then
        echo "$PRG13 al actief!"
        return
    else
        $PRG_PATH$PRG13 &>/dev/null &
	echo "$PRG13.started"
        touch "$PID_PATH$PRG13.pid"
	sudo chmod a+rw "$PID_PATH$PRG13.pid" &>/dev/null
    fi

    # GPIO start
    if [ -e "$PID_PATH$PRG14.pid" ]; then
        echo "$PRG14 al actief!"
        return
    else
        $PRG_PATH$PRG14 &>/dev/null &
    echo "$PRG14.started"
        touch "$PID_PATH$PRG14.pid"
    sudo chmod a+rw "$PID_PATH$PRG14.pid" &>/dev/null
    fi

    # oude code, wordt gestart via de Watchdog.
    # Powerproduction start
    #if [ -e "$PID_PATH$PRG15.pid" ]; then
    #    echo "$PRG15 al actief!"
    #    return
    #else
    #    $PRG_PATH$PRG15 &>/dev/null &
    #echo "$PRG15.started"
    #    touch "$PID_PATH$PRG15.pid"
    #sudo chmod a+rw "$PID_PATH$PRG15.pid" &>/dev/null
    #fi

}


function is_script_running() {
    if [ $( ps -ef| grep $1 | grep -v grep | wc -l ) -gt 0 ]
    then
      echo " $1 already running"
      echo "1"
    else
      echo " $1 is not running"
      echo "0"
    fi
}

function process_kill() {
    PID=$( pidof -x $1 )
    #echo $PID
    if [ -z "$PID" ]
    then
        echo "Geen pid gevonden voor proces naam "$1
    else
        echo "Killing pid(s) "$PID" proces naam is "$1
        sudo kill -s SIGINT $PID 1>&2 >/dev/null
        if [ "$2" ]; then
            echo "timeout is "$2" seconden."
            sleep $2
        else
            sleep 3
            echo "timeout is 3 seconden."
        fi

        PID=$( pidof -x $1 )
        if [ -z "$PID" ]
        then
            echo "Er lopen geen processen meer met de naam "$1
            echo "--------------------------------------------"
        else 
            echo "Failsave kill gestart, dit is niet normaal voor proces "$1
            echo "------------------------------------------------------------"
            sudo kill -s SIGTERM $PID 1>&2 >/dev/null
        fi
    fi
}

stop() {

    echo "Processen worden gestopt, even geduld aub."

    # Powerproduction stop
    if [ -e "$PID_PATH$PRG15.pid" ]; then
        process_kill $PRG15 10
        sudo rm "$PID_PATH$PRG15.pid" &>/dev/null
    else
        echo "$PRG15 is niet actief!"
    fi

    # GPIO stop
    if [ -e "$PID_PATH$PRG14.pid" ]; then
        process_kill $PRG14
        sudo rm "$PID_PATH$PRG14.pid" &>/dev/null
    else
        echo "$PRG14 is niet actief!"
    fi

    # MQTT stop
    if [ -e "$PID_PATH$PRG13.pid" ]; then
        process_kill $PRG13
        sudo rm "$PID_PATH$PRG13.pid" &>/dev/null
    else
        echo "$PRG13 is niet actief!"
    fi

    # Watermeter stop
    if [ -e "$PID_PATH$PRG12.pid" ]; then
        process_kill $PRG12
        sudo rm "$PID_PATH$PRG12.pid" &>/dev/null
    else
        echo "$PRG12 is niet actief!"
    fi

     # API stop
     if [ -e "$PID_PATH$PRG8.pid" ]; then
        process_kill $PRG9
        #sudo killall --signal 2 $PRG9 1>&2 >/dev/null
        #failsave kill
        #sleep 2
        #sudo killall $PRG9 &>/dev/null
        sudo rm "$PID_PATH$PRG9_ALIAS.pid" &>/dev/null
    else
        echo "$PRG9_ALIAS is niet actief!" 
    fi

     #UDP broadcast stop
    if [ -e "$PID_PATH$PRG8.pid" ]; then
        process_kill $PRG8
        #sudo killall --signal 2 $PRG8 1>&2 >/dev/null
        #failsave kill
        #sleep 2
        #sudo killall $PRG8 &>/dev/null
        sudo rm "$PID_PATH$PRG8.pid" &>/dev/null
    else
        echo "$PRG8 is niet actief!" 
    fi

    #Dropbox stop
    if [ -e "$PID_PATH$PRG7.pid" ]; then
        process_kill $PRG7
        #sudo killall --signal 2 $PRG7 1>&2 >/dev/null
        #failsave kill
        #sleep 2
        #sudo killall $PRG7 &>/dev/null
        sudo rm "$PID_PATH$PRG7.pid" &>/dev/null
    else
        echo "$PRG7 is niet actief!" 
    fi

    #Udp Sender stop
    if [ -e "$PID_PATH$PRG6.pid" ]; then
        process_kill $PRG6 
        #sudo killall --signal 2 $PRG6 1>&2 >/dev/null
        #failsave kill
        #sleep 2
        #sudo killall $PRG6 &>/dev/null
        sudo rm "$PID_PATH$PRG6.pid" &>/dev/null
    else
        echo "$PRG6 is niet actief!" 
    fi

    # Watchdog stop
    if [ -e "$PID_PATH$PRG3.pid" ]; then
        process_kill $PRG3 
        #sudo killall --signal 2 $PRG3 1>&2 >/dev/null
        #failsave kill
        #sleep 2
        #sudo killall $PRG3 &>/dev/null
        sudo rm "$PID_PATH$PRG3.pid" &>/dev/null
    else
        echo "$PRG3 is niet actief!" 
    fi
    # Serial interface stop
    if [ -e "$PID_PATH$PRG1.pid" ]; then
        process_kill $PRG1
        #sudo killall --signal 2 $PRG1 &>/dev/null
	    #failsave kill
	    #sleep 2
 	    #sudo killall $PRG1 1>&2 >/dev/null
        sudo rm "$PID_PATH$PRG1.pid" &>/dev/null
    else
        echo "$PRG1 is niet actief!"
    fi

    # DB stop
    if [ -e "$PID_PATH$PRG2.pid" ]; then
        process_kill $PRG2
        #sudo killall --signal 2 $PRG2 &>/dev/null
	    #failsave kill
	    #sleep 2
        #sudo killall $PRG2 &>/dev/null
        sudo rm "$PID_PATH$PRG2.pid" &>/dev/null
    else
        echo "$PRG2 is niet actief!"
    fi

}

cleardb() {
  # database files worden hernoemd en niet gewist als noodmaatregel.
  # in ram zullen ze verdwijnen op disk blijven bestaan. 
  echo  "database files worden hernoemd met .bak extentie"
  # geef de bestaande db bestanden een bak extentie.
  echo "Backup maken van data folder "${DATADISK}
  cd $DATADISK &>/dev/null
  /usr/bin/rename --verbose --force "s/db$/db.bak/g" *
  echo "verwijderen van de ramdisk folder "${RAMDISK} 
  cd $RAMDISK &>/dev/null
  rm --force --verbose *.db
  cd $PRG_PATH &>/dev/null
}

case "$1" in
    start)
		#initScripts # no longer needed
        start
        exit 0
    ;;
    stop)
        stop
        exit 0
    ;;
    reload|restart|force-reload)
        stop
        sleep 5
        start
        exit 0
    ;;
    cleardatabase)
        stop
        echo "wissen van database gestart."
        cleardb
        start
        exit 0
    ;;
    **)
        echo "Usage: $0 {start|stop|restart|cleardatabase}" 
        exit 1
    ;;
esac
