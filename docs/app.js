(function(){
"use strict";
const DATA_URL="./agenda.json";
const WEATHER_URL="https://api.open-meteo.com/v1/forecast?latitude=-25.4284&longitude=-49.2733&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&forecast_days=4&timezone=America%2FSao_Paulo";
const $=s=>document.querySelector(s);
const els={events:$("#events"),empty:$("#empty"),error:$("#load-error"),status:$("#status"),search:$("#search"),category:$("#category-filter"),count:$("#event-count"),updated:$("#last-update"),clear:$("#clear-filters"),retry:$("#retry"),template:$("#event-template"),weather:$("#weather-temp"),weatherDetail:$("#weather-detail"),weatherIcon:$("#weather-icon"),weatherForecast:$("#weather-forecast"),calendarMonth:$("#calendar-month"),calendarYear:$("#calendar-year"),calendarGrid:$("#calendar-grid"),selected:$("#selected-date"),dayEvents:$("#day-events")};
let allEvents=[],range="all",calendarDate=new Date(),selectedDate=new Date();calendarDate.setDate(1);
function value(o,keys){for(const k of keys){if(o&&o[k]!==undefined&&o[k]!==null&&String(o[k]).trim()!=="")return o[k]}return""}
function normalize(raw,i){const e=raw||{},title=String(value(e,["title","name","nome"])||"Evento cultural"),summary=String(value(e,["summary","description","descricao","resumo"])||"");const match=summary.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/);const date=String(value(e,["startDate","start_date","date","data","data_inicio","start"])||(match?((match[3].length===2?"20":"")+match[3]+"-"+match[2].padStart(2,"0")+"-"+match[1].padStart(2,"0")):""));return{id:String(value(e,["id","slug"])||title+"-"+i),title,description:summary,category:String(value(e,["category","categoria","type","tipo"])||"Cultura"),startDate:date,startTime:String(value(e,["startTime","start_time","time","horario","hora"])||""),venue:String(value(e,["venue","local","location","place","espaco"])||"Curitiba"),address:String(value(e,["address","endereco"])||""),price:String(value(e,["price","preco","valor","ingresso"])||""),organizer:String(value(e,["organizer","organizacao","organizacao_responsavel"])||""),source:String(value(e,["source","sourceName","fonte"])||""),free:Boolean(e.free),publicSpace:Boolean(e.publicSpace),outdoor:Boolean(e.outdoor),url:String(value(e,["sourceUrl","source_url","url","link"])||"")}}
function extract(payload){if(Array.isArray(payload))return{items:payload,updatedAt:null};if(payload&&Array.isArray(payload.items))return{items:payload.items,updatedAt:payload.updatedAt};if(payload&&Array.isArray(payload.events))return{items:payload.events,updatedAt:payload.updatedAt};if(payload&&Array.isArray(payload.data))return{items:payload.data,updatedAt:payload.updatedAt};return{items:[],updatedAt:null}}
function parseDate(v){if(!v)return null;const d=new Date(/^\d{4}-\d{2}-\d{2}$/.test(v)?v+"T12:00:00":v);return isNaN(d)?null:d}
function keyDate(d){return d?d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"):""}
function today(){const d=new Date();d.setHours(0,0,0,0);return d}
function inRange(e){if(range==="all")return true;const d=parseDate(e.startDate),t=today();if(!d)return false;const n=Math.round((d-t)/86400000);if(range==="today")return n===0;if(range==="tomorrow")return n===1;if(range==="week")return n>=0&&n<=7;if(range==="weekend"){const start=(6-t.getDay()+7)%7;return n>=start&&n<=start+1}return true}
function norm(s){return String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase()}
function dateParts(v){const d=parseDate(v);if(!d)return{day:"—",month:"data",weekday:""};return{day:d.toLocaleDateString("pt-BR",{day:"2-digit"}),month:d.toLocaleDateString("pt-BR",{month:"short"}).replace(".",""),weekday:d.toLocaleDateString("pt-BR",{weekday:"short"})}}
function dateText(v){const d=parseDate(v);return d?d.toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"long"}):"Data a confirmar"}
function searchScore(e,q){
  if(!q)return 0;
  const terms=q.split(/\s+/).filter(Boolean);
  const title=norm(e.title), venue=norm(e.venue), category=norm(e.category), description=norm(e.description), address=norm(e.address), organizer=norm(e.organizer), source=norm(e.source);
  const hay=[title,venue,category,description,address,organizer,source].join(" ");
  let score=0;
  for(const term of terms){
    if(title.includes(term))score+=10;
    else if(venue.includes(term))score+=8;
    else if(category.includes(term)||organizer.includes(term)||source.includes(term))score+=6;
    else if(address.includes(term))score+=5;
    else if(description.includes(term))score+=2;
    else if(hay.includes(term))score+=1;
    else return -1;
  }
  if(e.free && terms.some(t=>["gratuito","gratuita","gratis","livre"].includes(t)))score+=8;
  if(e.publicSpace && terms.some(t=>["parque","praca","praça","publico","público","aberto"].includes(t)))score+=8;
  return score;
}
function render(){const q=norm(els.search.value),cat=norm(els.category.value);const list=allEvents.filter(e=>inRange(e)&&(cat==="all"||categorySlug(e.category)===cat)&&(!q||searchScore(e,q)>=0));list.sort((a,b)=>{if(q){const diff=searchScore(b,q)-searchScore(a,q);if(diff)return diff}return(parseDate(a.startDate)?.getTime()||Infinity)-(parseDate(b.startDate)?.getTime()||Infinity)});els.events.innerHTML="";els.count.textContent=list.length+" "+(list.length===1?"evento":"eventos");els.empty.hidden=list.length!==0;els.clear.hidden=!(q||cat!=="all"||range!=="all");for(const e of list){const f=els.template.content.cloneNode(true),p=dateParts(e.startDate);f.querySelector(".day").textContent=p.day;f.querySelector(".month").textContent=p.month;f.querySelector(".weekday").textContent=p.weekday;f.querySelector(".category-badge").textContent=categoryLabel(e.category);f.querySelector(".event-title").textContent=e.title;f.querySelector(".time").textContent="◷ "+dateText(e.startDate)+(e.startTime?" · "+e.startTime:"");f.querySelector(".venue").textContent="⌖ "+e.venue+(e.address?" · "+e.address:"");f.querySelector(".price").textContent=e.price||"Informações";const link=f.querySelector(".event-link");link.href=e.url||"#";if(!e.url)link.style.display="none";els.events.appendChild(f)}renderCalendar()}
function categorySlug(value){const s=norm(value);if(s.includes("esporte")||s.includes("futebol")||s.includes("coritiba")||s.includes("athletico")||s.includes("couto pereira")||s.includes("ligga arena"))return"esporte";if(s.includes("cinema")||s.includes("filme"))return"cinema";if(s.includes("musica")||s.includes("show"))return"musica";if(s.includes("teatro")||s.includes("circo")||s.includes("danca"))return"teatro";return"cidade"}
function categoryLabel(value){const s=categorySlug(value);return s==="musica"?"Música":s==="teatro"?"Teatro":s==="cinema"?"Cinema":s==="esporte"?"Esporte":"Cidade"}
function categories(){els.category.value="all"}
function sameDay(a,b){return a&&b&&keyDate(a)===keyDate(b)}
function eventsOn(d){return allEvents.filter(e=>sameDay(parseDate(e.startDate),d)).sort((a,b)=>(a.startTime||"").localeCompare(b.startTime||""))}
function renderCalendar(){const y=calendarDate.getFullYear(),m=calendarDate.getMonth();els.calendarMonth.textContent=calendarDate.toLocaleDateString("pt-BR",{month:"long"});els.calendarYear.textContent=y;const first=new Date(y,m,1),last=new Date(y,m+1,0),prevLast=new Date(y,m,0).getDate(),cells=[];for(let i=first.getDay()-1;i>=0;i--)cells.push({d:new Date(y,m-1,prevLast-i),other:true});for(let i=1;i<=last.getDate();i++)cells.push({d:new Date(y,m,i),other:false});while(cells.length<42)cells.push({d:new Date(y,m+1,cells.length-last.getDate()-first.getDay()+1),other:true});els.calendarGrid.innerHTML="";cells.forEach(c=>{const ev=eventsOn(c.d),cell=document.createElement("button");cell.type="button";cell.className="calendar-cell"+(c.other?" other":"")+(sameDay(c.d,today())?" today":"")+(sameDay(c.d,selectedDate)?" selected":"");cell.innerHTML='<span class="cell-day">'+c.d.getDate()+'</span><span class="cell-events">'+ev.slice(0,4).map(()=>'<i class="cell-event-dot"></i>').join("")+(ev.length>4?'<span class="cell-count">+'+(ev.length-4)+'</span>':"")+'</span>';cell.addEventListener("click",()=>{selectedDate=new Date(c.d);renderCalendar();renderDayEvents()});els.calendarGrid.appendChild(cell)});renderDayEvents()}
function renderDayEvents(){els.selected.textContent=selectedDate.toLocaleDateString("pt-BR",{weekday:"long",day:"2-digit",month:"long"});const list=eventsOn(selectedDate);els.dayEvents.innerHTML=list.length?list.slice(0,8).map(e=>'<div class="mini-event"><small>'+categoryLabel(e.category)+'</small><strong>'+escapeHtml(e.title)+'</strong><span>'+(e.startTime?e.startTime+" · ":"")+escapeHtml(e.venue)+'</span></div>').join(""):'<div class="no-day-events">Nenhum evento encontrado para este dia.</div>'}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
async function load(){try{const r=await fetch(DATA_URL+"?v="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);const parsed=extract(await r.json());allEvents=parsed.items.map(normalize);categories();render();els.updated.textContent=parsed.updatedAt?"Atualizado "+new Date(parsed.updatedAt).toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"Dados atualizados automaticamente";els.status.textContent=allEvents.length?allEvents.length+" itens carregados da agenda":"A agenda não contém itens";els.error.hidden=true}catch(e){console.error(e);els.error.hidden=false;els.status.textContent="Erro ao carregar agenda: "+e.message}}
async function weather(){try{const r=await fetch(WEATHER_URL,{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);const j=await r.json(),t=Math.round(j.current.temperature_2m),code=j.current.weather_code;els.weather.textContent=t+"°";els.weatherDetail.textContent=weatherText(code);els.weatherIcon.textContent=weatherIcon(code);renderForecast(j.daily)}catch(e){console.error(e);els.weather.textContent="—°";els.weatherDetail.textContent="Clima indisponível";if(els.weatherForecast)els.weatherForecast.innerHTML=""}}
function renderForecast(daily){if(!els.weatherForecast||!daily||!daily.time)return;const labels=["Hoje","Amanhã"];const extra=new Date(daily.time[2]+"T12:00:00").toLocaleDateString("pt-BR",{weekday:"short"}).replace(".","");els.weatherForecast.innerHTML=daily.time.slice(0,3).map((date,i)=>{const label=labels[i]||extra;const max=Math.round(daily.temperature_2m_max[i]);const min=Math.round(daily.temperature_2m_min[i]);const code=daily.weather_code[i];return '<div class="forecast-day"><span class="forecast-label">'+label+'</span><span class="forecast-icon">'+weatherIcon(code)+'</span><strong>'+max+"°</strong><small>"+min+"°</small></div>"}).join("")}
function weatherText(c){if(c===0)return"Céu limpo";if([1,2,3].includes(c))return"Parcialmente nublado";if([45,48].includes(c))return"Névoa";if([51,53,55,56,57].includes(c))return"Chuvisco";if([61,63,65,66,67].includes(c))return"Chuva";if([71,73,75,77].includes(c))return"Neve";if([80,81,82].includes(c))return"Pancadas de chuva";if([95,96,99].includes(c))return"Trovoada";return"Condição atual"}
function weatherIcon(c){if(c===0)return"☼";if([1,2,3].includes(c))return"☁";if([45,48].includes(c))return"≋";if(c>=51&&c<=82)return"☂";if(c>=95)return"ϟ";return"☼"}
document.querySelectorAll(".date-tab").forEach(b=>b.addEventListener("click",()=>{range=b.dataset.range;document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x===b));render()}));
els.search.addEventListener("input",render);els.category.addEventListener("change",render);els.clear.addEventListener("click",()=>{els.search.value="";els.category.value="all";range="all";document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x.dataset.range==="all"));render()});els.retry.addEventListener("click",load);
$("#prev-month").addEventListener("click",()=>{calendarDate.setMonth(calendarDate.getMonth()-1);renderCalendar()});$("#next-month").addEventListener("click",()=>{calendarDate.setMonth(calendarDate.getMonth()+1);renderCalendar()});
document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();els.search.focus()}});
load();weather();
})();
document.querySelectorAll("[data-discovery]").forEach(button=>{
  button.addEventListener("click",()=>{
    const presets={
      eventos:"",
      filmes:"cinema",
      exposicoes:"exposição",
      parques:"parque",
      universidade:"UFPR"
    };
    const value=presets[button.dataset.discovery]||"";
    els.search.value=value;
    if(button.dataset.discovery==="filmes")els.category.value="cinema";
    else els.category.value="all";
    document.querySelectorAll("[data-discovery]").forEach(x=>x.classList.toggle("active",x===button));
    render();
    els.search.focus();
  });
});
