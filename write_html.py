# Write HTML template
import os

html = '''<!DOCTYPE html>
<html lang=\"zh-CN\">
<head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">
<title>Invoice Recon System</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0e1a;--bg2:#111827;--card:#1a1f35;--border:#2a3050;--primary:#00d4ff;--primary-dim:rgba(0,212,255,0.15);--accent:#7c3aed;--success:#10b981;--warn:#f59e0b;--danger:#ef4444;--text:#e2e8f0;--text2:#94a3b8;--font:'Segoe UI',system-ui,sans-serif}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden;
  background-image:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(0,212,255,0.06),transparent),radial-gradient(ellipse 50% 40% at 80% 30%,rgba(124,58,237,0.05),transparent),radial-gradient(ellipse 40% 30% at 20% 70%,rgba(0,212,255,0.04),transparent)}
.bg-grid{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;overflow:hidden}
.bg-grid::before{content:\"\";position:absolute;top:0;left:0;width:200%;height:200%;background-image:linear-gradient(rgba(0,212,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,0.03) 1px,transparent 1px);background-size:60px 60px;transform:rotate(-15deg);animation:gridMove 40s linear infinite}
@keyframes gridMove{0%{transform:rotate(-15deg) translateY(0)}100%{transform:rotate(-15deg) translateY(-60px)}}
.glow-orb{position:fixed;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:0;animation:float 12s ease-in-out infinite}
.glow-orb.orb1{width:400px;height:400px;background:rgba(0,212,255,0.06);top:-100px;right:-100px}
.glow-orb.orb2{width:350px;height:350px;background:rgba(124,58,237,0.06);bottom:-50px;left:-80px;animation-delay:-4s}
.glow-orb.orb3{width:250px;height:250px;background:rgba(16,185,129,0.04);top:40%;left:50%;animation-delay:-8s}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-30px) scale(1.1)}66%{transform:translate(-20px,20px) scale(0.9)}}
.app{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:0 24px 40px}
.header{padding:24px 0 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);margin-bottom:32px}
.header h1{font-size:20px;font-weight:600;background:linear-gradient(135deg,var(--text),var(--primary));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.steps-nav{display:flex;gap:0;margin-bottom:32px;background:var(--card);border-radius:16px;padding:6px;border:1px solid var(--border)}
.step-btn{flex:1;padding:12px 8px;border:none;background:transparent;color:var(--text2);font-size:13px;font-weight:500;cursor:pointer;border-radius:12px;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:8px}
.step-btn:hover{color:var(--text);background:var(--primary-dim)}
.step-btn.active{background:linear-gradient(135deg,var(--primary-dim),var(--accent-dim));color:var(--primary)}
.step-btn .step-num{width:22px;height:22px;border-radius:50%;background:var(--bg2);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600}
.step-btn.active .step-num{background:var(--primary);color:#000}
.step-btn.done .step-num{display:none}
.step-btn.done .step-check{display:inline;color:var(--success)}
.step-btn .step-check{display:none}
.panel{display:none;animation:fadeIn .4s ease}
.panel.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px;margin-bottom:24px;transition:border-color .3s}
.card:hover{border-color:rgba(0,212,255,0.15)}
.card-title{font-size:16px;font-weight:600;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.card-title .icon{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px}
.card-title .icon.blue{background:var(--primary-dim);color:var(--primary)}
select,input[type=\"file\"],textarea{width:100%;padding:12px 16px;background:var(--bg2);border:1px solid var(--border);border-radius:10px;color:var(--text);font-size:14px;outline:none;transition:all .3s}
select:focus,textarea:focus{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-dim)}
textarea{min-height:200px;font-family:monospace;font-size:13px;resize:vertical}
.form-group{margin-bottom:18px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.upload-zone{border:2px dashed var(--border);border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:all .3s;position:relative}
.upload-zone:hover,.upload-zone.dragover{border-color:var(--primary);background:var(--primary-dim)}
.upload-zone input[type=\"file\"]{position:absolute;top:0;left:0;width:100%;height:100%;opacity:0;cursor:pointer}
.btn{padding:10px 24px;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:all .3s;display:inline-flex;align-items:center;gap:8px}
.btn-primary{background:linear-gradient(135deg,var(--primary),#0099cc);color:#000}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(0,212,255,0.3)}
.btn-accent{background:linear-gradient(135deg,var(--accent),#5b21b6);color:#fff}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-outline:hover{border-color:var(--primary);color:var(--primary)}
.table-wrap{overflow-x:auto;border-radius:12px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--bg2);color:var(--text2);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
td{color:var(--text)}
tr:hover td{background:rgba(0,212,255,0.02)}
.tag{padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;display:inline-block}
.tag-ok{background:rgba(16,185,129,0.15);color:var(--success)}
.tag-auto{background:rgba(0,212,255,0.12);color:var(--primary)}
.tag-minor{background:rgba(245,158,11,0.15);color:var(--warn)}
.tag-mismatch{background:rgba(239,68,68,0.15);color:var(--danger)}
.tag-review{background:rgba(124,58,237,0.15);color:var(--accent)}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center}
.stat-card .stat-value{font-size:28px;font-weight:700;margin-bottom:4px}
.stat-card .stat-label{font-size:12px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}
.stat-card .stat-value.green{color:var(--success)}
.stat-card .stat-value.blue{color:var(--primary)}
.stat-card .stat-value.amber{color:var(--warn)}
.stat-card .stat-value.red{color:var(--danger)}
.stat-card .stat-value.purple{color:var(--accent)}
.progress-wrap{height:4px;background:var(--bg2);border-radius:4px;margin:20px 0;overflow:hidden}
.progress-bar{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent));transition:width .6s ease;width:0%}
.loading{display:none;align-items:center;justify-content:center;padding:40px;gap:12px}
.loading.active{display:flex}
.spinner{width:24px;height:24px;border:3px solid var(--border);border-top-color:var(--primary);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.rule-toggle{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--bg2);border-radius:10px;margin-bottom:10px}
.rule-toggle .rule-name{font-size:14px;font-weight:600}
.rule-toggle .rule-desc{font-size:12px;color:var(--text2);margin-top:2px}
.toggle-switch{width:44px;height:24px;background:var(--border);border-radius:12px;position:relative;cursor:pointer;transition:.3s;flex-shrink:0}
.toggle-switch.on{background:var(--primary)}
.toggle-switch::after{content:\"\";position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:.3s}
.toggle-switch.on::after{left:22px}
.rule-params{padding:12px 16px;background:var(--bg2);border-radius:0 0 10px 10px;margin-top:-10px;margin-bottom:10px;display:none}
.rule-params.open{display:block}
.toast{position:fixed;bottom:30px;right:30px;padding:14px 24px;border-radius:12px;font-size:14px;z-index:100;transform:translateY(100px);opacity:0;transition:all .4s}
.toast.show{transform:translateY(0);opacity:1}
.toast-success{background:var(--success);color:#fff}
.toast-error{background:var(--danger);color:#fff}
.toast-info{background:var(--primary);color:#000}
</style></head><body>
<div class=\"bg-grid\"></div>
<div class=\"glow-orb orb1\"></div><div class=\"glow-orb orb2\"></div><div class=\"glow-orb orb3\"></div>

<div class=\"app\">
<header class=\"header\">
<div><h1>Invoice Reconciliation System</h1></div>
<span style=\"padding:6px 14px;border-radius:20px;font-size:12px;background:var(--primary-dim);color:var(--primary);border:1px solid rgba(0,212,255,0.2)\" id=\"statusBadge\">System Ready</span>
</header>

<div class=\"steps-nav\" id=\"stepsNav\">
<button class=\"step-btn active\" data-step=\"0\"><span class=\"step-num\">1</span><span class=\"step-check\">&#10003;</span> Select Supplier</button>
<button class=\"step-btn\" data-step=\"1\"><span class=\"step-num\">2</span><span class=\"step-check\">&#10003;</span> Upload Attendance</button>
<button class=\"step-btn\" data-step=\"2\"><span class=\"step-num\">3</span><span class=\"step-check\">&#10003;</span> Review</button>
<button class=\"step-btn\" data-step=\"3\"><span class=\"step-num\">4</span><span class=\"step-check\">&#10003;</span> Upload Invoices</button>
<button class=\"step-btn\" data-step=\"4\"><span class=\"step-num\">5</span><span class=\"step-check\">&#10003;</span> Reconcile</button>
<button class=\"step-btn\" data-step=\"5\"><span class=\"step-num\">6</span><span class=\"step-check\">&#10003;</span> Results</button>
</div>
<div class=\"progress-wrap\"><div class=\"progress-bar\" id=\"progressBar\"></div></div>

<div class=\"panel active\" id=\"panel0\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon blue\">&#9881;</span> Select Country &amp; Supplier</div>
<div class=\"form-row\">
<div class=\"form-group\"><label>Country</label><select id=\"selCountry\"><option value=\"belgium\">Belgium</option></select></div>
<div class=\"form-group\"><label>Supplier</label><select id=\"selSupplier\"><option value=\"TEMPOTEAM\">TEMPOTEAM</option></select></div>
</div>
<div style=\"margin-top:20px;display:flex;gap:12px\">
<button class=\"btn btn-primary\" onclick=\"goStep(1)\">Next &#8594;</button>
<button class=\"btn btn-outline\" onclick=\"openRules()\">&#9998; Edit Rules</button>
</div></div></div>

<div class=\"panel\" id=\"panel1\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon blue\">&#128196;</span> Upload Attendance Sheet</div>
<div class=\"upload-zone\" id=\"attZone\">
<input type=\"file\" id=\"attFile\" accept=\".xlsx\">
<div style=\"font-size:40px;margin-bottom:12px\">&#128196;</div>
<div>Drop Excel here, or <strong style=\"color:var(--primary)\">browse</strong></div>
<div class=\"file-info\" id=\"attFileInfo\" style=\"margin-top:12px;display:none\"></div>
</div>
<div class=\"loading\" id=\"attLoading\"><div class=\"spinner\"></div><span>Parsing...</span></div>
<div style=\"margin-top:20px;display:flex;gap:12px\">
<button class=\"btn btn-outline\" onclick=\"goStep(0)\">&#8592; Back</button>
<button class=\"btn btn-primary\" id=\"btnParseAtt\" onclick=\"parseAttendance()\">Parse Attendance</button>
</div></div></div>

<div class=\"panel\" id=\"panel2\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon green\">&#128200;</span> Attendance Overview</div>
<div class=\"stats-grid\" id=\"attStats\"></div>
<div class=\"table-wrap\"><table><thead><tr><th>Employee</th><th>Hours</th><th>Days</th><th>Shifts</th></tr></thead><tbody id=\"attTable\"></tbody></table></div>
<div style=\"margin-top:20px\"><button class=\"btn btn-primary\" onclick=\"goStep(3)\">Next &#8594;</button></div>
</div></div>

<div class=\"panel\" id=\"panel3\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon purple\">&#128203;</span> Upload Invoice PDFs</div>
<div class=\"upload-zone\" id=\"invZone\">
<input type=\"file\" id=\"invFiles\" accept=\".pdf\" multiple>
<div style=\"font-size:40px;margin-bottom:12px\">&#128203;</div>
<div>Drop PDFs here, or <strong style=\"color:var(--primary)\">browse</strong> (multiple)</div>
<div class=\"file-info\" id=\"invFileInfo\" style=\"margin-top:12px;display:none\"></div>
</div>
<div class=\"loading\" id=\"invLoading\"><div class=\"spinner\"></div><span>Parsing...</span></div>
<div style=\"margin-top:20px;display:flex;gap:12px\">
<button class=\"btn btn-outline\" onclick=\"goStep(2)\">&#8592; Back</button>
<button class=\"btn btn-primary\" id=\"btnParseInv\" onclick=\"parseInvoices()\">Parse Invoices</button>
</div></div></div>

<div class=\"panel\" id=\"panel4\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon amber\">&#9889;</span> Ready to Reconcile</div>
<div class=\"stats-grid\" id=\"reconPreview\"></div>
<div style=\"text-align:center;padding:20px\">
<button class=\"btn btn-accent\" onclick=\"runRecon()\" style=\"font-size:18px;padding:16px 48px\">&#9889; Run Reconciliation</button>
</div>
<div class=\"loading\" id=\"reconLoading\"><div class=\"spinner\"></div><span>Reconciling...</span></div>
</div></div>

<div class=\"panel\" id=\"panel5\">
<div class=\"card\">
<div class=\"card-title\"><span class=\"icon green\">&#9989;</span> Results</div>
<div class=\"stats-grid\" id=\"resultStats\"></div>
<div class=\"table-wrap\"><table><thead><tr><th>Employee</th><th>Attendance</th><th>Invoice</th><th>Diff</th><th>Verdict</th></tr></thead><tbody id=\"resultTable\"></tbody></table></div>
</div>
<div class=\"card\" id=\"reviewCard\" style=\"display:none\">
<div class=\"card-title\"><span class=\"icon red\">&#9888;</span> Manual Review</div>
<div id=\"reviewContent\"></div>
</div></div>
</div>

<div id=\"rulesModal\" style=\"display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:200;backdrop-filter:blur(4px)\">
<div style=\"max-width:800px;margin:40px auto;background:var(--card);border-radius:16px;border:1px solid var(--border);padding:32px;max-height:85vh;overflow-y:auto\">
<div style=\"display:flex;justify-content:space-between;margin-bottom:24px\">
<h2 style=\"font-size:18px\">&#9998; Rules Editor</h2>
<button onclick=\"closeRules()\" style=\"background:none;border:none;color:var(--text2);font-size:24px;cursor:pointer\">&times;</button>
</div>
<div id=\"rulesContent\"></div>
<div style=\"margin-top:20px;display:flex;gap:12px;justify-content:flex-end\">
<button class=\"btn btn-outline\" onclick=\"closeRules()\">Cancel</button>
<button class=\"btn btn-primary\" onclick=\"saveRules()\">&#128190; Save</button>
</div></div></div>

<div class=\"toast\" id=\"toast\"></div>

<script>
let state={step:0,attendance:null,invoices:null,results:null,currentRules:null};
const panels=['panel0','panel1','panel2','panel3','panel4','panel5'];

function goStep(n){
  state.step=n;
  panels.forEach((p,i)=>{document.getElementById(p).classList.toggle('active',i===n)});
  document.querySelectorAll('.step-btn').forEach((b,i)=>{
    b.classList.toggle('active',i===n);b.classList.toggle('done',i<n)
  });
  document.getElementById('progressBar').style.width=((n/(panels.length-1))*100)+'%';
}

document.getElementById('attFile').onchange=function(){
  const info=document.getElementById('attFileInfo');
  if(this.files.length){info.style.display='block';info.textContent=this.files[0].name+' ('+(this.files[0].size/1024).toFixed(1)+' KB)'}
};
document.getElementById('invFiles').onchange=function(){
  const info=document.getElementById('invFileInfo');
  if(this.files.length){info.style.display='block';info.textContent=this.files.length+' file(s) selected'}
};

async function parseAttendance(){
  const fi=document.getElementById('attFile');
  if(!fi.files.length){toast('Select a file','error');return}
  const fd=new FormData();
  fd.append('file',fi.files[0]);fd.append('country',document.getElementById('selCountry').value);
  fd.append('supplier',document.getElementById('selSupplier').value);
  const el=document.getElementById('attLoading');el.classList.add('active');
  document.getElementById('btnParseAtt').disabled=true;
  try{
    const r=await fetch('/api/parse-attendance',{method:'POST',body:fd});
    const d=await r.json();
    if(d.error){toast(d.error,'error');return}
    state.attendance=d;
    const s=document.getElementById('attStats');
    s.innerHTML='<div class=\"stat-card\"><div class=\"stat-value blue\">'+d.employee_count+'</div><div class=\"stat-label\">Employees</div></div><div class=\"stat-card\"><div class=\"stat-value blue\">'+d.total_hours.toFixed(2)+'h</div><div class=\"stat-label\">Total Hours</div></div><div class=\"stat-card\"><div class=\"stat-value blue\">'+d.period_start+'</div><div class=\"stat-label\">Period</div></div><div class=\"stat-card\"><div class=\"stat-value blue\">'+d.period_end+'</div><div class=\"stat-label\">End</div></div>';
    const tb=document.getElementById('attTable');
    tb.innerHTML='';
    d.employees.forEach(e=>{
      const recs=d.records.filter(r=>r.name===e&&r.status==='present');
      const h=recs.reduce((s,r)=>s+r.hours,0);
      const days=recs.length;
      const shifts=recs.map(r=>r.raw_time).filter(Boolean).join(', ');
      tb.innerHTML+='<tr><td>'+e+'</td><td>'+h.toFixed(2)+'h</td><td>'+days+'</td><td style=\"font-size:11px;color:var(--text2)\">'+shifts+'</td></tr>';
    });
    goStep(2);toast('Parsed: '+d.employee_count+' employees, '+d.total_hours+'h','success');
  }catch(e){toast('Failed: '+e.message,'error')}
  finally{el.classList.remove('active');document.getElementById('btnParseAtt').disabled=false}
}

async function parseInvoices(){
  const fi=document.getElementById('invFiles');
  if(!fi.files.length){toast('Select PDFs','error');return}
  const fd=new FormData();
  for(const f of fi.files)fd.append('files',f);
  const el=document.getElementById('invLoading');el.classList.add('active');
  document.getElementById('btnParseInv').disabled=true;
  try{
    const r=await fetch('/api/parse-invoices',{method:'POST',body:fd});
    const d=await r.json();
    if(d.error){toast(d.error,'error');return}
    state.invoices=d;
    goStep(4);toast(Object.keys(d).length+' invoice(s) parsed','success');
    const p=document.getElementById('reconPreview');
    const att=state.attendance;
    const invCount=Object.keys(d).length;
    const empCount=Object.values(d).reduce((s,i)=>s+(i.employees?i.employees.length:0),0);
    const invHours=Object.values(d).reduce((s,i)=>s+i.total_hours,0);
    p.innerHTML='<div class=\"stat-card\"><div class=\"stat-value green\">'+att.employee_count+'</div><div class=\"stat-label\">Att. Employees</div></div><div class=\"stat-card\"><div class=\"stat-value blue\">'+empCount+'</div><div class=\"stat-label\">Inv. Employees</div></div><div class=\"stat-card\"><div class=\"stat-value amber\">'+invCount+'</div><div class=\"stat-label\">Invoices</div></div><div class=\"stat-card\"><div class=\"stat-value purple\">'+invHours.toFixed(2)+'h</div><div class=\"stat-label\">Inv. Hours</div></div>';
  }catch(e){toast('Failed: '+e.message,'error')}
  finally{el.classList.remove('active');document.getElementById('btnParseInv').disabled=false}
}

async function runRecon(){
  const el=document.getElementById('reconLoading');el.classList.add('active');
  try{
    const r=await fetch('/api/reconcile',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({country:document.getElementById('selCountry').value,supplier:document.getElementById('selSupplier').value})});
    const d=await r.json();
    if(d.error){toast(d.error,'error');return}
    state.results=d;
    const v={};
    d.results.forEach(r=>v[r.verdict]=(v[r.verdict]||0)+1);
    document.getElementById('resultStats').innerHTML=
      '<div class=\"stat-card\"><div class=\"stat-value blue\">'+d.total_att.toFixed(2)+'h</div><div class=\"stat-label\">Attendance</div></div>'+
      '<div class=\"stat-card\"><div class=\"stat-value green\">'+d.total_inv.toFixed(2)+'h</div><div class=\"stat-label\">Invoice</div></div>'+
      '<div class=\"stat-card\"><div class=\"stat-value '+(v.mismatch?'red':'green')+'\">'+(v.auto_approved||0)+'</div><div class=\"stat-label\">Auto OK</div></div>'+
      '<div class=\"stat-card\"><div class=\"stat-value '+((v.mismatch||0)>0?'red':'green')+'\">'+(v.mismatch||0)+'</div><div class=\"stat-label\">Mismatch</div></div>'+
      '<div class=\"stat-card\"><div class=\"stat-value purple\">'+(v.manual_review||0)+'</div><div class=\"stat-label\">Review</div></div>'+
      '<div class=\"stat-card\"><div class=\"stat-value amber\">$'+d.total_amt.toFixed(2)+'</div><div class=\"stat-label\">Amount</div></div>';
    const tb=document.getElementById('resultTable');tb.innerHTML='';
    let reviewHtml='';
    d.results.forEach(r=>{
      const vc=r.verdict==='auto_approved'?'tag-auto':r.verdict==='match'?'tag-ok':r.verdict==='minor_diff'?'tag-minor':r.verdict==='manual_review'?'tag-review':'tag-mismatch';
      const vl=r.verdict==='auto_approved'?'Auto':r.verdict==='match'?'OK':r.verdict==='minor_diff'?'Minor':r.verdict==='manual_review'?'Review':'Mismatch';
      const ds=(r.diff_hours>0?'+':'')+r.diff_hours.toFixed(2);
      const cl=r.diff_hours>0.5?'var(--danger)':r.diff_hours<-0.5?'var(--warn)':'var(--success)';
      tb.innerHTML+='<tr><td>'+r.att_name+'</td><td>'+r.att_hours.toFixed(2)+'h</td><td>'+r.inv_hours.toFixed(2)+'h</td><td style=\"color:'+cl+'\">'+ds+'h</td><td><span class=\"tag '+vc+'\">'+vl+'</span></td></tr>';
      if(r.verdict==='manual_review'||r.verdict==='mismatch'){
        reviewHtml+='<div style=\"padding:10px 14px;background:var(--bg2);border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between\"><span><strong>'+r.att_name+'</strong> '+r.att_hours.toFixed(2)+'h vs '+r.inv_hours.toFixed(2)+'h</span><span class=\"tag '+vc+'\">'+r.verdict+'</span></div>'
      }
    });
    if(reviewHtml){document.getElementById('reviewCard').style.display='block';document.getElementById('reviewContent').innerHTML=reviewHtml}
    goStep(5);toast('Reconciliation complete','success');
  }catch(e){toast('Failed: '+e.message,'error')}
  finally{el.classList.remove('active')}
}

async function openRules(){
  document.getElementById('rulesModal').style.display='block';
  try{
    const r=await fetch('/api/rules/'+document.getElementById('selCountry').value+'/'+document.getElementById('selSupplier').value);
    const d=await r.json();
    if(d.error){toast('No rules found','info');return}
    state.currentRules=d;
    let html='<div class=\"form-group\"><label>Label</label><input id=\"ruleLabel\" value=\"'+d.label+'\" style=\"width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:10px;color:var(--text)\"></div>';
    Object.entries(d.rules).forEach(([key,rule])=>{
      const en=rule.enabled!==false;
      html+='<div class=\"rule-toggle\"><div><div class=\"rule-name\">'+key.replace(/_/g,' ')+'</div><div class=\"rule-desc\">'+(rule.description||'')+'</div></div><div class=\"toggle-switch '+(en?'on':'')+'\" data-key=\"'+key+'\" onclick=\"this.classList.toggle(\\'on\\')\"></div></div>';
      html+='<div class=\"rule-params '+(en?'open':'')+'\" id=\"rp-'+key+'\">';
      Object.entries(rule).forEach(([pk,pv])=>{
        if(pk==='description'||pk==='enabled')return;
        html+='<div class=\"form-group\" style=\"margin-bottom:8px\"><label>'+pk+'</label>';
        if(typeof pv==='boolean')html+='<select data-par="'+key+'" data-key="'+pk+'"><option'+(pv?' selected':'')+'>true</option><option'+(pv?'':' selected')+'>false</option></select>';
        else html+='<input value=\"'+(Array.isArray(pv)?JSON.stringify(pv):pv)+'\" data-par="'+key+'" data-key="'+pk+'" style=\"width:100%;padding:8px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px\">';
        html+='</div>';
      });
      html+='</div>';
    });
    html+='<div class=\"form-group\" style=\"margin-top:16px\"><label>Item Classification (JSON)</label><textarea id=\"ruleItemClass\">'+JSON.stringify(d.item_classification||{},null,2)+'</textarea></div>';
    document.getElementById('rulesContent').innerHTML=html;
  }catch(e){toast('Failed: '+e.message,'error')}
}
function closeRules(){document.getElementById('rulesModal').style.display='none'}

async function saveRules(){
  if(!state.currentRules)return;
  const rules={};
  Object.entries(state.currentRules.rules).forEach(([key,rule])=>{
    const en=document.querySelector('.toggle-switch[data-key="'+key+'"]')?.classList.contains('on');
    rules[key]={...rule,enabled:en};
    document.querySelectorAll('#rp-'+key+' input[data-key],#rp-'+key+' select[data-key]').forEach(el=>{
      const pk=el.dataset.key;let val=el.value;
      if(val==='true')val=true;else if(val==='false')val=false;
      else if(!isNaN(val)&&val!=='')val=parseFloat(val);
      else{try{val=JSON.parse(val)}catch(e){}}
      rules[key][pk]=val;
    });
  });
  let ic;
  try{ic=JSON.parse(document.getElementById('ruleItemClass').value)}catch(e){toast('Invalid JSON','error');return}
  const payload={...state.currentRules,label:document.getElementById('ruleLabel').value,rules,item_classification:ic};
  try{
    const r=await fetch('/api/rules/'+payload.country+'/'+payload.supplier,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await r.json();
    if(d.status==='ok'){state.currentRules=payload;toast('Rules saved','success');closeRules()}
    else toast('Save failed','error');
  }catch(e){toast('Error: '+e.message,'error')}
}

function toast(msg,type){
  const el=document.getElementById('toast');
  el.textContent=msg;el.className='toast toast-'+type+' show';
  setTimeout(()=>el.classList.remove('show'),3500);
}
</script></body></html>
'''

with open(r'project/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done! index.html written')
