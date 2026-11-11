"""Cache sourced English etymology excerpts for the existing Anki notes."""
import concurrent.futures, json, re, time, threading, urllib.request, urllib.parse, gzip
RATE_LOCK=threading.Lock()
NEXT_REQUEST=0.0
def pace():
    global NEXT_REQUEST
    with RATE_LOCK:
        time.sleep(max(0,NEXT_REQUEST-time.monotonic()))
        NEXT_REQUEST=time.monotonic()+1.1
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/etymology';DEST.mkdir(exist_ok=True)

def clean(el):
    el=BeautifulSoup(str(el),'html.parser')
    for x in el.select('.reference, .mw-editsection, .maintenance-line, .error'):x.decompose()
    return re.sub(r'\s+',' ',el.get_text()).strip()

def fetch(word):
    file=DEST/(urllib.parse.quote(word,safe='')+'.json')
    if file.exists():return json.loads(file.read_text())
    if word.startswith('Magoosh'):return {'word':word,'etymologies':[],'skipped':'promotional entry'}
    url='https://en.wiktionary.org/wiki/'+urllib.parse.quote(word.replace(' ','_'),safe='')
    result={'word':word,'source':url,'etymologies':[]}
    for attempt in range(4):
      try:
        pace()
        req=urllib.request.Request(url,headers={'User-Agent':'PersonalVocabularyAnki/1.0 (personal study; cached, low concurrency)', 'Accept-Encoding':'gzip'})
        with urllib.request.urlopen(req,timeout=45) as r:
          raw=r.read()
          if r.headers.get('Content-Encoding')=='gzip':raw=gzip.decompress(raw)
          soup=BeautifulSoup(raw,'html.parser')
        break
      except Exception as e:
        if attempt==3:return {**result,'error':str(e)}
        time.sleep(15*(attempt+1))
    english=soup.find(id='English')
    if english:
      heading=english if english.name=='h2' else english.find_parent('h2')
      start=heading.parent if heading.parent.name=='div' and 'mw-heading' in heading.parent.get('class',[]) else heading
      current=None;in_etym=False
      for node in start.next_siblings:
        if not getattr(node,'name',None):continue
        h=node if re.fullmatch(r'h[2-6]',node.name) else node.find(re.compile(r'^h[2-6]$'),recursive=False)
        if h:
          level=int(h.name[1]);title=clean(h)
          if level==2:break
          in_etym=title.startswith('Etymology')
          if in_etym:
            current={'heading':title,'paragraphs':[],'senses':[]};result['etymologies'].append(current)
        elif current is not None:
          if in_etym and node.name=='ul':
            for li in node.find_all('li',recursive=False):
              t=clean(li)
              if t:current['paragraphs'].append(t)
          if in_etym and node.name=='p':
            t=clean(node)
            if t:current['paragraphs'].append(t)
          if node.name=='ol':
            for li in node.find_all('li',recursive=False)[:2]:
              clone=BeautifulSoup(str(li),'html.parser')
              for child in clone.select('ul, dl, ol'):child.decompose()
              current['senses'].append(clean(clone)[:350])
    file.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
 manifest=json.loads((ROOT/'data/manifest.json').read_text())
 words=[c['word'] for d in manifest['decks'] for c in json.loads((ROOT/'data'/(d['url'].rsplit('/',1)[-1]+'.json')).read_text())['cards']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(fetch,w):w for w in words}
  for i,f in enumerate(concurrent.futures.as_completed(futures),1):
   r=f.result()
   if 'error' in r:print('ERROR',r['word'],r['error'],flush=True)
   if i%40==0 or i==len(words):print('Fetched',i,'/',len(words),flush=True)
