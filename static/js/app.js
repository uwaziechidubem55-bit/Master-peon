const $ = s => document.querySelector(s);
if(!Auth.get()) location.href = '/login.html';

async function loadMe(){
  const r = await Auth.api('/api/me'); if(r.status !== 200) return;
  const m = await r.json();
  $('#u-name').textContent = m.username;
  $('#u-tier').textContent = m.tier.toUpperCase();
  $('#u-usage').textContent = m.chats_today + '/' + (m.chat_limit || '∞') +
    ' chats · ' + m.tool_calls_today + '/' + (m.tool_limit || '∞') + ' tools';
}
function addMsg(role, text){
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  const b = document.createElement('div');
  b.className = 'bubble';
  b.textContent = text;
  d.appendChild(b);
  $('#messages').appendChild(d);
  $('#messages').scrollTop = $('#messages').scrollHeight;
}
$('#chat-form').addEventListener('submit', async e => {
  e.preventDefault();
  const msg = $('#chat-input').value.trim(); if(!msg) return;
  $('#chat-input').value = '';
  addMsg('user', msg);
  const r = await Auth.api('/api/chat', { method:'POST', body: JSON.stringify({message: msg}) });
  if(r.status === 429){ addMsg('bot', 'Daily chat limit reached.'); return; }
  const d = await r.json();
  addMsg('bot', d.reply + (d.tool_request ? ' (request #' + d.tool_request.id + ' queued)' : ''));
  loadReqs();
});
async function loadReqs(){
  const r = await Auth.api('/api/tool_requests/mine'); if(r.status !== 200) return;
  const list = await r.json();
  $('#req-list').innerHTML = list.map(x =>
    '<div class="req ' + x.status.toLowerCase() + '">#' + x.id + ' ' + x.tool + ' - ' + x.status +
    (x.output ? '<pre>' + x.output.slice(-800) + '</pre>' : '') +
    (x.reason ? '<div class="deny">' + x.reason + '</div>' : '') + '</div>').join('');
}
loadMe(); loadReqs(); setInterval(loadReqs, 5000);
$('#logout').onclick = () => { Auth.clear(); location.href = '/login.html'; };
