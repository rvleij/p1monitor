# p1monitor

This is a Docker container running P1-Monitor from https://www.ztatz.nl/p1-monitor/. P1 Monitor is intended to monitor smart meters (used in NL, maybe other countries) using a P1 cable (basically serial cable). The software monitors the telegrams sent by the meter via serial interface, interprets them and stores the data in a SQLite DB running in memory (to prevent writing to SDHC which has limited write cycles). From there, it's displayed in a web interface, sent via MQTT, UDP broadcasts etc etc. See the above website for more information.

Normally this (great!) software is distributed as a complete package for flashing on a Raspberry Pi SDHC card, including upgrades. I wanted to use my Pi4 for a bit more than just this one application and decided to see if this runs as a container along other stuff.

I found some work done by a guy called "JeroenJ" to make it work in a container and I decided to publish a ready made container for easy use. See for more information: https://www.ztatz.nl/p1-monitor-download-202006/#comment-6824

I built the container image based on this work and published it here so others can find it. I intent to keep this container updated as soon as new P1 Monitor releases are made, until the maintainer for the software releases Docker containers himself (seems to be more or less the plan).
