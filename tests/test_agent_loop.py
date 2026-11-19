import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast, re

p=Path(__file__).resolve().parents[1] / 'AgentsVisualForGrad.ipynb'
nb=json.load(open(p,encoding='utf8'))
code=''.join(nb['cells'][7]['source'])
ctx=dict(pd=pd,px=px,go=go,ast=ast,re=re,json=json,DEMO_MODE=True,PLANNER_MODEL='planner',CODER_MODEL='coder',REVIEWER_MODEL='reviewer')
exec(code,ctx)
Validator=ctx['ChartCodeValidator']; DataTools=ctx['DataTools']; Agent=ctx['VisualAgent']
DF=pd.DataFrame({'order_date':pd.to_datetime(['2024-01-10','2024-01-15','2024-02-05']), 'revenue':[100.,120.,300.], 'profit':[30.,-5.,75.]})

def demo_test():
 a=Agent(DF, demo_mode=True, max_attempts=3, auto_execute=True)
 r=a.run_once('Show monthly revenue',show=False)
 assert r['status']=='success'; assert len(r['figure'].data)>=1
 assert r['attempts']==[{'attempt':1,'status':'success'}]
 assert a.history[0]['attempts']==1

class RetryAgent(Agent):
 def __init__(self,df):
  super().__init__(df,demo_mode=True,max_attempts=3,auto_execute=True)
  self.calls=0
 def coder_step(self,plan,observation,feedback='',previous_code=''):
  self.calls+=1
  if self.calls==1:
   return 'import os\nfig = px.line(master_df, x="order_date", y="revenue")'
  assert 'Disallowed Python syntax' in feedback, feedback
  return 'fig = px.line(master_df, x="order_date", y="revenue")'

def correction_test():
 a=RetryAgent(DF)
 r=a.run_once('Trend',show=False)
 assert a.calls==2 and r['status']=='success'
 assert [v['status'] for v in r['attempts']]==['rejected','success']

class ReviewerRetryAgent(Agent):
 def __init__(self,df):
  super().__init__(df,demo_mode=True,max_attempts=3,auto_execute=True)
  self.cnt=0; self.fb=''
 def reviewer_step(self,question,plan,observation,generated_code):
  self.cnt+=1
  if self.cnt==1: return {'approved':False, 'feedback':'Fix axes', 'source':'llm-reviewer'}
  return super().reviewer_step(question,plan,observation,generated_code)
 def coder_step(self,plan,observation,feedback='',previous_code=''):
  if feedback: self.fb=feedback
  return super().coder_step(plan,observation,feedback,previous_code)

def reviewer_test():
 a=ReviewerRetryAgent(DF)
 r=a.run_once('Trend',show=False)
 assert a.cnt==2 and a.fb=='Fix axes'
 assert [v['status'] for v in r['attempts']]==['rejected','success']

def bad_code_test():
 bad=[
 'import os\nfig = px.line(master_df, x="order_date",y="revenue")',
 'master_df.to_csv("/tmp/file")\nfig = px.line(master_df,x="order_date",y="revenue")',
 'print("x")\nfig = px.line(master_df,x="order_date",y="revenue")',
 'fig=__import__("os")',
 'fig=px.line(master_df, x="order_date",y="revenue"); fig.show()',
 'fig=px.line(master_df, x="order_date",y="revenue"); fig.__class__',
 'fig=px.line(master_df["fake"],x="order_date",y="revenue")',
 'for x in range(10): pass\nfig = px.line(master_df, x="order_date",y="revenue")'
 ]
 for raw in bad:
  try:
   Validator.validate(raw,DF)
  except ctx['CodeRejected']:
   continue
  raise AssertionError('Allowed dangerous: '+raw)

class RuntimeRetryAgent(Agent):
 def __init__(self,df):
  super().__init__(df,demo_mode=True,max_attempts=3)
  self.calls=0
 def coder_step(self,plan,observation,feedback='',previous_code=''):
  self.calls+=1
  if self.calls==1: return 'fig = px.line(master_df, x="not_a_column", y="revenue")'
  assert 'ValueError' in feedback
  return 'fig = px.line(master_df, x="order_date", y="revenue")'

def runtime_test():
 a=RuntimeRetryAgent(DF)
 r=a.run_once('Trend',show=False)
 assert r['status']=='success'
 assert [v['status'] for v in r['attempts']]==['error','success']

class GiveUpAgent(Agent):
 def coder_step(self,plan,observation,feedback='',previous_code=''):
  return 'import os'

def giveup_test():
 a=GiveUpAgent(DF, demo_mode=True,max_attempts=2)
 try: a.run_once('Trend',show=False)
 except RuntimeError as e:
  assert '2 attempts' in str(e)
 else: raise AssertionError('Expected give up')

class ChatFake:
 def __init__(self): self.calls=[]
 def chat_completion(self,model,messages,max_tokens):
  self.calls.append(model)
  if model=='planner': content='{"tool_name":"get_sample","tool_args":["order_date","revenue"],"viz_goal":"Revenue trend"}'
  elif model=='coder': content='```python\nfig = px.line(master_df, x="order_date", y="revenue")\n```'
  elif model=='reviewer': content='{"approved": true, "feedback": "good"}'
  else: raise ValueError(model)
  class Obj: pass
  obj=Obj(); msg=Obj(); choice=Obj(); msg.content=content; choice.message=msg; obj.choices=[choice];return obj

def live_mock_test():
 client=ChatFake()
 a=Agent(DF,client=client,demo_mode=False,max_attempts=3,auto_execute=True)
 r=a.run_once('Trend',show=False)
 assert r['status']=='success' and client.calls==['planner','coder','reviewer']

for test in [demo_test,correction_test,reviewer_test,runtime_test,giveup_test,bad_code_test,live_mock_test]:
 print('RUNNING',test.__name__)
 test()
print('ALL TESTS PASSED')
