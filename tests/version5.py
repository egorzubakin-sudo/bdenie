import json
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload()
 assert page.evaluate('project.version')==5
 page.evaluate('validate(project)');assert page.evaluate('project.scenes.filter(s=>s.course===2).length')==11
 # Old edition migration preserves author edits/assets and only fills missing practice awards.
 prev=page.evaluate('clone(project)');prev['version']=4;prev.pop('edition5',None);prev['scenes']=[sc for sc in prev['scenes'] if sc.get('course')!=2]
 for sc in prev['scenes']:
  if sc['id']=='__ending':sc['choices']=[]
  for c in sc['choices']:
   if c.pop('practice5',False):c.get('effect',{}).pop('stats',None)
 result=page.evaluate("""p=>{p.scenes.find(s=>s.id==='speech').title='Авторская речь';p.scenes.find(s=>s.id==='tenth').choices[0].effect.stats={combat:3};const q=migrate(p);validate(q);return{title:q.scenes.find(s=>s.id==='speech').title,skill:q.scenes.find(s=>s.id==='tenth').choices[0].effect.stats.combat,year2:q.scenes.filter(s=>s.course===2).length,background:q.scenes.find(s=>s.id==='speech').background,version:q.version}}""",prev)
 assert result['title']=='Авторская речь' and result['skill']==3 and result['year2']==11 and result['version']==5
 assert result['background']==next(sc for sc in prev['scenes'] if sc['id']=='speech').get('background')
 assert page.evaluate("(()=>{const p=clone(project);p.scenes=p.scenes.filter(s=>s.id!=='y2_workshop');return !migrate(p).scenes.some(s=>s.id==='y2_workshop')})()")
 page.locator('#cadetName').fill('Старший курсант');page.get_by_text('Начать историю →',exact=True).click()
 # Long-text editor has a draft boundary, preview and keyboard formatting.
 field=page.locator('#step-editor-0 textarea').first;before=field.input_value()
 page.locator('#step-editor-0').get_by_text('Развернуть текст',exact=True).first.click();assert page.locator('#writerDialog').is_visible()
 page.locator('#writerText').fill('Черновик, который отменим');page.locator('#writerCancel').click();assert field.input_value()==before
 page.locator('#step-editor-0').get_by_text('Развернуть текст',exact=True).first.click();page.locator('#writerText').fill('Новый разговор')
 page.locator('#writerText').evaluate('(n)=>n.setSelectionRange(0,5)');page.locator('#writerText').press('Control+b')
 assert page.locator('#writerPreview strong').inner_text()=='Новый'
 page.locator('#writerApply').click();assert field.input_value()=='**Новый** разговор'
 page.wait_for_timeout(750);page.get_by_text('Отменить',exact=True).click();assert page.locator('#step-editor-0 textarea').first.input_value()==before
 # No audio is created without the player clicking. Music can be toggled repeatedly.
 assert page.evaluate('musicEngine.context===null')
 page.locator('#musicMenu summary').click();page.locator('#musicToggle').click()
 page.wait_for_function('musicEngine.playing&&musicEngine.context.state==="running"');assert page.evaluate('musicEngine.nodes.size')>0
 page.locator('#musicVolume').fill('40');assert page.locator('#volumeValue').inner_text()=='40%'
 page.locator('#musicToggle').click();page.wait_for_timeout(450);assert page.evaluate('musicEngine.nodes.size')==0
 assert page.evaluate('musicEngine.timer===null')
 page.locator('#musicToggle').click();page.wait_for_function('musicEngine.playing');page.locator('#musicToggle').click()
 # Reduced motion removes animation while keeping choices fully usable.
 page.evaluate("test={...fresh(),playerName:'Тест',nameConfirmed:true,scene:'speech',step:0};render()")
 page.emulate_media(reduced_motion='reduce');assert page.locator('#choices .choice').first.evaluate('n=>getComputedStyle(n).transitionDuration')=='0s'
 page.emulate_media(reduced_motion='no-preference')
 # Peaceful practice is awarded once; replay returns it to baseline.
 page.evaluate("selected='tenth';startTest();test.step=current().steps.length-1;render()")
 prior=page.evaluate('test.stats.study');page.locator('#choices .choice').first.click();assert page.evaluate('test.stats.study')==prior+1
 page.get_by_text('Переиграть выбор',exact=True).click();assert page.evaluate('test.stats.study')==prior
 # Play the complete second year through both social routes, no direct scene jumps.
 for route in [0,1]:
  page.evaluate("selected='__ending';startTest();test.step=current().steps.length-1;render()")
  assert page.evaluate('current().special')=='ending';page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click()
  visited=[];guard=0
  while page.evaluate('current().special')!='graduation' or page.get_by_text('Далее →',exact=True).count():
   guard+=1;assert guard<80
   if page.get_by_text('Далее →',exact=True).count():page.get_by_text('Далее →',exact=True).click();continue
   id=page.evaluate('test.scene');visited.append(id)
   if id=='y2_clubs':idx=route
   elif id=='y2_workshop':idx=1 # Deliberately choose the peaceful, trusting route.
   else:idx=0
   page.locator('#choices .choice').nth(idx).click();page.get_by_text('Продолжить →',exact=True).click()
  assert page.evaluate('test.scene')=='y2_graduation'
  assert ('y2_workshop' if route==0 else 'y2_rooftop') in visited
  assert 'Характеристики после второго курса' in page.locator('#prose').inner_text()
  assert page.evaluate('test.flags.y2_letters_promise')
  assert 'Первое общее письмо писать вам' in page.locator('#prose').inner_text()
  assert page.evaluate('test.story.filter(e=>e.type==="stats"&&e.key==="graduation").length')==1
  page.locator('#saveMenu summary').click()
  with page.expect_download() as d:page.locator('#dossierExport').click()
  assert 'ИТОГИ ВТОРОГО КУРСА' in Path(d.value.path()).read_text()
  page.locator('#saveMenu summary').click()
 assert page.evaluate('game.scene')==page.evaluate('project.startScene')
 report=page.evaluate('sequenceAudit(project)');assert not any('Нет пути к завершению' in t for t in report['warnings'])
 # Mobile writing dialog fits the viewport and keeps Apply reachable.
 page.set_viewport_size({'width':500,'height':900});page.locator('#step-editor-0').get_by_text('Развернуть текст',exact=True).first.click();assert page.locator('#writerApply').is_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('#writerCancel').click()
 assert not errors,errors
 page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path='/workspace/bdenie/version5-preview.png',full_page=True)
 print('PASS: safe 4→5 migration; 11 social scenes; draft/apply/undo text editor and mobile; local music on/off/volume; reduced-motion animation; peaceful skill/replay; both second-year routes to graduation, relationship flags, stats and dossier export')
 b.close()
