(async()=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));const id=new URLSearchParams(location.search).get('id');
const findBtn=(root,txt)=>{const e=[...root.querySelectorAll('*')].filter(e=>e.textContent.trim()===txt);return e.map(x=>x.closest('[role=button]')).find(Boolean)||e[e.length-1]};
let dlg=null;for(let i=0;i<20;i++){dlg=[...document.querySelectorAll('[role=dialog]')].find(d=>d.innerText.includes('Library ID: '+id));if(dlg)break;await sleep(300)}
if(!dlg)return JSON.stringify({id,err:'nodialog'});
const b=findBtn(dlg,'See ad details');if(!b)return JSON.stringify({id,err:'nobtn'});b.click();
let det=null;for(let i=0;i<20;i++){det=[...document.querySelectorAll('[role=dialog]')].find(d=>d.innerText.includes('Ad details'));if(det)break;await sleep(300)}
if(!det)return JSON.stringify({id,err:'nodetails'});
let hs=[];for(let i=0;i<25;i++){hs=[...det.querySelectorAll('*')].filter(e=>e.textContent.trim()==='Transparency by location');if(hs.length)break;await sleep(300)}if(!hs.length)return JSON.stringify({id,err:'notransp'});(hs.find(x=>x.getAttribute('role')==='link')||hs.map(x=>x.closest('[role=button],[role=link]')).find(Boolean)||hs[0]).click();
let t='';for(let i=0;i<25;i++){t=det.innerText;if(/EU ad delivery[\s\S]*Reach\n[\d,.]+/.test(t))break;await sleep(300)}
const m=t.match(/EU ad delivery\s*\nReach\n([\d,.]+)/);if(!m)return JSON.stringify({id,err:'noreach'});
const reach=+m[1].replace(/[,.]/g,'');const seg=t.split('Reach by location, age and gender')[1]||'';const lines=seg.split('\n').map(s=>s.trim()).filter(Boolean);
const ctry={},age={},gen={};for(let i=0;i+3<lines.length;i++){if(/^\d+$/.test(lines[i+3])&&/^(\d\d-\d\d|65\+|Unknown)$/.test(lines[i+1])&&/^(Male|Female|Unknown)$/.test(lines[i+2])){const v=+lines[i+3];ctry[lines[i]]=(ctry[lines[i]]||0)+v;age[lines[i+1]]=(age[lines[i+1]]||0)+v;gen[lines[i+2]]=(gen[lines[i+2]]||0)+v;i+=3}}
return JSON.stringify({id,reach,ctry,age,gen})})()