FROM debian:buster-slim

# Add p1mon and www-data with correct UID/GID
RUN addgroup --gid 1004 p1mon;addgroup -gid 997 gpio;useradd --gid 1004 --uid 1001 --create-home --password '$6$YrKO7PGalxElg00B$DhGh02AJO4gst7rA5YENOd5Y8zp/ksqvWnTzv2gZtq0C2GeuGPaI7Y7CW8NXS0N63LI3YlJPEl4/FZToYKnpS1' --groups dialout,sudo,www-data,gpio p1mon;adduser www-data p1mon

# Set timezone
RUN ln -fs /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime;dpkg-reconfigure -f noninteractive tzdata

# Install packages
RUN apt update;apt upgrade -y;apt install -y procps python3-venv python3-pip nginx-full php-fpm sqlite3 php-sqlite3 python3-cairo python3-apt nano cron git logrotate libsodium-dev libffi-dev iputils-ping socat iw

# Install sudo with RUNLEVEL env var to prevent complaints...
RUN rm /etc/sudoers;RUNLEVEL=1 apt install -y sudo

# Setup sudo without password for p1mon and www-data
RUN echo >>/etc/sudoers "p1mon ALL=(ALL) NOPASSWD: ALL";echo >>/etc/sudoers "www-data ALL=(p1mon) NOPASSWD: /p1mon/scripts/*"

# Install Python packages required
RUN pip3 install wheel setuptools asn1crypto bcrypt certifi cffi chardet colorzero cryptography dropbox entrypoints falcon future gpiozero idna iso8601 keyring keyrings.alt paho-mqtt pip psutil pycparser pycrypto PyGObject pyserial python-crontab python-dateutil pytz pyxdg PyYAML requests RPi.GPIO SecretStorage setuptools six spidev urllib3;SODIUM_INSTALL=system pip3 install PyNaCl

# Install PyCRC (not available as pip module)
RUN cd /tmp;git clone https://github.com/alexbutirskiy/PyCRC.git;cd PyCRC;python3 ./setup.py build;python3 ./setup.py install;cd ..;rm -rf PyCRC

# Copy settings, scripts and other p1mon specifics, nginx / fpm-php and remove cron scripts
COPY . .
RUN rm /etc/cron.daily/apt-compat /etc/cron.daily/dpkg /etc/cron.daily/exim4-base /etc/cron.daily/passwd /etc/logrotate.d/alternatives /etc/logrotate.d/apt /etc/logrotate.d/dpkg /etc/logrotate.d/exim4-base /etc/logrotate.d/exim4-paniclog 

# Replace commands and scripts:
RUN mv /p1mon/scripts/p1monExec /p1mon/scripts/p1monExec-orig;cp -a /opt/p1mon-mods/* /;chown -R p1mon:p1mon /p1mon;chown -R www-data:www-data /var/lib/nginx;chmod +s /bin/ping

# Install Docker scripts and socat loop
RUN cp -a /opt/docker-mods/socat_loop.py /usr/local/bin;chmod +x /usr/local/bin/socat_loop.py

# Install missing python packages
USER p1mon
RUN pip3 install gunicorn

USER root

HEALTHCHECK CMD curl -f http://127.0.0.1/nginx_status/ || exit 1

CMD [ "/start_all.sh" ]

