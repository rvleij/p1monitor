#!/bin/bash
# script om export naar SDHC card naar SDA te maken.
echo "[*] file rechten herstellen"
/p1mon/scripts/setok.sh
#echo  "[*] sda vullen met 0 voor de eerste 256MB+, dit kan even duren"
#sudo dd if=/dev/zero of=/dev/sda bs=512 count=570000
echo "[*] clone maken naar SDA extern card"
rpi-clone -v sda
echo "[*] data en andere gegevens van de SDA card verwijderen"
/p1mon/scripts/clean-clone.sh sda