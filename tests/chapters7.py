from pathlib import Path
import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload();page.evaluate('validate(project)')
 assert page.evaluate('project.chapters.length')==6
 assert page.evaluate('project.scenes.filter(s=>s.chapterStory).length')==52
 assert page.evaluate('sequenceAudit(project).warnings')==[]
 assert page.locator('#randomBiography').is_disabled()
 page.locator('#cadetName').fill('Ирина');page.get_by_text('Начать историю →',exact=True).click();page.locator('#randomBiography').click()
 assert page.evaluate('game.scene')=='c7_profile';assert page.evaluate('Object.keys(game.bioChoice).length')==6
 assert page.evaluate('Object.values(game.stats).reduce((a,b)=>a+b,0)')==6
 assert page.evaluate('game.playerName')=='Ирина'
 assert page.locator('#prose li').count()==6
 assert page.get_by_text('Переиграть выбор',exact=True).count()==0
 # Full normal play: named chapters, direct choices, one companion selection, no replay/no Next.
 page.evaluate('Math.random=()=>0.99')
 seen=[];hangouts=0;guard=0;blocked=0
 while True:
  guard+=1;assert guard<70
  id=page.evaluate('game.scene');seen.append(id)
  assert page.get_by_text('Далее →',exact=True).count()==0
  assert page.get_by_text('Переиграть выбор',exact=True).count()==0
  if id=='c7_hangout':hangouts+=1
  choices=page.locator('#choices .choice');assert choices.count()>0
  disabled=choices.evaluate_all('ns=>ns.filter(n=>n.disabled).length');blocked+=disabled
  if id=='c7_arrival':idx=0
  elif id=='c7_lore':idx=2 # Public law and institutions.
  elif id=='c7_teacher':idx=0
  elif id=='c7_hangout':idx=4 # Mage, once.
  elif id=='c7_debrief':idx=3 # Teacher relationship chain.
  elif id=='c7_catchup':idx=3 # Continue old bond, not reselect.
  elif id=='c7_epilogue':idx=3
  else:idx=0
  if choices.nth(idx).is_disabled():idx=next(i for i in range(choices.count()) if not choices.nth(i).is_disabled())
  choices.nth(idx).click();assert page.evaluate('Boolean(game.outcome)')
  assert page.get_by_text('Переиграть выбор',exact=True).count()==0
  assert not page.locator('#prose').is_visible()
  if id=='c7_epilogue':break
  page.get_by_text('Продолжить →',exact=True).click()
 assert hangouts==1 and len(set(seen))==len(seen)
 assert page.evaluate('game.flags.c7_bond_mage') and page.evaluate('game.flags.c7_hangout_spent')
 assert 'c7_friend_mage2' in seen and 'c7_spear' in seen and 'c7_party' in seen and 'c7_lane' in seen
 assert 'c7_year_report' in seen and 'c7_muster' in seen
 assert page.evaluate('game.flags.c7_mentor')
 assert blocked>0
 assert 'Последнее задание впереди' in page.locator('#choices').inner_text()
 # Reload preserves the committed ending.
 page.reload();assert page.evaluate('game.scene')=='c7_epilogue' and page.evaluate('Boolean(game.outcome)')
 # All six companions resolve to their own later encounter.
 for npc in ['cav','eng','scout','tech','mage','drakh']:
  page.evaluate('(npc)=>{test={...fresh(),playerName:"Тест",nameConfirmed:true,chapterRun:7,scene:"c7_catchup",flags:{c7_hangout_spent:true,c7_bond_ready:true,["c7_bond_"+npc]:true}};render()}',npc)
  page.locator('#choices .choice').nth(3).click();assert page.evaluate('test.outcome.next')=='c7_friend_'+npc+'2'
 # Prior event and relationship both gate the mentor chain.
 page.evaluate("test={...fresh(),playerName:'Тест',nameConfirmed:true,chapterRun:7,scene:'c7_debrief',flags:{c7_checked_order:true},relations:{tactics:0}};render()")
 assert page.locator('#choices .choice').nth(3).is_disabled()
 page.evaluate('test.relations.tactics=2;render()');assert page.locator('#choices .choice').nth(3).is_enabled()
 # New prologue has no mandatory dialogue advances; manual path still gives exactly six awards.
 page.evaluate("game={...fresh(),playerName:'Ручной',nameConfirmed:true,chapterRun:7};test=null;render()")
 for key in ['watch','family','career','ties','dream','ambition']:
  assert page.evaluate('current().bioKey')==key
  page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click()
 assert page.evaluate('game.scene')=='c7_profile';assert page.evaluate('Object.values(game.stats).reduce((a,b)=>a+b,0)')==6
 # Original drafts remain recoverable, without polluting active route map.
 assert page.evaluate('project.scenes.some(s=>s.archived&&s.id==="speech")')
 page.evaluate("selected='c7_arrival';editor()")
 page.get_by_text('Карта сцен и реплик',exact=True).click();assert page.locator('#storyMap .node').count()==54 # 52 + punishment + return marker.
 # Public canon only: future GM campaign mysteries are not embedded in playable HTML.
 text=Path('/workspace/bdenie/index.html').read_text()
 for forbidden in ['Костяная тропа','Архитектор Тропы','тайно строит по морскому дну']:
  assert forbidden not in text,forbidden
 assert not errors,errors
 print('PASS: six chapters, random/manual biography, complete normal route, 1 irreversible bond, direct choice/consequence scenes, normal training, mentor gates, six later bond branches, committed reload, archive, public lore only')
 b.close()
