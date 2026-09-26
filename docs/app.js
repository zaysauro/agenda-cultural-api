(function(){
"use strict";

const DATA_URL="./agenda.json";
const CINEMA_URL="./cinema.json";
const WEATHER_URL="https://api.open-meteo.com/v1/forecast?latitude=-25.4284&longitude=-49.2733&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&forecast_days=4&timezone=America%2FSao_Paulo";
const $=s=>document.querySelector(s);

const els={
  events:$("#events"),empty:$("#empty"),error:$("#load-error"),status:$("#status"),
  count:$("#event-count"),updated:$("#last-update"),retry:$("#retry"),
  template:$("#event-template"),weather:$("#weather-temp"),weatherDetail:$("#weather-detail"),
  weatherIcon:$("#weather-icon"),weatherForecast:$("#weather-forecast"),
  calendarMonth:$("#calendar-month"),calendarYear:$("#calendar-year"),
  calendarGrid:$("#calendar-grid"),selected:$("#selected-date"),dayEvents:$("#day-events"),
  cinemaFilms:$("#cinema-films"),cinemaEmpty:$("#cinema-empty"),cinemaDate:$("#cinema-date")
};

let allEvents=[];
let range="all";
let calendarDate=curitibaNow();
let selectedDate=curitibaNow();
calendarDate.setDate(1);

function curitibaNow(){
  const parts=new Intl.DateTimeFormat("en-US",{
    timeZone:"America/Sao_Paulo",year:"numeric",month:"2-digit",day:"2-digit",
    hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"
  }).formatToParts(new Date());
  const get=t=>Number(parts.find(p=>p.type===t)?.value||0);
  return new Date(get("year"),get("month")-1,get("day"),get("hour"),get("minute"),get("second"));
}
function today(){const d=curitibaNow();d.setHours(0,0,0,0);return d}
function value(o,keys){
  for(const k of keys){
    if(o&&o[k]!==undefined&&o[k]!==null&&String(o[k]).trim()!=="")return o[k];
  }
  return "";
}
function normalize(raw,i){
  const e=raw||{};
  const summary=String(value(e,["summary","description","descricao","resumo"])||"");
  const explicitDate=String(value(e,["startDate","start_date","date","data","data_inicio","start"])||"");
  const summaryDate=(summary.match(/\b\d{1,2}\/\d{1,2}\/\d{4}\b/)||[])[0]||"";
  return {
    id:String(value(e,["id","slug"])||value(e,["title","name"])+"-"+i),
    title:String(value(e,["title","name","nome"])||"Evento cultural"),
    description:summary,
    category:String(value(e,["category","categoria","type","tipo"])||"Cultura"),
    categorySlug:String(value(e,["categorySlug","category_slug"])||""),
    startDate:explicitDate||summaryDate,
    startTime:String(value(e,["startTime","start_time","time","horario","hora"])||""),
    venue:String(value(e,["venue","local","location","place","espaco"])||"Curitiba"),
    address:String(value(e,["address","endereco"])||""),
    price:String(value(e,["price","preco","valor","ingresso"])||""),
    organizer:String(value(e,["organizer","organizacao","organizacao_responsavel"])||""),
    source:String(value(e,["source","sourceName","fonte"])||""),
    free:Boolean(e.free),
    publicSpace:Boolean(e.publicSpace),
    outdoor:Boolean(e.outdoor),
    url:String(value(e,["sourceUrl","source_url","url","link"])||"")
  };
}
function extract(payload){
  if(Array.isArray(payload))return{items:payload,updatedAt:null};
  if(payload&&Array.isArray(payload.items))return{items:payload.items,updatedAt:payload.updatedAt};
  if(payload&&Array.isArray(payload.events))return{items:payload.events,updatedAt:payload.updatedAt};
  if(payload&&Array.isArray(payload.data))return{items:payload.data,updatedAt:payload.updatedAt};
  return{items:[],updatedAt:null};
}
function parseDate(v){
  if(!v)return null;
  const s=String(v).trim();
  let d;
  const br=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if(br)d=new Date(Number(br[3]),Number(br[2])-1,Number(br[1]),12);
  else if(/^\d{4}-\d{2}-\d{2}$/.test(s))d=new Date(s+"T12:00:00");
  else d=new Date(s);
  return Number.isNaN(d.getTime())?null:d;
}
function dateParts(v){
  const d=parseDate(v);
  if(!d)return{day:"—",month:"data",weekday:""};
  return{
    day:d.toLocaleDateString("pt-BR",{day:"2-digit"}),
    month:d.toLocaleDateString("pt-BR",{month:"short"}).replace(".",""),
    weekday:d.toLocaleDateString("pt-BR",{weekday:"short"})
  };
}
function dateText(v){
  const d=parseDate(v);
  return d?d.toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"long"}):"Data a confirmar";
}
function sameDay(a,b){return a&&b&&a.getFullYear()===b.getFullYear()&&a.getMonth()===b.getMonth()&&a.getDate()===b.getDate()}
function eventsOn(d){return allEvents.filter(e=>{const x=parseDate(e.startDate);return x&&sameDay(x,d)})}
function inRange(e){
  if(range==="all")return true;
  const d=parseDate(e.startDate),t=today();
  if(!d)return false;
  const n=Math.round((d-t)/86400000);
  if(range==="today")return n===0;
  if(range==="tomorrow")return n===1;
  if(range==="week")return n>=0&&n<=7;
  if(range==="weekend"){
    const saturday=new Date(t);
    saturday.setDate(t.getDate()+(6-t.getDay()+7)%7);
    const sunday=new Date(saturday);sunday.setDate(saturday.getDate()+1);
    return d>=saturday&&d<new Date(sunday.getFullYear(),sunday.getMonth(),sunday.getDate()+1);
  }
  return true;
}
function categoryLabel(value){
  const s=String(value||"").toLowerCase();
  if(s.includes("cinema")||s.includes("filme"))return"Cinema";
  if(s.includes("musica")||s.includes("música")||s.includes("show"))return"Música";
  if(s.includes("teatro")||s.includes("circo"))return"Teatro";
  if(s.includes("danca")||s.includes("dança"))return"Dança";
  if(s.includes("esporte"))return"Esporte";
  if(s.includes("expos"))return"Exposição";
  return value||"Cultura";
}
function escapeHtml(s){
  return String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function render(){
  const list=allEvents.filter(inRange).sort((a,b)=>
    (parseDate(a.startDate)?.getTime()??Infinity)-(parseDate(b.startDate)?.getTime()??Infinity)
  );
  els.events.innerHTML="";
  els.count.textContent=list.length+" "+(list.length===1?"evento":"eventos");
  els.empty.hidden=list.length>0;
  for(const e of list){
    const fragment=els.template.content.cloneNode(true);
    const p=dateParts(e.startDate);
    fragment.querySelector(".day").textContent=p.day;
    fragment.querySelector(".month").textContent=p.month;
    fragment.querySelector(".weekday").textContent=p.weekday;
    fragment.querySelector(".category-badge").textContent=categoryLabel(e.category);
    fragment.querySelector(".event-title").textContent=e.title;
    fragment.querySelector(".time").textContent="◷ "+dateText(e.startDate)+(e.startTime?" · "+e.startTime:"");
    fragment.querySelector(".venue").textContent="⌖ "+e.venue+(e.address?" · "+e.address:"");
    fragment.querySelector(".price").textContent=e.price||"Informações";
    const link=fragment.querySelector(".event-link");
    link.href=e.url||"#";
    if(!e.url)link.style.display="none";
    els.events.appendChild(fragment);
  }
  renderCalendar();
  renderWeekend();
}
function renderCalendar(){
  const y=calendarDate.getFullYear(),m=calendarDate.getMonth();
  els.calendarMonth.textContent=calendarDate.toLocaleDateString("pt-BR",{month:"long"});
  els.calendarYear.textContent=y;
  const first=new Date(y,m,1),last=new Date(y,m+1,0),cells=[];
  const offset=first.getDay();
  for(let i=offset-1;i>=0;i--)cells.push({d:new Date(y,m-1,new Date(y,m,0).getDate()-i),other:true});
  for(let i=1;i<=last.getDate();i++)cells.push({d:new Date(y,m,i),other:false});
  while(cells.length<42)cells.push({d:new Date(y,m+1,cells.length-offset-last.getDate()+1),other:true});
  els.calendarGrid.innerHTML="";
  cells.forEach(c=>{
    const ev=eventsOn(c.d);
    const cell=document.createElement("button");
    cell.type="button";
    cell.className="calendar-cell"+(c.other?" other":"")+(sameDay(c.d,today())?" today":"")+(sameDay(c.d,selectedDate)?" selected":"");
    cell.innerHTML='<span class="cell-day">'+c.d.getDate()+'</span><span class="cell-events">'+ev.slice(0,4).map(()=>'<i class="cell-event-dot"></i>').join("")+(ev.length>4?'<span class="cell-count">+'+(ev.length-4)+'</span>':"")+'</span>';
    cell.addEventListener("click",()=>{selectedDate=new Date(c.d);renderCalendar();renderDayEvents()});
    els.calendarGrid.appendChild(cell);
  });
  renderDayEvents();
}
function renderDayEvents(){
  els.selected.textContent=selectedDate.toLocaleDateString("pt-BR",{weekday:"long",day:"2-digit",month:"long"});
  const list=eventsOn(selectedDate);
  els.dayEvents.innerHTML=list.length?list.slice(0,8).map(e=>'<div class="mini-event"><small>'+categoryLabel(e.category)+'</small><strong>'+escapeHtml(e.title)+'</strong><span>'+(e.startTime?e.startTime+" · ":"")+escapeHtml(e.venue)+'</span></div>').join(""):'<div class="no-day-events">Nenhum evento encontrado para este dia.</div>';
}
function weekendBounds(){
  const t=today();
  const saturday=new Date(t);saturday.setDate(t.getDate()+(6-t.getDay()+7)%7);
  const sunday=new Date(saturday);sunday.setDate(saturday.getDate()+1);
  return{saturday,sunday};
}
function renderWeekend(){
  const box=$("#weekend-events"),empty=$("#weekend-empty"),label=$("#weekend-range");
  if(!box)return;
  const {saturday,sunday}=weekendBounds();
  const end=new Date(sunday.getFullYear(),sunday.getMonth(),sunday.getDate()+1);
  const list=allEvents.filter(e=>{const d=parseDate(e.startDate);return d&&d>=saturday&&d<end}).sort((a,b)=>(parseDate(a.startDate)?.getTime()??Infinity)-(parseDate(b.startDate)?.getTime()??Infinity));
  label.textContent=saturday.toLocaleDateString("pt-BR",{day:"2-digit",month:"long"})+" — "+sunday.toLocaleDateString("pt-BR",{day:"2-digit",month:"long"});
  box.innerHTML=list.slice(0,9).map(e=>{
    const d=parseDate(e.startDate);
    const day=d.toLocaleDateString("pt-BR",{weekday:"long",day:"2-digit"});
    return '<article class="weather-weekend-card"><div><div class="weather-weekend-card-top"><span class="weather-weekend-day">'+escapeHtml(day)+'</span>'+(e.free?'<span class="weather-weekend-free">Gratuito</span>':"")+'</div><h3>'+escapeHtml(e.title)+'</h3><div class="weather-weekend-meta">'+escapeHtml([e.startTime,e.venue,e.address].filter(Boolean).join(" · ")||"Curitiba")+'</div></div>'+(e.url?'<a class="weather-weekend-link" href="'+escapeHtml(e.url)+'" target="_blank" rel="noreferrer">Ver evento ↗</a>':"")+'</article>';
  }).join("");
  empty.hidden=list.length>0;
}

function formatSessionTime(value){
  if(!value)return "";
  const raw=String(value).trim();
  const direct=raw.match(/\b([01]?\d|2[0-3]):([0-5]\d)\b/);
  if(direct)return direct[0];
  const d=new Date(raw);
  if(!Number.isNaN(d.getTime())){
    return d.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"});
  }
  return raw;
}

function renderCinema(data){
  if(!els.cinemaFilms)return;
  const films=Array.isArray(data?.filmes_em_cartaz)?data.filmes_em_cartaz:[];
  const sessions=Array.isArray(data?.sessoes_hoje)?data.sessoes_hoje:[];
  const byFilmId=new Map();
  const byFilmTitle=new Map();

  for(const s of sessions){
    const id=String(s.filme_id||"").trim();
    const title=String(s.filme||"").trim();
    if(id){
      if(!byFilmId.has(id))byFilmId.set(id,[]);
      byFilmId.get(id).push(s);
    }
    if(title){
      const key=title.toLocaleLowerCase("pt-BR");
      if(!byFilmTitle.has(key))byFilmTitle.set(key,[]);
      byFilmTitle.get(key).push(s);
    }
  }

  els.cinemaFilms.innerHTML=films.map((film,index)=>{
    const filmId=String(film.id_ingresso||"").trim();
    const filmTitle=String(film.titulo||"").trim();
    const sessionsForFilm=(
      (filmId&&byFilmId.get(filmId)) ||
      byFilmTitle.get(filmTitle.toLocaleLowerCase("pt-BR")) ||
      []
    );

    const grouped=new Map();
    sessionsForFilm.forEach(session=>{
      const cinema=session.cinema||"Cinema";
      if(!grouped.has(cinema))grouped.set(cinema,[]);
      grouped.get(cinema).push(session);
    });

    const sessionHtml=[...grouped.entries()].slice(0,5).map(([cinema,list])=>{
      const times=list.slice(0,10).map(session=>{
        const label=[
          formatSessionTime(session.horario),
          session.tipo,
          session.sala
        ].filter(Boolean).join(" · ");
        const href=session.url_compra||"";
        return href
          ? '<a class="cinema-time" href="'+escapeHtml(href)+'" target="_blank" rel="noreferrer">'+escapeHtml(label||"Ver sessão")+' ↗</a>'
          : '<span class="cinema-time cinema-time-disabled">'+escapeHtml(label||"Horário indisponível")+'</span>';
      }).join("");
      return '<div class="cinema-theater"><strong>'+escapeHtml(cinema)+'</strong><div class="cinema-times">'+times+'</div></div>';
    }).join("");

    const meta=[
      film.classificacao?escapeHtml(film.classificacao):"",
      film.duracao?escapeHtml(String(film.duracao).replace(/\s*min\b/i," min")):"",
      (Array.isArray(film.generos)?film.generos:[]).slice(0,2).map(escapeHtml).join(" · ")
    ].filter(Boolean).join(" · ");

    const original=film.titulo_original&&film.titulo_original!==film.titulo
      ? '<p class="cinema-original">'+escapeHtml(film.titulo_original)+'</p>'
      : "";

    return '<article class="cinema-card">'+
      '<div class="cinema-poster-wrap">'+
      (film.poster
        ? '<img class="cinema-poster" src="'+escapeHtml(film.poster)+'" alt="Pôster de '+escapeHtml(filmTitle)+'" loading="lazy">'
        : '<div class="cinema-poster cinema-poster-empty">Cinema</div>')+
      '<div class="cinema-card-body">'+
      '<span class="cinema-index">'+String(index+1).padStart(2,"0")+'</span>'+
      '<h3>'+escapeHtml(filmTitle||"Filme em cartaz")+'</h3>'+
      original+
      (meta?'<p class="cinema-meta">'+meta+'</p>':"")+
      (film.sinopse?'<p class="cinema-synopsis">'+escapeHtml(film.sinopse)+'</p>':"")+
      '<div class="cinema-sessions">'+
      (sessionHtml||'<span class="cinema-no-sessions">Sem sessões disponíveis para hoje.</span>')+
      '</div></div></div></article>';
  }).join("");

  els.cinemaEmpty.hidden=films.length>0;
  if(els.cinemaDate&&data?.data_sessoes){
    const d=parseDate(data.data_sessoes);
    els.cinemaDate.textContent=d
      ?"Sessões de "+d.toLocaleDateString("pt-BR",{day:"2-digit",month:"long"})
      :"Sessões de hoje";
  }
}

async function cinema(){
  try{
    const response=await fetch(CINEMA_URL+"?v="+Date.now(),{cache:"no-store"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    renderCinema(await response.json());
  }catch(error){
    console.error("Cinema:",error);
    if(els.cinemaFilms)els.cinemaFilms.innerHTML="";
    if(els.cinemaEmpty)els.cinemaEmpty.hidden=false;
  }
}

async function load(){
  try{
    const response=await fetch(DATA_URL+"?v="+Date.now(),{cache:"no-store"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    const parsed=extract(await response.json());
    allEvents=parsed.items.map(normalize);
    render();
    if(parsed.updatedAt){
      els.updated.textContent="Atualizado "+new Date(parsed.updatedAt).toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"});
    }
    els.status.textContent=allEvents.length?allEvents.length+" itens carregados da agenda":"A agenda não contém itens";
    els.error.hidden=true;
  }catch(error){
    console.error("Agenda:",error);
    els.error.hidden=false;
    els.status.textContent="Erro ao carregar agenda: "+error.message;
  }
}

async function weather(){
  try{
    const response=await fetch(WEATHER_URL,{cache:"no-store"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    const data=await response.json();
    const temp=Math.round(data.current.temperature_2m),code=data.current.weather_code;
    els.weather.textContent=temp+"°";
    els.weatherDetail.textContent=weatherText(code);
    els.weatherIcon.textContent=weatherIcon(code);
    renderForecast(data.daily);
  }catch(error){
    els.weather.textContent="—°";
    els.weatherDetail.textContent="Clima indisponível";
    if(els.weatherForecast)els.weatherForecast.innerHTML="";
  }
}
function renderForecast(daily){
  if(!els.weatherForecast||!daily?.time)return;
  els.weatherForecast.innerHTML=daily.time.slice(0,3).map((date,i)=>{
    const label=i===0?"Hoje":i===1?"Amanhã":new Date(date+"T12:00:00").toLocaleDateString("pt-BR",{weekday:"short"}).replace(".","");
    return '<div class="forecast-day"><span class="forecast-label">'+label+'</span><span class="forecast-icon">'+weatherIcon(daily.weather_code[i])+'</span><strong>'+Math.round(daily.temperature_2m_max[i])+"°</strong><small>"+Math.round(daily.temperature_2m_min[i])+"°</small></div>";
  }).join("");
}
function weatherText(c){
  if(c===0)return"Céu limpo";
  if([1,2,3].includes(c))return"Parcialmente nublado";
  if([45,48].includes(c))return"Névoa";
  if([51,53,55,56,57].includes(c))return"Chuvisco";
  if([61,63,65,66,67,80,81,82].includes(c))return"Chuva";
  if([71,73,75,77].includes(c))return"Neve";
  if([95,96,99].includes(c))return"Trovoada";
  return"Condição atual";
}
function weatherIcon(c){
  if(c===0)return"☼";
  if([1,2,3].includes(c))return"☁";
  if([45,48].includes(c))return"≋";
  if(c>=51&&c<=82)return"☂";
  if(c>=95)return"ϟ";
  return"☼";
}

document.querySelectorAll(".date-tab").forEach(button=>{
  button.addEventListener("click",()=>{
    range=button.dataset.range||"all";
    document.querySelectorAll(".date-tab").forEach(x=>x.classList.toggle("active",x===button));
    render();
  });
});
if(els.retry)els.retry.addEventListener("click",load);
$("#prev-month")?.addEventListener("click",()=>{calendarDate.setMonth(calendarDate.getMonth()-1);renderCalendar()});
$("#next-month")?.addEventListener("click",()=>{calendarDate.setMonth(calendarDate.getMonth()+1);renderCalendar()});

load();
cinema();
weather();
})();