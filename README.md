## General
This is a Docker container running P1-Monitor from https://www.ztatz.nl/p1-monitor/.

P1 Monitor is intended to monitor smart meters (used in NL, maybe other countries) using a P1 cable (basically serial cable). The software monitors the telegrams sent by the meter via serial interface, interprets them and stores the data in a SQLite DB running in memory (to prevent writing to SDHC which has limited write cycles).
From there, it's displayed in a web interface, sent via MQTT, UDP broadcasts etc etc. See the above website for more information.

Normally this (great!) software is distributed as a complete package for flashing on a Raspberry Pi SDHC card, including upgrades. I wanted to use my Pi4 for a bit more than just this one application and decided to see if this runs as a container along other stuff.

I found some work done by someone called "JeroenJ" to make it work in a container and I decided to publish a ready made container for easy use. See for more information: https://www.ztatz.nl/p1-monitor-download-202006/#comment-6824

I built the container image based on this work and published it here so others can find it. I intent to keep this container updated as soon as new P1 Monitor releases are made, until the maintainer for the software releases Docker containers himself (seems to be more or less the plan). I have compiled for amd64 (if you want to run this on a x86) and arm (for the Pi).


## Running
I run the container using the following run command:

    docker run -d -p 80:80 -p 10721:10721 -p 40721:40721 --name="p1mon" \
    -h p1mon --cap-add=SYS_NICE \
    --tmpfs /tmp --tmpfs /run --tmpfs /p1mon/mnt/ramdisk \
    -v /<insert local path>/p1mon/data:/p1mon/data:rw -v /<insert local path>/p1mon/usbdisk:/p1mon/mnt/usb:rw \
    -v /etc/localtime:/etc/localtime:ro \
    --device=/dev/<your USB device> \
    --restart=unless-stopped \
    rvleij/p1monitor

## Updating
1. Create the memory dump to /usbstick (mounted seperately) by running the Upgrade Assistant from within P1 Monitor
2. Stop P1 Monitor by using the "system" section and using the "shutdown" button (as if you shutdown your Pi)
3. docker pull rvleij/p1monitor
4. docker stop p1-mon (or whatever you named it)
5. docker rm p1mon
6. run the start command above under "running" to start a new instance. It'll load the data from /usbstick and continue operations.

## Compiling container images and pushing to Docker Hub

docker buildx build -t rvleij/p1monitor --platform linux/amd64,linux/arm64,linux/arm/v7 --push .
docker buildx imagetools inspect rvleij/p1monitor:latest
