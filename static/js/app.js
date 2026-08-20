const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// ===== AUTH GUARD =====
if (!Auth.get()) location.href = '/login.html';

// ===== STATE =====
let currentMode = 'ask';

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

  // If in agent mode, auto-open terminal
  if (currentMode === 'agent' && window.Term) {
    Term.openTerminal();
    Term.runCommand();
  }

  const r = await Auth.api('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message: msg })
  });
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
    // In agent mode, show a shortcut hint
    if (currentMode === 'agent') {
      addSystemMsg('🔄 Agent mode — press Ctrl+` to open terminal, or type a target below.');
    }
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
    $('#model-popup').classList.add('hidden');
    showUpgradeModal();
  });
});

// ===== CLOSE POPUPS =====
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

// ===== COMPUTER MODAL =====
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
  addSystemMsg('🖥 Download the Desktop App for macOS, Windows, or Linux to connect your local machine.');
  $('#computer-modal').classList.add('hidden');
});
$('#comp-cloud').addEventListener('click', () => {
  addSystemMsg('☁️ Cloud Computer requires an upgraded plan. Visit pricing to unlock.');
  $('#computer-modal').classList.add('hidden');
});

// ===== LOGOUT =====
$('#logout').onclick = () => { Auth.clear(); location.href = '/login.html'; };