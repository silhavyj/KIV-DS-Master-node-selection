import logging
import threading
from flask import Flask, request, jsonify

from bully import Bully

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# bully = Bully('docker0')

bully = Bully('eth1')

thread = threading.Thread(target=bully.discover_other_nodes, args=(5,))
thread.start()

@app.route('/node-details', methods=['GET'])
def get_details():
    return jsonify({
        'name'      : bully.network_info.hostname,
        'node_id'   : str(bully.node_id),
        'master'    : str(bully.master),
        'election'  : str(bully.election),
        'interface' : str(bully.network_info.interface.ip),
    })


if __name__ == '__main__':
    app.run(host=str(bully.network_info.interface.ip))