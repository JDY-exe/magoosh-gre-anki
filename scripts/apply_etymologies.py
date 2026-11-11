"""Enrich existing Anki notes, preserving their identity and scheduling."""
import json
from pathlib import Path
from anki_api import invoke
ROOT=Path(__file__).resolve().parents[1]
MODEL='Magoosh GRE Vocabulary'
SCHEDULING=['cardId','note','ord','factor','interval','type','queue','due','reps','lapses','left','flags','deckName']

def schedule(cards):return {str(c['cardId']):{k:c[k] for k in SCHEDULING} for c in cards}

if __name__=='__main__':
 origins=json.loads((ROOT/'data/etymology-cards.json').read_text())
 ids=invoke('findNotes',query='note:"Magoosh GRE Vocabulary"')
 notes=invoke('notesInfo',notes=ids)
 card_ids=[cid for n in notes for cid in n['cards']]
 before_cards=invoke('cardsInfo',cards=card_ids)
 before={n['noteId']:n for n in notes}
 vocab=[n for n in notes if not n['fields']['Word']['value'].startswith('Magoosh')]
 assert all(n['fields']['Word']['value'] in origins for n in vocab),'Missing sourced etymology'
 snapshot={'notes':notes,'scheduling':schedule(before_cards)}
 (ROOT/'backups/before-etymology/immediately-before-field-update.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2))
 for offset in range(0,len(vocab),25):
  batch=vocab[offset:offset+25]
  actions=[{'action':'updateNoteFields','params':{'note':{'id':n['noteId'],'fields':{'Etymology':origins[n['fields']['Word']['value']]['html']}}}} for n in batch]
  results=invoke('multi',actions=actions)
  assert len(results)==len(batch)
  for r in results:
   if isinstance(r,dict):assert not r.get('error'),r
  print('Updated',min(offset+25,len(vocab)),'/',len(vocab),flush=True)
 after_notes=invoke('notesInfo',notes=ids)
 after_cards=invoke('cardsInfo',cards=card_ids)
 assert schedule(before_cards)==schedule(after_cards),'Scheduling changed during operation; inspect snapshot'
 assert set(invoke('findNotes',query='note:"Magoosh GRE Vocabulary"'))==set(ids)
 for n in after_notes:
  old=before[n['noteId']]
  assert n['cards']==old['cards']
  for field in ['Word','Senses','OriginalDeck','SourceURL']:
   assert n['fields'][field]['value']==old['fields'][field]['value'],(n['noteId'],field)
  word=n['fields']['Word']['value']
  if word in origins:assert n['fields']['Etymology']['value']==origins[word]['html']
 templates=invoke('modelTemplates',modelName=MODEL)
 assert all('Recall the meaning' not in side for t in templates.values() for side in t.values())
 rendered=after_cards[0]
 assert 'Word origin' in rendered['answer'] and 'Recall the meaning' not in rendered['question']
 assert 'class="etymology"' not in rendered['question']
 export=ROOT/'output/Magoosh_GRE_with_etymology.apkg'
 assert invoke('exportPackage',deck='Magoosh GRE',path=str(export),includeSched=True)
 report={'notes':len(ids),'cards':len(card_ids),'vocabularyEnriched':len(vocab),'promotionalEntriesPreserved':len(notes)-len(vocab),'studySchedulingPreserved':True,'originalFieldsPreserved':True,'cardAndNoteIdsPreserved':True,'recallPromptRemoved':True,'answerSideOnly':True,'collapsedByDefault':True,'package':str(export)}
 (ROOT/'output/etymology-validation.json').write_text(json.dumps(report,indent=2))
 # Render the actual Anki answer for visual verification.
 (ROOT/'output/etymology-preview.html').write_text('<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Anki word origin preview</title><style>'+invoke('modelStyling',modelName=MODEL)['css']+'</style><body class="card">'+rendered['answer']+'</body></html>')
 print(json.dumps(report,indent=2))
