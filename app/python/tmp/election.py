import sys
import requests

from logger import log
from node import Node

RED_COLOR = 'red'
GREEN_COLOR = 'green'

def discover_nodes(node, port, max_nodes=6):
    log.debug('Scanning the network')

    master_found = False

    for ip_addr in node._interface.network:
        if ip_addr == node._interface.ip:
            continue

        endpoint = f'http://{ip_addr}:{port}/node-details'

        try:
            response = requests.get(api)
            if response.status_code == 200:
                log.info(f'{ip_addr} is up')
                data = response.json()
                if data['is_master'] == 'True':
                    if master_found is False:
                        master_ip_addr = ip_addr
                        node.set_master_ip_addr(ip_addr)
                        log.info(f'Found the master node: {ip_addr}')
                    else:
                        log.critical(f'Two or more master nodes found on the network. Exiting...')
                        sys.exit(1)
                node.add_node(ip_addr)
            else:
                log.error('{ip_addr} seems to be up but status code 200 was not received')
        except:
            log.debug('{ip_addr} is down')
    
    log.debug('Finished scanning the network')

    if len(node._nodes) == 0:
        log.info('No other nodes have been found on the network')
        node.set_is_master()
        node.set_color(GREEN_COLOR)
    elif node._master_ip_addr is not None:
        log.info(f'Registering with master node ({node._master_ip_addr})')
        try:
            response = requests.post(f'http://{node._master_ip_addr}:{port}/register')
            if response.status_code != 200:
                log.error('Failed to register with the master')
                init_new_master(node)
            else:
                node.set_color(response.json()['color'])
        except:
            log.error('Failed to register with the master')
            init_new_master(node)
    else:
        init_new_master(node)
        

def init_new_master(node):
    pass