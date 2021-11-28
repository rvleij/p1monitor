import os

enable,host,port=os.environ.get('SOCAT_ENABLE'),os.environ.get('SOCAT_HOST'),os.environ.get('SOCAT_PORT')

import os

while enable:
  os.system("socat pty,link=/dev/ttyUSB4,raw,user=p1mon,group=dialout,mode=777 tcp:%s:%s,forever,interval=10" %(host,port))
