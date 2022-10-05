import sys
import time
import logging
import requests
from threading import Thread, Lock

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
        self.master_health_check = None


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


    def delete_all_nodes(self):
        self.mtx.acquire()
        self.nodes = {}
        self.mtx.release()


    def set_election(self, value):
        self.mtx.acquire()
        self.election = value
        self.mtx.release()


    def remove_node(self, ip_addr):
        self.mtx.acquire()
        self.nodes.pop(ip_addr)
        self.mtx.release()

    
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

            self.master_health_check = Thread(target=self.ping_master)
            self.master_health_check.start()


    def ping_master(self):
        logging.info('Starting periodically pinging the master')
        api = f'http://{self.master_ip_addr}:5000/health-check'
        while True:
            try:
                response = requests.get(api)
                if response.status_code != 200:
                    break
            except:
                break
            time.sleep(2) # sleep for 2 secs

        logging.error(f'Master {self.master_ip_addr} seems to be down')
        self.run_bully_algorithm()


    def announce_new_master(self):
        logging.info('I AM THE MASTER')
        pass

    
    def wait_until_master_announcement(self, secs):
        for i in range(0, secs):
            if self.election == False:
                # TODO register with the new master (new color)
                return
            time.sleep(1)
        self.run_bully_algorithm()

    
    def run_bully_algorithm(self):
        # Set the flag (ongoing algorithm)
        self.set_election(True)

        # remove the master form the list of active nodes
        self.remove_node(self.master_ip_addr)

        exists_higher_node_id = False
        nodes_to_del = []
        ongoing_election = False

        # Check if the election is possible
        # filter out higher node_ids
        for ip_addr in self.nodes:
            if self.node_id < self.nodes[ip_addr]['node_id']:
                try:
                    response = requests(f'http://{ip_addr}:500/election')
                    if response.status == 200:
                        status = response.json()['status']
                        if status == 'False':
                            exists_higher_node_id = True
                        else:
                            ongoing_election = True
                except:
                    nodes_to_del.append(ip_addr)

        for ip_addr in nodes_to_del:
            self.remove_node(ip_addr)

        # This is the new master
        if exists_higher_node_id == False:
            delete_all_nodes() # they're supposed to register again (does it matter tho?)
            self.announce_new_master()
        else:
            # Wait till timeout or till a new master is announced
            self.wait_until_master_announcement(5)