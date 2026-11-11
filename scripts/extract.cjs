const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const BASE = 'https://gre.magoosh.com/flashcards/vocabulary/decks';
const delay = ms => new Promise(r => setTimeout(r,ms));
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
 const listing=await browser.newPage();
 await listing.goto(BASE,{waitUntil:'domcontentloaded'});
 const decks=await listing.locator('a').evaluateAll(as=>as.filter(a=>/words mastered/.test(a.innerText)).map(a=>({name:a.innerText.split('\n')[0].trim(),expected:Number(a.innerText.match(/of (\d+) words/)[1]),url:a.href})));
 const advanced=process.argv.includes('--advanced');
 const end=decks.findIndex(d=>d.name==='Basic IX');
 if(end<0)throw Error('Basic IX not found');
 const selected=advanced?decks.filter(d=>/^Advanced /.test(d.name)):decks.slice(0,end+1);
 if(advanced&&selected.length!==9)throw Error('Expected nine Advanced decks');
 fs.writeFileSync(advanced?'data/manifest-advanced.json':'data/manifest.json',JSON.stringify({source:BASE,extractedAt:new Date().toISOString(),decks:selected},null,2));
 await listing.close();
 let next=0;
 async function worker(){
 while(next<selected.length){
 const deck=selected[next++];
 const filename=path.join('data',new URL(deck.url).pathname.split('/').pop()+'.json');
 if(fs.existsSync(filename)&&JSON.parse(fs.readFileSync(filename)).cards.length===deck.expected){console.log('CACHED',deck.name);continue;}
 const context=await browser.newContext(); // Anonymous, isolated progress; never touches an existing login.
 await context.route('**/*',route=>{
 const req=route.request(),url=new URL(req.url());
 if(['image','font','media'].includes(req.resourceType())||!/magoosh\.com$|cloudfront\.net$/.test(url.hostname))return route.abort();
 return route.continue();
 });
 const page=await context.newPage();
 await page.goto(deck.url,{waitUntil:'domcontentloaded'});
 const saved=fs.existsSync(filename)?JSON.parse(fs.readFileSync(filename)).cards:[];
 const cards=new Map(saved.map(c=>[c.url,c]));let steps=0;
 while(cards.size<deck.expected){
 await page.waitForFunction(()=>document.querySelectorAll('.flashcard').length===1);
 const card=await page.locator('.back .flashcard-content').evaluate(el=>{
 const word=el.querySelector('.flashcard-word').textContent.trim();
 const senses=[];
 for(const child of el.children){
 if(child.classList.contains('flashcard-text'))senses.push({definitionHtml:child.innerHTML,definition:child.textContent.trim(),exampleHtml:'',example:''});
 else if(child.classList.contains('flashcard-example')){
 if(!senses.length)throw Error('Example without definition');
 senses[senses.length-1].exampleHtml=child.innerHTML;senses[senses.length-1].example=child.textContent.trim();
 }
 }
 return {word,senses:senses.filter(s=>s.definition)};
 });
 card.url=page.url().split('#')[0];
 if(!card.word||!card.senses.length||card.senses.some(s=>!s.definition))throw Error('Empty card '+JSON.stringify(card));
 cards.set(card.url,card);
 fs.writeFileSync(filename,JSON.stringify({...deck,cards:[...cards.values()]},null,2));
 if(cards.size%10===0||cards.size===deck.expected)console.log(`${deck.name}: ${cards.size}/${deck.expected} (${steps} advances)`);
 if(cards.size===deck.expected)break;
 if(++steps>deck.expected*8)throw Error('Too many repeats '+deck.name);
 const before=page.url();
 await page.locator('.front .card-footer').click();
 await page.locator('.back .card-footer-success').click();
 await page.waitForFunction(before=>location.href!==before,before,{timeout:30000});
 await delay(200);
 }
 await context.close();
 }
 }
 await Promise.all([worker(),worker()]);
 console.log('COMPLETE',selected.reduce((n,d)=>n+d.expected,0),'cards across',selected.length,'decks');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
