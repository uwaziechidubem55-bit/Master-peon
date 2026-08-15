const Auth = {
  TOKEN_KEY: 'mp_token',
  set(t){ localStorage.setItem(this.TOKEN_KEY, t); },
  get(){ return localStorage.getItem(this.TOKEN_KEY); },
  clear(){ localStorage.removeItem(this.TOKEN_KEY); },
  async api(url, opts={}){
    opts.headers = opts.headers || {};
    if(this.get()) opts.headers['Authorization'] = 'Bearer ' + this.get();
    if(opts.body && typeof opts.body === 'string')
      opts.headers['Content-Type'] = 'application/json';
    const r = await fetch(url, opts);
    if(r.status === 401){ this.clear(); location.href = '/login.html'; }
    return r;
  }
};
