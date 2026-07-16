import pandas as pd
import numpy as np
import datetime
import requests
import os
import json
from github import Github

#%%
# Empres-i
empresi = pd.read_csv('https://onehealthportal.github.io/CSV/Avian_Influenza/empresi_1.csv')
start_date = str(max(pd.to_datetime(empresi['observation_date'])))[:10]
end_date = datetime.datetime.now().strftime('%Y-%m-%d')[:10]

params = {
    "disease":"avian_influenza",
    "diagnosis_status":"confirmed",
    "animal_type":"all",
    "start_date":start_date,
    "end_date":end_date
}
r = requests.get(
    "https://europe-west1-fao-empresi.cloudfunctions.net/getLatestEventsByDate",
    params=params
)

df = r.text#.replace('"','')
df = df.split('\n')
cols = df[0].split(',')
cols = [item.replace('"','') for item in cols]
body = []
for i in range(1, len(df)):
    item = df[i]
    a = item.split(',')
    a[3] = '"'+a[3]+'"'
    a[4] = '"' + a[4] + '"'
    a[-3] = '"' + a[-3] + '"'
    a[-2] = '"' + a[-2] + '"'
    a = ['""' if item == '' else item for item in a]
    a = ','.join(a)
    a = a.split('","')
    a = [item.replace('"','') for item in a]
    body.append(a)

df = pd.DataFrame.from_records(body, columns= cols)
if len(df) > 0:
    df = pd.concat([empresi, df])
else:
    df = empresi.copy()
df = df[~pd.isnull(df['id_event'])]
df = df.drop_duplicates(subset='id_event')
df = df.reset_index(drop=True)
mycsv = df.to_csv(index=False)

#Convert to .js
myjs = df.to_json()
myjs = "const empresi = " + myjs + ";"
    
#----------------------- GitHub -----------------------
my_token = os.environ["PAGES_TOKEN"]
g = Github(my_token)
repo = g.get_user().get_repo("OneHealthPortal.github.io")
#------------------------------------------------------

#Update GitHub
empresi_1js = repo.get_contents("/JS/Avian_Influenza/empresi_1.js")
empresi_1csv = repo.get_contents("/CSV/Avian_Influenza/empresi_1.csv")

repo.update_file (empresi_1js.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), myjs, empresi_1js.sha)
repo.update_file (empresi_1csv.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), mycsv, empresi_1csv.sha)

#%% 
# WOAH/WAHIS
woah = pd.read_csv('https://onehealthportal.github.io/CSV/Avian_Influenza/woah_1.csv')
start_date = str(max(pd.to_datetime(woah['startDate'])))[:10]
end_date = datetime.datetime.now().strftime('%Y-%m-%d')[:10]

url = "https://wahis.woah.org/api/v1/pi/map-data/outbreaks-from-event-filter?language=en"
payload = {"eventIds":[],"reportIds":[],"countries":[],"firstDiseases":[922,668,671],
           "secondDiseases":[],"typeStatuses":[],"reasons":[],"eventStatuses":[],
           "reportTypes":[],"reportStatuses":[],"eventStartDate":{"from":start_date,"to":end_date},
           "submissionDate":None,"animalTypes":[],"sortColumn":"submissionDate","sortOrder":"desc",
           "pageSize":10,"pageNumber":0}
r = requests.post(url, json=payload)
j = json.loads(r.text)
df = pd.DataFrame.from_dict(j)
df = df[~pd.isnull(df['outbreakId'])]
df = df.drop_duplicates(subset=['outbreakId'])
oid = list(df['outbreakId'])

url2 = "https://wahis.woah.org/api/v1/pi/outbreak/additional-information"
data = []
dummy = ''
for i in range(0, len(df), 180):
    if i+180 < len(df):
        dummy = df[df.index.isin(list(range(i, i+180)))]
        payload2 = {"outbreakInfoIds":oid[i:i+180]}
    else:
        dummy = df[df.index.isin(list(range(i, len(df))))]
        payload2 = {"outbreakInfoIds":oid[i:]}

    dummy = dummy.set_index('outbreakId', drop=False)
    r2 = requests.post(url2, json=payload2)
    j2 = json.loads(r2.text)
    df2 = pd.DataFrame.from_dict(j2)
    df2 = df2.drop_duplicates(subset=['outbreakInfoId'])
    df2 = df2.set_index('outbreakInfoId', drop=False)
    dummy['totalCases'] = [df2['totalCases'][idx] if idx in df2.index else dummy['totalCases'][idx] for idx in dummy.index]
    #dummy['diseaseId'] = [df2['diseaseId'][idx] for idx in dummy.index]
    dummy['diseaseName'] = [df2['diseaseName'][idx] for idx in dummy.index]
    dummy['diseaseCategory'] = [df2['diseaseCategory'][idx] for idx in dummy.index]
    dummy['diseaseType'] = [df2['diseaseType'][idx] for idx in dummy.index]
    dummy['speciesDetails'] = [df2['speciesDetails'][idx] for idx in dummy.index]

    data.append(dummy)
    
if len(data) > 0:
    df = pd.concat([woah] + data)
else:
    df = woah.copy()
df = df[~pd.isnull(df['outbreakId'])]
df = df.drop_duplicates(subset=['outbreakId'])
df = df.reset_index(drop=True)

#Convert to .csv
mycsv = df.to_csv(index=False)

#Convert to .js
myjs = df.to_json()
myjs = "const wahis = " + myjs + ";"
    
#Update GitHub
woah_1js = repo.get_contents("/JS/Avian_Influenza/woah_1.js")
woah_1csv = repo.get_contents("/CSV/Avian_Influenza/woah_1.csv")

repo.update_file (woah_1js.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), myjs, woah_1js.sha)
repo.update_file (woah_1csv.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), mycsv, woah_1csv.sha)

#%%

