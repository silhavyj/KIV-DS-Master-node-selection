import os
import sys
import signal
from threading import Thread
from flask import Flask, request, jsonify

from election import discover_nodes, init_new_master, ping_master
from node import Node
from logger import log

# Custom CTR+C signal handler to ensure that all threads
# of the process are immediately terminated.
def _terminate_signal_handler(sig, frame):
    os.kill(os.getpid(), signal.SIGKILL)

app = Flask(__name__)

# Register the CTR+C signal handler
signal.signal(signal.SIGINT, _terminate_signal_handler)

# Create an instance of Node and start scanning the network.
node = Node(interface_name='eth1', port=5000)
Thread(target=discover_nodes, args=(node, )).start()


@app.route('/node-details', methods=['GET'])
def get_details():
    return jsonify(node.get_details()), 200


@app.route('/greetings', methods=['POST'])
def greetings():
    # Store the ip address of the caller into 
    # the list of known nodes.
    node.add_node(request.remote_addr)
    return jsonify(node.get_details()), 200


@app.route('/health-check', methods=['GET'])
def is_alive():
    return "", 200


@app.route('/election', methods=['POST'])
def election():
    log.info('Received an election message')

    # If this node is not the new master and has not yet
    # forwarded the election message, start the election process
    # on this node as well.
    if node._is_master is False and node._election is False:
        log.info('Forwarding the election message')

        # The election process has started.
        node.set_election_flag(True)

        # Start the election process.
        Thread(target=init_new_master, args=(node, )).start()
    else:
        log.info('Ignoring the election message')
    return "", 200


@app.route('/master-announcement', methods=['POST'])
def set_new_master():
    # The election process is over.
    node.set_election_flag(False)

    # Store the ip address of the new master.
    node.set_master_ip_addr(request.remote_addr)
    log.info(f'New master has been announced {request.remote_addr}')

    # Start pinging the new master
    Thread(target=ping_master, args=(node, )).start()
    return "", 200


@app.route('/color', methods=['POST'])
def set_color():
    if node._is_master is False:
        node.set_color(request.get_json()['color'])
    return "", 200


if __name__ == '__main__':
    app.run(host=str(node._interface.ip))