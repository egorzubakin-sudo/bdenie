import json,tempfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload();page.evaluate('validate(project)');assert page.evaluate('project.version')==6
 assert page.evaluate('project.scenes.filter(s=>s.course===2).length')==17
 assert page.evaluate("project.scenes.find(s=>s.id==='speech').steps.length")>=3
 # Version 5 migration appends dialogue and missions while preserving author text/branches/media.
 assert page.evaluate("""(()=>{const p=clone(project);p.version=5;delete p.edition6;const source=p.scenes.find(s=>s.id==='speech');const image=p.assets[source.background.slice(6)].data;source.title='Авторская речь';source.steps=source.steps.filter(s=>!s.addition6);source.steps.push({speaker:'Автор',text:'Моя реплика'});for(const sc of p.scenes)for(const o of [sc,...sc.steps,...sc.choices])for(const k of ['image','background','sprite'])if(o[k]?.startsWith('asset:'))o[k]=p.assets[o[k].slice(6)].data;delete p.assets;delete p.characters;delete p.rewards;delete p.trials;p.scenes=p.scenes.filter(s=>s.id!=='y2_archive'&&!s.id.startsWith('y6_'));for(const sc of p.scenes)for(const c of sc.choices){if(c.next==='y2_archive')c.next='y2_festival';if(c.next==='y6_beacon')c.next='y2_attestation'}p.scenes.find(s=>s.id==='y2_letter').choices[0].next='speech';const q=migrate(p);validate(q);const sc=q.scenes.find(s=>s.id==='speech');return sc.title==='Авторская речь'&&sc.steps.some(s=>s.text==='Моя реплика')&&sc.steps.filter(s=>s.addition6).length===2&&q.assets[sc.background.slice(6)].data===image&&q.scenes.find(s=>s.id==='y2_letter').choices[0].next==='speech'&&q.scenes.filter(s=>s.course===2).length===17})()""")
 # Reusable image/folder library: two unique files and a repeated file only add two entries.
 base=page.evaluate('Object.keys(project.assets).length')
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);Image.new('RGB',(60,80),'red').save(root/'red.png');Image.new('RGB',(60,80),'blue').save(root/'blue.png');(root/'repeat.png').write_bytes((root/'red.png').read_bytes());(root/'note.txt').write_text('ignore')
  page.locator('#libraryOpen').click();page.locator('#libraryFolder').set_input_files(folder)
  page.wait_for_function('(base)=>Object.keys(project.assets).length===base+2',arg=base)
  assert page.locator('#libraryGrid .asset-card').count()==base+2
  page.locator('[data-close=libraryDialog]').click()
 # Choose same library item for two fields; do not duplicate its data.
 page.evaluate("selected=project.startScene;editor()")
 for key in ['image','background']:
  page.evaluate('(key)=>openLibrary(editing().steps[0],key)',key)
  page.locator('#librarySearch').fill('blue.png');page.locator('#libraryGrid .asset-card').get_by_text('Выбрать',exact=True).click()
 assert page.evaluate('editing().steps[0].image===editing().steps[0].background')
 assert page.evaluate('Object.keys(project.assets).length')==base+2
 page.locator('#libraryOpen').click();page.locator('#librarySearch').fill('blue.png');assert page.locator('#libraryGrid .asset-card').get_by_text('Удалить',exact=True).is_disabled();page.locator('[data-close=libraryDialog]').click()
 page.reload();page.evaluate('validate(project)');assert page.evaluate('assetData(editing().steps[0].image).startsWith("data:image/png")')
 # Named slots restore gameplay and can undo a mistaken load; project remains intact.
 page.locator('#cadetName').fill('Елена');page.get_by_text('Начать историю →',exact=True).click()
 page.evaluate('game.stats.study=3;game.flags.slotFlag=true;render()')
 page.locator('#slotsOpen').click();first=page.locator('#slotsList .slot-card').nth(0);first.locator('input').fill('Перед дорогой');first.get_by_text('Сохранить',exact=True).click()
 page.evaluate('game.stats.study=9;game.flags.slotFlag=false;render()');first.get_by_text('Загрузить',exact=True).click();assert page.evaluate('game.stats.study')==3 and page.evaluate('game.flags.slotFlag')
 page.locator('#undoSlotLoad').click();assert page.evaluate('game.stats.study')==9 and not page.evaluate('game.flags.slotFlag')
 first.get_by_text('Загрузить',exact=True).click();page.locator('[data-close=slotsDialog]').click();page.reload();assert page.evaluate('game.stats.study')==3
 page.locator('#slotsOpen').click();assert first.locator('input').input_value()=='Перед дорогой';page.locator('[data-close=slotsDialog]').click()
 # Real skill and relationship consequences produce character memories; replay removes them.
 page.evaluate("selected='speech';startTest();test.step=current().steps.length-1;render()")
 page.locator('#choices .choice').first.click();page.locator('#friendsOpen').click();assert 'Внимательно слушать' in page.locator('#friendsList').inner_text()
 friend=page.locator('#friendsList .friend-card').first;friend.get_by_text('Редактировать карточку',exact=True).click();friend.locator('textarea').fill('**Верный товарищ**');assert friend.locator('p strong').inner_text()=='Верный товарищ'
 friend.get_by_text('Выбрать из библиотеки',exact=True).click();page.locator('#librarySearch').fill('blue.png');page.locator('#libraryGrid .asset-card').get_by_text('Выбрать',exact=True).click();assert page.locator('#friendsList .friend-card').first.locator('img').is_visible();page.locator('[data-close=friendsDialog]').click()
 page.get_by_text('Переиграть выбор',exact=True).click();assert page.evaluate('test.relationshipEvents.length')==0
 page.locator('#slotsOpen').click();assert page.locator('#slotsList .slot-card').first.get_by_text('Сохранить',exact=True).is_disabled();page.locator('[data-close=slotsDialog]').click()
 # Three-stage bridge trial: two successes earn reward; replay/second visits cannot farm it.
 def trial(start,dice,choice=0):
  page.evaluate('(id)=>{test={...fresh(),playerName:"Испытание",nameConfirmed:true,scene:id,step:0};render()}',start)
  for die in dice:
   page.evaluate('test.step=current().steps.length-1;render()');page.locator('#forcedRoll').select_option(str(die));page.locator('#choices .choice').nth(choice).click()
   if len(dice)>1 and page.evaluate('Boolean(test.outcome.next)') and page.evaluate('test.scene')!=('y6_bridge_extract' if start=='y6_bridge_plan' else 'y6_beacon_hold'):page.get_by_text('Продолжить →',exact=True).click()
 trial('y6_bridge_plan',[20,1,20]);assert page.evaluate('Boolean(test.rewards.bridge_badge)');assert page.evaluate('test.stats.initiative')==1
 page.get_by_text('Переиграть выбор',exact=True).click();assert not page.evaluate('Boolean(test.rewards.bridge_badge)') and page.evaluate('test.stats.initiative')==0
 page.locator('#choices .choice').first.click();assert page.evaluate('test.stats.initiative')==1
 page.evaluate('test.outcome=null;render()');page.locator('#choices .choice').first.click();assert page.evaluate('test.stats.initiative')==1
 trial('y6_bridge_plan',[1,1,20]);assert not page.evaluate('Boolean(test.rewards.bridge_badge)');assert 'обучение продолжается' in page.locator('#result').inner_text()
 trial('y6_beacon',[20,20]);assert page.evaluate('Boolean(test.rewards.beacon_badge)') and page.evaluate('test.stats.study')==1
 # Character cards, compact chronicle and rewards appear in the final and both history formats.
 page.evaluate("test.scene='y2_graduation';test.step=current().steps.length-1;test.outcome=null;render()")
 assert 'Хроника ключевых событий' in page.locator('#prose').inner_text() and 'Знак надёжной связи' in page.locator('#prose').inner_text()
 page.locator('#chronicleOpen').click();assert page.locator('#chronicleBody li').count()>0;page.locator('[data-close=chronicleDialog]').click()
 for id in ['historyTxt','historyHtml']:
  page.evaluate("document.getElementById('saveMenu').open=true")
  with page.expect_download() as d:page.locator('#'+id).click()
  content=Path(d.value.path()).read_text();assert ('ХРОНИКА' if id=='historyTxt' else 'Хроника') in content and 'Знак надёжной связи' in content
 # Larger type sizes and usable narrow-screen cards.
 page.evaluate("selected='speech';startTest();test.step=current().steps.length-1;render()")
 assert page.locator('#choices .choice').first.evaluate('n=>getComputedStyle(n).fontSize')=='24px'
 assert page.locator('#choices .choice').first.locator('small').first.evaluate('n=>getComputedStyle(n).fontSize')=='16px'
 page.set_viewport_size({'width':400,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.locator('#friendsOpen').click();assert page.locator('#friendsDialog').bounding_box()['width']<=400;page.locator('[data-close=friendsDialog]').click()
 # Asset/reward validation catches broken references and bad numeric consequences.
 assert page.evaluate("(()=>{const p=clone(project);p.scenes[0].steps[0].image='asset:missing';try{validate(p);return false}catch(e){return true}})()")
 assert page.evaluate("(()=>{const p=clone(project);p.rewards.bridge_badge.effect.stats.initiative='bad';try{validate(p);return false}catch(e){return true}})()")
 assert not errors,errors
 print('PASS: preserving 5→6 migration; folder library/dedup/references/persistence; named slots/load/undo; character memories; 3-stage and 2-stage rewards, failure and anti-farming; chronicle TXT/HTML; larger fonts/mobile; validation')
 b.close()
