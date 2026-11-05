import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload();page.evaluate('validate(project)')
 assert page.evaluate('project.version')==6
 page.locator('#cadetName').fill('Алексей');page.get_by_text('Начать историю →',exact=True).click();assert page.locator('#titleView').inner_text()=='Вступление'
 # Finish authored introduction.
 while page.get_by_text('Далее →',exact=True).count():page.get_by_text('Далее →',exact=True).click()
 page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click()
 # All six biography answers award +1; concentrate points to prove no +2 ceiling.
 for key in ['watch','family','career','ties','dream','ambition']:
  assert page.evaluate('current().bioKey')==key
  page.evaluate("current().choices[0].bonus='study';render()")
  page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click()
 assert page.evaluate('game.stats.study')==6
 assert page.evaluate('current().special')=='prologueStats'
 assert 'Характеристики после пролога' in page.locator('#prose').inner_text()
 assert page.locator('.score-row').filter(has_text='Учёба и тактика').inner_text().endswith('6')
 page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('game.scene')=='speech'
 saved=page.evaluate('JSON.stringify(game)')
 # Rich text toolbar & safe render.
 page.evaluate('selected=game.scene;editor();startTest()')
 area=page.locator('#step-editor-0 textarea').first;area.fill('Новый текст');area.evaluate('(n)=>{n.focus();n.setSelectionRange(0,5)}')
 page.locator('#step-editor-0').get_by_role('button',name='Жирный',exact=True).first.click()
 assert area.input_value()=='**Новый** текст'
 assert page.locator('#prose strong').inner_text()=='Новый'
 page.evaluate("rich(document.getElementById('prose'),'__линия__ *курсив* <img src=x onerror=alert(1)>')")
 assert page.locator('#prose u').inner_text()=='линия';assert page.locator('#prose em').inner_text()=='курсив';assert page.locator('#prose img').count()==0
 # Forced dice outcomes use classes, replay doesn't double-award.
 page.evaluate("test.step=current().steps.length-1;let c=current().choices[0];c.check='study';c.dc=10;c.effect={stats:{study:1}};render()")
 page.locator('#forcedRoll').select_option('1');page.locator('#choices .choice').first.click();assert page.locator('#result').evaluate('(n)=>n.classList.contains("roll-fail")')
 page.get_by_text('Переиграть выбор',exact=True).click();assert page.evaluate('test.stats.study')==6
 page.locator('#forcedRoll').select_option('20');page.locator('#choices .choice').first.click();assert page.locator('#result').evaluate('(n)=>n.classList.contains("roll-success")')
 assert page.evaluate('JSON.stringify(game)')==saved
 # Export actual played history, not all branches.
 page.locator('#exitTest').click()
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.get_by_text('Скачать историю (.txt)',exact=True).click()
 txt=open(d.value.path()).read();assert 'Алексей' in txt and 'Вступление' in txt and 'После пролога' in txt and 'Учёба и тактика: 6' in txt
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.get_by_text('Скачать историю (.html)',exact=True).click()
 html=open(d.value.path()).read();assert '<html lang="ru">' in html and 'Алексей' in html
 # Map ordering and real edge editing.
 page.get_by_text('Карта сцен и реплик',exact=True).click();page.locator('#mapEdit > summary').click()
 old=page.evaluate('project.scenes.indexOf(editing())')
 page.get_by_text('↑ Раньше на карте',exact=True).click();assert page.evaluate('project.scenes.indexOf(editing())')==old-1
 page.get_by_text('Сделать стартом игры',exact=True).click();assert page.evaluate('project.startScene')=='speech'
 selects=page.locator('#mapEditFields select');selects.nth(0).select_option('0|next');selects.nth(1).select_option('barracks');page.get_by_text('Применить переход',exact=True).click();assert page.evaluate('editing().choices[0].next')=='barracks'
 # Resize via keyboard persists.
 page.locator('#closeMap').click();width=page.locator('#editorV2').evaluate('(n)=>n.getBoundingClientRect().width')
 page.locator('#editorResize').focus();page.locator('#editorResize').press('ArrowRight');assert page.locator('#editorV2').evaluate('(n)=>n.getBoundingClientRect().width')==width+20
 # Discipline detour still returns to the interrupted path.
 page.evaluate("selected='speech';startTest();test.step=current().steps.length-1;current().choices[0].check='';current().choices[0].effect={discipline:1};render()")
 page.locator('#choices .choice').first.click();assert page.evaluate('test.outcome.next')=='__manure'
 page.get_by_text('Продолжить →',exact=True).click();page.locator('#choices .choice').first.click();assert page.evaluate('test.manureTimes')==1
 page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('test.scene')=='barracks'
 # Final skill sheet.
 page.evaluate("test=JSON.parse(JSON.stringify(game));test.scene='__ending';test.step=0;test.outcome=null;render()")
 assert 'Характеристики после первого курса' in page.locator('#prose').inner_text()
 # Older imports get uncapped bonuses + post-prologue stats scene.
 assert page.evaluate("(()=>{const p=clone(project);p.version=3;p.scenes=p.scenes.filter(s=>s.special!=='prologueStats');for(const s of p.scenes)if(s.bioKey)for(const c of s.choices){delete c.bonus;if(c.next==='__prologue_stats')c.next='speech'}const m=migrate(p);validate(m);return m.scenes.filter(s=>s.bioKey).every(s=>s.choices.every(c=>c.bonus))&&m.scenes.some(s=>s.special==='prologueStats')})()")
 assert not errors,errors
 page.screenshot(path='/workspace/bdenie/preview.png',full_page=True)
 print('PASS: name + authored intro; six uncapped bonuses; prologue/final stats; rich toolbar + XSS safety; dice colors/replay; actual story TXT/HTML exports; map order/start/edge editing; resizable editor; old import migration; no JS errors')
 b.close()
