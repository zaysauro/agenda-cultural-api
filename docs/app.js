(function(){
"use strict";
const DATA_URL="./agenda.json";
const WEATHER_URL="https://api.open-meteo.com/v1/forecast?latitude=-25.4284&longitude=-49.2733&current=temperature_2m&timezone=America%2FSao_Paulo";
const $=s=>document.querySelector(s);
const els={events:$("#events"),empty:$("#empty"),error:$("#load-error"),status:$("#status"),search:$("#search"),category:$("#category-filter"),count:$("#event-count"),updated:$("#last-update"),clear:$("#clear-filters"),retry:$("#retry"),template:$("#event-template"),weather:$("#weather-temp"),weatherLabel:$("#weather-label")};
let allEvents=[],range="all";
function value(o,keys){for(const k of keys){if(o&&o[k]!==undefined&&o[k]!==null&&String(o[k]).trim()!=="")return o[k]}return ""}
function normalize(raw,i){
 const e=raw||{}, title=String(value(e,["title","name","nome"])||"Evento cultural"), summary=String(value(e,["summary","description","descricao","resumo"])||"");
 const match=summary.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/);
 const date=String(value(e,["startDate","start_date","date","data","data_inicio","start"])||(match?((match[3].length===2?"20":"")+match[3]+"-"+match[2].padStart(2,"0")+"-"+match[1].padStart(2,"0")):""));
 return {id:String(value(e,["id","slug"])||title+"-"+i),title,description:summary,category:String(value(e,["category","categoria","type","tipo"])||"Cultura"),startDate:date,startTime:String(value(e,["startTime","start_time","time","horario","hora"])||""),venue:String(value(e,["venue","local","location","place","espaco"])||"Curitiba"),address:String(value(e,["address","endereco"])||""),price:String(value(e,["price","preco","valor","ingresso"])||""),image:String(value(e,["image","imageUrl","image_url","imagem","foto"])||""),url:String(value(e,["sourceUrl","source_url","url","link"])||"")};
}
function extract(payload){
 if(Array.isArray(payload))return {items:payload,updatedAt:null};
 if(payload&&Array.isArray(payload.items))return {items:payload.items,updatedAt:payload.updatedAt};
 if(payload&&Array.isArray(payload.events))return {items:payload.events,updatedAt:payload.updatedAt};
 if(payload&&Array.isArray(payload.data))return {items:payload.data,updatedAt:payload.updatedAt};
 return {items:[],updatedAt:null};
}
function date(v){if(!v)return null;const d=new Date(/^\d{4}-\d{2}-\d{2}$/.test(v)?v+"T12:00:00":v);return isNaN(d)?null:d}
function today(){const d=new Date();d.setHours(0,0,0,0);return d}
function inRange(e){if(range==="all")return true;const d=date(e.startDate);if(!d)return false;const n=Math.round((d-today())/86400000);if(range==="today")return n===0;if(range==="tomorrow")return n===1;if(range==="week")return n>=0&&n<=7;if(range==="weekend"){const start=(6-today().getDay()+7)%7;return n>=start&&n<=start+1}return true}
function norm(s){return String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase()}
function dateText(v){const d=date(v);return d?d.toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"long"}):"Data a confirmar"}
function render(){
 const q=norm(els.search.value),cat=norm(els.category.value);
 const list=allEvents.filter(e=>inRange(e)&&(cat==="all"||norm(e.category)===cat)&&(!q||norm([e.title,e.description,e.category,e.venue,e.address].join(" ")).includes(q)));
 list.sort((a,b)=>(date(a.startDate)?.getTime()||Infinity)-(date(b.startDate)?.getTime()||Infinity));
 els.events.innerHTML="";
 els.count.textContent=list.length+" "+(list.length===1?"evento":"eventos");
 els.empty.hidden=list.length!==0;
 els.clear.hidden=!(q||cat!=="all"||range!=="all");
 for(const e of list){
  const f=els.template.content.cloneNode(true),d=date(e.startDate);
  f.querySelector(".day").textContent=d?d.toLocaleDateString("pt-BR",{day:"2-digit"}):"—";
  f.querySelector(".month").textContent=d?d.toLocaleDateString("pt-BR",{month:"short"}).replace(".",""):"data";
  f.querySelector(".category-badge").textContent=e.category;
  f.querySelector(".event-title").textContent=e.title;
  f.querySelector(".time").textContent="◷ "+dateText(e.startDate)+(e.startTime?" · "+e.startTime:"");
  f.querySelector(".venue").textContent="⌖ "+e.venue+(e.address?" · "+e.address:"");
  f.querySelector(".price").textContent=e.price||"Ver informações";
  const link=f.querySelector(".event-link");link.href=e.url||"#";if(!e.url)link.style.display="none";
  const img=f.querySelector(".event-image");if(e.image){img.src=e.image;img.alt=e.title}else img.style.display="none";
  els.events.appendChild(f);
 }
}
function categories(){const set=new Set(allEvents.map(e=>e.category).filter(Boolean));els.category.innerHTML='<option value="all">Todas as categorias</option>';[...set].sort().forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;els.category.appendChild(o)})}
async function load(){
 try{
  const r=await fetch(DATA_URL+"?v="+Date.now(),{cache:"no-store"});
  if(!r.ok)throw new Error("HTTP "+r.status);
  const payload=await r.json(),parsed=extract(payload);
  allEvents=parsed.items.map(normalize);
  categories();render();
  els.updated.textContent=parsed.updatedAt?"Atualizado "+new Date(parsed.updatedAt).toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"Dados atualizados automaticamente";
  els.status.textContent=allEvents.length?allEvents.length+" itens carregados da agenda":"A agenda não contém itens";
  els.error.hidden=true;
 }catch(e){console.error(e);els.error.hidden=false;els.status.textContent="Erro ao carregar agenda: "+e.message}
}
async function weather(){try{const r=await fetch(WEATHER_URL+"", {cache:"no-store"});const j=await r.json();els.weather.textContent=Math.round(j.current.temperature_2m)+"°C";els.weatherLabel.textContent="Curitiba agora"}catch(e){els.weather.textContent="—°C"}}
document.querySelectorAll(".date-tab").forEach(b=>b.addEventListener("click",()=>{range=b.dataset.range;document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x===b));render()}));
els.search.addEventListener("input",render);els.category.addEventListener("change",render);els.clear.addEventListener("click",()=>{els.search.value="";els.category.value="all";range="all";document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x.dataset.range==="all"));render()});els.retry.addEventListener("click",load);
load();weather();
})();