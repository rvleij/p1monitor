#!/bin/bash

echo "Starting cron for timed backups"
cron

echo "Fake /dev/sda1"
touch /dev/sda1

rm /var/log/p1monitor/shutdown

echo "Killing old processes"
pkill nginx
pkill php-fpm
pkill smbd

echo "Starting nginx"
mkdir -p /var/log/nginx
/usr/sbin/nginx -t -q -g 'daemon on; master_process on;'
/usr/sbin/nginx -g 'daemon on; master_process on;'
echo "Starting php-fpm"
mkdir /run/php
/usr/sbin/php-fpm7.3 --fpm-config /etc/php/7.3/fpm/php-fpm.conf

echo "Starting p1mon"
#mkdir /p1mon/mnt/ramdisk
#rm -rf /p1mon/mnt/ramdisk/*
#mount -t tmpfs tmpfs /p1mon/mnt/ramdisk
chmod 777 /p1mon/mnt/ramdisk
rm -rf /var/log/p1monitor/*
cd /p1mon/scripts
sudo -u p1mon bash -c './p1mon.sh start'

# On SIGTERM stop services as well 
trap 'echo "Extern SIGTERM";touch /var/log/p1monitor/shutdown' SIGTERM

# Waiting until p1mon shutdown is requested
while [ ! -e /var/log/p1monitor/shutdown ]
do
   sleep 2
done

echo "Stopping p1mon"
/p1mon/scripts/p1mon.sh stop
echo "Stopping nginx, php-fpm, smbd"
pkill nginx
pkill php-fpm
pkill smbd
echo "Exit start_all.sh"
exit 0
