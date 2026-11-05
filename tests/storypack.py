from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload();page.evaluate('validate(project)')
 assert page.evaluate('Object.keys(project.characters).length')==6
 assert page.evaluate('project.scenes.filter(s=>s.storyPack).length')==22
 page.evaluate("game={...fresh(),playerName:'Курсант',nameConfirmed:true,scene:'sp_free_early'};render()")
 names={'peoples':'народы мира','geography':'география','kingdom':'Бдение','eternity':'Вечность'}
 for key,name in names.items():
  while page.get_by_text('Далее →',exact=True).count():page.get_by_text('Далее →',exact=True).click()
  page.get_by_role('button',name='Узнать больше: '+name,exact=True).click();page.get_by_text('Продолжить →',exact=True).click()
  page.evaluate('game.step=current().steps.length-1;render()');page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click()
  assert page.evaluate('(key)=>game.flags["sp_know_"+key]',key)
  assert page.get_by_role('button',name='Узнать больше: '+name,exact=True).count()==0
 while page.get_by_text('Далее →',exact=True).count():page.get_by_text('Далее →',exact=True).click()
 page.get_by_role('button',name='Вернуться к обязательным занятиям',exact=True).click();page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('game.scene')=='march'
 for id in ['cav','eng','scout','tech','mage','drakh']:
  for n in [1,2]:
   page.evaluate('(id)=>{selected=id;startTest();test.step=current().steps.length-1;render()}',f'sp_friend_{id}{n}')
   prior=page.evaluate('(id)=>test.relations[id]||0',id);page.locator('#choices .choice').first.click();assert page.evaluate('(id)=>test.relations[id]',id)==prior+2
   page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('test.scene')==('sp_free_early' if n==1 else 'sp_free_late')
 for id,flag in [('y2_juniors','peoples'),('y6_bridge_plan','geography'),('y2_archive','kingdom'),('y6_beacon','eternity')]:
  page.evaluate('({id,flag})=>{selected=id;startTest();test.flags["sp_know_"+flag]=false;test.step=current().steps.length-1;render()}',{'id':id,'flag':flag})
  assert page.locator('#choices .choice').last.is_disabled()
  page.evaluate('(flag)=>{test.flags["sp_know_"+flag]=true;render()}',flag);assert page.locator('#choices .choice').last.is_enabled()
 for id in ['sp_spear','sp_lane','sp_simulator','sp_party']:
  page.evaluate('(id)=>{selected=id;startTest();test.step=current().steps.length-1;render()}',id)
  page.locator('#choices .choice').last.click();assert page.evaluate('test.outcome.next')=='__manure'
  page.get_by_text('Продолжить →',exact=True).click();assert page.locator('#choices .choice').count()==1
  assert page.locator('#choices .choice').inner_text()=='Молча разгружать тулоний навоз'
  page.locator('#choices .choice').click();page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('test.scene')=='sp_free_late'
 assert page.evaluate('sequenceAudit(project).warnings')==['Недостижима от старта: «F»']
 assert not errors,errors
 print('PASS: 22 optional scenes; 4 lore subjects open second-year solutions; two encounters for all six friends; all four drills/party detour to the single silent manure option and return; no broken paths')
 b.close()
