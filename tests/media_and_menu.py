import io,json
from PIL import Image
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload()
 for width in [1440,500]:
  page.set_viewport_size({'width':width,'height':1000})
  lab=page.locator('.name-start label').bounding_box();inp=page.locator('#cadetName').bounding_box()
  assert lab['y']+lab['height']<=inp['y']
  assert page.locator('.story h2').evaluate("n=>getComputedStyle(n).fontFamily").startswith('Georgia')
  assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
 page.set_viewport_size({'width':1440,'height':1000})
 page.screenshot(path='/workspace/bdenie/name-screen.png',full_page=True)
 page.locator('#cadetName').fill('Курсант');page.get_by_text('Начать историю →',exact=True).click()
 assert page.locator('#choices .history-export').count()==0
 page.locator('#saveMenu summary').click();page.get_by_text('Сохранить в браузере',exact=True).click()
 with page.expect_download() as d:page.locator('#historyTxt').click()
 assert 'Курсант' in open(d.value.path()).read()
 page.evaluate("selected=game.scene;editor();startTest()")
 buf=io.BytesIO();Image.new('RGB',(600,300),(35,80,130)).save(buf,format='PNG');payload={'name':'art.png','mimeType':'image/png','buffer':buf.getvalue()}
 for key in ['image','background','sprite']:
  page.locator('#step-editor-0 input[data-asset='+key+']').set_input_files(payload)
  page.wait_for_function('(k)=>Boolean(editing().steps[0][k])',arg=key)
 assert page.locator('#passageImage').is_visible()
 assert page.locator('#passageBg').get_attribute('src')==page.evaluate('editing().steps[0].background')
 assert page.locator('#bg').get_attribute('src')==page.evaluate('editing().background||null')
 assert page.locator('#actor').get_attribute('src')==page.evaluate('editing().steps[0].sprite')
 assert page.evaluate('current().steps[1].image===undefined')
 page.get_by_text('Далее →',exact=True).click();assert not page.locator('#passageImage').is_visible()
 page.reload();assert page.evaluate('project.scenes.find(s=>s.id===project.startScene).steps[0].image.startsWith("data:image/png")')
 page.locator('#saveMenu summary').click()
 with page.expect_download() as d:page.locator('#export').click()
 project=json.load(open(d.value.path()));first=next(s for s in project['scenes'] if s['id']==project['startScene']);assert all(first['steps'][0][k].startswith('data:image/png') for k in ['image','background','sprite'])
 assert not errors,errors
 print('PASS: save menu; no story exports under choices; name form desktop/mobile alignment and serif heading; per-step illustration/background/sprite upload, transitions, persistence and export')
 b.close()
