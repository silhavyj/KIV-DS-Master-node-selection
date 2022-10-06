import sys
import logging
from threading import Thread
from flask import Flask, request, jsonify

from bully import Bully

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

bully = Bully('eth1')

Thread(target=bully.discover_other_nodes, args=(18,)).start()


@app.route('/health-check', methods=['GET'])
def is_alive():
    return jsonify({'Response': 'OK'}), 200
    

@app.route('/node-details', methods=['GET'])
def get_details():
    data = request.get_json()
    bully.add_node(data['ip_addr'], data)
    return jsonify(bully.get_info()), 200


@app.route('/color', methods=['POST'])
def set_color():
    if bully.master == True:
        return jsonify({
            'response' : 'ERROR',
            'message'  : 'Cannot set the color of the master'
        }), 400

    data = request.get_json()

    if 'color' in data:
        bully.set_color(data['color'])
        return jsonify({'Response': 'OK'}), 200
    
    return jsonify({
        'response' : 'ERROR',
        'message'  : 'Invalid data (color is missing)'
    }), 400


@app.route('/worker_register', methods=['POST'])
def worker_register():
    if bully.master == False:
        return jsonify({
            'response' : 'ERROR',
            'message'  : 'I am not the master on the network'
        }), 400

    data = request.get_json()
    logging.info(f"Node {data['ip_addr']} has registered with the master")

    color = bully.calculate_node_color() 
    bully.add_node(data['ip_addr'], data)
    bully.set_node_color(data['ip_addr'], color)
    Thread(target=bully.worker_health_check, args=(data['ip_addr'], )).start()

    return jsonify({
        'response' : 'OK',
        'color'    :  color
    }), 200


@app.route('/election', methods=['GET'])
def get_election():
    if bully.election == False:
        bully.election = True
        Thread(bully.run_bully_algorithm).start()

    return jsonify({
        'response' : 'OK',
        'status'   : bully.election 
    }), 200


@app.route('/master-announcement', methods=["POST"])
def set_new_master():
    bully.set_election(False)
    return jsonify({'Response': 'OK'}), 200


if __name__ == '__main__':
    #app.run(host=str(bully.network_info.interface.ip), port=int(sys.argv[1]))
    app.run(host=str(bully.network_info.interface.ip))