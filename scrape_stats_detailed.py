from bs4 import BeautifulSoup
import csv

with open('browns_stats.html','r',encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(),'html.parser')

# desired columns (split into first_name/last_name)
columns = ['first_name','last_name','ATT','COMP','YDS','COMP PER','YDS/ATT','TD','TD Per','INT','INT Per','LONG','SCK','SCK LOST','RATE','REC','ASSIST','SCK','SFTY','F']

rows = []

for table in soup.select('div.nfl-o-teamstats table'):
    # get header names
    hdrs = []
    for th in table.select('thead th'):
        text = th.get_text(strip=True)
        hdrs.append(text)
    # iterate rows
    for tr in table.select('tbody tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if not cells:
            continue
        data = {'first_name':'','last_name':'','ATT':'','COMP':'','YDS':'','COMP PER':'','YDS/ATT':'','TD':'','TD Per':'','INT':'','INT Per':'','LONG':'','SCK':'','SCK LOST':'','RATE':'','REC':'','ASSIST':'','SCK':'','SFTY':'','F':''}
        # player cell might include name within
        if hdrs and hdrs[0].lower().startswith('player'):
            name = cells[0]
            parts = name.split()
            if parts:
                data['first_name'] = parts[0]
                data['last_name'] = ' '.join(parts[1:]) if len(parts) > 1 else ''
        # map remaining cells to headers
        for i,h in enumerate(hdrs[1:],start=1):
            key = h
            # normalize header like COMP% -> COMP PER, TD% -> TD Per, INT% -> INT Per
            if key.endswith('%'):
                if key == 'COMP%':
                    key = 'COMP PER'
                elif key == 'TD%':
                    key = 'TD Per'
                elif key == 'INT%':
                    key = 'INT Per'
                else:
                    key = key.replace('%',' PER')
            # rename LONG? keep same, SCK/LOST -> SCK LOST
            if key == 'SCK/LOST':
                key = 'SCK LOST'
            if key == 'YDS/REC':
                key = 'YDS/ATT'  # not perfect but map
            # lowercase? use as is but user columns uppercase
            if key in data:
                data[key] = cells[i] if i < len(cells) else ''
        rows.append(data)

# write CSV
with open('browns_stats_detailed.csv','w',newline='',encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=columns)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f'wrote {len(rows)} rows with {len(columns)} columns')
