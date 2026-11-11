"""Compile attributed, meaning-matched word origins; fail on missing vocabulary."""
import html,json,re,urllib.parse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
basic_manifest=json.loads((ROOT/'data/manifest.json').read_text())
notes=[{'fields':{'Word':{'value':c['word']}}} for deck in basic_manifest['decks'] for c in json.loads((ROOT/'data'/(deck['url'].rsplit('/',1)[-1]+'.json')).read_text())['cards']]
if '--advanced' in sys.argv:
 manifest=json.loads((ROOT/'data/manifest-advanced.json').read_text())
 for deck in manifest['decks']:
  data=json.loads((ROOT/'data'/(deck['url'].rsplit('/',1)[-1]+'.json')).read_text())
  assert len(data['cards'])==deck['expected'], ('Incomplete extraction', deck['name'])
  notes.extend({'fields':{'Word':{'value':c['word']}}} for c in data['cards'])
overrides=json.loads((ROOT/'data/etymology-overrides.json').read_text())
records={};missing=[];ambiguous=[]
for note in notes:
 word=note['fields']['Word']['value']
 if word.startswith('Magoosh'):continue
 override=overrides.get(word,{})
 lemma=override.get('lemma',word)
 file=ROOT/'data/etymology'/(urllib.parse.quote(lemma,safe='')+'.json')
 if not file.exists():missing.append(word);continue
 entry=json.loads(file.read_text());etymologies=entry['etymologies']
 indices=override.get('indices',[0])
 if not etymologies or any(i>=len(etymologies) for i in indices):missing.append(word);continue
 text=override.get('text')
 if not text:
  paragraphs=[etymologies[i]['paragraphs'][0] for i in indices if etymologies[i]['paragraphs']]
  if not paragraphs:missing.append(word);continue
  text=' '.join(paragraphs)
 text=re.sub(r'[\u200e\u200f]','',text)
 # Avoid dropping origin information by mechanically truncating mid-sentence.
 if len(text.split())>180:raise ValueError('Needs a shorter reviewed explanation: '+word)
 if len(etymologies)>1:ambiguous.append(word)
 source=entry['source']+'#English'
 content=html.escape(text)+'<div class="origin-credit">'+(
  '<a href="'+html.escape(source,quote=True)+'">Wiktionary contributors</a> · '+
  '<a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> · '+
  ('adapted' if 'text' in override or len(indices)>1 else 'excerpt')+'</div>')
 records[word]={'text':text,'html':content,'source':source,'originIndices':indices,'lemma':lemma,'reviewedOverride':word in overrides}
(ROOT/'data/etymology-cards.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('Compiled',len(records),'origins. Missing:',missing)
print('Multiple origins requiring meaning review:',', '.join(sorted(ambiguous)))
if missing:raise SystemExit(1)
