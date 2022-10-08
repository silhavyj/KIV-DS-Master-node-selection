import socket
import netifaces as ni
from threading import Thread, Lock
from ipaddress import IPv4Interface
from enum import Enum

from logger import log


RED   = 'RED'
GRAY  = 'GRAY'
GREEN = 'GREEN'


class Node:

    def __init__(self, interface_name, port, timeout=0.5):
        self._election = False
        self._is_master = False
        self._master_ip_addr = None
        self._lock = Lock()
        self._nodes = []
        self._color = GRAY
        self._port = port
        self._timeout = 0.5
        self._hostname = socket.gethostname()

        interface_info = ni.ifaddresses(interface_name)[ni.AF_INET][0]
        ip_addr = interface_info['addr']
        netmask = interface_info['netmask']
        self._interface = IPv4Interface(f'{ip_addr}/{netmask}')


    def get_details(self):
        return {
            'is_master' : self._is_master,
            'color'     : self._color,
            'hostname'  : self._hostname
        }


    def set_election_flag(self, value):
        self._lock.acquire()
        self._election = value
        self._lock.release()


    def add_node(self, ip_addr):
        self._lock.acquire()
        if ip_addr not in self._nodes:
            self._nodes.append(str(ip_addr))
            log.info(f'New node discovered {str(ip_addr)}')
        self._lock.release()

    
    def remove_node(self, ip_addr):
        self._lock.acquire()
        if ip_addr in self._nodes:
            self._nodes.remove(str(ip_addr))
            log.info(f'Removed node {str(ip_addr)}')
        self._lock.release()

    
    def set_color(self, value, thread_safe=True):
        if thread_safe is True:
            self._lock.acquire()
        if self._color != value:
            log.info(f'The color has been changed to {value}')
            self._color = value
        if thread_safe is True:
            self._lock.release()

    
    def set_as_master(self):
        self._lock.acquire()
        self._is_master = True
        self._election = False
        self.set_color(GREEN, False)
        self._lock.release()
        log.info(f'This node ({self._interface.ip} has now become the master)')

    
    def set_master_ip_addr(self, ip_addr):
        self._lock.acquire()
        self._master_ip_addr = ip_addr
        self._lock.release()


    def get_nodes_copy(self):
        self._lock.acquire()
        nodes_copy = self._nodes.copy()
        self._lock.release()
        return nodes_copy