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
        self.color_counter = 0

        self.nodes = {}

    def get_info(self):
        return {
            'name'     : self.network_info.hostname,
            'node_id'  : str(self.node_id),
            'master'   : str(self.master),
            'election' : str(self.election),
            'ip_addr'  : str(self.network_info.interface.ip),
            'color'    : self.color
        }

    def calculate_node_color(self):
        color = None
        if self.color_counter < 2:
            color = 'GREEN'
        else:
            color = 'RED'

        self.mtx.acquire()
        self.color_counter = (self.color_counter + 1) % 3
        self.mtx.release()
        return color

    
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
        logging.info(f"Color has been changed to '{self.color}'")

    
    def discover_other_nodes(self, max_nodes, skip_itself=False):
        logging.info('Scanning the network...')
        
        count = 0
        master_ip_addr = None

        for ip_addr in self.network_info.interface.network:
            
            if skip_itself == True and ip_addr == self.network_info.interface.ip:
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
                            master_ip_addr = ip_addr
                            self.set_master_ip_addr(master_ip_addr)
                            logging.info(f'Master found - {master_ip_addr}')
                        else:
                            logging.critical(f"Two or more masters found on the network - {master_ip_addr} and {ip_addr}. Exiting...")
                            sys.exit(1)
                    self.add_node(ip_addr, data)                    
                else:
                    logging.error(f'{api} seems to be up but status code 200 was not received')
            except:
                logging.info(f"'{api}' is DOWN")
            
            count += 1
            if count == max_nodes:
                break

        logging.info('Finished scanning the network')

        if len(self.nodes) == 0:
            self.set_master(True)
            self.set_color('GREEN')
            logging.info('No other nodes have been found on the network -> becoming the master')
        elif self.master == False:
            logging.info('Registering with the master')
            api = f'http://{ip_addr}:5000/worker_register'
            response = requests.post(api, json=self.get_info(), verify=False, timeout=0.5)
            if response.status_code != 200:
                logging.error('Failed to register with the master. Exiting...')
                sys.exit(2)
            self.set_color(response.json()['color'])

            # TODO start pinging the master