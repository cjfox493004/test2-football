from bs4 import BeautifulSoup
import csv

with open('browns_stats.html','r',encoding='utf-8') as f:
    html = f.read()
soup = BeautifulSoup(html,'html.parser')

rows = []
# each stat group
for obj in soup.select('div.d3-o-object'):
    header = obj.select_one('div.d3-o-object__header p')
    stat_name = header.get_text(strip=True) if header else ''
    table = obj.find('table')
    if not table:
        continue
    for tr in table.select('tbody tr'):
        cells = tr.find_all('td')
        if len(cells) < 2:
            continue
        # player cell may contain link
        name = cells[0].get_text(' ',strip=True)
        # split name
        fn = ''
        ln = ''
        if name:
            parts = name.split()
            if len(parts) > 1:
                fn = parts[0]
                ln = ' '.join(parts[1:])
            else:
                fn = name
        # value cell contains number and span unit
        value_text = cells[1].get_text(' ',strip=True)
        # separate unit if present (last token)
        unit = ''
        val = value_text
        if value_text:
            parts = value_text.split()
            if parts[-1].isalpha():
                unit = parts[-1]
                val = ' '.join(parts[:-1])
        rows.append({
            'stat': stat_name,
            'first_name': fn,
            'last_name': ln,
            'value': val,
            'unit': unit
        })

keys = ['stat','first_name','last_name','value','unit']
with open('browns_stats.csv','w',newline='',encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile,fieldnames=keys)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
print(f'wrote {len(rows)} rows to browns_stats.csv')
