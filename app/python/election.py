import sys
import time
import requests
import ipaddress
from threading import Thread

from logger import log
from node import Node

RED_COLOR = 'red'
GREEN_COLOR = 'green'

def discover_nodes(node, max_nodes=6):
    log.info('Scanning the network')

    count = 0
    master_found = False

    for ip_addr in node._interface.network:
        if ip_addr == node._interface.ip:
            continue

        endpoint = f'http://{ip_addr}:{node._port}/node-details'
        try:
            response = requests.get(endpoint, verify=False, timeout=0.5)
            if response.status_code == 200:
                log.info(f'{ip_addr} is up')
                data = response.json()
                if data['is_master'] is True:
                    if master_found is False:
                        master_found = True
                        node.set_master_ip_addr(ip_addr)
                        log.info(f'Found the master node: {ip_addr}')
                    else:
                        log.critical(f'Two or more master nodes found on the network. Exiting...')
                        sys.exit(1)
                node.add_node(ip_addr)
            else:
                log.error(f'{ip_addr} seems to be up but status code 200 was not received')
        except:
            log.debug(f'{ip_addr} is down')

        count += 1
        if count == max_nodes:
            break
    
    log.info('Finished scanning the network')

    if len(node._nodes) == 0:
        log.info('No other nodes have been found on the network')
        node.set_as_master()
    elif node._master_ip_addr is not None:
        Thread(target=ping_master, args=(node, )).start()
    else:
        log.info('No master has been found on the network')
        init_new_master(node)
        

def init_new_master(node):
    log.info('Starting election of a new master')
    if node._is_master is True:
        return
    
    node.set_election_flag(True)
    node.remove_node(node._master_ip_addr)

    exist_superior_node = False
    nodes = node.get_nodes_copy()

    for ip_addr in nodes:
        if node._interface.ip < ipaddress.ip_address(ip_addr):
            try:
                log.info(f'Sending an election message from {node._interface.ip} to {ip_addr}')
                response = requests.get(f'http://{ip_addr}:{node._port}/election')
                if response.status_code == 200:
                    exist_superior_node = True
            except:
                node.remove_node(ip_addr)

    if exist_superior_node is False:
        announce_new_master(node)
    else:
        # TODO wait for e.g. 3s and then run the init process again
        pass


def ping_master(node):
    log.info(f"Starting periodically pinging the master ({node._master_ip_addr})")
    while True:
        endpoint = f'http://{node._master_ip_addr}:{node._port}/health-check'
        try:
            response = requests.get(endpoint)
            if response.status_code != 200:
                break
        except:
            break
        time.sleep(2)
    
    if node._is_master is False:
        log.error(f'Master ({node._master_ip_addr}) seems to be down')
        init_new_master(node)


def announce_new_master(node):
    if node._is_master is True:
        return
        
    node.set_as_master()

    nodes = node.get_nodes_copy()
    for ip_addr in nodes:
        try:
            log.info(f'Announcing the new master to {ip_addr}')
            response = requests.post(f'http://{ip_addr}:{node._port}/master-announcement', json={'ip_addr' : str(node._interface.ip)})
            if response.status_code != 200:
                node.remove_node(ip_addr)    
        except:
            node.remove_node(ip_addr)
