# Magoosh GRE vocabulary for Anki

An unofficial Anki conversion of [Magoosh's GRE vocabulary flashcards](https://gre.magoosh.com/flashcards/vocabulary/decks), with definitions, examples, source links, and sourced etymology. Each word has one card; the **Word origin** section is collapsed below the answer so the definition stays easy to scan.

## Install

1. Install [Anki](https://apps.ankiweb.net/).
2. Download an `.apkg` from the [latest release](https://github.com/JDY-exe/magoosh-gre-anki/releases/latest):

   | Package | Vocabulary | Study subdecks |
   | --- | ---: | ---: |
   | [All levels — recommended](https://github.com/JDY-exe/magoosh-gre-anki/releases/latest/download/Magoosh_GRE_All_Levels.apkg) | 1,251 | 25 |
   | [Advanced I–IX only](https://github.com/JDY-exe/magoosh-gre-anki/releases/latest/download/Magoosh_GRE_Advanced.apkg) | 451 | 9 |
   | [Original Common + Basic I–IX](https://github.com/JDY-exe/magoosh-gre-anki/releases/latest/download/Magoosh_GRE_through_Basic_IX.apkg) | 800 | 16 |

3. In Anki, choose **File → Import** and select the downloaded file. The subdecks appear under **Magoosh GRE**.

If you already use the original deck, import **Advanced only** to add the new vocabulary. The original package retains seven source promotional cards; the Advanced and All Levels packages contain vocabulary only. All packages include etymology and the revised styling, with no recall prompt. They contain fresh cards and no personal study history.

## Build locally

Requires Node.js and Python 3.9+. The extracted data and reviewed origins are included, so rebuilding needs no AnkiConnect session or new scraping:

```sh
npm ci
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm run build
npm run build:advanced
npm run build:all
```

Packages are written to `output/`. Builds verify the packaged database, card counts, unique notes, fields, and fresh-card status. Vocabulary note GUIDs and deck IDs are stable across packages.

To refresh Magoosh data, install the local browser with `npx playwright install chromium`, then run `npm run extract` and/or `npm run extract:advanced`. Playwright runs on your own computer in anonymous sessions, checks each deck's advertised count, and reuses complete cached decks. Etymology lookup and review tools are in `scripts/`; reviewed spelling, base-word, and meaning choices are recorded in `data/etymology-overrides.json`. Review new origins before running `npm run compile:all` and rebuilding.

## Attribution

Definitions and examples are from Magoosh; each card links to its source. Etymology excerpts and adaptations are attributed to [Wiktionary contributors](https://en.wiktionary.org/), linked to their entries, and licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Adapted wording is labeled on the cards. This project is not affiliated with Magoosh or Anki.
