import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/manifest.json').read_text())
cards=[c for d in manifest['decks'] for c in json.loads((ROOT/'data'/(d['url'].rsplit('/',1)[-1]+'.json')).read_text())['cards']]
meanings={c['word']:'; '.join(s['definition'] for s in c['senses']) for c in cards}
entries=[json.loads(p.read_text()) for p in (ROOT/'data/etymology').glob('*.json')]
for d in sorted(entries,key=lambda x:x['word']):
 if len(d['etymologies'])!=1 or not d['etymologies'][0]['paragraphs']:
  print('\nWORD:',d['word'],'MAGOOSH:',meanings.get(d['word'],''))
  for i,e in enumerate(d['etymologies']):print(i, 'ORIGIN:',e['paragraphs'],'SENSES:',e['senses'])
