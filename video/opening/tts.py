import edge_tts, asyncio, json, os, subprocess
os.environ.setdefault('SSL_CERT_FILE','/root/.ccr/ca-bundle.crt')
S=json.load(open('script.json'))
proxy=os.environ['HTTPS_PROXY']
async def one(seg):
    out=f"assets/voice/{seg['id']}.mp3"
    words=[]; sents=[]; data=b''
    for boundary in ('WordBoundary','WordBoundary','SentenceBoundary'):
        try:
            c=edge_tts.Communicate(seg['en'], S['voice'], rate=S['rate'], proxy=proxy, boundary=boundary)
            words=[]; sents=[]; data=b''
            async for ch in c.stream():
                if ch['type']=='audio': data+=ch['data']
                elif ch['type']=='WordBoundary': words.append({'text':ch['text'],'start':ch['offset']/1e7,'end':(ch['offset']+ch['duration'])/1e7})
                elif ch['type']=='SentenceBoundary': sents.append({'text':ch['text'],'start':ch['offset']/1e7,'end':(ch['offset']+ch['duration'])/1e7})
            break
        except Exception as e:
            print(seg['id'], boundary, 'failed:', type(e).__name__); await asyncio.sleep(2)
    if not data: raise SystemExit('no audio for '+seg['id'])
    open(out,'wb').write(data)
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out]).decode().strip())
    return {'id':seg['id'],'file':out,'duration':dur,'words':words,'sentences':sents}
async def main():
    res=[]
    for seg in S['segments']:
        r=await one(seg); res.append(r); print(r['id'], round(r['duration'],2),'s', len(r['words']),'words', len(r['sentences']),'sentences')
    json.dump(res,open('assets/voice/timings.json','w'),indent=1,ensure_ascii=False)
    print('total speech', round(sum(r['duration'] for r in res),1),'s')
asyncio.run(main())
