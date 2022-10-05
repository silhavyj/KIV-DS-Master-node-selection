import sys
import logging
from threading import Thread
from flask import Flask, request, jsonify

from bully import Bully

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

bully = Bully('enp0s25')

network_scan = Thread(target=bully.discover_other_nodes, args=(18,))
network_scan.start()

@app.route('/node-details', methods=['GET'])
def get_details():
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
    
    bully.add_node(data['ip_addr'], data)
    return jsonify({
        'response' : 'OK',
        'color'    : bully.calculate_node_color() 
    }), 200


@app.route('/master_announcement', methods=['POST'])
def register_new_node():
    pass


if __name__ == '__main__':
    app.run(host=str(bully.network_info.interface.ip), port=int(sys.argv[1]))