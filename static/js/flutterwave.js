async function buyTier(tier, period){
  const r = await Auth.api('/api/payments/initiate?tier=' + tier + '&period=' + period);
  const d = await r.json();
  if(d.link) window.location.href = d.link;
  else throw new Error(d.detail || 'Payment error');
}
