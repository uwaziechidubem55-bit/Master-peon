const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// ===== AUTH GUARD =====
if (!Auth.get()) location.href = '/login.html';

// ===== STATE =====
let currentMode = 'ask';
let terminalVisible = false;

// ===== LOADING SCREEN =====
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const ls = $('#loading-screen');
    if (ls) {
      ls.style.opacity = '0';
      setTimeout(() => {
        ls.classList.add('hidden');
        $('#app').classList.remove('hidden');
      }, 600);
    }
  }, 1200);
});

// ===== LOAD USER =====
async function loadMe() {
  const r = await Auth.api('/api/me');
  if (r.status !== 200) return;
  const m = await r.json();
  $('#u-name').textContent = m.username;
  $('#u-tier').textContent = m.tier.toUpperCase();
}
loadMe();

// ===== MESSAGE SYSTEM =====
function addMsg(role, text) {
  // Remove welcome on first message
  const welc = document.querySelector('.welcome-msg');
  if (welc) welc.remove();

  const d = document.createElement('div');
  d.className = 'msg ' + role;
  const b = document.createElement('div');
  b.className = 'bubble';
  b.textContent = text;
  d.appendChild(b);
  $('#messages').appendChild(d);
  $('#messages').scrollTop = $('#messages').scrollHeight;
}

function addSystemMsg(text) {
  const d = document.createElement('div');
  d.className = 'msg system';
  const b = document.createElement('div');
  b.className = 'bubble';
  b.textContent = text;
  d.appendChild(b);
  $('#messages').appendChild(d);
  $('#messages').scrollTop = $('#messages').scrollHeight;
}

// ===== SEND MESSAGE =====
async function sendMessage() {
  const msg = $('#chat-input').value.trim();
  if (!msg) return;
  $('#chat-input').value = '';
  addMsg('user', msg);
  addSystemMsg('⏳ Processing...');

  // Show terminal drawer automatically in agent mode
  if (currentMode === 'agent' && !terminalVisible) {
    showTerminal();
  }

  const r = await Auth.api('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message: msg })
  });
  // Remove loading
  const sysMsgs = document.querySelectorAll('.msg.system');
  if (sysMsgs.length) sysMsgs[sysMsgs.length - 1].remove();

  if (r.status === 429) {
    addMsg('bot', 'Daily chat limit reached.');
    return;
  }
  const d = await r.json();
  let reply = d.reply || '';
  if (d.tool_request) {
    reply += '\n\n(🔧 Tool request #' + d.tool_request.id + ' queued — waiting for admin approval.)';
  }
  addMsg('bot', reply);
}

