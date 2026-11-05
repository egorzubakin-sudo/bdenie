import io,json,tempfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload()
 # Previous edition is preserved as archive; unique media and authored drafts are retained.
 assert page.evaluate("""(()=>{const old=clone(project);delete old.chapterEdition;delete old.chapters;old.scenes=old.scenes.filter(s=>!s.chapterStory);old.startScene=old.scenes.find(s=>s.title==='Вступление').id;const authored=old.scenes.find(s=>s.id==='speech');authored.steps[0].text='Мой авторский текст';const p=migrate(old);validate(p);return p.startScene==='c7_bio_watch'&&p.scenes.find(s=>s.id==='speech').steps[0].text==='Мой авторский текст'&&p.scenes.find(s=>s.id==='speech').archived&&p.scenes.filter(s=>s.chapterStory).length===52})()""")
 assert page.evaluate("(()=>{const g={...fresh(),scene:'sp_free_early',flags:{sp_visit_tech1:true},log:[]};upgradeChapterRun(g);return g.scene==='c7_party'&&g.flags.c7_bond_tech&&g.flags.c7_hangout_spent})()")
 page.locator('#cadetName').fill('Тест');page.get_by_text('Начать историю →',exact=True).click();page.locator('#randomBiography').click()
 # Writer applies one undoable edit; closing a draft is harmless.
 field=page.locator('#step-editor-0 textarea').first;before=field.input_value();page.locator('#step-editor-0').get_by_text('Развернуть текст',exact=True).first.click();page.locator('#writerText').fill('**Новая фраза**');page.locator('#writerApply').click();assert field.input_value()=='**Новая фраза**';page.get_by_text('Отменить',exact=True).click();assert page.locator('#step-editor-0 textarea').first.input_value()==before
 # Folder library and reusable references remain valid in the new edition.
 n=page.evaluate('Object.keys(project.assets).length')
 with tempfile.TemporaryDirectory() as folder:
  Image.new('RGB',(20,30),'navy').save(Path(folder)/'portrait.png');page.locator('#libraryOpen').click();page.locator('#libraryFolder').set_input_files(folder);page.wait_for_function('(n)=>Object.keys(project.assets).length===n+1',arg=n);page.locator('[data-close=libraryDialog]').click()
 page.evaluate("openLibrary(editing().steps[0],'image')");page.locator('#librarySearch').fill('portrait.png');page.get_by_text('Выбрать',exact=True).click();assert page.evaluate('assetData(editing().steps[0].image).startsWith("data:image/png")')
 # Save slots restore committed gameplay; they do not alter edited project text.
 page.locator('#slotsOpen').click();slot=page.locator('#slotsList .slot-card').first;slot.get_by_text('Сохранить',exact=True).click();page.locator('[data-close=slotsDialog]').click();page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('game.scene')=='c7_arrival'
 page.locator('#slotsOpen').click();slot.get_by_text('Загрузить',exact=True).click();assert page.evaluate('game.scene')=='c7_profile';page.locator('[data-close=slotsDialog]').click()
 page.locator('#friendsOpen').click();assert page.locator('#friendsList .friend-card').count()==8;assert 'Преподаватель тактики' in page.locator('#friendsList').inner_text();page.locator('[data-close=friendsDialog]').click()
 assert page.evaluate('musicEngine.context===null');page.locator('#musicMenu summary').click();page.locator('#musicToggle').click();page.wait_for_function('musicEngine.playing');page.locator('#musicToggle').click();assert not page.evaluate('musicEngine.playing');page.locator('#musicMenu summary').click()
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.locator('#export').click()
 exported=json.loads(Path(d.value.path()).read_text());assert exported['chapterEdition']==7 and exported['assets'] and len(exported['chapters'])==6
 # Actual story and larger scene cards remain usable at phone width.
 page.locator('#choices .choice').first.click();page.get_by_text('Продолжить →',exact=True).click();page.set_viewport_size({'width':420,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert page.locator('#choices .choice').first.evaluate('n=>getComputedStyle(n).fontSize')=='20px'
 assert page.locator('#choices .choice').first.locator('small').first.evaluate('n=>getComputedStyle(n).fontSize')=='14px'
 page.emulate_media(reduced_motion='reduce');assert page.locator('#choices .choice').first.evaluate('n=>getComputedStyle(n).transitionDuration')=='0s'
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.locator('#historyHtml').click()
 assert 'Хроника' in Path(d.value.path()).read_text()
 assert not errors,errors
 print('PASS: previous project/archive/media migration, existing-bond migration, writer/undo, library, slots, 8 character cards, music, export, mobile sizes and reduced motion')
 b.close()
