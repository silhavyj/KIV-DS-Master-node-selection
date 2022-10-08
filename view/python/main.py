import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HTML_START = "<html>\
<head>\
<meta name='viewport' content='width=device-width, initial-scale=1'>\
<style>\
.rows {\
  margin: 0;\
  padding: 0;\
  \
  li {\
    text-decoration: none;\
    list-style: none;\
    margin-bottom: 10px;\
    display: flex; \
    justify-content: space-around;\
    width: 50%;\
    \
    span { \
      margin-right: 20px;\
    }\
  }\
}\
</style>\
</head>\
<body>\
\
<h2>Status monitoring</h2>\
<ul class='rows'>"

HTML_END = "</ul>\
\
</body>\
</html> "

config_file = open('/opt/view/python/config.ini', 'r')
lines = config_file.readlines()
config_file.close()

nodes = []
for line in lines:
    line = line.strip()
    if line != '':
        print(f'Read {line} from the config file')
        nodes.append(line)


def get_status():
    status = ''
    for ip_addr in nodes:
        try:
            print(f'Checking the status of {ip_addr}')
            response = requests.get(f'http://{ip_addr}:5000/node-details', verify=False, timeout=0.5)
            if response.status_code == 200:
                data = response.json()
                status += "<li><span>"
                status += data['hostname']
                status += "</span> | "
                if data['is_master'] is True:
                    status += "<span style='font-weight: bold; color: purple;'>"
                    status += 'M'
                else:
                    status += "<span style='font-weight: bold;'>"
                    status += 'S'
                status += ' | </span><span>'
                status += ip_addr
                status += " | </span><span style='color: "
                if data['color'] == 'GREEN':
                    status += "green;'>GREEN</span><hr></li>"
                elif data['color'] == 'GRAY':
                    status += "gray;'>GRAY</span><hr></li>"
                else:
                    status += "red;'>RED</span><hr></li>"
        except Exception as e:
            print(e)
    return status


@app.route('/status', methods=['GET'])
def get_view():
    html = HTML_START
    html += get_status()
    html += HTML_END
    return html


if __name__ == '__main__':
    app.run(host='0.0.0.0')