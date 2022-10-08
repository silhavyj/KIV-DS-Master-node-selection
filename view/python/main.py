import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.rows {
  margin: 0;
  padding: 0;

  li {
    text-decoration: none;
    list-style: none;
    margin-bottom: 10px;
    display: flex; 
    justify-content: space-around;
    width: 50%;

    span {
      margin-right: 20px;
    }
  }
}
</style>
</head>
<body>

<ul class="rows">
	<li><span style='font-weight: bold;'>M | </span><span>176.0.0.2 | </span><span style='color: red;'>RED</span><hr></li>
    <li><span>S | </span><span>176.0.0.3 | </span><span style='color: green;'>GREEN</span><hr></li>
    <li><span>S | </span><span>176.0.0.4 | </span><span style='color: green;'>GREEN</span><hr></li>
</ul>

</body>
</html> 
"""

config_file = open('/opt/view/python/config.ini', 'r')
lines = config_file.readlines()
config_file.close()

nodes = []
for line in lines:
    line.strip()
    if line != '':
        print(f'Read {line} from the config file')
        nodes.append(line)


def get_status():
    status = []
    for ip_addr in nodes:
        try:
            print(f'Checking the status of {ip_addr}')
            response = requests.get(f'http://{ip_addr}:5000/node-details')
            if response.status_code == 200:
                status.append(response.json())
        except Exception as e:
            print(e)
    return status


@app.route('/status', methods=['GET'])
def get_view():
    return jsonify(get_status()), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')