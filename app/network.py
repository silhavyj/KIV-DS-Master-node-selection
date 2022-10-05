import socket
import netifaces as ni
from ipaddress import IPv4Interface

class NetworkInfo:

    def __init__(self, interface_name):
        interface_info = ni.ifaddresses(interface_name)[ni.AF_INET][0]

        ip_addr = interface_info['addr']
        netmask = interface_info['netmask']

        self.hostname = socket.gethostname()
        self.interface = IPv4Interface(ip_addr + '/' + netmask)
        