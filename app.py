from functools import lru_cache
from urllib.parse import unquote

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Cleveland Browns Player Stats")

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cleveland Browns Player Search</title>
    <style>
        :root {
            --bg: #111111;
            --card: #1e1b18;
            --panel: #2f2a23;
            --text: #f5f1ea;
            --accent: #ff3c18;
            --accent-dark: #8e2f16;
            --border: rgba(255,255,255,0.08);
            --muted: #c4b9aa;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            background: radial-gradient(circle at top left, rgba(255,60,24,0.18), transparent 25%),
                        linear-gradient(180deg, #1a1511 0%, #0f0d0b 100%);
            color: var(--text);
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }
        main {
            width: min(1200px, calc(100% - 2rem));
            margin: 0 auto;
            padding: 2rem 0 3rem;
        }
        header {
            display: grid;
            gap: 1rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, rgba(255,60,24,0.9), rgba(92,61,29,0.95));
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 28px 80px rgba(0,0,0,0.35);
        }
        header h1 {
            margin: 0;
            font-size: clamp(2rem, 3vw, 3rem);
            letter-spacing: -0.04em;
        }
        header p {
            margin: 0.5rem 0 0;
            color: rgba(245,241,234,0.88);
            max-width: 42rem;
            line-height: 1.7;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.8rem 1rem;
            border-radius: 999px;
            background: rgba(0,0,0,0.24);
            color: #fff;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            width: fit-content;
        }
        .grid {
            display: grid;
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        .panel {
            border-radius: 24px;
            background: var(--panel);
            border: 1px solid var(--border);
            padding: 1.5rem;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
        }
        .panel h2 {
            margin-top: 0;
            color: var(--text);
        }
        .field {
            display: grid;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        label {
            color: var(--muted);
            font-size: 0.95rem;
        }
        select {
            width: 100%;
            max-width: 460px;
            padding: 0.95rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            background: #fff;
            color: #111;
            font-size: 1rem;
        }
        option {
            color: #111;
        }
        .table-wrap {
            overflow-x: auto;
            margin-top: 1rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 640px;
        }
        th, td {
            padding: 0.85rem 1rem;
            border: 1px solid rgba(255,255,255,0.08);
        }
        th {
            text-align: left;
            background: rgba(255,255,255,0.04);
            color: #fff;
        }
        td {
            color: var(--text);
        }
        .message {
            margin-top: 1rem;
            color: var(--muted);
            line-height: 1.7;
        }
        .notice {
            margin-top: 1rem;
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .footer {
            margin-top: 2rem;
            color: rgba(245,241,234,0.72);
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
<main>
    <header>
        <div class="badge">
            <span>🏈</span>
            Cleveland Browns Stats
        </div>
        <div>
            <h1>Find player bio and game stats</h1>
            <p>Search the current Cleveland Browns roster and display available season stats for each player. Players with available stats are marked with a lightning icon.</p>
        </div>
    </header>

    <div class="grid">
        <section class="panel">
            <div class="field">
                <label for="player-select">Choose a player</label>
                <select id="player-select" disabled>
                    <option value="">Loading players…</option>
                </select>
            </div>
            <div class="notice">Players are sorted with available stats first. If a player has no stats yet, the roster information is still shown.</div>
        </section>

        <section class="panel" id="bio-panel">
            <h2>Player Bio</h2>
            <div id="bio-content" class="message">Select a player to view bio information.</div>
        </section>

        <section class="panel" id="stats-panel">
            <h2>Player Stats</h2>
            <div id="stats-content" class="message">Select a player to view stats.</div>
        </section>
    </div>

    <div class="footer">Data sources: <code>browns_roster.csv</code> and <code>browns_stats_detailed.csv</code>.</div>
</main>

<script>
    const playerSelect = document.getElementById('player-select');
    const bioContent = document.getElementById('bio-content');
    const statsContent = document.getElementById('stats-content');

    async function fetchPlayers() {
        const response = await fetch('/api/players');
        const data = await response.json();
        playerSelect.innerHTML = '';

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = '-- Choose a player --';
        playerSelect.appendChild(placeholder);

        data.players.forEach(player => {
            const option = document.createElement('option');
            option.value = player.name;
            option.textContent = player.stats_available ? `${player.name} ⚡` : player.name;
            playerSelect.appendChild(option);
        });

        playerSelect.disabled = false;
    }

    function renderTable(items) {
        if (!items.length) {
            return '<div class="message">No records found.</div>';
        }

        const columns = Object.keys(items[0]);
        const header = columns.map(col => `<th>${col}</th>`).join('');
        const rows = items.map(row => {
            return '<tr>' + columns.map(col => `<td>${row[col] ?? ''}</td>`).join('') + '</tr>';
        }).join('');

        return `<div class="table-wrap"><table><thead><tr>${header}</tr></thead><tbody>${rows}</tbody></table></div>`;
    }

    function showError(message) {
        bioContent.innerHTML = `<div class="message">${message}</div>`;
        statsContent.innerHTML = '';
    }

    async function fetchPlayerData(name) {
        if (!name) {
            bioContent.innerHTML = 'Select a player to view bio information.';
            statsContent.innerHTML = 'Select a player to view stats.';
            return;
        }

        const response = await fetch(`/api/player?name=${encodeURIComponent(name)}`);
        if (!response.ok) {
            const errorText = await response.text();
            showError(errorText);
            return;
        }

        const data = await response.json();
        bioContent.innerHTML = renderTable(data.bio);
        statsContent.innerHTML = data.stats.length
            ? renderTable(data.stats)
            : '<div class="message">No detailed stats found for this player.</div>';
    }

    playerSelect.addEventListener('change', () => {
        fetchPlayerData(playerSelect.value);
    });

    fetchPlayers().catch(error => showError('Unable to load players.'));
</script>
</body>
</html>
"""

def normalize_stat_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        'COMP PER': 'COMP_PER',
        'YDS/ATT': 'YDS_ATT',
        'TD Per': 'TD_Per',
        'INT Per': 'INT_Per',
        'SCK LOST': 'SCK_LOST',
    }
    df = df.rename(columns=rename_map)

    columns = []
    seen = {}
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            columns.append(f'{col}_{seen[col]}')
        else:
            seen[col] = 0
            columns.append(col)
    df.columns = columns
    return df

@lru_cache(maxsize=1)
def load_data():
    roster = pd.read_csv('browns_roster.csv', dtype=str).fillna('')
    stats = pd.read_csv('browns_stats_detailed.csv', dtype=str).fillna('')

    roster['full_name'] = roster['first_name'].str.strip() + ' ' + roster['last_name'].str.strip()
    stats['full_name'] = stats['first_name'].str.strip() + ' ' + stats['last_name'].str.strip()
    stats = normalize_stat_columns(stats)

    numeric_columns = [col for col in stats.columns if col not in {'first_name', 'last_name', 'full_name'}]
    for column in numeric_columns:
        stats[column] = pd.to_numeric(stats[column].replace('', pd.NA), errors='coerce')

    return roster, stats

@app.get('/', response_class=HTMLResponse)
def root():
    return HTMLResponse(content=HTML_PAGE, status_code=200)

@app.get('/api/players')
def get_players():
    roster, stats = load_data()
    stats_lookup = stats['full_name'].value_counts().to_dict()

    players = [
        {'name': name, 'stats_available': bool(stats_lookup.get(name))}
        for name in sorted(roster['full_name'].dropna().unique())
    ]
    players.sort(key=lambda item: (not item['stats_available'], item['name']))
    return {'players': players}

@app.get('/api/player')
def get_player(name: str = Query(..., description='Full player name')):
    name = unquote(name).strip()
    roster, stats = load_data()
    bio = roster[roster['full_name'].str.casefold() == name.casefold()]
    if bio.empty:
        raise HTTPException(status_code=404, detail='Player not found')

    player_stats = stats[stats['full_name'].str.casefold() == name.casefold()]
    bio_records = (
        bio.drop(columns=['full_name'])
           .rename(columns={'Number': 'Jersey', 'Exp': 'Experience'})
           .replace({pd.NA: None})
           .to_dict(orient='records')
    )
    player_stats = player_stats.astype(object).where(pd.notna(player_stats), None)
    stats_records = (
        player_stats.drop(columns=['full_name'])
            .replace({pd.NA: None})
            .to_dict(orient='records')
    )
    return {
        'bio': bio_records,
        'stats': stats_records,
    }
