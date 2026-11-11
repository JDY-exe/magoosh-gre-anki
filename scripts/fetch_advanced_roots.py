"""Fetch reviewed spelling/base-word aliases needed by Advanced origins."""
import json
from fetch_etymologies import ROOT,fetch
manifest=json.loads((ROOT/'data/manifest-advanced.json').read_text())
words={c['word'] for d in manifest['decks'] for c in json.loads((ROOT/'data'/(d['url'].rsplit('/',1)[-1]+'.json')).read_text())['cards']}
overrides=json.loads((ROOT/'data/etymology-overrides.json').read_text())
for word in sorted(words):
 lemma=overrides.get(word,{}).get('lemma',word)
 if lemma!=word:
  data=fetch(lemma)
  print(word,'→',lemma, json.dumps(data,ensure_ascii=False),flush=True)
