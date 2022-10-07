from threading import Thread
from flask import Flask, request, jsonify

from election import discover_nodes, init_new_master
from node import Node
from logger import log

app = Flask(__name__)

#node = Node(interface_name='enp0s25', port=5000)
node = Node(interface_name='eth1', port=5000)
Thread(target=discover_nodes, args=(node, )).start()


@app.route('/node-details', methods=['GET'])
def get_details():
    node.add_node(request.remote_addr)
    return jsonify(node.get_details()), 200


@app.route('/health-check', methods=['GET'])
def is_alive():
    return "", 200


@app.route('/election', methods=['GET'])
def election():
    log.info('Received an election message')
    if node._is_master is True:
        log.info('Ignoring the election message (I have already selected myself as the master)')
        return "", 200
    
    if node._election is True:
        log.info('Ignoring the election message (I have already tried to forward it)')
    else:
        log.info('Forwarding the election message')
        node.set_election_flag(True)
        Thread(target=init_new_master, args=(node, )).start()

    return "", 200

if __name__ == '__main__':
    app.run(host=str(node._interface.ip))