"""Show Advanced origin ambiguities and extraction gaps for meaning review."""
import json,re,urllib.parse
from fetch_etymologies import ROOT
manifest=json.loads((ROOT/'data/manifest-advanced.json').read_text())
reviewed_file=ROOT/'data/etymology-reviewed-advanced.json'
reviewed=set(json.loads(reviewed_file.read_text())) if reviewed_file.exists() else set()
overrides=json.loads((ROOT/'data/etymology-overrides.json').read_text())
for deck in manifest['decks']:
 file=ROOT/'data'/(deck['url'].rsplit('/',1)[-1]+'.json')
 if not file.exists():continue
 for card in json.loads(file.read_text())['cards']:
  word=card['word']
  if word.startswith('Magoosh') or word in reviewed:continue
  file=ROOT/'data/etymology'/(urllib.parse.quote(word,safe='')+'.json')
  if not file.exists():continue
  d=json.loads(file.read_text());es=d['etymologies']
  problem=not es or not es[0]['paragraphs']
  if not problem:
   text=es[0]['paragraphs'][0]
   problem=text.endswith(':') or text.startswith(('See ','Either','Partly','From the following')) or len(text.split())>180
  if len(es)>1 or problem:
   print('\nWORD:',word,'MAGOOSH:',[(s['definition']) for s in card['senses']])
   for i,e in enumerate(es):print(i,'ORIGIN:',e['paragraphs'],'SENSES:',e['senses'])
