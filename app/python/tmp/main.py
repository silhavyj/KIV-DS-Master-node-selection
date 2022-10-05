import requests

r = requests.post('http://10.10.41.17:5000/color', json={"d" : "GREEN"})
print(r.text)