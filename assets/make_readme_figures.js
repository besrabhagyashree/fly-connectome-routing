const fs=require('fs');const OUT=process.argv[2];
const T={light:{bg:'#ffffff',fg:'#1d1c45',muted:'#6b6a86',line:'#dddcea',ind:'#33318a',pink:'#b53b6d',soft:'#f3f2fa',amber:'#b87400'},
         dark:{bg:'#0d1117',fg:'#e8e7f5',muted:'#9d9cb8',line:'#2c2b45',ind:'#8f8cf0',pink:'#ec6fa0',soft:'#161530',amber:'#f2b437'}};
const F='font-family="Segoe UI, Helvetica, Arial, sans-serif"';
function rng(s){return()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296}}
const deg=[123.7,117.6,118.5,121.9,118.3,124.3,123.4,105.6,124.8,113.1,121.3,113.1,118.5,123.4,131.1,120.5,121.3,127.5,124.9,124.1,122.9,122.0,130.2,123.4,121.1,121.8,115.0,131.2,119.5,134.2,122.3,114.8,120.3,124.6,126.6];
const in1=[17.201,17.168,17.202,17.193,17.188,17.199,17.196,17.188,17.160,17.189,17.200,17.197,17.202,17.199,17.201,17.188,17.203,17.208,17.193,17.192,17.185,17.200,17.151,17.194,17.188,17.192,17.192,17.191,17.187,17.193,17.197,17.197,17.175,17.200,17.190];
const in2=[17.164,17.162,17.167,17.175,17.165,17.165,17.172,17.161,17.168,17.171,17.152,17.170,17.163,17.171,17.171,17.157,17.165,17.170,17.168,17.173,17.161,17.164,17.150,17.166,17.162,17.174,17.163,17.165,17.159,17.169,17.178,17.160,17.164,17.164,17.172];
const blk=[102.8,101.5,100.2,99.6,107.8,100.5,103.9,101.7,103.2,98.7,101.6,101.9,103.7,104.3,101.2,100.0,100.8,103.8,100.3,97.8,100.8,101.1,104.0,101.8,101.2,99.4,101.2,99.5,97.1,97.6,103.5,102.4,97.2,98.6,100.7];

