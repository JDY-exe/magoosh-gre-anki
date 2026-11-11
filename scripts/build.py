#!/usr/bin/env python3
"""Build and validate a self-contained Anki package from Playwright's extraction."""
import csv
import hashlib
import html
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile
import genanki
import argparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
parser = argparse.ArgumentParser()
scope = parser.add_mutually_exclusive_group()
scope.add_argument('--advanced', action='store_true')
scope.add_argument('--all', action='store_true')
args = parser.parse_args()
manifest_names = (['manifest.json', 'manifest-advanced.json'] if args.all else
                  ['manifest-advanced.json'] if args.advanced else ['manifest.json'])
manifests = [json.loads((ROOT / 'data' / name).read_text()) for name in manifest_names]
manifest = {**manifests[0], 'decks': [deck for m in manifests for deck in m['decks']]}
stem = ('Magoosh_GRE_All_Levels' if args.all else
        'Magoosh_GRE_Advanced' if args.advanced else 'Magoosh_GRE_through_Basic_IX')
suffix = '-all' if args.all else '-advanced' if args.advanced else ''

def stable_id(value):
    return 1_000_000_000 + int(hashlib.sha256(value.encode()).hexdigest()[:8], 16) % 1_000_000_000

CSS = '''
.card {font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
 font-size: 20px; line-height: 1.55; text-align: left; color: #23313a; background: #f7f5f0;
 max-width: 660px; margin: 0 auto; padding: 30px 22px; box-sizing: border-box;}
.deck-label {font-size: 12px; text-transform: uppercase; letter-spacing: .12em; color: #6b787d; margin-bottom: 24px;}
.word {font-family: Georgia, serif; font-size: 44px; font-weight: 500; line-height: 1.2; overflow-wrap: anywhere; margin: 0 0 20px;}
.prompt {font-size: 15px; color: #6b787d;}
hr {border: 0; border-top: 1px solid #d8dcd7; margin: 28px 0;}
.sense {margin: 0 0 26px;}
.definition p {margin: 0 0 10px;}
.definition strong {color: #226c63;}
.example {font-size: 17px; color: #617077; border-left: 3px solid #b8cdc2; padding-left: 16px;}
.example p {margin: 0;}
.example strong {color: #23313a; font-weight: 600;}
.source {font-size: 12px; color: #7b8587; margin-top: 30px;}
a {color: #226c63;}
.nightMode.card, .night_mode.card {background: #1d2529; color: #e5e9e6;}
.nightMode .word, .nightMode .example strong, .night_mode .example strong {color: #e5e9e6;}
.nightMode .definition strong, .nightMode a, .night_mode .definition strong, .night_mode a {color: #8ac9b7;}
.nightMode .example, .nightMode .prompt, .nightMode .deck-label,
.night_mode .example, .night_mode .prompt, .night_mode .deck-label {color: #b0bebf;}
'''
front = '<div class="deck-label">{{OriginalDeck}}</div><div class="word">{{Word}}</div><div class="prompt">Recall the meaning, then reveal the answer.</div>'
back = '{{FrontSide}}<hr id="answer">{{Senses}}<div class="source">Magoosh GRE Vocabulary · <a href="{{SourceURL}}">Original card</a></div>'
origins_path = ROOT / 'data/etymology-cards.json'
origins = json.loads(origins_path.read_text()) if origins_path.exists() else {}
layout_path = ROOT / 'data/etymology-template.json'
if layout_path.exists():
    layout = json.loads(layout_path.read_text())
    CSS = layout['css']
    front = layout['templates']['Word → Meaning']['Front']
    back = layout['templates']['Word → Meaning']['Back']

model = genanki.Model(
    stable_id('magoosh-gre-vocabulary-v1'), 'Magoosh GRE Vocabulary',
    fields=[{'name': n} for n in ['Word', 'Senses', 'OriginalDeck', 'SourceURL', 'Etymology']],
    templates=[{'name': 'Word → Meaning', 'qfmt': front, 'afmt': back}], css=CSS,
    sort_field_index=0)

