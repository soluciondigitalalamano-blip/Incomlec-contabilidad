const fs=require('fs'),vm=require('vm');
const f=process.argv[2], html=fs.readFileSync(f,'utf8');
// 1) todo el JS del archivo debe parsear
const scripts=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(s=>s.trim());
scripts.forEach((s,i)=>{try{new vm.Script(s);}catch(e){console.log('ERROR de sintaxis en script',i,':',e.message);process.exit(1);}});
console.log('sintaxis OK ('+scripts.length+' bloques <script>)');
// 2) coherencia de los datos
function grab(n){const i=html.indexOf('const '+n);let d=0;for(let k=html.indexOf('=',i);k<html.length;k++){const ch=html[k];if(ch==='{'||ch==='[')d++;else if(ch==='}'||ch===']')d--;else if(ch===';'&&d===0)return html.slice(i,k+1);}}
const D={};vm.runInNewContext(['monthlyData','weeklyData','clientData','INV_CLIENTS','INV_NITS','INVOICES'].map(grab).join('\n')+'\nObject.assign(OUT,{monthlyData,weeklyData,clientData,INV_CLIENTS,INV_NITS,INVOICES});',{OUT:D});
const R=n=>Math.round(n*100)/100, fm=n=>R(n).toLocaleString('es-CO');
let bad=0;
if(D.INV_CLIENTS.length!==D.INV_NITS.length){console.log('ERROR: INV_CLIENTS y INV_NITS no miden igual');bad++;}
const meses=Object.keys(D.monthlyData);
console.log('mes         semanas  mensual=suma semanas   facturas=clientes   idx facturas');
let anual=0;
for(const m of meses){
  const mt=D.monthlyData[m].Suplec+D.monthlyData[m].Incomelec+D.monthlyData[m].Intercompany; anual+=mt;
  const ws=(D.weeklyData[m]||[]).reduce((s,w)=>s+w.Incomelec+w.Suplec+w.Intercompany,0);
  const inv=(D.INVOICES[m]||[]);
  const si=inv.reduce((s,r)=>s+r[4]-r[5],0);
  const cs=(D.clientData[m]||[]).reduce((s,c)=>s+c.Incomelec+c.Suplec,0);
  const idxok=inv.every(r=>r[0]>=0&&r[0]<D.INV_CLIENTS.length);
  const a=Math.abs(mt-ws)<2, b=Math.abs(si-cs)<2;
  if(!a||!b||!idxok)bad++;
  console.log(`${m.padEnd(11)} ${String((D.weeklyData[m]||[]).length).padStart(4)}   ${(a?'ok':'DIF '+fm(mt)+' vs '+fm(ws)).padEnd(22)} ${(b?'ok':'DIF').padEnd(18)} ${idxok?'ok':'FUERA DE RANGO'}`);
}
const acum=(D.clientData.Acumulado||[]).reduce((s,c)=>s+c.Incomelec+c.Suplec,0);
const porMes=meses.reduce((s,m)=>s+(D.clientData[m]||[]).reduce((t,c)=>t+c.Incomelec+c.Suplec,0),0);
if(Math.abs(acum-porMes)>2){console.log('ERROR: Acumulado no cuadra');bad++;}else console.log('Acumulado de clientes: ok ('+fm(acum)+')');
console.log('Total grupo 2026 segun el dashboard: $'+fm(anual));
console.log(bad?('\n'+bad+' PROBLEMA(S)'):'\nTodas las validaciones pasaron');
process.exit(bad?1:0);
