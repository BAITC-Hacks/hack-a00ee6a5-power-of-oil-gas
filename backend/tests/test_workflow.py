import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ['USE_AI']='false'
from fastapi.testclient import TestClient
from app import database
from app.main import app
from app.services.rating_service import WEIGHTS,RUBRIC,rate_card,preview_score,calculate_score,card_hash,assess_card,readiness_level
from app.services.ai_service import analyze_description

CARD={
 'title':'Раннее обнаружение отказов насосов',
 'context':'Сейчас инженеры вручную проверяют 20 насосов ежедневно. Отказы приводят к простоям.',
 'need':'Нужно раньше выявлять риск отказов насосов, чтобы снизить простои и определить приоритет проверок.',
 'data_materials':'Есть CSV с вибрацией и температурой 20 насосов за 6 месяцев. Обезличенные данные передаются куратором.',
 'expected_result':'Прототип модели и интерфейс, показывающий список насосов и оценку риска. Передать исходный код и инструкцию запуска.',
 'success_criteria':'Recall не ниже 0.8, Precision не ниже 0.6 на отложенном тестовом наборе; сравнить с baseline.',
 'constraints':'3 недели; Python, без подключения к сети предприятия; только обезличенные исторические данные.',
 'users':'Инженеры по надёжности: каждый день открывают список и принимают решение о проверке.',
 'contact':'Куратор отвечает по адресу curator@example.com.',
 'interaction_format':'Две онлайн-встречи в неделю. Куратор проверяет и принимает результаты этапов.'
}
HEADERS={'X-Requested-With':'Alem'}

class QualityTests(unittest.TestCase):
 def test_weights_boundaries_and_no_points_for_gibberish(self):
  self.assertEqual(sum(WEIGHTS.values()),100)
  for field,checks in RUBRIC.items():self.assertEqual(sum(c[2] for c in checks),WEIGHTS[field])
  self.assertEqual(preview_score({k:'абракадабра очень длинная '*30 for k in WEIGHTS})['score'],0)
  self.assertEqual(preview_score({k:'Не знаю' for k in WEIGHTS})['score'],0)
  self.assertEqual(calculate_score(CARD,False)['score'],0)
  self.assertEqual([readiness_level(s) for s in [39,40,69,70,89,90]],['Черновик','Рабочая','Рабочая','Готовая','Готовая','Приоритетная'])
 def test_partial_credit_and_explanations(self):
  rating=preview_score({'data_materials':'CSV с показаниями','contact':'curator@example.com'})
  self.assertEqual(rating['score'],7)
  self.assertEqual(rating['breakdown'][2]['points'],4)
  self.assertTrue(rating['breakdown'][2]['suggestions'])
  self.assertGreater(preview_score(CARD)['score'],80)
  self.assertLess(preview_score({'need':'Нужен AI','data_materials':'CSV'})['score'],20)
 def test_ai_evidence_and_no_invented_points(self):
  evidence={f'{f}.{key}':None for f,checks in RUBRIC.items() for key,*_ in checks}
  evidence['data_materials.format']='CSV'
  evidence['data_materials.source']='Есть база 10000 строк' # not in source
  with patch('app.services.ai_service._openai_json',return_value={'evidence':evidence,'summary':'Добавьте период данных.'}):
   result=assess_card({'data_materials':'CSV с показаниями'})
  self.assertEqual(result['mode'],'openai');self.assertEqual(result['score'],4)
 def test_malformed_ai_and_timeout_are_labelled_fallback(self):
  for bad in [None,{}, {'evidence':[],'summary':'bad'}]:
   with patch('app.services.ai_service._openai_json',return_value=bad):self.assertEqual(assess_card(CARD)['mode'],'fallback')
  with patch('app.services.ai_service._openai_json',side_effect=TimeoutError):self.assertEqual(assess_card(CARD)['mode'],'fallback')
 def test_analysis_quotes_and_questions(self):
  raw='Хотим снизить поломки насосов.'
  with patch('app.services.ai_service._openai_json',return_value={'extracted_fields':{'need':raw,'contact':'invented@example.com'},'questions':[]}):analysis,mode=analyze_description(raw)
  self.assertEqual(mode,'openai');self.assertIsNone(analysis.extracted_fields['contact']);self.assertGreaterEqual(len(analysis.questions),3)
 def test_fingerprint_changes_with_text(self):
  self.assertNotEqual(card_hash(CARD),card_hash({**CARD,'constraints':'Две недели'}))
  self.assertEqual(card_hash(CARD),card_hash({**CARD,'confirmed':True}))

class AccessWorkflowTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=database.DB_PATH;database.DB_PATH=Path(self.temp.name)/'test.db'
  self.client=TestClient(app,headers=HEADERS);self.client.__enter__()
  self.owner=self.account('owner@example.com','business','Первый бизнес')
  self.other=self.account('other@example.com','business','Второй бизнес')
  self.worker=self.account('worker@example.com','performer','Команда исполнителя')
  self.worker2=self.account('worker2@example.com','performer','Другая команда')
 def tearDown(self):
  self.client.__exit__(None,None,None);database.DB_PATH=self.old;self.temp.cleanup()
 def account(self,email,role,name):
  client=TestClient(app,headers=HEADERS)
  result=client.post('/api/auth/register',json={'email':email,'password':'Test-password-2026','display_name':name,'role':role})
  self.assertEqual(result.status_code,200,result.text)
  return client
 def create(self,client=None):
  result=(client or self.owner).post('/api/challenges/analyze',json={'raw_description':'Хотим снизить поломки насосов.','industry':'Oil & Gas'})
  self.assertEqual(result.status_code,200,result.text);return result.json()
 def confirm(self,cid,card=CARD,client=None):
  client=client or self.owner
  assessment=client.post(f'/api/challenges/{cid}/assess',json=card)
  self.assertEqual(assessment.status_code,200,assessment.text)
  result=client.put(f'/api/challenges/{cid}/confirm',json={**card,'confirmed':True,'assessment_id':assessment.json()['assessment_id']})
  self.assertEqual(result.status_code,200,result.text);return result.json()
 def proposal(self,cid,client=None):
  response=(client or self.worker).post('/api/proposals',json={'challenge_id':cid,'team_name':'Попытка чужого имени','team_id':1,'solution_idea':'Сравним baseline с моделью.','plan':'Подготовка данных, модель, проверка.','deadline':'3 недели','prototype_url':'https://example.com/prototype'})
  self.assertEqual(response.status_code,200,response.text);return response.json()['proposal']
 def test_registration_login_logout_and_session(self):
  result=self.owner.get('/api/auth/me');self.assertEqual(result.json()['user']['role'],'business');self.assertNotIn('password_hash',result.text)
  cookie=self.owner.cookies.get('alem_session');self.assertTrue(cookie)
  self.owner.post('/api/auth/logout');self.assertEqual(self.owner.get('/api/auth/me').status_code,401)
  self.assertEqual(self.owner.post('/api/auth/login',json={'email':'owner@example.com','password':'wrong-password'}).status_code,401)
  self.assertEqual(self.owner.post('/api/auth/login',json={'email':'OWNER@example.com','password':'Test-password-2026'}).status_code,200)
  self.assertEqual(self.owner.post('/api/auth/register',json={'email':'owner@example.com','password':'Test-password-2026','role':'business','display_name':'Дубль'}).status_code,409)
  self.assertEqual(self.client.post('/api/auth/register',json={'email':'admin@example.com','password':'Test-password-2026','role':'admin','display_name':'Admin'}).status_code,422)
 def test_guest_and_csrf(self):
  self.assertEqual(self.client.get('/api/challenges').status_code,401)
  self.assertEqual(self.client.get('/api/teams').status_code,401)
  self.assertEqual(TestClient(app).post('/api/auth/login',json={}).status_code,403)
  self.assertEqual(self.owner.post('/api/challenges/preview',json={},headers={'Origin':'https://evil.example'}).status_code,403)
 def test_business_sees_only_owned_tasks_even_with_direct_link(self):
  cid=self.create()['challenge']['id'];other_id=self.create(self.other)['challenge']['id']
  self.assertEqual([i['id'] for i in self.owner.get('/api/challenges?include_drafts=true').json()['items']],[cid])
  self.assertEqual(self.owner.get(f'/api/challenges/{other_id}').status_code,404)
  for route in ['publish','assess','build-card']:
   payload={} if route!='build-card' else {'answers':[{'field':'context','question':'Вопрос','answer':'Ответ'}]*3}
   self.assertEqual(self.other.post(f'/api/challenges/{cid}/{route}',json=payload).status_code,404)
  self.assertEqual(self.other.get(f'/api/challenges/{cid}/proposals').status_code,404)
  self.assertEqual(self.worker.get(f'/api/challenges/{cid}').status_code,404)
  self.assertNotIn(cid,[i['id'] for i in self.worker.get('/api/challenges?include_drafts=true').json()['items']])
 def test_performer_cannot_mutate_or_spoof_business(self):
  cid=self.create()['challenge']['id']
  self.assertEqual(self.worker.post('/api/challenges/analyze',json={'raw_description':'Пытаюсь создать чужую задачу'}).status_code,403)
  self.assertEqual(self.worker.post('/api/challenges/preview',json={}).status_code,403)
  self.assertEqual(self.worker.post(f'/api/challenges/{cid}/assess',json=CARD).status_code,403)
  self.assertEqual(self.worker.get(f'/api/challenges/{cid}/proposals').status_code,403)
  self.assertEqual(self.owner.get('/api/my-proposals').status_code,403)
 def test_end_to_end_rating_edit_proposal_and_progress(self):
  analysis=self.create();cid=analysis['challenge']['id']
  self.assertEqual(self.owner.post(f'/api/challenges/{cid}/publish').status_code,400)
  answers=[{'field':q['field'],'question':q['question'],'answer':CARD[q['field']]} for q in analysis['questions']]
  built=self.owner.post(f'/api/challenges/{cid}/build-card',json={'answers':answers})
  self.assertEqual(built.status_code,200,built.text)
  self.assertEqual(built.json()['challenge']['data_materials'],CARD['data_materials'])
  confirmed=self.confirm(cid);self.assertGreater(confirmed['rating']['score'],80)
  self.owner.post(f'/api/challenges/{cid}/publish')
  changed=self.confirm(cid,{**CARD,'data_materials':'CSV'})['challenge']
  self.assertEqual(changed['status'],'published');self.assertLess(changed['score'],confirmed['rating']['score'])
  self.assertEqual(changed['score'],changed['rating']['score'])
  public=self.worker.get('/api/challenges').json()['items'];self.assertIn(cid,[c['id'] for c in public]);self.assertEqual([c['score'] for c in public],sorted([c['score'] for c in public],reverse=True))
  proposal=self.proposal(cid);pid=proposal['id'];self.assertEqual(proposal['team_name'],'Команда исполнителя')
  self.assertEqual(len(self.worker.get('/api/my-proposals').json()['items']),1)
  self.assertEqual(len(self.worker2.get('/api/my-proposals').json()['items']),0)
  stage={'points':17,'stage':'prototype','evidence':'Прототип проверен на согласованных сценариях.','confirmed':True}
  self.assertEqual(self.worker.post(f'/api/proposals/{pid}/decision',json={'decision':'accepted'}).status_code,403)
  self.assertEqual(self.other.post(f'/api/proposals/{pid}/decision',json={'decision':'accepted'}).status_code,404)
  self.assertEqual(self.other.post(f'/api/proposals/{pid}/milestones',json=stage).status_code,404)
  self.assertEqual(self.owner.post(f'/api/proposals/{pid}/milestones',json=stage).status_code,409)
  self.owner.post(f'/api/proposals/{pid}/decision',json={'decision':'accepted'})
  self.assertEqual(self.owner.post(f'/api/proposals/{pid}/milestones',json=stage).json()['proposal']['progress_points'],17)
  self.assertEqual(self.owner.post(f'/api/proposals/{pid}/milestones',json=stage).status_code,409)
  self.assertEqual(self.worker.get('/api/my-proposals').json()['items'][0]['progress_points'],17)
 def test_reputation_and_unique_applicants(self):
  cid=self.create()['challenge']['id'];self.confirm(cid);self.owner.post(f'/api/challenges/{cid}/publish')
  proposal=self.proposal(cid);pid=proposal['id'];uid=proposal['owner_id']
  self.assertEqual(proposal['performer_rating'],{'average_score':None,'completed_count':0,'max_score':100})
  self.proposal(cid);self.proposal(cid,self.worker2)
  listed=next(c for c in self.owner.get('/api/challenges').json()['items'] if c['id']==cid)
  self.assertEqual(listed['applicant_count'],2)
  self.assertEqual(self.worker.get(f'/api/challenges/{cid}').json()['challenge']['applicant_count'],2)
  with database.db_session() as conn:
   for index,points in enumerate(([10,10,20],[15,25,40],[20,30])):
    prior=conn.execute("INSERT INTO challenges(raw_description,title,owner_id) VALUES('Past fixture','Past fixture',?)",(self.owner.get('/api/auth/me').json()['user']['id'],)).lastrowid
    p=conn.execute("INSERT INTO proposals(challenge_id,team_name,solution_idea,plan,deadline,prototype_url,status,owner_id) VALUES(?,'Test','Idea','Plan','Soon','https://example.com','accepted',?)",(prior,uid)).lastrowid
    for stage,score in zip(('discovery','prototype','validation'),points):
     conn.execute('INSERT INTO milestones(proposal_id,stage,evidence,points) VALUES(?,?,?,?)',(p,stage,'Verified evidence',score))
   conn.execute("UPDATE proposals SET status='accepted' WHERE id=?",(pid,))
   for stage,score in [('discovery',20),('prototype',30),('validation',50)]:
    conn.execute('INSERT INTO milestones(proposal_id,stage,evidence,points) VALUES(?,?,?,?)',(pid,stage,'Current task must not count',score))
  items=self.owner.get(f'/api/challenges/{cid}/proposals').json()['items']
  rating=next(p for p in items if p['id']==pid)['performer_rating']
  self.assertEqual(rating,{'average_score':60.0,'completed_count':2,'max_score':100})
  other=next(p for p in items if p['owner_id']!=uid)
  self.assertIsNone(other['performer_rating']['average_score'])
 def test_localized_questions_and_unchanged_user_text(self):
  for locale,raw in [('en','We need to reduce unexpected pump failures.'),('kk','Сорғылардың күтпеген ақауларын азайту керек.')]:
   r=self.owner.post('/api/challenges/analyze',json={'raw_description':raw},headers={'Accept-Language':locale})
   self.assertEqual(r.status_code,200,r.text)
   data=r.json();self.assertEqual(data['challenge']['raw_description'],raw)
   self.assertTrue(all(q['language']==locale for q in data['questions']))
   self.assertTrue(all(q['hint'] for q in data['questions']))
   if locale=='en':self.assertTrue(all(not any('а'<=ch<='я' for ch in q['question']) for q in data['questions']))
  self.assertEqual(self.create()['questions'][0]['language'],'ru')
 def test_milestone_partial_zero_and_limits(self):
  cid=self.create()['challenge']['id'];self.confirm(cid);self.owner.post(f'/api/challenges/{cid}/publish')
  pid=self.proposal(cid)['id'];self.owner.post(f'/api/proposals/{pid}/decision',json={'decision':'accepted'})
  url=f'/api/proposals/{pid}/milestones'
  base={'stage':'discovery','evidence':'Проверены материалы и обоснование исследования.','confirmed':True}
  for score in [-1,21,1.5,True,'12']:
   self.assertEqual(self.owner.post(url,json={**base,'points':score}).status_code,422)
  self.assertEqual(self.owner.post(url,json=base).status_code,422)
  first=self.owner.post(url,json={**base,'points':12})
  self.assertEqual(first.status_code,200);self.assertEqual(first.json()['proposal']['progress_points'],12)
  self.assertEqual(self.owner.post(url,json={**base,'points':20}).status_code,409)
  second=self.owner.post(url,json={**base,'stage':'prototype','points':0})
  self.assertEqual(second.status_code,200);self.assertEqual(second.json()['proposal']['progress_points'],12)
  self.assertEqual(self.owner.post(url,json={**base,'stage':'validation','points':51}).status_code,422)
  self.assertEqual(self.owner.post(url,json={**base,'stage':'validation','points':50}).json()['proposal']['progress_points'],62)
  self.assertEqual(self.worker.get('/api/my-proposals').json()['items'][0]['progress_points'],62)
 def test_stale_or_foreign_assessment_cannot_confirm(self):
  cid=self.create()['challenge']['id'];second=self.create(self.other)['challenge']['id']
  result=self.owner.post(f'/api/challenges/{cid}/assess',json=CARD).json()
  payload={**CARD,'confirmed':True,'assessment_id':result['assessment_id']}
  self.assertEqual(self.owner.put(f'/api/challenges/{cid}/confirm',json={**payload,'context':'Теперь другой процесс'}).status_code,409)
  self.assertEqual(self.other.put(f'/api/challenges/{second}/confirm',json=payload).status_code,409)
  self.assertEqual(self.other.put(f'/api/challenges/{cid}/confirm',json=payload).status_code,404)
  self.assertEqual(self.owner.put(f'/api/challenges/{cid}/confirm',json={**payload,'confirmed':False}).status_code,422)
 def test_ai_cached_and_confirmation_retains_exact_score(self):
  cid=self.create()['challenge']['id']
  evidence={f'{f}.{key}':None for f,checks in RUBRIC.items() for key,*_ in checks};evidence['contact.channel']='curator@example.com'
  with patch('app.services.ai_service._openai_json',return_value={'evidence':evidence,'summary':'Нужны детали.'}) as mock:
   first=self.owner.post(f'/api/challenges/{cid}/assess',json=CARD).json()
   second=self.owner.post(f'/api/challenges/{cid}/assess',json=CARD).json()
   self.assertEqual(mock.call_count,1);self.assertTrue(second['cached']);self.assertEqual(first['rating']['score'],3)
  confirmed=self.owner.put(f'/api/challenges/{cid}/confirm',json={**CARD,'confirmed':True,'assessment_id':first['assessment_id']}).json()
  self.assertEqual(confirmed['rating']['score'],3)
  self.assertEqual(self.owner.get(f'/api/challenges/{cid}').json()['challenge']['rating']['mode'],'openai')
 def test_low_score_open_multiple_teams_and_validation(self):
  cid=self.create()['challenge']['id'];self.confirm(cid,{'title':'Мало сведений','need':'Нужно снизить простои'})
  self.owner.post(f'/api/challenges/{cid}/publish')
  for worker in [self.worker,self.worker2]:
   pid=self.proposal(cid,worker)['id'];self.owner.post(f'/api/proposals/{pid}/decision',json={'decision':'accepted'})
  self.assertEqual(len(self.owner.get(f'/api/challenges/{cid}/proposals').json()['items']),2)
  self.assertLess(self.worker.get(f'/api/challenges/{cid}').json()['challenge']['score'],40)
  payload={'challenge_id':cid,'team_name':'Имя','solution_idea':'Идея достаточно длинная','plan':'План достаточно длинный','deadline':'3 недели','prototype_url':'javascript:alert(1)'}
  self.assertEqual(self.worker.post('/api/proposals',json=payload).status_code,422)
  self.assertEqual(self.owner.post('/api/challenges/analyze',json={'raw_description':' '*20}).status_code,422)
 def test_migration_and_seed_idempotent(self):
  database.init_db()
  from app.routers.auth import migrate_legacy_owners
  from app.services.rating_service import migrate_ratings
  migrate_legacy_owners();migrate_ratings()
  with database.db_session() as conn:
   self.assertEqual(conn.execute('SELECT count(*) FROM challenges WHERE owner_id IS NULL').fetchone()[0],0)
   self.assertGreaterEqual(conn.execute('SELECT count(*) FROM challenges').fetchone()[0],5)
   self.assertEqual(conn.execute("SELECT count(*) FROM users WHERE email='owner@alem.local'").fetchone()[0],1)
  self.assertEqual(self.owner.get('/api/challenges').json()['items'],[])

if __name__=='__main__':unittest.main()