decks, rows, expected_counts, all_cards = [], [], {}, []
for info in manifest['decks']:
    slug = info['url'].rsplit('/',1)[-1]
    data = json.loads((ROOT / 'data' / (slug + '.json')).read_text())
    cards = data['cards']
    assert len(cards) == info['expected'], (info['name'],len(cards),info['expected'])
    assert len({c['url'] for c in cards}) == len(cards), 'Duplicate source URLs'
    category = ('Advanced' if info['name'].startswith('Advanced') else
                'Basic' if info['name'].startswith('Basic') else 'Common Words')
    # Preserve the original package's contents; new Advanced and combined exports
    # contain vocabulary rather than the site's interspersed promotional cards.
    if args.all or args.advanced:
        cards = [c for c in cards if not c['word'].startswith('Magoosh')]
    index = 1 + sum(1 for d in decks if f'::{category}::' in d.name)
    name = f"Magoosh GRE::{category}::{index:02d} - {info['name']}"
    deck = genanki.Deck(stable_id(info['url']), name)
    deck.description = f"Vocabulary from {info['name']}, Magoosh GRE. Includes original definitions and examples. Source: {info['url']}"
    expected_counts[str(deck.deck_id)] = len(cards)
    for card in cards:
        assert card['word'] and card['senses']
        if not card['word'].startswith('Magoosh'):
            assert card['word'] in origins, ('Missing etymology', card['word'])
        senses_html = ''
        for sense in card['senses']:
            assert sense['definition'] and sense['example'], (card['word'],sense)
            senses_html += '<section class="sense"><div class="definition">' + sense['definitionHtml'] + '</div><div class="example">' + sense['exampleHtml'] + '</div></section>'
        fields = [html.escape(card['word']), senses_html, html.escape(info['name']), card['url'], origins.get(card['word'], {}).get('html', '')]
        note = genanki.Note(model=model, fields=fields,
            guid=genanki.guid_for('magoosh-gre',card['url']),
            tags=['Magoosh_GRE',category.replace(' ','_'),slug.replace('-','_')])
        deck.add_note(note)
        rows.append([name] + fields)
        all_cards.append({**card, 'deck': name, 'etymology': origins.get(card['word'])})
    decks.append(deck)

package_path = OUT / (stem + '.apkg')
genanki.Package(decks).write_to_file(str(package_path))
with (OUT / (stem + '.tsv')).open('w',newline='') as f:
    f.write('#separator:Tab\n#html:true\n#notetype:Magoosh GRE Vocabulary\n#deck column:1\n#columns:Deck\tWord\tSenses\tOriginalDeck\tSourceURL\tEtymology\n')
    csv.writer(f,delimiter='\t').writerows(rows)
(OUT / ('vocabulary' + suffix + '.json')).write_text(json.dumps({'source':manifest['source'],'extractedAt':manifest['extractedAt'],'cards':all_cards},ensure_ascii=False,indent=2))

# Verify the actual packaged SQLite database, rather than just input objects.
with tempfile.TemporaryDirectory() as temp:
    with zipfile.ZipFile(package_path) as z:
        assert z.testzip() is None
        z.extract('collection.anki2',temp)
        assert json.loads(z.read('media')) == {}
    db = sqlite3.connect(str(Path(temp)/'collection.anki2'))
    assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
    actual = {str(did):count for did,count in db.execute('select did,count(*) from cards group by did')}
    assert actual == expected_counts, (actual,expected_counts)
    assert db.execute('select count(*) from notes').fetchone()[0] == len(rows)
    assert db.execute('select count(distinct guid) from notes').fetchone()[0] == len(rows)
    assert db.execute('select count(*) from cards where type != 0 or queue != 0').fetchone()[0] == 0
    for (fields,) in db.execute('select flds from notes'):
        assert len(fields.split('\x1f')) == 5 and all(fields.split('\x1f')[:4])
    db.close()

preview = rows[0]
preview_front = front.replace('{{OriginalDeck}}',preview[3]).replace('{{Word}}',preview[1])
preview_back = back.replace('{{FrontSide}}',preview_front).replace('{{Senses}}',preview[2]).replace('{{SourceURL}}',preview[4]).replace('{{#Etymology}}','').replace('{{/Etymology}}','').replace('{{Etymology}}',preview[5])
(OUT / ('card-preview' + suffix + '.html')).write_text('<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Anki card preview</title><style>'+CSS+'</style><body class="card">'+preview_back+'</body></html>')
report = {'notes':len(rows),'cards':len(rows),'vocabularyWithEtymology':sum(bool(r[5]) for r in rows),'leafSubdecks':len(decks),'mediaRequired':False,'validation':'passed','decks':[{'name':d.name,'cards':len(d.notes)} for d in decks]}
(OUT / ('validation' + suffix + '.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print('Created',package_path)
