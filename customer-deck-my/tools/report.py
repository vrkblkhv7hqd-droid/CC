import json,sys
d=json.load(sys.stdin)
print('mode',d['mode'],'slides',d['slides'],'blocked',d['blocked'],'errors',d['errors'])
for r in d['report']:
    if 'id' in r:
        flag = 'OVERFLOW' if r['slack']<0 else ('tight' if r['slack']<16 else ('loose' if r['slack']>140 else 'ok'))
        print(r['id'].ljust(18),'bottom',str(r['contentBottom']).rjust(5),'slack',str(r['slack']).rjust(5),flag.ljust(8),'right',r['maxRight'],'minFont',r['minFont'],r['small'],'| lowest:',r['lowest'])
    else:
        print(r)
