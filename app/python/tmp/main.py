import requests

#r = requests.post('http://10.10.41.17:5000/color', json={"d" : "GREEN"})
#print(r.json())

r = requests.get('http://10.10.41.17:5000/node-details')
data = r.json()

print(data)
if data['master'] == 'True':
    print("AAA")