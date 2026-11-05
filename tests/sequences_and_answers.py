import io,json
from PIL import Image
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/index.html');page.evaluate('localStorage.clear()');page.reload()
 page.evaluate("game.playerName='Проверка';game.nameConfirmed=true;render()")
 stable=page.evaluate('JSON.stringify(game)');scenes=page.evaluate('project.scenes.map(s=>({id:s.id,choices:s.choices.length}))');runs=0
 for sc in scenes:
  for i in range(sc['choices']):
   for die in [1,20]:
    page.evaluate('''({id,i,die})=>{selected=id;startTest();test.nameConfirmed=true;test.step=current().steps.length-1;test.resumeScene='speech';const c=current().choices[i];for(const a of c.conditions||[]){if(a.kind==='flags')test.flags[a.key]=a.value;else test[a.kind][a.key]=a.value}document.getElementById('forcedRoll').value=String(die);render()}''',{'id':sc['id'],'i':i,'die':die})
    before=page.evaluate('({stats:structuredClone(test.stats),discipline:test.discipline,log:test.log.length,manureTimes:test.manureTimes})')
    page.evaluate('(i)=>choose(i)',i);out=page.evaluate('test.outcome');assert out,(sc,i,die)
    assert not out['next'] or page.evaluate('(id)=>project.scenes.some(s=>s.id===id)',out['next']),(sc,i,die,out)
    # Check replay exactly rolls back counters, including biography and punishment.
    page.get_by_text('Переиграть выбор',exact=True).click()
    after=page.evaluate('({stats:test.stats,discipline:test.discipline,log:test.log.length,manureTimes:test.manureTimes})');assert before==after,(sc,i,die,before,after)
    page.evaluate('(i)=>choose(i)',i);out=page.evaluate('test.outcome')
    if out['next']:
     page.get_by_text('Продолжить →',exact=True).click();assert page.evaluate('test.scene')==out['next'],(sc,i,die)
    assert page.evaluate('JSON.stringify(game)')==stable
    runs+=1
 # Backgrounds never inherit/duplicate between areas; icons live in their own choice.
 page.evaluate("selected='speech';startTest();test.step=current().steps.length-1;editor();render()")
 def png(color):
  buf=io.BytesIO();Image.new('RGB',(400,180),color).save(buf,format='PNG');return {'name':'art.png','mimeType':'image/png','buffer':buf.getvalue()}
 for selector,color in [('#editorV2 > input[data-asset=background]','navy'),('#step-editor-0 input[data-asset=background]','green')]:
  page.locator(selector).set_input_files(png(color));page.wait_for_timeout(100)
 card=page.locator('#answer-editor-0');card.locator('summary').first.click();art=card.locator('details').filter(has=page.get_by_text('Изображения карточки ответа',exact=True));art.locator('summary').first.click()
 art.locator('input[data-asset=background]').set_input_files(png('red'));page.wait_for_timeout(100)
 # Upload redraws editor; open the same card again if necessary.
 card=page.locator('#answer-editor-0');page.evaluate("document.querySelector('#answer-editor-0').open=true")
 art=card.locator('details').filter(has=page.get_by_text('Изображения карточки ответа',exact=True));art.evaluate('(n)=>n.open=true');art.locator('input[data-asset=sprite]').set_input_files(png('gold'));page.wait_for_timeout(100)
 page.evaluate('render()');assert page.locator('#bg').get_attribute('src')!=page.locator('#passageBg').get_attribute('src')
 assert page.locator('#choices .choice').first.locator('.answer-backdrop').count()==1
 assert page.locator('#choices .choice').first.locator('.answer-icon').count()==1
 assert page.locator('#choices .choice').nth(1).locator('.answer-icon').count()==0
 page.evaluate('delete current().steps[0].background;render()');assert not page.locator('#passageBg').is_visible();assert page.locator('#bg').is_visible()
 page.evaluate("document.getElementById('saveMenu').open=true")
 with page.expect_download() as d:page.locator('#export').click()
 exported=json.load(open(d.value.path()));answer=next(s for s in exported['scenes'] if s['id']=='speech')['choices'][0];assert answer['background'] and answer['sprite']
 assert page.evaluate("(()=>{const p=clone(project);p.scenes[0].choices[0].background='javascript:alert(1)';try{validate(p);return false}catch(e){return true}})()")
 audit=page.evaluate('sequenceAudit(project)');print('Audit:',json.dumps(audit['warnings'],ensure_ascii=False));assert not any('Нет пути к завершению' in x for x in audit['warnings'])
 assert not errors,errors
 page.screenshot(path='/workspace/bdenie/preview.png',full_page=True)
 print(f'PASS: {runs} choice/die paths, valid transitions, replay rollback, isolated game; independent scene/passage/answer backgrounds; per-choice icons; asset export and validation')
 b.close()
