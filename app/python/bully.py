import logging
import requests

from network import NetworkInfo
from utils import generate_node_id

class Bully:

    def __init__(self, interface_name):
        self.network_info = NetworkInfo(interface_name)
        self.name = self.network_info.hostname
        self.node_id = generate_node_id()
        self.election = False
        self.master = False

    
    def discover_other_nodes(self, max_nodes):
        logging.info('Scanning the network...')
        
        count = 0
        for ip_addr in self.network_info.interface.network:
            if ip_addr == self.network_info.interface.ip:
                logging.info(f'Skipping {ip_addr} (local machine)')
                continue

            api = f'http://{ip_addr}:5000/node-details'
            try:
                response = requests.get(api, verify=False, timeout=0.5)

                if response.status_code == 200:
                    logging.info(f"'{api}' is UP")
                    
                else:
                    logging.error(f'{api} seems to be up but status code 200 was not received')
            except:
                logging.info(f"'{api}' is DOWN")
            
            count += 1
            if count == max_nodes:
                break
        
        logging.info('Finished scanning the network')