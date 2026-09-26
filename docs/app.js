(function(){
const DATA_URL="./agenda.json";
const WEATHER_URL="https://api.open-meteo.com/v1/forecast?latitude=-25.4284&longitude=-49.2733&current=temperature_2m,weather_code&timezone=America%2FSao_Paulo";
const $=s=>document.querySelector(s);
const els={events:$("#events"),empty:$("#empty"),error:$("#load-error"),status:$("#status"),search:$("#search"),category:$("#category-filter"),count:$("#event-count"),updated:$("#last-update"),clear:$("#clear-filters"),retry:$("#retry"),template:$("#event-template"),weather:$("#weather-temp"),weatherLabel:$("#weather-label")};
let allEvents=[],range="all";
const pick=(e,...keys)=>keys.map(k=>e&&e[k]).find(v=>v!==undefined&&v!==null&&v!=="");
const normalize=(raw,index)=>{
 const e=raw||{}, title=pick(e,"title","name","nome")||"Evento cultural", summary=String(pick(e,"description","descricao","summary","resumo")||"");
 const m=summary.match(/\b(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})\b/);
 const date=pick(e,"startDate","start_date","date","data","data_inicio","start")||(m?(m[3].length===2?"20"+m[3]:m[3])+"-"+m[2].padStart(2,"0")+"-"+m[1].padStart(2,"0"):"");
 const source=typeof e.source==="object"?e.source:{};
 return {id:pick(e,"id","slug")||title+"-"+date+"-"+index,title:String(title),description:summary,category:String(pick(e,"category","categoria","type","tipo")||"Cultura"),startDate:String(date),endDate:String(pick(e,"endDate","end_date","data_fim")||""),startTime:String(pick(e,"startTime","start_time","time","horario","hora")||""),venue:String(pick(e,"venue","local","location","place","espaco")||"Curitiba"),address:String(pick(e,"address","endereco")||""),price:String(pick(e,"price","preco","valor","ingresso")||""),image:String(pick(e,"image","imageUrl","image_url","imagem","foto")||""),sourceName:String(source.name||pick(e,"sourceName","fonte","source")||"Fonte original"),url:String(source.url||pick(e,"url","link","sourceUrl","source_url")||"")};
};
const parsePayload=p=>Array.isArray(p)?{events:p,updatedAt:null}:{events:Array.isArray(p.events)?p.events:Array.isArray(p.items)?p.items:Array.isArray(p.data)?p.data:[],updatedAt:p.updatedAt||p.updated_at||null};
const parseDate=v=>{if(!v)return null;const s=String(v).trim(),d=new Date(/^\d{4}-\d{2}-\d{2}$/.test(s)?s+"T12:00:00":s);return isNaN(d.getTime())?null:d};
const today=()=>{const d=new Date();d.setHours(0,0,0,0);return d};
const diff=d=>Math.round((d-today())/86400000);
const inRange=e=>{if(range==="all")return true;const d=parseDate(e.startDate);if(!d)return false;const n=diff(d);if(range==="today")return n===0;if(range==="tomorrow")return n===1;if(range==="week")return n>=0&&n<=7;if(range==="weekend"){const day=today().getDay(),toSat=(6-day+7)%7;return n>=toSat&&n<=toSat+1}return true};
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const matches=(e,q)=>!q||norm([e.title,e.category,e.venue,e.address,e.description].join(" ")).includes(norm(q));
const dateBadge=v=>{const d=parseDate(v);return d?{day:d.toLocaleDateString("pt-BR",{day:"2-digit"}),month:d.toLocaleDateString("pt-BR",{month:"short"}).replace(".","")}:{day:"—",month:"data"}};
const dateText=v=>{const d=parseDate(v);return d?d.toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"long"}):"Data a confirmar"};
function render(){
 const q=els.search.value.trim(),cat=els.category.value;
 const list=allEvents.filter(e=>inRange(e)&&(cat==="all"||norm(e.category)===norm(cat))&&matches(e,q)).sort((a,b)=>(parseDate(a.startDate)?.getTime()||Infinity)-(parseDate(b.startDate)?.getTime()||Infinity));
 els.events.innerHTML="";els.empty.hidden=list.length>0;els.clear.hidden=!(q||cat!=="all"||range!=="all");els.count.textContent=list.length+" "+(list.length===1?"evento":"eventos");
 list.forEach(e=>{const f=els.template.content.cloneNode(true),b=dateBadge(e.startDate);f.querySelector(".day").textContent=b.day;f.querySelector(".month").textContent=b.month;f.querySelector(".category-badge").textContent=e.category;f.querySelector(".event-title").textContent=e.title;f.querySelector(".time").textContent=e.startTime?"◷ "+dateText(e.startDate)+" · "+e.startTime:"◷ "+dateText(e.startDate);f.querySelector(".venue").textContent="⌖ "+e.venue+(e.address?" · "+e.address:"");f.querySelector(".price").textContent=e.price||"Informações na fonte";const link=f.querySelector(".event-link");link.href=e.url||"#";if(!e.url)link.style.display="none";const img=f.querySelector(".event-image");if(e.image){img.src=e.image;img.alt=e.title;img.onerror=()=>{img.removeAttribute("src");img.style.display="none"}}else{img.removeAttribute("src");img.style.display="none"}els.events.appendChild(f)});
}
function categories(){const cats=[...new Set(allEvents.map(e=>e.category).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"pt-BR"));els.category.innerHTML='<option value="all">Todas as categorias</option>';cats.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;els.category.appendChild(o)})}
async function load(){els.error.hidden=true;els.empty.hidden=true;els.status.textContent="Carregando agenda…";try{const r=await fetch(DATA_URL+"?v="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);const p=parsePayload(await r.json());allEvents=p.events.map(normalize).filter(e=>e.title);categories();render();const stamp=p.updatedAt?new Date(p.updatedAt):null;els.updated.textContent=stamp&&!isNaN(stamp.getTime())?"Atualizado "+stamp.toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"Dados atualizados automaticamente";els.status.textContent=allEvents.length?"":"A fonte de dados ainda não publicou eventos."}catch(err){console.error(err);els.events.innerHTML="";els.error.hidden=false;els.status.textContent="";els.count.textContent="— eventos"}}
async function loadWeather(){try{const r=await fetch(WEATHER_URL,{cache:"no-store"});if(!r.ok)throw Error("weather");const w=await r.json(),temp=Math.round(w.current.temperature_2m);if(els.weather)els.weather.textContent=temp+"°C";if(els.weatherLabel)els.weatherLabel.textContent="Curitiba agora"}catch(e){if(els.weather)els.weather.textContent="—°C";if(els.weatherLabel)els.weatherLabel.textContent="Clima indisponível"}}
function clear(){els.search.value="";els.category.value="all";range="all";document.querySelectorAll(".date-tab").forEach(b=>b.classList.toggle("active",b.dataset.range==="all"));render()}
document.querySelectorAll(".date-tab").forEach(b=>b.addEventListener("click",()=>{range=b.dataset.range;document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x===b));render()}));
els.search.addEventListener("input",render);els.category.addEventListener("change",render);els.clear.addEventListener("click",clear);els.retry.addEventListener("click",load);
document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();els.search.focus()}if(e.key==="Escape"&&document.activeElement===els.search)els.search.blur()});
load();loadWeather();
})();