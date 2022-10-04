import socket
import time

hostname = socket.gethostname()   
ip_addr = socket.gethostbyname(hostname)   

while (True):
    print(f'hostname = {hostname}')
    print(f'ip_addr  = {ip_addr}')
    time.sleep(3)