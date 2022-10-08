import sys
import time
import requests
import ipaddress
from threading import Thread

from logger import log
from node import Node, GREEN, RED


"""
Discovers other nodes on the network. It goes ip address by
ip address and tries to call the '/greetings' endpoint. If
a status code of 200 is received, it stores the ip address into
the list of known nodes. It also checks if one of the nodes
is the master on the network. There are three possible outcomes
at the end of this function. If no other nodes are discovered,
this node becomes the master. If there are other nodes but no 
master has been discovered, it engages the election process.
And finally, if a master has been discovered, it'll start
performing a periodic health check on it (ping). For the sake 
of speeding up the whole process, the method only scans first 
'max_nodes' ip addresses.
"""
def discover_nodes(node, max_nodes=20):
    log.info('Scanning the network')

    count = 0
    master_found = False

    for ip_addr in node._interface.network:
        # Skip this node (there is no point of discovering ourselves).
        if ip_addr == node._interface.ip:
            continue

        # Construct the API to be called.
        endpoint = f'http://{ip_addr}:{node._port}/greetings'
        try:
            # Call the API
            response = requests.post(endpoint, verify=False, timeout=node._timeout)

            # If code 200 is received, a node has been discovered.
            if response.status_code == 200:
                log.info(f'{ip_addr} is up')
                data = response.json()

                # Check if the node is the master.
                if data['is_master'] is True:
                    # Make sure there is no more than one master on the network.
                    if master_found is False:
                        master_found = True
                        node.set_master_ip_addr(ip_addr)
                        log.info(f'Found the master node: {ip_addr}')
                    else:
                        # Kill the process if there are two or more masters.
                        log.critical(f'Two or more master nodes found on the network. Exiting...')
                        os.kill(os.getpid(), signal.SIGKILL)

                # Add the ip address to the list of known nodes.
                node.add_node(str(ip_addr))
            else:
                log.error(f'{ip_addr} seems to be up but status code 200 was not received')
        except:
            log.debug(f'{ip_addr} is down')

        # Check if we exceeded the maximum number of ip addresses to be scanned.
        count += 1
        if count == max_nodes:
            break
    
    log.info('Finished scanning the network')

    # If no other nodes have been discovered, this node becomes the master.
    if len(node._nodes) == 0:
        log.info('No other nodes have been found on the network')
        node.set_as_master()
        _handle_clients(node)
    elif node._master_ip_addr is not None:
        # If a master has been found, start pinging it (health check)
        Thread(target=ping_master, args=(node, )).start()
    else:
        # If there are other nodes on the network but no master, start the election process.
        log.info('No master has been found on the network')
        init_new_master(node)
        

"""
This function performs the election process. It'll go over
the known nodes and to those who have a higher ip address, it
will send an election message. If there are no nodes with a higher
ip address, this node then becomes the master. Otherwise, it'll
wait for the new master to be announced.
"""
def init_new_master(node):
    # Do not do anything if this node has been set to be the master.
    if node._is_master is True:
        return
    
    log.info('Starting election of a new master')
    
    # Set the election flag.
    node.set_election_flag(True)

    # If this node has the highest ip address, it will become the master.
    exist_superior_node = False
    
    # Create a copy of the list of known nodes (thread safety).
    # The list might be changes if another node is discovered while
    # electing a new master.
    nodes = node.get_nodes_copy()

    # Go over the known nodes
    for ip_addr in nodes:
        # Check if the current node has a higher ip address.
        # If so, send him an election message.
        if node._interface.ip < ipaddress.ip_address(ip_addr):
            try:
                log.info(f'Sending an election message from {node._interface.ip} to {ip_addr}')
                response = requests.post(f'http://{ip_addr}:{node._port}/election', verify=False, timeout=node._timeout)

                # If the node response with the status code of 200, our job is done
                # as he is a superior node (he'll take over the election process from now on)
                # and we'll just wait for the new master to be announced.
                if response.status_code == 200:
                    exist_superior_node = True
                else:
                    log.warning(f'Sending an election message from {node._interface.ip} to {ip_addr} was not successful')
            except:
                # The node is apparently down, therefore remove it from the list of known nodes.
                node.remove_node(ip_addr)
                log.warning(f'Sending an election message from {node._interface.ip} to {ip_addr} was not successful')

    # If this node happens to have the highest ip address
    # on the network, ti becomes the master.
    if exist_superior_node is False:
        _announce_new_master(node)


"""
Performs a periodical health check on the master node.
If the master is not responding, it's considered to be down
and the process of election is kicked off.
"""
def ping_master(node):
    # Store the master's ip address locally (thread safety).
    master_ip_addr = node._master_ip_addr

    # Construct the endpoint to be called.
    endpoint = f'http://{master_ip_addr}:{node._port}/health-check'

    log.info(f"Starting periodically pinging the master ({master_ip_addr})")
    while True:
        try:
            # The node must return a status code 200. Otherwise, it's considered to be down.
            response = requests.get(endpoint, verify=False, timeout=node._timeout)
            if response.status_code != 200:
                break
        except Exception as e:
            print(e) # Just for debugging because debugging a distribution application is a lot of fun :)
            break

        # Perform the health check every 2s.
        time.sleep(2)
    
    # We could've been elected as the master. In that case, do not do anything.
    # Otherwise, start the election process.
    if node._is_master is False:
        log.error(f'Master ({master_ip_addr}) seems to be down')
        node.remove_node(master_ip_addr)
        init_new_master(node)


"""
"""
def _announce_new_master(node):
    # We could've been selected as the master. If so, then do not do anything.
    if node._is_master is True:
        return

    # Set the node as the master.
    node.set_as_master()

    # Copy the list of known nodes (thread safety).
    nodes = node.get_nodes_copy()

    for ip_addr in nodes:
        try:
            log.info(f'Announcing the new master to {ip_addr}')
            response = requests.post(f'http://{ip_addr}:{node._port}/master-announcement', verify=False, timeout=node._timeout)
            if response.status_code != 200:
                log.warning(f'Node {ip_addr} seems to be down')
                node.remove_node(ip_addr)    
        except:
            log.warning(f'Node {ip_addr} seems to be down')
            node.remove_node(ip_addr)

    # Start handling the clients (assigning them colors)
    _handle_clients(node)



"""
"""
def _handle_clients(node):
    def get_color(index):
        remainder = index % 3
        if remainder == 2:
            return RED
        return GREEN

    while True:
        index = 1 # not 0 because the master is always green
        nodes = node.get_nodes_copy()
    
        for ip_addr in nodes:
            try:
                response = requests.post(f'http://{ip_addr}:{node._port}/color', json={'color' : get_color(index)}, verify=False, timeout=node._timeout)
                if response.status_code != 200:
                    log.warning(f'Node {ip_addr} seems to be down')
                    node.remove_node(ip_addr)
                else:
                    index += 1
            except:
                log.warning(f'Node {ip_addr} seems to be down')
                node.remove_node(ip_addr)

        time.sleep(1)