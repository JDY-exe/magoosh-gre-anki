"""Update the existing note type without replacing cards or scheduling."""
import json,re
from pathlib import Path
from anki_api import invoke
MODEL='Magoosh GRE Vocabulary'
ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT/'backups/before-etymology'
EXTRA_CSS='''
/* Word origin stays secondary to the definition and examples. */
.etymology {font-size: 14px; line-height: 1.5; color: #68777b; margin-top: 24px; border-top: 1px solid #d8dcd7; padding-top: 12px;}
.etymology summary {cursor: pointer; font-size: 13px; color: #68777b;}
.etymology .origin-text {margin: 10px 0 0;}
.etymology .origin-credit {font-size: 11px; margin-top: 8px;}
.etymology a {color: inherit; text-decoration: underline;}
.nightMode .etymology, .night_mode .etymology {color: #a8b5b8; border-color: #465359;}
.nightMode .etymology summary, .night_mode .etymology summary {color: #a8b5b8;}
'''
SECTION='{{#Etymology}}<details class="etymology"><summary>Word origin</summary><div class="origin-text">{{Etymology}}</div></details>{{/Etymology}}'
if __name__=='__main__':
 assert invoke('exportPackage',deck='Magoosh GRE',path=str(BACKUP/'Magoosh_GRE_with_study_progress.apkg'),includeSched=True)
 if 'Etymology' not in invoke('modelFieldNames',modelName=MODEL):
  invoke('modelFieldAdd',modelName=MODEL,fieldName='Etymology')
 templates=json.loads((BACKUP/'templates.json').read_text())
 for template in templates.values():
  for face in ['Front','Back']:
   template[face]=re.sub(r'<div class="prompt">Recall the meaning, then reveal the answer\.</div>','',template[face])
  template['Back']=template['Back'].replace('<div class="source">',SECTION+'<div class="source">',1)
 styling=json.loads((BACKUP/'styling.json').read_text())['css']+EXTRA_CSS
 invoke('updateModelTemplates',model={'name':MODEL,'templates':templates})
 invoke('updateModelStyling',model={'name':MODEL,'css':styling})
 (ROOT/'data/etymology-template.json').write_text(json.dumps({'templates':templates,'css':styling},ensure_ascii=False,indent=2))
 print('Prompt removed. Subtle, collapsed Word origin section added to answer side.')