$('#chat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
$('#btn-send').addEventListener('click', sendMessage);

// ===== MODE DROPDOWN =====
$('#btn-mode').addEventListener('click', e => {
  e.stopPropagation();
  const popup = $('#mode-popup');
  const isOpen = !popup.classList.contains('hidden');
  closeAllPopups();
  if (!isOpen) popup.classList.remove('hidden');
});

$$('#mode-popup .popup-option').forEach(opt => {
  opt.addEventListener('click', () => {
    currentMode = opt.dataset.mode;
    $('.dropdown-label').textContent = currentMode === 'ask' ? 'Ask' : 'Agent';
    $('#mode-popup').classList.add('hidden');
    addSystemMsg('🔄 Switched to ' + currentMode + ' mode');
  });
});

// ===== MODEL DROPDOWN =====
$('#btn-model').addEventListener('click', e => {
  e.stopPropagation();
  const popup = $('#model-popup');
  const isOpen = !popup.classList.contains('hidden');
  closeAllPopups();
  if (!isOpen) popup.classList.remove('hidden');
});

$$('#model-popup .model-option').forEach(opt => {
  opt.addEventListener('click', () => {
    const name = opt.dataset.model;
    const display = name === 'ai-pro' ? 'AI Pro' : name === 'ai-advance' ? 'AI Advance' : 'AI Master';
    // Just show upgrade modal since all are paid
    $('#model-popup').classList.add('hidden');
    showUpgradeModal();
  });
});

// ===== CLOSE POPUPS ON OUTSIDE CLICK =====
document.addEventListener('click', closeAllPopups);
function closeAllPopups() {
  $$('.popup-card').forEach(p => p.classList.add('hidden'));
}

// ===== + BUTTON → UPGRADE MODAL =====
$('#btn-plus').addEventListener('click', e => {
  e.stopPropagation();
  closeAllPopups();
  showUpgradeModal();
});

function showUpgradeModal() {
  $('#upgrade-modal').classList.remove('hidden');
}
$('#upgrade-close').addEventListener('click', () => {
  $('#upgrade-modal').classList.add('hidden');
});
$('#upgrade-modal').addEventListener('click', e => {
  if (e.target === e.currentTarget) $('#upgrade-modal').classList.add('hidden');
});
$('#upgrade-btn').addEventListener('click', () => {
  window.location.href = '/pricing.html';
});

// ===== COMPUTER BUTTON → COMPUTER MODAL =====
$('#btn-computer').addEventListener('click', e => {
  e.stopPropagation();
  closeAllPopups();
  $('#computer-modal').classList.remove('hidden');
});
$('#computer-close').addEventListener('click', () => {
  $('#computer-modal').classList.add('hidden');
});
$('#computer-modal').addEventListener('click', e => {
  if (e.target === e.currentTarget) $('#computer-modal').classList.add('hidden');
});
$('#cloud-upgrade-btn').addEventListener('click', () => {
  window.location.href = '/pricing.html';
});
$('#comp-local').addEventListener('click', () => {
  addSystemMsg('🖥 Please download the Desktop App for macOS, Windows, or Linux to connect your local machine.');
  $('#computer-modal').classList.add('hidden');
});
$('#comp-cloud').addEventListener('click', () => {
  addSystemMsg('☁️ Cloud Computer requires an upgraded plan. Visit pricing to unlock.');
  $('#computer-modal').classList.add('hidden');
});

// ===== TERMINAL DRAWER =====
function showTerminal() {
  $('#terminal-drawer').classList.remove('hidden');
  terminalVisible = true;
  $('#terminal-input').focus();
}

$('#terminal-close').addEventListener('click', () => {
  $('#terminal-drawer').classList.add('hidden');
  terminalVisible = false;
});

// Keyboard shortcut: Ctrl+` to toggle terminal
document.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === '`') {
    e.preventDefault();
    if (terminalVisible) {
      $('#terminal-drawer').classList.add('hidden');
      terminalVisible = false;
    } else {
      showTerminal();
    }
  }
});

async function runTerminalCommand() {
  const input = $('#terminal-input');
  const cmd = input.value.trim();
  if (!cmd) return;
  input.value = '';

  const out = $('#terminal-output');
  const line = document.createElement('div');
  line.className = 'term-line';
  line.textContent = '$ ' + cmd;
  out.appendChild(line);

  if (cmd === 'clear') {
    out.innerHTML = '';
    return;
  }

  // Parse: first word = tool, rest = args
  const parts = cmd.split(/\s+/);
  const tool = parts[0];
  const args = parts.slice(1);

  // Check if it's a valid known tool
  const knownTools = ['nmap','nikto','sqlmap','hydra','john','hashcat','tcpdump','dirb','ffuf',
    'whatweb','sublist3r','netcat','tshark','whois','medusa','crunch','chisel','ligolo',
    'linpeas','winpeas','pspy','msfconsole','routersploit','burpsuite','netdiscover'];

  if (knownTools.includes(tool)) {
    const resultLine = document.createElement('div');
    resultLine.className = 'term-line term-welcome';
    resultLine.textContent = '⏳ Sending tool request for "' + tool + '"...';
    out.appendChild(resultLine);
    out.scrollTop = out.scrollHeight;

    try {
      const r = await Auth.api('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: 'Run ' + cmd })
      });
      const d = await r.json();
      const resLine = document.createElement('div');
      resLine.className = 'term-line term-success';
      resLine.textContent = '✓ ' + (d.reply || 'Request sent').slice(0, 300);
      out.appendChild(resLine);
    } catch (err) {
      const errLine = document.createElement('div');
      errLine.className = 'term-line term-error';
      errLine.textContent = '✗ Error: ' + err.message;
      out.appendChild(errLine);
    }
  } else {
    const resLine = document.createElement('div');
    resLine.className = 'term-line term-error';
    resLine.textContent = 'Unknown tool. Available: ' + knownTools.slice(0, 8).join(', ') + '...';
    out.appendChild(resLine);
  }
  out.scrollTop = out.scrollHeight;
}

$('#terminal-run').addEventListener('click', runTerminalCommand);
$('#terminal-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    runTerminalCommand();
  }
});

// ===== LOGOUT =====
$('#logout').onclick = () => { Auth.clear(); location.href = '/login.html'; };