#!/bin/bash
# script om export naar SDHC card naar SDA te maken.
echo "[*] file rechten herstellen"
/p1mon/scripts/setok.sh
echo "[*] clone maken naar SDA extern card"
rpi-clone -v sda
echo "[*] data en andere gegevens van de SDA card verwijderen"
/p1mon/scripts/clean-clone.sh sda

