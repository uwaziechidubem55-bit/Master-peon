const $ = s => document.querySelector(s);
const esc = s => (s || '').replace(/</g, '&lt;');
if(!Auth.get()){ document.getElementById('login-view').classList.remove('hidden'); }
else { enter(); }

$('#admin-login').addEventListener('submit', async e => {
  e.preventDefault();
  const r = await fetch('/api/auth/login', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ email: $('#auser').value.trim(), password: $('#apass').value }) });
  const d = await r.json();
  if(r.status !== 200){ $('#aerr').textContent = 'Access denied'; return; }
  Auth.set(d.token); enter();
});
function enter(){
  $('#login-view').classList.add('hidden');
  $('#panel').classList.remove('hidden');
  loadAll();
}
$('#alogout').onclick = () => { Auth.clear(); location.reload(); };

document.querySelectorAll('.tab-btn').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  document.querySelectorAll('.tabpane').forEach(x => x.classList.add('hidden'));
  $('#' + b.dataset.tab).classList.remove('hidden');
});

function loadAll(){ stats(); queue(); users(); pricing(); policy(); finance(); }

async function stats(){
  const r = await Auth.api('/api/admin/stats'); if(r.status !== 200) return;
  const d = await r.json();
  $('#s-users').textContent = d.users;
  $('#s-pending').textContent = d.pending;
  $('#s-rev').textContent = '$' + d.revenue;
}
async function queue(){
  const r = await Auth.api('/api/admin/queue'); if(r.status !== 200) return;
  const list = await r.json();
  $('#q-list').innerHTML = list.length ? list.map(x =>
    '<div class="card row"><div><b>#' + x.id + '</b> ' + esc(x.tool) +
    ' <code>' + esc(x.args) + '</code> (user ' + x.user_id + ')</div>' +
    '<div><button class="btn-gold" onclick="approve(' + x.id + ')">Approve</button> ' +
    '<button class="btn-red" onclick="deny(' + x.id + ')">Deny</button></div></div>').join('')
    : '<p class="muted">No pending requests</p>';
}
async function approve(id){ await Auth.api('/api/admin/approve/' + id, { method:'POST' }); queue(); }
async function deny(id){
  const reason = prompt('Reason for denial:') || '';
  await Auth.api('/api/admin/deny/' + id + '?reason=' + encodeURIComponent(reason), { method:'POST' });
  queue();
}
async function users(){
  const r = await Auth.api('/api/admin/users'); if(r.status !== 200) return;
  const list = await r.json();
  $('#u-list').innerHTML = list.map(u =>
    '<div class="card row"><div><b>' + esc(u.username) + '</b> - ' + u.tier +
    (u.expiry ? ' · exp ' + u.expiry : '') +
    (u.suspended ? ' <span class="bad">SUSPENDED</span>' : '') +
    '<div class="small"><a href="' + u.selfie_smile + '" target="_blank">Smile</a> · ' +
    '<a href="' + u.selfie_vex + '" target="_blank">Vex</a></div></div>' +
    '<button class="btn-' + (u.suspended ? 'gold' : 'red') + '" onclick="suspend(' + u.id + ')">' +
    (u.suspended ? 'Unsuspend' : 'Suspend') + '</button></div>').join('');
}
async function suspend(id){ await Auth.api('/api/admin/users/' + id + '/suspend', { method:'POST' }); users(); }

async function pricing(){
  const r = await Auth.api('/api/admin/limits'); if(r.status !== 200) return;
  const t = await r.json();
  $('#p-edit').innerHTML = Object.keys(t).map(k => {
    const v = t[k];
    return '<div class="card"><h4>' + k.toUpperCase() + '</h4>' +
      '<label>Chats/day <input id="L_' + k + '_chats" type="number" value="' + v.chats + '"></label>' +
      '<label>Tool calls/day <input id="L_' + k + '_toolcalls" type="number" value="' + v.tool_calls + '"></label>' +
      '<label>Price month <input id="L_' + k + '_pm" type="number" step="0.01" value="' + v.price_month + '"></label>' +
      '<label>Price year <input id="L_' + k + '_py" type="number" step="0.01" value="' + v.price_year + '"></label>' +
      '<label>Tools (comma list, ALL = everything) <input id="L_' + k + '_tools" type="text" value="' + (v.tools || []).join(',') + '"></label></div>';
  }).join('');
}
$('#p-save').onclick = async () => {
  const tiers = {};
  ['free','pro','master'].forEach(k => {
    const tools = $('#L_' + k + '_tools').value.split(',').map(s => s.trim()).filter(Boolean);
    tiers[k] = {
      chats: +$('#L_' + k + '_chats').value,
      tool_calls: +$('#L_' + k + '_toolcalls').value,
      price_month: +$('#L_' + k + '_pm').value,
      price_year: +$('#L_' + k + '_py').value,
      tools: tools.length ? tools : ['ALL']
    };
  });
  await Auth.api('/api/admin/limits', { method:'POST', body: JSON.stringify({ tiers }) });
  alert('Saved');
};

async function policy(){
  const r = await Auth.api('/api/admin/policy'); if(r.status !== 200) return;
  const list = await r.json();
  $('#p-rules').value = list.map(x => x.text).join('\n');
}
$('#p-enforce').onclick = async () => {
  const rules = $('#p-rules').value.split('\n').map(s => s.trim()).filter(Boolean);
  await Auth.api('/api/admin/policy/enforce', { method:'POST', body: JSON.stringify({ rules }) });
  alert('Policy enforced');
};

async function runTool(){
  const tool = $('#t-tool').value;
  const raw = $('#t-args').value.trim();
  const args = raw ? raw.split(/\s+/) : [];
  const r = await Auth.api('/api/admin/run-tool', { method:'POST', body: JSON.stringify({ tool, args }) });
  const d = await r.json();
  $('#t-out').textContent = r.status === 200 ? (d.output || 'done') : (d.detail || 'error');
}
async function finance(){
  const r = await Auth.api('/api/admin/finance'); if(r.status !== 200){ $('#f-bal').textContent = 'Set FLW_SECRET_KEY in .env'; return; }
  const d = await r.json();
  $('#f-bal').textContent = JSON.stringify(d.balance);
}
$('#f-withdraw').onclick = async () => {
  const amt = +$('#f-amt').value;
  const r = await Auth.api('/api/payments/withdraw?amount=' + amt, { method:'POST' });
  $('#f-out').textContent = JSON.stringify(await r.json());
};
