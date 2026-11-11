import json, urllib.request

def invoke(action, **params):
    req=urllib.request.Request('http://127.0.0.1:8765',data=json.dumps({'action':action,'version':6,'params':params}).encode(),headers={'Content-Type':'application/json'})
    response=json.load(urllib.request.urlopen(req,timeout=120))
    if response['error']: raise RuntimeError(response['error'])
    return response['result']
