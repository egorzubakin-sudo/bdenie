from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload();page.evaluate("game.playerName='База';game.nameConfirmed=true;render()")
 baseline=page.evaluate('JSON.stringify(game)');scenes=page.evaluate('project.scenes.filter(s=>!s.archived).map(s=>({id:s.id,count:s.choices.length}))');runs=0
 for sc in scenes:
  for i in range(sc['count']):
   for die in [1,20]:
    page.evaluate('''({id,i,die})=>{test={...fresh(),nameConfirmed:true,playerName:'Проверка',chapterRun:7,scene:id,resumeScene:'c7_spear'};test.flags.c7_bond_cav=true;test.flags.c7_bond_ready=true;test.flags.c7_hangout_spent=true;const c=current().choices[i];for(const a of c.conditions||[]){if(a.kind==='flags')test.flags[a.key]=a.value;else test[a.kind][a.key]=a.value}render();document.getElementById('forcedRoll').value=String(die)}''',{'id':sc['id'],'i':i,'die':die})
    state=page.evaluate('({stats:structuredClone(test.stats),relations:structuredClone(test.relations),flags:structuredClone(test.flags),discipline:test.discipline,log:test.log.length})')
    page.evaluate('(i)=>choose(i)',i);out=page.evaluate('test.outcome');assert out,(sc,i,die)
    assert not out['next'] or page.evaluate('(id)=>project.scenes.some(s=>s.id===id&&!s.archived)',out['next']),(sc,i,die,out)
    page.get_by_text('Переиграть выбор',exact=True).click();after=page.evaluate('({stats:test.stats,relations:test.relations,flags:test.flags,discipline:test.discipline,log:test.log.length})');assert state==after,(sc,i,die)
    assert page.evaluate('JSON.stringify(game)')==baseline
    runs+=1
 # An unfriendly/no-knowledge route remains playable to the same unexpected posting.
 page.evaluate("test=null;game={...fresh(),playerName:'Упрямый',nameConfirmed:true,chapterRun:7,scene:'c7_arrival'};Math.random=()=>0;render()")
 chosen_bond=0;guard=0
 while True:
  guard+=1;assert guard<80
  id=page.evaluate('game.scene');buttons=page.locator('#choices .choice');assert buttons.count()>0
  if id=='c7_lore':idx=0
  elif id=='c7_lore_peoples':idx=3
  elif id=='c7_teacher':idx=1
  elif id=='c7_hangout':idx=5;chosen_bond+=1
  elif id=='c7_friend_drakh1':idx=3
  elif id=='c7_catchup':
   assert buttons.nth(3).is_disabled();idx=0
  elif id=='c7_law':idx=2
  elif id=='c7_epilogue':
   assert buttons.nth(3).is_disabled();idx=2
  else:idx=next(i for i in range(buttons.count()) if not buttons.nth(i).is_disabled())
  buttons.nth(idx).click();assert page.get_by_text('Переиграть выбор',exact=True).count()==0
  if id=='c7_epilogue':break
  page.get_by_text('Продолжить →',exact=True).click()
 assert chosen_bond==1 and page.evaluate('game.discipline')>0
 assert not page.evaluate('Boolean(game.flags.c7_mentor)')
 assert not errors,errors
 print(f'PASS: {runs} active choice/die combinations; valid non-archive targets; exact stat/flag/relation rollback in tests; untouched main game; unfriendly failure route reaches epilogue without a dead end')
 b.close()
