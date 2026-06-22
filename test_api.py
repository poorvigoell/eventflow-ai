import urllib.request, json
try:
    req = urllib.request.urlopen('http://127.0.0.1:8000/api/marl/next-action')
    data = json.loads(req.read())
    print("Agents:", len(data.get('agents', [])))
    print("Adjacency:", data.get('adjacency', []))
except Exception as e:
    print(e)
