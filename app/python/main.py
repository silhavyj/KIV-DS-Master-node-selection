import logging
from threading import Thread, Lock
from flask import Flask, request, jsonify

from bully import Bully

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

bully = Bully('enp0s25')
bully_mtx = Lock()

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
    data = request.get_json()
    if 'color' in data:
        bully_mtx.acquire()
        bully.color = data['color']
        bully_mtx.release()
        logging.info(f"color has been changed to '{bully.color}'")
        return jsonify({'Response': 'OK'}), 200
    else:
        return jsonify({'Response': 'ERROR'}), 400


@app.route('/register', methods=['POST'])
def register_new_node():
    pass


if __name__ == '__main__':
    app.run(host=str(bully.network_info.interface.ip))