for(const [mode,c] of Object.entries(T)){
  // Banner
  let s=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 260" ${F}><rect width="1200" height="260" rx="14" fill="${c.soft}"/>`;
  const r=rng(7);
  for(let i=0;i<70;i++){const x=640+r()*540,y=20+r()*220,x2=x+(r()-.5)*160,y2=y+(r()-.5)*120;
    s+=`<line x1="${x.toFixed(1)}" y1="${y.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${c.ind}" stroke-opacity=".18" stroke-width="1"/>`}
  const r2=rng(11);
  for(let i=0;i<55;i++){const x=640+r2()*540,y=20+r2()*220;
    s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(2+r2()*3).toFixed(1)}" fill="${c.ind}" fill-opacity=".35"/>`}
  const pts=[[700,190],[810,150],[930,165],[1040,100],[1140,80]];
  s+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${c.pink}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
  pts.forEach((p,i)=>{s+=`<circle cx="${p[0]}" cy="${p[1]}" r="${i===0||i===4?7:5}" fill="${c.pink}"/>`});
  s+=`<text x="700" y="215" font-size="12" fill="${c.pink}" text-anchor="middle">sense</text>`;
  s+=`<text x="1140" y="62" font-size="12" fill="${c.pink}" text-anchor="middle">descending neuron</text>`;
  s+=`<text x="48" y="92" font-size="42" font-weight="700" fill="${c.fg}">fly-connectome-routing</text>`;
  s+=`<text x="48" y="134" font-size="20" fill="${c.fg}">Where do senses reach the brain-to-body neurons,</text>`;
  s+=`<text x="48" y="162" font-size="20" fill="${c.fg}">and is it the wiring or the statistics?</text>`;
  s+=`<text x="48" y="212" font-size="15" fill="${c.muted}">FlyWire v783 · 139,255 neurons · 2.7M connections · null-model tests</text></svg>`;
  fs.writeFileSync(`${OUT}/banner-${mode}.svg`,s);

  // Results strip plot (real data)
  const X0=230,X1=1110,max=140,sx=v=>X0+(X1-X0)*v/max;
  let q=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 440" ${F}><rect width="1160" height="440" fill="${c.bg}"/>`;
  q+=`<text x="24" y="36" font-size="18" font-weight="700" fill="${c.fg}">How widely each sense spreads over the 1,305 descending neurons</text>`;
  q+=`<text x="24" y="60" font-size="13" fill="${c.muted}">Participation ratio, mean over 7 senses. Lower = more focused. Each dot is one whole brain.</text>`;
  for(let v=0;v<=max;v+=20){
    q+=`<line x1="${sx(v)}" x2="${sx(v)}" y1="80" y2="380" stroke="${c.line}"/>`;
    q+=`<text x="${sx(v)}" y="400" font-size="12" fill="${c.muted}" text-anchor="middle">${v}</text>`}
  q+=`<text x="${(X0+X1)/2}" y="426" font-size="12" fill="${c.muted}" text-anchor="middle">effective number of descending neurons carrying the signal</text>`;
  const rows=[['Real brain',[17.1],c.ind,105,'17.1',false],
              ['Standard shuffle (degree)',deg,c.pink,165,'mean 122',false],
              ['Standard shuffle (block)',blk,c.pink,225,'mean 101',false],
              ['Inside-only (degree)',in1,c.amber,285,'mean 17.19 · all 35 above real',false],
              ['Inside-only (block)',in2,c.amber,345,'mean 17.17 · all 35 above real',false]];
  const rr=rng(3);
  rows.forEach(([lab,vals,col,y,note,hollow])=>{
    q+=`<text x="${X0-16}" y="${y+5}" font-size="14" font-weight="600" fill="${c.fg}" text-anchor="end">${lab}</text>`;
    vals.forEach(v=>{const yy=vals.length>1?y+(rr()-.5)*26:y;
      q+=hollow?`<circle cx="${sx(v).toFixed(1)}" cy="${yy}" r="7" fill="none" stroke="${col}" stroke-width="2.5"/>`
               :`<circle cx="${sx(v).toFixed(1)}" cy="${yy.toFixed(1)}" r="${vals.length>1?4.5:7}" fill="${col}" fill-opacity="${vals.length>1?.65:1}"/>`});
    const m=vals.reduce((a,b)=>a+b)/vals.length;
    q+=`<text x="${(sx(m)+(vals.length>1?0:14)).toFixed(1)}" y="${vals.length>1?y-20:y+5}" font-size="12" fill="${col}" font-weight="600" text-anchor="${vals.length>1?'middle':'start'}">${note}</text>`});
  q+=`</svg>`;
  fs.writeFileSync(`${OUT}/results-${mode}.svg`,q);

  // Mechanism: what each shuffle may change
  const P={S:[50,125],I1:[160,75],I2:[160,125],I3:[160,175],D1:[270,75],D2:[270,125],D3:[270,175]};
  const R={S:13,I1:10,I2:10,I3:10,D1:11,D2:11,D3:11};
  const panels=[["Real brain",[["S","I1","b"],["I1","I2","i"],["I2","D2","b"],["I3","D1","b"],["I3","D3","b"],["I2","I3","i"]],"smell→DN direct 0.012% · spread 17.1"],
    ["Standard shuffle",[["S","D1","s"],["I1","I2","i"],["I2","D2","b"],["I3","I1","i"],["I3","D3","b"],["I2","I3","i"]],"3.2–10.6% · spread ~101–122"],
    ["Inside-only shuffle",[["S","I1","b"],["I1","I3","i"],["I2","D2","b"],["I3","D1","b"],["I3","D3","b"],["I3","I2","i"]],"0.012% · spread 17.2 (35 + 35 brains)"]];
  const col={b:c.fg,i:c.muted,s:c.pink};
  let m=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 300" ${F}><rect width="1000" height="300" fill="${c.bg}"/><defs>`;
  for(const k of ['b','i','s'])m+=`<marker id="m${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0L10,5L0,10z" fill="${col[k]}"/></marker>`;
  m+=`</defs>`;
  panels.forEach(([t,E,st],k)=>{const ox=20+k*330;
    m+=`<text x="${ox+160}" y="30" font-size="16" font-weight="700" fill="${c.fg}" text-anchor="middle">${t}</text>`;
    E.forEach(([a,b,ty])=>{const[x1,y1]=P[a],[x2,y2]=P[b],dx=x2-x1,dy=y2-y1,L=Math.hypot(dx,dy);
      m+=`<line x1="${(ox+x1+dx/L*R[a]).toFixed(1)}" y1="${(y1+dy/L*R[a]+10).toFixed(1)}" x2="${(ox+x2-dx/L*(R[b]+3)).toFixed(1)}" y2="${(y2-dy/L*(R[b]+3)+10).toFixed(1)}" stroke="${col[ty]}" stroke-width="${ty==='s'?2.8:ty==='b'?2.2:1.4}" ${ty==='i'?'stroke-dasharray="5 4"':''} marker-end="url(#m${ty})"/>`;
      if(ty==='s')m+=`<text x="${ox+(x1+x2)/2-6}" y="${(y1+y2)/2}" font-size="12" font-weight="600" fill="${c.pink}" text-anchor="middle">1-hop shortcut</text>`});
    Object.entries(P).forEach(([n,[x,y]])=>{y+=10;
      m+=n[0]==='D'?`<rect x="${ox+x-11}" y="${y-11}" width="22" height="22" rx="4" fill="${c.bg}" stroke="${c.fg}" stroke-width="1.5"/>`
                  :`<circle cx="${ox+x}" cy="${y}" r="${R[n]}" fill="${n==='S'?c.amber:c.bg}" stroke="${n==='S'?c.amber:c.fg}" stroke-width="1.5"/>`});
    [['sense',50],['inside',160],['descending',270]].forEach(([l,x])=>{m+=`<text x="${ox+x}" y="222" font-size="12" fill="${c.muted}" text-anchor="middle">${l}</text>`});
    m+=`<text x="${ox+160}" y="250" font-size="13" fill="${c.muted}" text-anchor="middle">${st}</text>`});
  m+=`<line x1="250" y1="280" x2="280" y2="280" stroke="${c.fg}" stroke-width="2.2"/><text x="288" y="284" font-size="12" fill="${c.muted}">boundary edge</text>`;
  m+=`<line x1="410" y1="280" x2="440" y2="280" stroke="${c.muted}" stroke-width="1.4" stroke-dasharray="5 4"/><text x="448" y="284" font-size="12" fill="${c.muted}">inside edge</text>`;
  m+=`<line x1="550" y1="280" x2="580" y2="280" stroke="${c.pink}" stroke-width="2.8"/><text x="588" y="284" font-size="12" fill="${c.muted}">shortcut created by shuffling</text></svg>`;
  fs.writeFileSync(`${OUT}/shuffles-${mode}.svg`,m);

  // Pipeline: swimlanes, labelled data flows, gate. Edit STATUS as steps progress.
  const STATUS={data:'done',s1:'done',s2:'done',s3:'done',s4:'done',s5:'done',s6:'done',s7:'done',out:'wait'};
  const stc={done:mode==='light'?'#1f8a5c':'#3fcf98',run:c.amber,wait:c.muted};
  let p=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1250 470" ${F}><rect width="1250" height="470" fill="${c.bg}"/><defs>`;
  [['a',c.muted],['y',stc.done],['n',c.pink]].forEach(([k,f])=>{p+=`<marker id="p${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="${f}"/></marker>`});
  p+=`</defs>`;
  ['DATA','SHUFFLES','SIMULATION','VALIDATION','OUTPUT'].forEach((l,i)=>{const y=20+i*80;
    if(i%2===0)p+=`<rect x="0" y="${y}" width="1250" height="80" fill="${c.soft}"/>`;
    p+=`<text x="16" y="${y+44}" font-size="11" font-weight="700" letter-spacing="1" fill="${c.muted}">${l}</text>`});
  const E=(d,lab,lx,ly,kind='a',anchor='middle')=>{const sc=kind==='y'?stc.done:kind==='n'?c.pink:c.muted;
    p+=`<path d="${d}" fill="none" stroke="${sc}" stroke-width="1.5" marker-end="url(#p${kind})"/>`;
    if(lab)p+=`<text x="${lx}" y="${ly}" font-size="11" fill="${sc}" text-anchor="${anchor}"${kind!=='a'?' font-weight="700"':''}>${lab}</text>`};
  E('M205,86 V140 H316','2.7M edges',262,133);
  E('M470,140 H506','graphs',488,133);
  E('M395,166 V220 H506','70 brains',452,213);
  E('M660,220 H696','reach',678,213);
  E('M850,220 H886','yes',868,213,'y');
  // Gate rule (empirical permutation p, both inside-only types). The map comparison is not behind the gate.
  E('M775,192 V170 H846','no',783,186,'n','start');
  p+=`<text x="852" y="174" font-size="11" font-weight="700" fill="${c.pink}">skip scaling</text>`;
  p+=`<text x="775" y="262" font-size="10" fill="${c.muted}" text-anchor="middle">p &lt; 0.05 for both types</text>`;
  E('M585,246 V270','~17 DNs per sense',593,264,'a','start');
  E('M470,300 H506','root_id',488,293);
  E('M660,300 H696','labels',678,293);
  E('M850,300 H886','labels',868,293);
  E('M395,114 V100 H1155 V190','same inside-only rewire code',775,94);
  E('M1040,220 H1060 V380 H1076');
  p+=`<path d="M1040,300 H1060" fill="none" stroke="${c.muted}" stroke-width="1.5"/>`;
  E('M1155,246 V350');
  const N=(x,y,t,sub,st)=>{const col=stc[st];
    p+=`<g transform="translate(${x},${y})"><rect width="150" height="52" rx="6" fill="${c.bg}" stroke="${col}" stroke-width="${st==='run'?2.5:1.5}"${st==='wait'?' stroke-dasharray="4 3"':''}/>`+
       `<circle cx="137" cy="12" r="5" fill="${col}"/><text x="12" y="23" font-size="13" font-weight="700" fill="${c.fg}">${t}</text>`+
       `<text x="12" y="40" font-size="11" fill="${c.muted}">${sub}</text></g>`};
  N(130,34,'FlyWire v783','139k neurons',STATUS.data);
  N(320,114,'Inside-only shuffle','boundary locked',STATUS.s1);
  N(510,114,'Shortcut stats','7 senses',STATUS.s2);
  N(510,194,'Rate model runs','35 × 2 shuffles',STATUS.s1);
  p+=`<g transform="translate(775,220)"><polygon points="0,-28 75,0 0,28 -75,0" fill="${c.bg}" stroke="${stc.done}" stroke-width="2"/>`+
     `<text x="0" y="-3" font-size="11" font-weight="700" fill="${c.fg}" text-anchor="middle">Real more focused</text>`+
     `<text x="0" y="11" font-size="11" font-weight="700" fill="${c.fg}" text-anchor="middle">than shuffles?</text></g>`;
  N(890,194,'Scale to 200','p floor 1/201',STATUS.s5);
  N(1080,194,'Shiu spiking model','50 + 50 + 19 brains',STATUS.s6);
  N(320,274,'Stürner DN table','1,315 DNs',STATUS.s3);
  N(510,274,'Behaviour labels','published only',STATUS.s3);
  N(700,274,'Simulation vs map','flow model',STATUS.s4);
  N(890,274,'Leakage','cross-behaviour',STATUS.s7);
  N(1080,354,'Preprint + code','public repo',STATUS.out);
  [['done','done'],['run','in progress'],['wait','planned']].forEach(([k,l],i)=>{const x=130+i*150;
    p+=`<rect x="${x}" y="440" width="22" height="14" rx="3" fill="${c.bg}" stroke="${stc[k]}" stroke-width="${k==='run'?2.5:1.5}"${k==='wait'?' stroke-dasharray="4 3"':''}/>`+
       `<text x="${x+30}" y="451" font-size="12" fill="${c.muted}">${l}</text>`});
  p+=`</svg>`;
  fs.writeFileSync(`${OUT}/pipeline-${mode}.svg`,p);
}
