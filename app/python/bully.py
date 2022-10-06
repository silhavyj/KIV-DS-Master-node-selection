import sys
import time
import logging
import requests
import ipaddress 
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
        self.color_counter = 1
        self.green = 0
        self.red = 0
        self.nodes = {}
        self.node_colors = {}


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
            self.green += 1
        else:
            color = 'RED'
            self.red += 1

        self.mtx.acquire()
        self.color_counter = (self.color_counter + 1) % 3
        self.mtx.release()
        return color

    
    def set_node_color(self, ip_addr, color):
        self.mtx.acquire()
        self.node_colors[ip_addr] = color
        self.mtx.release()

    
    def reset_color_counter(self):
        self.mtx.acquire()
        self.color_counter = 1 # the master is always green
        self.mtx.release()


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
        if self.nodes.get(ip_addr) is not None:
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

    
    def worker_health_check(self, ip_addr):
        # TODO make this one thread!!
        api = f'http://{ip_addr}:5000/health-check'
        while True:
            try:
                response = requests.get(api)
                if response.status_code != 200:
                    break
            except:
                break
            time.sleep(2)
        
        self.mtx.acquire()
        lost_color = self.node_colors[ip_addr]
        self.node_colors.pop(ip_addr)
        if lost_color == 'RED':
            self.red -= 1
        else:
            self.green -= 1
        self.mtx.release()

        # TODO do some math to figure out if what nodes need to be changed
        # diff = self.green - self.red
        print(f'R={self.red}; G={self.green}')
        

    def discover_other_nodes(self, max_nodes, skip_itself=True):
        logging.info('Scanning the network...')
        
        count = 0
        master_ip_addr = None

        for ip_addr in self.network_info.interface.network:
            
            if skip_itself == True and ip_addr == self.network_info.interface.ip:
                logging.info(f'Skipping {ip_addr} (local machine)')
                continue

            api = f'http://{ip_addr}:5000/node-details'
            try:
                response = requests.get(api, verify=False, timeout=0.5, json=self.get_info())

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
        elif self.master_ip_addr != None:
            logging.info(f"Registering with the master ('{self.master_ip_addr}')")
            api = f'http://{self.master_ip_addr}:5000/worker_register'
            try:
                response = requests.post(api, json=self.get_info(), verify=False)
                if response.status_code != 200:
                    logging.error('Failed to register with the master. Exiting...')
                    run_bully_algorithm(self)
            except:
                logging.error('Failed to register with the master. Exiting...')
                run_bully_algorithm(self)
            self.set_color(response.json()['color'])

            Thread(target=ping_master, args=(self, )).start()
        else:
            run_bully_algorithm(self)

    
    #def wait_until_master_announcement(self, secs):
    #    for i in range(0, secs):
    #        if self.election == False:
    #            # TODO register with the new master (new color)
    #            return
    #        time.sleep(1)
    #    run_bully_algorithm(self)


def run_bully_algorithm(bully):
    if bully.master is True:
        return

    # Set the flag (ongoing algorithm)
    bully.set_election(True)

    # remove the master form the list of active nodes
    bully.remove_node(bully.master_ip_addr)

    exists_higher_node_id = False
    nodes_to_del = []

    # Check if the election is possible
    # filter out higher node_ids
    for ip_addr in bully.nodes:
        if bully.network_info.interface.ip < ipaddress.ip_address(ip_addr):
            try:
                logging.info(f'Sending election message from {bully.network_info.interface.ip} to {ip_addr}')
                response = requests.get(f'http://{ip_addr}:5000/election')
                if response.status_code == 200:
                    exists_higher_node_id = True
            except:
                nodes_to_del.append(ip_addr)

    for ip_addr in nodes_to_del:
        bully.remove_node(ip_addr)

    # This is the new master
    if exists_higher_node_id is False:
        # self.delete_all_nodes() # they're supposed to register again (does it matter tho?)
        announce_new_master(bully)
    else:
        # Wait till timeout or till a new master is announced
        # self.wait_until_master_announcement(5)
        pass


def ping_master(bully):
    logging.info(f"Starting periodically pinging the master ({bully.master_ip_addr})")
    while True:
        api = f'http://{bully.master_ip_addr}:5000/health-check'
        #logging.info(f'pinging {api}')
        try:
            response = requests.get(api)
            if response.status_code != 200:
                break
        except Exception as e:
            #print(e)
            break
        time.sleep(2) # sleep for 2 secs

    # Might've been pronounced a master already
    if bully.master is False:
        logging.error(f'Master {bully.master_ip_addr} seems to be down')
        run_bully_algorithm(bully)


def announce_new_master(bully):
    if bully.master is True:
        return
        
    logging.info('I AM THE MASTER')
    bully.reset_color_counter()
    bully.set_election(False)
    bully.set_master(True)

    nodes_to_del = []
    for ip_addr in bully.nodes:
        logging.info(ip_addr)
        try:
            logging.info(f'Announcing myself as the new master to {ip_addr}')
            response = requests.post(f'http://{ip_addr}:5000/master-announcement', json={'ip_addr' : str(bully.network_info.interface.ip)})
            #print(f'status_code = {response.status_code}')
        except Exception as e:
            #print(e)
            nodes_to_del.append(ip_addr)

    for ip_addr in nodes_to_del:
        bully.remove_node(ip_addr)