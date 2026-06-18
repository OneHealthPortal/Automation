import pandas as pd
import numpy as np
import datetime
import requests
import os
from github import Github

#%%
empresi = pd.read_csv('https://onehealthportal.github.io/CSV/empresi_1.csv')
start_date = str(max(pd.to_datetime(empresi['observation_date'])))[:10]
end_date = datetime.datetime.now().strftime('%Y-%m-%d')[:10]

#%%
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

#%%
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
mycsv = df.to_csv()

#%%
# Convert to .js
myjs = df.to_json(orient='records')
myjs = "const empresi = " + myjs + ";"
    
#%%
# Update GitHub
my_token = os.environ["PAGES_TOKEN"]
g = Github(my_token)
repo = g.get_user().get_repo("OneHealthPortal.github.io")

empresi_1js = repo.get_contents("/JS/empresi_1.js")
empresi_1csv = repo.get_contents("/CSV/empresi_1.csv")

repo.update_file (empresi_1js.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), myjs, empresi_1js.sha)
repo.update_file (empresi_1csv.path, 'Last Updated: '+ datetime.date.today().strftime("%d/%m/%Y"), mycsv, empresi_1csv.sha)

