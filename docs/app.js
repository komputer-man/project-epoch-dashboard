// Theme toggle logic
const themeToggle = document.getElementById('themeToggle');
const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
let currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', currentTheme);
themeToggle.textContent = currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
themeToggle.addEventListener('click', () => {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  localStorage.setItem('theme', currentTheme);
  themeToggle.textContent = currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
});

// Service data fetch & render as cards
async function fetchData() {
  try {
    const res = await fetch('epoch_dashboard_log.md');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const raw = await res.text();

    const lines = raw
      .split('\n')
      .filter(l => /^\|\s*\d{4}-\d{2}-\d{2}/.test(l));

    if (lines[0]?.includes('Service')) lines.splice(0, 2);

    // Fix: track last "real" timestamp for each service
    const latest = {};
    const lastKnownTime = {};

    lines.forEach(line => {
      const [ time, service, status, lastSeen ] = line
        .replace(/^\|\s*/, '')
        .replace(/\s*\|$/, '')
        .split(/\s*\|\s*/);

      // Always set the latest entry
      latest[service] = { time, status, lastSeen };

      // Track last real timestamp (not N/A)
      if (lastSeen !== 'N/A') {
        lastKnownTime[service] = lastSeen;
      }
    });

    const grid = document.querySelector('.service-grid');
    grid.innerHTML = '';
    Object.entries(latest).forEach(([service, info]) => {
      // Use last real timestamp if lastSeen is N/A
      let displayLastSeen;
      if (info.lastSeen === 'N/A') {
        displayLastSeen = lastKnownTime[service]
          ? new Date(lastKnownTime[service].replace(' ', 'T') + 'Z').toLocaleString('de-DE', { timeZone: 'Europe/Berlin', hour12: false }) + ' CEST'
          : 'N/A';
      } else {
        displayLastSeen = new Date(info.lastSeen.replace(' ', 'T') + 'Z').toLocaleString('de-DE', { timeZone: 'Europe/Berlin', hour12: false }) + ' CEST';
      }

      const card = document.createElement('div');
      card.className = 'service-card';
      card.innerHTML = `
        <div class="service-name">${service}</div>
        <div class="status ${info.status.toLowerCase()}">${info.status}</div>
        <div class="last-seen">
          <abbr title="This is the last time the dashboard checked and updated the status, not a real-time heartbeat.">
            Last Update:
          </abbr><br>
          ${displayLastSeen}
        </div>
      `;
      grid.appendChild(card);
    });

    document.getElementById('lastUpdated').textContent =
      new Date().toLocaleString('de-DE', {
        timeZone: 'Europe/Berlin',
        hour12: false
      });
  } catch (e) {
    console.error('Failed to load data:', e);
  }
}

fetchData();
setInterval(fetchData, 300_000); // Refresh every 5 minutes

// --- GitHub commits widget ---
async function fetchCommits() {
  // Array of [repo, branch, label]
  const targets = [
    {
      repo: 'Project-Epoch/TrinityCore',
      branch: 'only-fixes',
      label: 'only-fixes'
    },
    {
      repo: 'Project-Epoch/TrinityCore',
      branch: 'epoch-core',
      label: 'epoch-core'
    }
  ];
  const out = [];
  for (const t of targets) {
    try {
      const url = `https://api.github.com/repos/${t.repo}/commits?sha=${t.branch}&per_page=3`;
      const res = await fetch(url, {headers: {Accept: 'application/vnd.github+json'}});
      if (!res.ok) throw new Error('GitHub API error');
      const commits = await res.json();

      out.push(`<div class="commit-branch-label">${t.label}</div>`);
      for (const c of commits) {
        const date = new Date(c.commit.author.date).toLocaleString('de-DE', {
          timeZone: 'Europe/Berlin', hour12: false
        });
        out.push(`
          <div class="commit-list-item">
            <div class="commit-message">
              ${c.commit.message.replace(/</g, "&lt;").split('\n')[0]}
            </div>
            <div class="commit-meta">
              <span title="${c.commit.author.name}">${c.commit.author.name}</span>
              <a href="${c.html_url}" class="commit-sha" target="_blank">${c.sha.slice(0,7)}</a>
              <span>${date}</span>
            </div>
          </div>
        `);
      }
    } catch (e) {
      out.push(`<div style="color:var(--offline);margin-bottom:0.8em;">Failed to load ${t.label} commits.</div>`);
    }
  }
  document.getElementById('github-commits-content').innerHTML = out.join('');
}

fetchCommits();
setInterval(fetchCommits, 300_000); // Refresh every 5 min like status

// --- Discord updates placeholder ---
// (To implement: just update #discord-updates-content via API/bot)
