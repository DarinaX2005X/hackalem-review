"""Enable Pages for this user-requested repository, without changing visibility."""
import json,urllib.error
from github_api import credential,request

token=credential()
path='repos/DarinaX2005X/hackalem-review/pages'
try:
    old=request(path,token=token)
    result=request(path,method='PUT',body={'build_type':'legacy','source':{'branch':'main','path':'/docs'}},token=token)
    print('Pages configuration updated')
except urllib.error.HTTPError as e:
    if e.code==404:
        try:
            result=request(path,method='POST',body={'build_type':'legacy','source':{'branch':'main','path':'/docs'}},token=token)
            print(json.dumps({'url':result.get('html_url'),'status':result.get('status')},ensure_ascii=False))
        except urllib.error.HTTPError as create_error:
            detail=json.loads(create_error.read())
            print(json.dumps({'status':create_error.code,'message':detail.get('message'),'errors':detail.get('errors')},ensure_ascii=False))
            raise SystemExit(1)
    else:
        print('Pages configuration failed, HTTP',e.code)
        raise SystemExit(1)
