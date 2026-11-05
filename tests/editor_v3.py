import json,base64,io
from PIL import Image
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload()
 assert page.evaluate('project.version')==4
 page.evaluate("game.scene='bio_watch';game.playerName='Тест';game.nameConfirmed=true;selected='bio_watch';editor();render()")
 assert 'Древняя столица Бдения' in page.locator('#choices .choice').first.inner_text()
 cards=page.locator('.answer-card');assert cards.count()==10
 cards.nth(1).locator('summary').first.click();desc=cards.nth(1).locator('textarea').first;desc.fill('Город воды и мастеров')
 assert 'Город воды и мастеров' in page.locator('#choices .choice').nth(1).inner_text()
 cards.nth(1).get_by_text('↑ Поднять ответ',exact=True).click()
 assert page.evaluate('editing().choices[0].label')=='Чёрная Башня'
 cards.nth(0).get_by_text('Дублировать ответ',exact=True).click();assert cards.count()==11
 assert page.evaluate('editing().choices[1].hint')=='Город воды и мастеров'
 page.wait_for_timeout(750);page.get_by_text('Отменить',exact=True).click();assert cards.count()==10
 # Test crop with actual raster image.
 buf=io.BytesIO();Image.new('RGB',(800,300),(170,80,35)).save(buf,format='PNG');png='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
 page.evaluate('(src)=>{editing().background=src;editor();startTest()}',png)
 crop=page.locator('#editorV2 > .crop-controls');crop.locator('summary').click()
 crop.locator('[data-frame=x]').fill('25');crop.locator('[data-frame=y]').fill('75');crop.locator('[data-frame=zoom]').fill('1.5')
 assert page.locator('#bg').evaluate('(n)=>n.style.objectPosition')=='25% 75%'
 assert page.locator('#bg').evaluate('(n)=>n.style.transform')=='scale(1.5)'
 crop.locator('select').select_option('contain');assert page.locator('#bg').evaluate('(n)=>n.style.objectFit')=='contain'
 # Scene frame inherited; step override then reset.
 step=page.locator('#step-editor-0');# Art controls are visible without expanding a details panel.
 sc=step.locator('.crop-controls');sc.locator('summary').click();sc.locator('[data-frame=x]').fill('80')
 assert page.evaluate('editing().backgroundFrame.x')==25
 assert page.evaluate('editing().steps[0].backgroundFrame.x')==80
 assert page.locator('#bg').evaluate('(n)=>n.style.objectPosition')=='80% 75%'
 sc.get_by_text('Наследовать кадр сцены',exact=True).click();assert page.locator('#bg').evaluate('(n)=>n.style.objectPosition')=='25% 75%'
 # Preserve on reload and old v2 migration, invalid import rejected.
 page.reload();assert page.evaluate("project.scenes.find(s=>s.id==='bio_watch').backgroundFrame.zoom")==1.5
 assert page.evaluate("(()=>{const p=clone(project);p.version=2;delete p.scenes[0].choices[0].hint;const q=migrate(p);validate(q);return q.version===4&&q.scenes[0].choices[0].hint.length>0})()")
 assert page.evaluate("(()=>{const p=clone(project);p.scenes[0].backgroundFrame.zoom=10;try{validate(p);return false}catch(e){return true}})()")
 page.get_by_text('Карта сцен и реплик',exact=True).click();page.locator('#mapSearch').fill('Город воды и мастеров');assert page.locator('.search-match').count()==1
 assert 'Найдено: 1' in page.locator('#mapSearchCount').inner_text()
 page.locator('#mapSearch').press('Enter');assert page.locator('.search-match').evaluate('(n)=>n===document.activeElement')
 page.locator('#mapSearch').fill('несуществующий текст');assert 'Найдено: 0' in page.locator('#mapSearchCount').inner_text()
 page.locator('#mapSearch').fill('');page.locator('#mapScope').select_option('dialogue')
 page.locator('#storyMap .node[aria-label="Чёрная Башня"]').first.click();assert page.locator('#answer-editor-0').evaluate('(n)=>n.open')
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.locator('#export').click()
 data=json.load(open(d.value.path()));assert data['version']==4 and data['scenes'][0]['backgroundFrame']['x']==25
 page.locator('#closeMap').click();page.screenshot(path='/workspace/bdenie/preview.png',full_page=True)
 assert not errors,errors
 print('PASS: descriptions, preserved hints, collapsed cards, reorder, duplicate, undo, scene crop, step override/inheritance, persistence, v2 migration, frame validation, map search and keyboard navigation, card navigation, export')
 b.close()
