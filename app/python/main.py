import logging
from threading import Thread
from flask import Flask, request, jsonify

from bully import Bully

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

bully = Bully('eth1')

network_scan = Thread(target=bully.discover_other_nodes, args=(5,))
network_scan.start()

@app.route('/node-details', methods=['GET'])
def get_details():
    return jsonify({
        'name'      : bully.network_info.hostname,
        'node_id'   : str(bully.node_id),
        'master'    : str(bully.master),
        'election'  : str(bully.election),
        'interface' : str(bully.network_info.interface.ip),
    })


@app.route('/color', methods=['POST'])
def set_color():
    if bully.master == True:
        return jsonify({
            'Response': 'ERROR',
            'Message' : 'Cannot set the color of the master'
        }), 400

    data = request.get_json()
    if 'color' in data:
        bully.set_color(data['color'])
        logging.info(f"color has been changed to '{bully.color}'")
        return jsonify({'Response': 'OK'}), 200
    
    return jsonify({
        'Response': 'ERROR',
        'Message' : 'Invalid data (color is missing)'
    }), 400


@app.route('/worker_register', methods=['POST'])
def worker_register():
    pass


@app.route('/master_announcement', methods=['POST'])
def register_new_node():
    pass


if __name__ == '__main__':
    app.run(host=str(bully.network_info.interface.ip))