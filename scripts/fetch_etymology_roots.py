import json
from fetch_etymologies import fetch,ROOT
# Transparent derived forms whose entry has no standalone etymology section.
roots={'becoming':'become','aboveboard':'above board','fete':'fête','hamstrung':'hamstring','plodding':'plod','muted':'mute','obliging':'oblige','carping':'carp','retiring':'retire','dilapidated':'dilapidate','embroiled':'embroil','chauvinist':'chauvinism','subversive':'subvert','decorous':'decorous'}
if __name__=='__main__':
 overrides=json.loads((ROOT/'data/etymology-overrides.json').read_text())
 for word,lemma in roots.items():
  if word=='decorous':
   file=ROOT/'data/etymology/decorous.json'
   if file.exists():file.unlink()
  d=fetch(lemma)
  if word not in overrides:overrides[word]={'lemma':lemma}
  print(word,lemma,d.get('etymologies'),flush=True)
 (ROOT/'data/etymology-overrides.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2)+'\n')
