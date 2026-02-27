import re
import csv
from bs4 import BeautifulSoup

with open('browns_roster.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

players = []

# try to parse the roster table where rich data like weight, age, exp, and college appear
for row in soup.select('table tr'):
    name_td = row.find('td', class_='sorter-lastname')
    if not name_td:
        continue
    name = name_td.get_text(' ', strip=True)
    tds = row.find_all('td')
    # fields are sequential
    def text(i):
        return tds[i].get_text(strip=True) if i < len(tds) else ''
    def dataval(i):
        if i < len(tds) and tds[i].has_attr('data-value'):
            return tds[i]['data-value']
        return text(i)
    number = text(1)
    position = text(2)
    height = text(3)
    weight = dataval(4)
    age = dataval(5)
    exp = dataval(6)
    college = dataval(7)

    # split name into first and last
    fn = ''
    ln = ''
    if name:
        parts = name.split()
        if len(parts) > 1:
            fn = parts[0]
            ln = ' '.join(parts[1:])
        else:
            fn = name
    players.append({
        'first_name': fn,
        'last_name': ln,
        'Number': number,
        'Position': position,
        'Height': height,
        'Weight': weight,
        'Age': age,
        'Exp': exp,
        'College': college
    })

# if table didn't yield any players, fallback to older generic approach
if not players:
    # existing generic parsing logic follows...
    for item in soup.select('[data-player-id], .nfl-o-roster__player'):
        # Try to extract common fields
        name = None
        number = None
        position = None
        height = None
        weight = None
        age = None
        exp = None
        college = None

        # Name
        nm = item.select_one('.nfl-c-player-name__link, .roster__player-name, .nfl-o-roster__player-name')
        if nm:
            name = nm.get_text(strip=True)
        else:
            # fallback: look for <h3> or <h2>
            h = item.find(['h2','h3'])
            if h:
                name = h.get_text(strip=True)

        # Number
        num = item.select_one('.nfl-c-player-number__value, .roster__player-number, .nfl-o-roster__player-number')
        if num:
            number = num.get_text(strip=True)
        else:
            # sometimes number is inside a div with aria-label
            nl = item.find(attrs={'aria-label': re.compile('number', re.I)})
            if nl:
                number = nl.get_text(strip=True)

        # Position
        pos = item.select_one('.nfl-c-player-position, .roster__player-position')
        if pos:
            position = pos.get_text(strip=True)

        # Biographical facts often in a list or paragraph; gather text and parse
        bio_text = ' '.join([t.get_text(' ', strip=True) for t in item.select('.nfl-o-roster__player-body p, .roster__player-body p, .nfl-c-player__meta, .nfl-o-roster__info')])
        if not bio_text:
            bio_text = item.get_text(' ', strip=True)

        # Attempt to parse Height, Weight, Age, Exp, College from bio_text using regex
        # Height like 6' 2" or 6-2 or 6'2" or 6' 2""
        h_match = re.search(r"(\d+\s*'\s*\d+\")|(\d+-\d+)|(\d+\s*ft\s*\d+\s*in)" , bio_text)
        if h_match:
            height = h_match.group(0)
        else:
            # also look for patterns like 6'2" or 6' 2"
            h2 = re.search(r"\d+'\s*\d+\"?", bio_text)
            if h2:
                height = h2.group(0)

        w_match = re.search(r"\b(\d{3})\s*lb\b|\b(\d{2,3})\s*lbs?\b", bio_text, re.I)
        if w_match:
            weight = w_match.group(0)

        age_match = re.search(r"Age\s*(\d{1,2})", bio_text, re.I)
        if age_match:
            age = age_match.group(1)
        else:
            # sometimes age appears as just a number followed by 'years' nearby
            a2 = re.search(r"(\d{1,2})\s*years", bio_text)
            if a2:
                age = a2.group(1)

        exp_match = re.search(r"Exp\.?\s*(\d+)", bio_text, re.I)
        if exp_match:
            exp = exp_match.group(1)
        else:
            e2 = re.search(r"(Rookie|\d+\s*yr[s]?)", bio_text, re.I)
            if e2:
                exp = e2.group(0)

        # College - look for 'College' label or the last capitalized phrase
        coll = None
        coll_match = re.search(r"College\s*[:\-]?\s*([A-Za-z&.\s\-']{2,})", bio_text)
        if coll_match:
            coll = coll_match.group(1).strip()
        else:
            # fallback: look for anchor or small label
            c_el = item.select_one('.nfl-c-player__college, .roster__player-college')
            if c_el:
                coll = c_el.get_text(strip=True)
        if coll:
            college = re.sub(r"\s+", ' ', coll)

        # If we didn't find name but item contains link to player page, try to get from that link's text
        if not name:
            a = item.find('a')
            if a:
                name = a.get_text(strip=True)

        # Normalize empty strings
        def norm(x):
            return x.strip() if x and x.strip() else ''

        player = {
            'Player': norm(name),
            'Number': norm(number),
            'Position': norm(position),
            'Height': norm(height),
            'Weight': norm(weight),
            'Age': norm(age),
            'Exp': norm(exp),
            'College': norm(college)
        }

        # Avoid blank entries
        if player['Player']:
            players.append(player)

# Write CSV with first_name and last_name
keys = ['first_name','last_name','Number','Position','Height','Weight','Age','Exp','College']
with open('browns_roster.csv','w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=keys)
    writer.writeheader()
    for p in players:
        writer.writerow(p)

print(f'Wrote {len(players)} players to browns_roster.csv')
