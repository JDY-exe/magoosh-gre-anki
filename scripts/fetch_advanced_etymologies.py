"""Fetch origins while local Playwright discovers Advanced vocabulary."""
import concurrent.futures,json,time
from fetch_etymologies import fetch,ROOT

def discover():
    file=ROOT/'data/manifest-advanced.json'
    if not file.exists():return [],False
    manifest=json.loads(file.read_text())
    words=[];complete=True
    for deck in manifest['decks']:
        file=ROOT/'data'/(deck['url'].rsplit('/',1)[-1]+'.json')
        if not file.exists():complete=False;continue
        try:data=json.loads(file.read_text())
        except json.JSONDecodeError:complete=False;continue
        complete &= len(data['cards'])==deck['expected']
        words.extend(c['word'] for c in data['cards'] if not c['word'].startswith('Magoosh'))
    return list(dict.fromkeys(words)),complete

if __name__=='__main__':
    submitted=set();finished={};pending={}
    overrides=json.loads((ROOT/'data/etymology-overrides.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        while True:
            words,complete=discover()
            for word in words:
                if word not in submitted:
                    lemma=overrides.get(word,{}).get('lemma',word)
                    pending[pool.submit(fetch,lemma)]=word;submitted.add(word)
            completed=[f for f in pending if f.done()]
            for f in completed:
                word=pending.pop(f);result=f.result();finished[word]=result
                if 'error' in result:print('ERROR',word,result['error'],flush=True)
                if len(finished)%25==0:print('Fetched',len(finished),'Advanced origins; discovered',len(words),flush=True)
            if complete and not pending:break
            time.sleep(.5)
    print('COMPLETE',len(finished),'Advanced vocabulary entries; lookup failures:',[w for w,r in finished.items() if 'error' in r],flush=True)
