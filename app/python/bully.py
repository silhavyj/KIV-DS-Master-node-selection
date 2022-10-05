import sys
import logging
import requests
from threading import Lock

from network import NetworkInfo
from utils import generate_node_id

class Bully:

    def __init__(self, interface_name):
        self.network_info = NetworkInfo(interface_name)
        self.name = self.network_info.hostname
        self.node_id = generate_node_id()
        self.election = False
        self.master = False
        self.master_ip_addr = None
        self.color = 'GRAY'
        self.mtx = Lock()

        self.nodes = {}

    
    def add_node(self, ip_addr, data):
        self.mtx.acquire()
        self.nodes[ip_addr] = data
        self.mtx.release()

    
    def set_master(self, value):
        self.mtx.acquire()
        self.master = value
        self.mtx.release()


    def set_master_ip_addr(self, ip_addr):
        self.mtx.acquire()
        self.master_ip_addr = ip_addr
        self.mtx.release()


    def set_color(self, color):
        self.mtx.acquire()
        self.color = color
        self.mtx.release()

    
    def discover_other_nodes(self, max_nodes):
        logging.info('Scanning the network...')
        
        count = 0
        master_ip_addr = None

        for ip_addr in self.network_info.interface.network:
            if ip_addr == self.network_info.interface.ip:
                logging.info(f'Skipping {ip_addr} (local machine)')
                continue

            api = f'http://{ip_addr}:5000/node-details'
            try:
                response = requests.get(api, verify=False, timeout=0.5)

                if response.status_code == 200:
                    logging.info(f"'{api}' is UP")
                    data = response.json()
                    if data['master'] == 'True':
                        if master_ip_addr is None:
                            master_ip_addr = data['ip_addr']
                            self.set_master_ip_addr(master_ip_addr)
                            logging.info(f'Master found - {master_ip_addr}')
                        else:
                            logging.critical(f"Two or more masters found on this network - {master_ip_addr} and {data['ip_addr']}. Exiting...")
                            sys.exit(1)
                    self.add_node(ip_addr, data)                    
                else:
                    logging.error(f'{api} seems to be up but status code 200 was not received')
            except:
                logging.info(f"'{api}' is DOWN")
            
            count += 1
            if count == max_nodes:
                break

        if len(self.nodes) == 0:
            self.set_master(True)
            logging.info('No other nodes have been found on this network -> becoming the master')
        
        logging.info('Finished scanning the network')