#!/usr/bin/env python3

import os
import platform
import getpass
import socket
import psutil
import distro
from datetime import timedelta

ASCII_ART = r"""
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     
  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   
 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@%#*****************************#%@@@@@@@@@@@@@@@
.                                      #@@@@@@@@@@@
                                         -@@@@@@@@@
                                           *@@@@@@@
    .=============================.         +@@@@@@
 :@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@.       #@@@@@
-@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:      .@@@@@
%@@@@@@@@@@@@@@@#*****#%@@@@@@@@@@@@@@@       @@@@@
%@@@@@@@@@@#              .#@@@@@@@@@@@.      @@@@@
%@@@@@@@@-                   -@@@@@@@@@.      @@@@@
%@@@@@@#                       #@@@@@@@.      @@@@@
%@@@@@*         .===+=.         +@@@@@@.      @@@@@
%@@@@%       .%@@@@@@@@@%.       %@@@@@.      @@@@@
%@@@@:      .@@@@@@@@@@@@@:      :@@@@@.      @@@@@
%@@@@       @@@@@@#-:......      .@@@@@.      @@@@@
%@@@@       @@@@@-               .@@@@@.      @@@@@
%@@@@       @@@@@.               .@@@@@.      @@@@@
%@@@@       @@@@@%.             .%@@@@#       @@@@@
%@@@@       @@@@@@@@@@@@@@@@@@@@@@@@@@.      =@@@@@
@@@@@       %@@@@@@@@@@@@@@@@@@@@@@@-        @@@@@@
@@@@@-       @@@@@@@@@@@@@@@@@@@@@=         %@@@@@@
 @@@@%        =@@@@@@@@@@@@@@@@@+         -@@@@@@@ 
   @@@%                                 .@@@@@@@   
     @@@.                              %@@@@@@     
"""

def format_bytes(size):
    # 2**10 = 1024
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

def get_uptime():
    uptime_seconds = int(psutil.boot_time())
    now_seconds = int(psutil.time.time())
    uptime = timedelta(seconds=(now_seconds - uptime_seconds))
    # Convert to days, hours, minutes
    days = uptime.days
    hours, rem = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"

def main():
    user = getpass.getuser()
    host = socket.gethostname()
    os_name = distro.name(pretty=True) or platform.system()
    os_version = distro.version(pretty=True) or platform.release()
    kernel = platform.release()
    uptime = get_uptime()
    mem = psutil.virtual_memory()
    mem_total = format_bytes(mem.total)
    mem_avail = format_bytes(mem.available)

    print(ASCII_ART)
    print("intsys — system info\n")
    print(f"User:    {user}")
    print(f"Host:    {host}")
    print(f"OS:      {os_name} {os_version}")
    print(f"Kernel:  {kernel}")
    print(f"Uptime:  {uptime}")
    print(f"RAM:     {mem_avail} / {mem_total}")

if __name__ == '__main__':
    main()