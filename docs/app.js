(function(){
const DATA_URL="./data/events.json";
const $=s=>document.querySelector(s);
const els={events:$("#events"),empty:$("#empty"),error:$("#load-error"),status:$("#status"),search:$("#search"),category:$("#category-filter"),count:$("#event-count"),updated:$("#last-update"),clear:$("#clear-filters"),retry:$("#retry"),template:$("#event-template")};
let allEvents=[],range="all";
const normalize=(raw,index)=>{
 const e=raw||{}, pick=(...keys)=>keys.map(k=>e[k]).find(v=>v!==undefined&&v!==null&&v!=="");
 const title=pick("title","name","nome")||"Evento cultural", date=pick("startDate","start_date","date","data","data_inicio","start")||"";
 return {id:pick("id","slug")||title+"-"+date+"-"+index,title:String(title),description:String(pick("description","descricao","summary","resumo")||""),category:String(pick("category","categoria","type","tipo")||"Cultura"),startDate:String(date),endDate:String(pick("endDate","end_date","data_fim")||""),startTime:String(pick("startTime","start_time","time","horario","hora")||""),venue:String(pick("venue","local","location","place","espaco")||"Curitiba"),address:String(pick("address","endereco")||""),price:String(pick("price","preco","valor","ingresso")||""),image:String(pick("image","imageUrl","image_url","imagem","foto")||""),sourceName:String(e.source&&e.source.name||pick("sourceName","fonte","source")||"Fonte original"),url:String(e.source&&e.source.url||pick("url","link","sourceUrl","source_url")||"")};
};
const parsePayload=p=>Array.isArray(p)?{events:p,updatedAt:null}:{events:Array.isArray(p.events)?p.events:Array.isArray(p.data)?p.data:Array.isArray(p.items)?p.items:[],updatedAt:p.updatedAt||p.updated_at||null};
const parseDate=v=>{if(!v)return null;const s=String(v),d=new Date(/^\d{4}-\d{2}-\d{2}$/.test(s)?s+"T12:00:00":s);return isNaN(d.getTime())?null:d};
const today=()=>{const d=new Date();d.setHours(0,0,0,0);return d};
const diff=d=>Math.round((d-today())/86400000);
const inRange=e=>{if(range==="all")return true;const d=parseDate(e.startDate);if(!d)return false;const n=diff(d);if(range==="today")return n===0;if(range==="tomorrow")return n===1;if(range==="week")return n>=0&&n<=7;if(range==="weekend"){const now=new Date().getDay(),until=(6-now+7)%7,s=until===0?0:until;return n>=s&&n<=s+1}return true};
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const matches=(e,q)=>!q||norm([e.title,e.category,e.venue,e.address,e.description].join(" ")).includes(norm(q));
const dateBadge=v=>{const d=parseDate(v);return d?{day:d.toLocaleDateString("pt-BR",{day:"2-digit"}),month:d.toLocaleDateString("pt-BR",{month:"short"}).replace(".","")}:{day:"—",month:"data"}};
const dateText=v=>{const d=parseDate(v);return d?d.toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"long"}):""};
function render(){
 const q=els.search.value.trim(),cat=els.category.value;
 const list=allEvents.filter(e=>inRange(e)&&(cat==="all"||norm(e.category)===norm(cat))&&matches(e,q)).sort((a,b)=>(parseDate(a.startDate)?.getTime()||Infinity)-(parseDate(b.startDate)?.getTime()||Infinity));
 els.events.innerHTML="";els.empty.hidden=list.length>0;els.clear.hidden=!(q||cat!=="all"||range!=="all");els.count.textContent=list.length+" "+(list.length===1?"evento":"eventos");
 list.forEach(e=>{
  const f=els.template.content.cloneNode(true), b=dateBadge(e.startDate);
  f.querySelector(".day").textContent=b.day;f.querySelector(".month").textContent=b.month;f.querySelector(".category-badge").textContent=e.category;f.querySelector(".event-title").textContent=e.title;
  f.querySelector(".time").textContent=e.startTime?"◷ "+dateText(e.startDate)+" · "+e.startTime:"◷ "+dateText(e.startDate);
  f.querySelector(".venue").textContent="⌖ "+e.venue+(e.address?" · "+e.address:"");f.querySelector(".price").textContent=e.price||"Informações na fonte";
  const link=f.querySelector(".event-link");link.href=e.url||"#";if(!e.url)link.style.display="none";
  const img=f.querySelector(".event-image");if(e.image){img.src=e.image;img.alt=e.title;img.onerror=()=>img.removeAttribute("src")}else img.removeAttribute("src");
  els.events.appendChild(f);
 });
}
function categories(){const cats=[...new Set(allEvents.map(e=>e.category).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"pt-BR"));els.category.innerHTML='<option value="all">Todas as categorias</option>';cats.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;els.category.appendChild(o)})}
async function load(){
 els.error.hidden=true;els.empty.hidden=true;els.status.textContent="Carregando eventos…";
 try{const r=await fetch(DATA_URL+"?v="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);const p=parsePayload(await r.json());
  allEvents=p.events.map(normalize).filter(e=>e.title).filter(e=>{const d=parseDate(e.startDate);return !d||d.getTime()>=today().getTime()-86400000});
  categories();render();
  const stamp=p.updatedAt?new Date(p.updatedAt):null;els.updated.textContent=stamp&&!isNaN(stamp.getTime())?"Atualizado "+stamp.toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"Dados atualizados automaticamente";
  els.status.textContent=allEvents.length?"":"A fonte de dados ainda não publicou eventos.";
 }catch(err){console.error(err);els.events.innerHTML="";els.error.hidden=false;els.status.textContent="";els.count.textContent="— eventos"}
}
function clear(){els.search.value="";els.category.value="all";range="all";document.querySelectorAll(".date-tab").forEach(b=>b.classList.toggle("active",b.dataset.range==="all"));render()}
document.querySelectorAll(".date-tab").forEach(b=>b.addEventListener("click",()=>{range=b.dataset.range;document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x===b));render()}));
els.search.addEventListener("input",render);els.category.addEventListener("change",render);els.clear.addEventListener("click",clear);els.retry.addEventListener("click",load);
document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();els.search.focus()}if(e.key==="Escape"&&document.activeElement===els.search)els.search.blur()});
load();
})();