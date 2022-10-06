import requests
import ipaddress

#r = requests.post('http://10.10.41.17:5000/color', json={"d" : "GREEN"})
#print(r.json())

#r = requests.get('http://10.10.41.17:5000/node-details')
#data = r.json()

#print(data)
#if data['master'] == 'True':
#    print("AAA")

print(ipaddress.ip_address('176.0.1.3') < ipaddress.ip_address('176.0.1.3'))

nodes = {}

nodes[1] = 'A'
print(nodes.get(1))
nodes.pop(1)
if nodes.get(1) is not None:
    nodes.pop(1)


requests.post('http://10.10.41.17:5000/master-announcement', json={'ip_addr' : 's'})