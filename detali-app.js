/* данные приходят расшифрованными в window.__D (см. detali.html + secure-lib.js) */

// ══════════════════════════════════════════════════════════
// DATA
// ══════════════════════════════════════════════════════════
const MONTHS = __D.MONTHS;
const MONTH_ORDER = __D.MONTH_ORDER;

// Weekly data — weeks as ordered array
const WEEKS = __D.WEEKS;
// Index for fast lookup
const WEEK_MAP = {};
WEEKS.forEach((w,i)=>{ WEEK_MAP[w.key]=i; });

// Weeks that have headcount data (starting from нед.6)
const W_HC_WEEKS  = WEEKS.filter(w=>w.hc!==null);
const W_HC_LABELS = W_HC_WEEKS.map(w=>w.label);
const W_HC_DATA   = W_HC_WEEKS.map(w=>w.hc);

// New hires per week (bar chart in weekly mode) — weeks with data
const W_NH_WEEKS  = WEEKS.filter(w=>w.newHires!==null);
const W_NH_LABELS = W_NH_WEEKS.map(w=>w.label);
const W_NH_DATA   = W_NH_WEEKS.map(w=>w.newHires);

const W_INT_LABELS = WEEKS.map(w=>w.label);
const W_INT_HR     = WEEKS.map(w=>w.hrInt);
const W_INT_HM     = WEEKS.map(w=>w.hmInt);

const SOURCES = __D.SOURCES;
const RECRUITERS = __D.RECRUITERS;
const AVATAR_COLORS = ['#3B6FE0','#10B981','#F79009','#06B6D4','#8B5CF6','#EC4899'];

const OPEN_VAC = __D.OPEN_VAC;

const CLOSED_DATA = __D.CLOSED_DATA;


const DEPT_COLORS = {
  'ИТ':'#3B6FE0','Маркетинг':'#06B6D4','Забота':'#10B981','HR':'#8B5CF6',
  'Финансы':'#F59E0B','Продукт':'#EC4899','Коммерческий':'#F79009','АУП':'#6B7280',
  'Другое':'#D1D5DB',
};

// Department breakdown (from employees sheet, 130 active — актуально 02.06.2026)
// ── Задачи на неделю (из Google Sheets, обновлено 09.06.2026) ──
const WEEKLY_TASKS = __D.WEEKLY_TASKS;

// обновлено из Google Sheets 16.06.2026 (нед. 24)
const DEPT_BREAKDOWN = __D.DEPT_BREAKDOWN;

// ══════════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════════
let mode = 'monthly';   // 'monthly' | 'weekly'
let period = 'all';     // 'all' | month number | week key
let mainChart = null;
let hcChart = null;
let intChart = null;
let initialized = false;

// ══════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════
const easeOut = t => 1 - Math.pow(1-t,3);
function countUp(el, to, dur=600, dec=0, sfx=''){
  if(el===null) return;
  const t0=performance.now();
  (function tick(now){
    const p=Math.min((now-t0)/dur,1);
    el.textContent=(dec>0?(to*easeOut(p)).toFixed(dec):Math.round(to*easeOut(p)))+sfx;
    if(p<1) requestAnimationFrame(tick);
    else el.textContent=(dec>0?to.toFixed(dec):to)+sfx;
  })(t0);
}
function showDelta(elId, val, sfx='', inv=false){
  const el=document.getElementById(elId);
  if(!el) return;
  if(val===null){el.innerHTML='';return;}
  const pos=val>0, cls=(inv?!pos:pos)?'up':'down';
  el.innerHTML=`<span class="delta ${cls}">${pos?'↑':'↓'} ${Math.abs(val)}${sfx}</span>`;
}
function setTxt(id, txt){ const e=document.getElementById(id); if(e) e.textContent=txt; }
Chart.defaults.font.family='Inter';
const TT={backgroundColor:'#0A0B0D',padding:10,cornerRadius:8,
  titleFont:{size:11},bodyFont:{size:13,weight:'600'}};

// ══════════════════════════════════════════════════════════
// PERIOD PILLS — build dynamically based on mode
// ══════════════════════════════════════════════════════════
function buildPeriodPills(){
  const container=document.getElementById('period-pills');
  container.innerHTML='';
  const pills=[];

  if(mode==='monthly'){
    pills.push({key:'all',label:'Все'});
    [...MONTH_ORDER].reverse().forEach(m=>pills.push({key:String(m),label:MONTHS[m].name}));
  } else {
    pills.push({key:'all',label:'Все'});
    [...WEEKS].reverse().forEach(w=>pills.push({key:w.key,label:w.label}));
  }

  pills.forEach(p=>{
    const btn=document.createElement('button');
    btn.className='period-btn'+(period===p.key?' active':'');
    btn.dataset.period=p.key;
    btn.textContent=p.label;
    btn.addEventListener('click',()=>selectPeriod(p.key));
    container.appendChild(btn);
  });
}

function selectPeriod(key){
  period=key;
  document.querySelectorAll('.period-btn').forEach(b=>
    b.classList.toggle('active',b.dataset.period===key)
  );
  renderKPIs();
  updateMainChart();
  updateWeeklyCharts();
}

// ══════════════════════════════════════════════════════════
// KPI RENDER
// ══════════════════════════════════════════════════════════
function renderKPIs(){
  const $ = id => document.getElementById(id);
  let hc, dHC, sHC;
  let hires, dHires, sHires;
  let kpi6val, dKpi6, sKpi6, lblKpi6;
  let openVac, sOpen;
  // открытые вакансии — всегда текущий срез (не зависят от выбранного периода)
  const openNow=(OPEN_VAC||[]).length;
  const ST0=__D.STAFF||{hc:143,plan:149};

  if(mode==='monthly'){
    // ── Monthly ──
    if(period==='all'){
      hc=ST0.hc; dHC=null; sHC=`${ST0.hc} действующих`;
      hires=Object.values(MONTHS).reduce((s,m)=>s+(m.hires||0),0); dHires=null; sHires='с начала года';
      const _tw=Object.values(MONTHS).filter(m=>m.tto!=null&&m.hires>0);
      const _tsum=_tw.reduce((s,m)=>s+m.tto*m.hires,0), _tn=_tw.reduce((s,m)=>s+m.hires,0);
      kpi6val=_tn?parseFloat((_tsum/_tn).toFixed(1)):null; dKpi6=null; sKpi6='дней до оффера'; lblKpi6='Среднее TTO';
      openVac=openNow; sOpen='сейчас в работе';
    } else {
      const m=parseInt(period), d=MONTHS[m], prev=m>1?MONTHS[m-1]:null;
      hc=d.hc; dHC=null; sHC=`на конец ${d.prep}`;
      hires=d.hires; dHires=prev?d.hires-prev.hires:null; sHires=`в ${d.prep}`;
      kpi6val=d.tto; dKpi6=prev&&prev.tto?parseFloat((d.tto-prev.tto).toFixed(1)):null;
      sKpi6='дней до оффера'; lblKpi6='Среднее TTO';
      openVac=openNow; sOpen='сейчас в работе';
    }
  } else {
    // ── Weekly ──
    if(period==='all'){
      // «Всего» в листе «Кол-во нанятых» — нарастающий итог найма, не штат; сотрудники — из ШТАТКИ
      hc=ST0.hc; dHC=null; sHC='действующих по ШТАТКЕ';
      hires=W_NH_DATA.reduce((s,v)=>s+v,0);
      dHires=null; sHires='за отслеживаемый период';
      const totalInt=WEEKS.reduce((s,w)=>s+w.hrInt+w.hmInt+(w.techInt||0)+(w.finInt||0),0);
      kpi6val=totalInt; dKpi6=null; sKpi6='за все недели'; lblKpi6='Интервью итого';
      openVac=openNow; sOpen='сейчас в работе';
    } else {
      const wi=WEEK_MAP[period];
      const w=WEEKS[wi], wprev=wi>0?WEEKS[wi-1]:null;
      hc=ST0.hc; dHC=null; sHC='действующих по ШТАТКЕ';
      hires=w.newHires??0;
      dHires=wprev&&w.newHires!==null&&wprev.newHires!==null?w.newHires-wprev.newHires:null;
      sHires=`оформлено за ${w.label.toLowerCase()}`;
      const intTotal=w.hrInt+w.hmInt+(w.techInt||0)+(w.finInt||0);
      const prevIntTotal=wprev?wprev.hrInt+wprev.hmInt+(wprev.techInt||0)+(wprev.finInt||0):null;
      kpi6val=intTotal; dKpi6=prevIntTotal!==null?intTotal-prevIntTotal:null;
      const techPart=w.techInt?` · тех: ${w.techInt}`:'';
      const finPart=w.finInt?` · фин: ${w.finInt}`:'';
      sKpi6=`HR: ${w.hrInt} · HM: ${w.hmInt}${techPart}${finPart}`; lblKpi6='Интервью за неделю';
      openVac=openNow; sOpen='сейчас в работе';
    }
  }

  // Animate
  if(hc!==null) countUp($('v-hc'),hc); else setTxt('v-hc','—');
  const ST=__D.STAFF||{hc:143,plan:149,managers:34,ic:109};
  countUp($('v-staff'),Math.round(ST.hc/ST.plan*100),600,0,'%');
  countUp($('v-mgr'),+(ST.managers/ST.hc*100).toFixed(1),600,1,'%');
  countUp($('v-open'),openVac);
  countUp($('v-hires'),hires);
  if(kpi6val!==null) countUp($('v-kpi6'),kpi6val,600,mode==='weekly'&&period!=='all'?0:1,mode==='weekly'&&period!=='all'?'':mode==='monthly'?'д.':'');

  // Текучесть — из MONTHS (в источнике больше нет причины увольнения → vol/inv могут быть null)
  // блок текучести удалён с дашборда по решению Екатерины (04.08.2026); данные fired остаются в MONTHS
  showDelta('d-hc',dHC);
  showDelta('d-hires',dHires);
  showDelta('d-kpi6',dKpi6,mode==='monthly'?'д.':'',mode==='monthly');
  showDelta('d-tv',null);

  setTxt('s-hc',sHC||'');
  setTxt('s-open',sOpen||'');
  setTxt('s-hires',sHires||'');
  setTxt('s-kpi6',sKpi6||'');
  setTxt('lbl-kpi6',lblKpi6||'Среднее TTO');

  // Update donut center number
  const dcEl=$('dc-num');
  if(dcEl){
    if(mode==='monthly'){
      countUp(dcEl,period==='all'?Object.values(MONTHS).reduce((s,m)=>s+m.hires,0):MONTHS[parseInt(period)]?.hires||0);
    } else {
      if(period==='all') countUp(dcEl,W_NH_DATA.reduce((s,v)=>s+v,0));
      else countUp(dcEl,WEEKS[WEEK_MAP[period]]?.newHires||0);
    }
  }
}

// ══════════════════════════════════════════════════════════
// MAIN BAR CHART (top-left)
// ══════════════════════════════════════════════════════════
const barLabelsPlugin = {
  id:'barLabels',
  afterDatasetsDraw(chart){
    const {ctx:c, scales:{x,y}, data} = chart;
    c.save();
    c.font = '600 12px Inter, sans-serif';
    c.textAlign = 'center';
    c.textBaseline = 'bottom';
    data.datasets[0].data.forEach((v,i)=>{
      if(!v) return;
      const xPx = x.getPixelForValue(i);
      const yPx = y.getPixelForValue(v);
      c.fillStyle = '#374151';
      c.fillText(v, xPx, yPx - 5);
    });
    c.restore();
  }
};

function buildMainChart(){
  if(mainChart){ mainChart.destroy(); mainChart=null; }
  const ctx=document.getElementById('ch-main').getContext('2d');

  if(mode==='monthly'){
    const labels=MONTH_ORDER.map(m=>MONTHS[m].name);
    const data=MONTH_ORDER.map(m=>MONTHS[m].hires);
    const bgColors=data.map((_,i)=>
      period==='all'?'#3B6FE0':(parseInt(period)===i+1?'#3B6FE0':'#C7D5F7')
    );
    mainChart=new Chart(ctx,{
      type:'bar',
      data:{labels,datasets:[{data,backgroundColor:bgColors,borderRadius:6,borderSkipped:false}]},
      options:{
        responsive:true,maintainAspectRatio:false,
        layout:{padding:{top:20}},
        plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>` ${c.raw} оформлений`}}},
        scales:{
          x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:12}}},
          y:{grid:{color:'#F3F4F6'},border:{display:false,dash:[4,4]},ticks:{color:'#9CA3AF',font:{size:12}},beginAtZero:true},
        },
        animation:{duration:500,easing:'easeOutCubic'},
      },
      plugins:[barLabelsPlugin],
    });
    setTxt('lbl-main-chart','Оформления по месяцам');
    const allTotal = data.reduce((s,v)=>s+v,0);
    setTxt('badge-main-chart',
      period==='all'?`${allTotal} итого`:`${MONTHS[parseInt(period)]?.hires||0} в ${MONTHS[parseInt(period)]?.prep||''}`);
  } else {
    // Weekly new hires
    const bgColors=W_NH_DATA.map((_,i)=>{
      if(period==='all') return '#3B6FE0';
      return W_NH_WEEKS[i].key===period?'#3B6FE0':'#C7D5F7';
    });
    const totalNH=W_NH_DATA.reduce((s,v)=>s+v,0);
    mainChart=new Chart(ctx,{
      type:'bar',
      data:{labels:W_NH_LABELS,datasets:[{data:W_NH_DATA,backgroundColor:bgColors,borderRadius:5,borderSkipped:false}]},
      options:{
        responsive:true,maintainAspectRatio:false,
        layout:{padding:{top:20}},
        plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>` ${c.raw} новых сотрудников`}}},
        scales:{
          x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:11},maxRotation:30}},
          y:{grid:{color:'#F3F4F6'},border:{display:false,dash:[4,4]},ticks:{color:'#9CA3AF',font:{size:11}},beginAtZero:true},
        },
        animation:{duration:500,easing:'easeOutCubic'},
      },
      plugins:[barLabelsPlugin],
    });
    setTxt('lbl-main-chart','Новые сотрудники по неделям');
    setTxt('badge-main-chart',
      period==='all'?`${totalNH} итого`:`${WEEKS[WEEK_MAP[period]]?.newHires||0} на ${WEEKS[WEEK_MAP[period]]?.label||''}`);
  }
}

function updateMainChart(){
  if(!mainChart){ buildMainChart(); return; }
  if(mode==='monthly'){
    mainChart.data.datasets[0].backgroundColor=MONTH_ORDER.map(i=>
      period==='all'?'#3B6FE0':(parseInt(period)===i?'#3B6FE0':'#C7D5F7')
    );
    mainChart.update('active');
    const allTotal=Object.values(MONTHS).reduce((s,m)=>s+m.hires,0);
    setTxt('badge-main-chart',
      period==='all'?`${allTotal} итого`:`${MONTHS[parseInt(period)]?.hires||0} в ${MONTHS[parseInt(period)]?.prep||''}`);
  } else {
    mainChart.data.datasets[0].backgroundColor=W_NH_DATA.map((_,i)=>
      period==='all'?'#3B6FE0':(W_NH_WEEKS[i].key===period?'#3B6FE0':'#C7D5F7')
    );
    mainChart.update('active');
    const totalNH=W_NH_DATA.reduce((s,v)=>s+v,0);
    setTxt('badge-main-chart',
      period==='all'?`${totalNH} итого`:`${WEEKS[WEEK_MAP[period]]?.newHires||0} на ${WEEKS[WEEK_MAP[period]]?.label||''}`);
  }
}

// ══════════════════════════════════════════════════════════
// WEEKLY CHARTS (headcount + interviews)
// ══════════════════════════════════════════════════════════
function buildWeeklyHC(){
  if(hcChart){ hcChart.destroy(); hcChart=null; }
  const ctx=document.getElementById('ch-whc').getContext('2d');

  // Point colors: highlight selected week
  const pointColors=W_HC_WEEKS.map(w=>
    period==='all'||w.key!==period?'#3B6FE0':'#F04438'
  );
  const pointRadius=W_HC_WEEKS.map(w=>
    period!=='all'&&w.key===period?6:3
  );

  const hcLabelsPlugin = {
    id:'hcLabels',
    afterDatasetsDraw(chart){
      const {ctx:c, scales:{x,y}, data} = chart;
      const vals = data.datasets[0].data;
      c.save();
      c.font = '600 10px Inter, sans-serif';
      c.textAlign = 'center';
      c.textBaseline = 'bottom';
      vals.forEach((v,i)=>{
        if(v==null) return;
        const xPx = x.getPixelForValue(i);
        const yPx = y.getPixelForValue(v);
        // фон-пилюля
        const txt = String(v);
        const w2 = c.measureText(txt).width + 8;
        c.fillStyle = 'rgba(255,255,255,0.85)';
        c.beginPath();
        c.roundRect(xPx - w2/2, yPx - 18, w2, 14, 4);
        c.fill();
        c.fillStyle = '#3B6FE0';
        c.fillText(txt, xPx, yPx - 5);
      });
      c.restore();
    }
  };

  hcChart=new Chart(ctx,{
    type:'line',
    data:{
      labels:W_HC_LABELS,
      datasets:[{
        data:W_HC_DATA,
        borderColor:'#3B6FE0',backgroundColor:'rgba(59,111,224,.09)',
        fill:true,tension:0.35,
        pointRadius,pointBackgroundColor:pointColors,
        borderWidth:2,
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      layout:{padding:{top:22}},
      plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>` ${c.raw} чел.`}}},
      scales:{
        x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:11},maxRotation:30}},
        y:{grid:{color:'#F3F4F6'},border:{display:false,dash:[3,3]},ticks:{color:'#9CA3AF',font:{size:11}},beginAtZero:false},
      },
      animation:{duration:500,easing:'easeOutCubic'},
    },
    plugins:[hcLabelsPlugin],
  });
}

function buildWeeklyInterviews(){
  if(intChart){ intChart.destroy(); intChart=null; }
  const ctx=document.getElementById('ch-wint').getContext('2d');
  const a=(key)=>period==='all'?1:(key===period?1:0.3);
  const hrBg   =WEEKS.map(w=>`rgba(59,111,224,${a(w.key)})`);
  const hmBg   =WEEKS.map(w=>`rgba(16,185,105,${a(w.key)})`);
  const techBg =WEEKS.map(w=>`rgba(247,144,9,${a(w.key)})`);
  const finBg  =WEEKS.map(w=>`rgba(139,92,246,${a(w.key)})`);
  const techData=WEEKS.map(w=>w.techInt);
  const finData =WEEKS.map(w=>w.finInt);
  const total=WEEKS.reduce((s,w)=>s+w.hrInt+w.hmInt+(w.techInt||0)+(w.finInt||0),0);
  setTxt('badge-int',`${total} итого`);

  const totalLabelsPlugin = {
    id:'stackTotals',
    afterDatasetsDraw(chart){
      const {ctx:c, scales:{x,y}, data} = chart;
      const n = data.labels.length;
      c.save();
      c.font = '600 11px Inter, sans-serif';
      c.fillStyle = '#374151';
      c.textAlign = 'center';
      c.textBaseline = 'bottom';
      for(let i=0;i<n;i++){
        let sum = 0;
        data.datasets.forEach(ds=>{ const v=ds.data[i]; if(v!=null&&v>0) sum+=v; });
        if(sum===0) continue;
        const xPx = x.getPixelForValue(i);
        const yPx = y.getPixelForValue(sum);
        c.fillText(sum, xPx, yPx - 4);
      }
      c.restore();
    }
  };

  intChart=new Chart(ctx,{
    type:'bar',
    data:{
      labels:W_INT_LABELS,
      datasets:[
        {label:'HR',          data:W_INT_HR,  backgroundColor:hrBg,  borderRadius:2,borderSkipped:false,stack:'s'},
        {label:'Заказчик',    data:W_INT_HM,  backgroundColor:hmBg,  borderRadius:2,borderSkipped:false,stack:'s'},
        {label:'Техническое', data:techData,  backgroundColor:techBg,borderRadius:2,borderSkipped:false,stack:'s'},
        {label:'Финальное',   data:finData,   backgroundColor:finBg, borderRadius:2,borderSkipped:false,stack:'s'},
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      layout:{padding:{top:20}},
      plugins:{
        legend:{display:false},
        tooltip:{...TT,mode:'index',intersect:false,callbacks:{
          label:c=>c.raw!=null&&c.raw>0?` ${c.dataset.label}: ${c.raw}`:null,
          footer:items=>{
            const sum=items.reduce((s,i)=>s+(i.raw||0),0);
            return sum>0?`Итого: ${sum}`:'';
          }
        }},
      },
      scales:{
        x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:11},maxRotation:30}},
        y:{grid:{color:'#F3F4F6'},border:{display:false,dash:[3,3]},ticks:{color:'#9CA3AF',font:{size:11}},stacked:true,beginAtZero:true},
      },
      animation:{duration:500,easing:'easeOutCubic'},
    },
    plugins:[totalLabelsPlugin],
  });
}

function updateWeeklyCharts(){
  // Rebuild to update highlight
  buildWeeklyHC();
  buildWeeklyInterviews();
}

// ══════════════════════════════════════════════════════════
// STATIC CHARTS (sources, roles)
// ══════════════════════════════════════════════════════════
function initSources(){
  if(!document.getElementById('ch-src')) return;
  new Chart(document.getElementById('ch-src').getContext('2d'),{
    type:'doughnut',
    data:{labels:SOURCES.map(s=>s.label),datasets:[{data:SOURCES.map(s=>s.count),backgroundColor:SOURCES.map(s=>s.color),borderWidth:0,hoverOffset:6}]},
    options:{responsive:false,cutout:'68%',plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>`${c.label}: ${c.raw} оформлений`}}},animation:{duration:700}},
  });
  const total=SOURCES.reduce((s,x)=>s+x.count,0);
  document.getElementById('src-legend').innerHTML=SOURCES.map(s=>`
    <div class="leg-row"><div class="leg-dot" style="background:${s.color}"></div>
    <span>${s.label}</span><span class="leg-pct">${Math.round(s.count/total*100)}%</span></div>`).join('');
}
function renderWeeklyTasks(){
  // приоритеты задач скрыты по решению Екатерины (04.08.2026)

  // подписи недель — из данных (обновляются вместе с задачами)
  const dl=document.getElementById('wt-done-lbl'), fl=document.getElementById('wt-focus-lbl');
  if(dl && WEEKLY_TASKS.done.week)  dl.textContent = WEEKLY_TASKS.done.week + ' — итоги';
  if(fl && WEEKLY_TASKS.focus.week) fl.textContent = WEEKLY_TASKS.focus.week + ' — план';

  // Итоги (выполнено)
  const doneEl = document.getElementById('tasks-done');
  if(doneEl) doneEl.innerHTML = WEEKLY_TASKS.done.items.map(t => {
    return `<div style="display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #F3F4F6">
      <div style="width:20px;height:20px;border-radius:50%;background:#DCFAE6;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">
        <span style="font-size:11px;line-height:1">\u2713</span>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-size:13px;font-weight:500;color:var(--text);line-height:1.4">${t.task}</div>
        ${t.result ? `<div style="font-size:11px;color:var(--muted);margin-top:4px;line-height:1.4">\u2192 ${t.result}</div>` : ''}
      </div>
    </div>`;
  }).join('');

  // Фокусы
  const focusEl = document.getElementById('tasks-focus');
  if(focusEl) focusEl.innerHTML = WEEKLY_TASKS.focus.items.map((t,i) => {
    const isLast = i === WEEKLY_TASKS.focus.items.length - 1;
    return `<div style="display:flex;gap:10px;align-items:flex-start;padding:10px 0;${isLast?'':'border-bottom:1px solid #F3F4F6'}">
      <div style="width:20px;height:20px;border-radius:50%;border:2px solid #3B6FE0;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px"></div>
      <div style="font-size:13px;font-weight:500;color:var(--text);line-height:1.4;flex:1">${t.task}</div>
    </div>`;
  }).join('');
}

function renderVacanciesTable(){
  const tbody = document.getElementById('vac-tbody');
  if(!tbody) return;
  const PRIORITY = {
    Critical: {label:'Critical', bg:'#FEE4E2', color:'#F04438'},
    High:     {label:'High',     bg:'#FEF6E7', color:'#F79009'},
    Medium:   {label:'Medium',   bg:'#EFF4FF', color:'#3B6FE0'},
    Low:      {label:'Low',      bg:'#E8F8F0', color:'#12B76A'},
  };
  const P_ORDER = {Critical:0, High:1, Medium:2, Low:3};
  const dayColor = d => d>=30?'#F04438':d>=15?'#F79009':d>=7?'#F59E0B':'#12B76A';
  const sorted = [...HF_OPEN_VACS].sort((a,b)=>{
    const pd = (P_ORDER[a.priority]||0)-(P_ORDER[b.priority]||0);
    return pd!==0 ? pd : b.days-a.days;
  });
  const badge = document.getElementById('vac-badge');
  if(badge) badge.textContent = sorted.length;
  tbody.innerHTML = sorted.map((v,i)=>{
    const pr = PRIORITY[v.priority]||PRIORITY.Medium;
    const dc = dayColor(v.days);
    const bg = i%2===0 ? '#fff' : '#FAFAFA';
    return `<tr style="background:${bg}">
      <td style="padding:10px 12px 10px 20px;border-bottom:1px solid #F3F4F6;font-size:13px;font-weight:500;color:var(--text)">${v.name}</td>
      <td style="padding:10px;border-bottom:1px solid #F3F4F6;font-size:12px;color:var(--muted);white-space:nowrap">${v.dept}</td>
      <td style="padding:10px;border-bottom:1px solid #F3F4F6;font-size:12px;color:var(--muted);white-space:nowrap">${v.recruiter}</td>
      <td style="padding:10px;border-bottom:1px solid #F3F4F6;text-align:right;white-space:nowrap">
        <span style="font-size:12px;font-weight:700;color:${dc};background:${dc}1A;padding:3px 9px;border-radius:20px">${v.days}д</span>
      </td>
      <td style="padding:10px 20px 10px 10px;border-bottom:1px solid #F3F4F6;text-align:center;white-space:nowrap">
        <span style="font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;background:${pr.bg};color:${pr.color}">${pr.label}</span>
      </td>
    </tr>`;
  }).join('');
}

function renderStructureCard(){
  const table = document.getElementById('dept-struct-table');
  if(!table) return;
  const openByDept = {};
  OPEN_VAC.forEach(v=>{ openByDept[v.dept]=(openByDept[v.dept]||0)+1; });
  const COLOR = {
    'Забота':'#10B981','ИТ':'#3B6FE0','Маркетинг':'#06B6D4','АУП':'#6B7280',
    'HR':'#8B5CF6','Партнеры':'#9CA3AF','Продукт':'#EC4899',
    'Рефералы':'#F59E0B','Фин':'#F59E0B','АХО':'#D1D5DB',
  };
  const status = pct =>
    pct < 60  ? {label:'Критично', c:'#F04438', bg:'#FEE4E2'} :
    pct < 80  ? {label:'Дефицит',  c:'#F79009', bg:'#FEF6E7'} :
    pct < 100 ? {label:'Внимание', c:'#F59E0B', bg:'#FFFBEB'} :
                {label:'Норма',    c:'#12B76A', bg:'#DCFAE6'};
  const rows = DEPT_BREAKDOWN.map(d=>{
    const open = openByDept[d.dept]||0;
    const total = d.count + open;
    const pct = Math.round(d.count/total*100);
    return {...d, open, pct};
  }).sort((a,b)=> a.pct!==b.pct ? a.pct-b.pct : b.count-a.count);

  const TH = t => `<th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 0 8px;border-bottom:1px solid var(--border);${t}">${arguments[1]||''}</th>`;
  table.innerHTML = `<thead><tr>
    <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 0 8px;border-bottom:1px solid var(--border);text-align:left">Отдел</th>
    <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 8px 8px;border-bottom:1px solid var(--border);text-align:right">Факт</th>
    <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 12px 8px;border-bottom:1px solid var(--border);text-align:left;min-width:120px">Укомпл.</th>
    <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 8px 8px;border-bottom:1px solid var(--border);text-align:right">Откр.</th>
    <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:10px 0 8px;border-bottom:1px solid var(--border);text-align:right">Статус</th>
  </tr></thead><tbody>` +
  rows.map(r=>{
    const c = COLOR[r.dept]||'#9CA3AF';
    const st = status(r.pct);
    const barColor = r.pct>=90?'#12B76A':r.pct>=70?'#F79009':'#F04438';
    const openCell = r.open>0
      ? `<span style="font-size:12px;font-weight:700;color:${st.c}">+${r.open}</span>`
      : `<span style="color:var(--micro);font-size:12px">—</span>`;
    return `<tr>
      <td style="padding:9px 0;font-size:13px;font-weight:500;border-bottom:1px solid #F9FAFB">
        <span style="display:inline-flex;align-items:center;gap:7px">
          <span style="width:7px;height:7px;border-radius:50%;background:${c};flex-shrink:0"></span>${r.dept}
        </span>
      </td>
      <td style="padding:9px 8px;text-align:right;font-size:13px;font-weight:700;border-bottom:1px solid #F9FAFB">${r.count}</td>
      <td style="padding:9px 12px;border-bottom:1px solid #F9FAFB">
        <div style="display:flex;align-items:center;gap:7px">
          <div style="flex:1;height:5px;background:#F3F4F6;border-radius:3px;overflow:hidden">
            <div style="height:100%;width:${r.pct}%;background:${barColor};border-radius:3px;transition:width .7s cubic-bezier(.22,1,.36,1)"></div>
          </div>
          <span style="font-size:11px;font-weight:700;color:${barColor};width:32px;text-align:right;flex-shrink:0">${r.pct}%</span>
        </div>
      </td>
      <td style="padding:9px 8px;text-align:right;border-bottom:1px solid #F9FAFB">${openCell}</td>
      <td style="padding:9px 0;text-align:right;border-bottom:1px solid #F9FAFB">
        <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;background:${st.bg};color:${st.c};white-space:nowrap">${st.label}</span>
      </td>
    </tr>`;
  }).join('') + `</tbody>`;
}

function initRoles(){
  if(!document.getElementById('ch-roles')) return;
  new Chart(document.getElementById('ch-roles').getContext('2d'),{
    type:'doughnut',
    data:{labels:['Руководители','Сотрудники'],datasets:[{data:[23,107],backgroundColor:['#3B6FE0','#E5E7EB'],borderWidth:0,hoverOffset:4}]},
    options:{responsive:false,cutout:'62%',plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>`${c.label}: ${c.raw}`}}},animation:{duration:700}},
  });
}

function initDeptsChart(){
  if(!document.getElementById('ch-depts')) return;
  const colors = DEPT_BREAKDOWN.map(d => DEPT_COLORS[d.dept] || '#D1D5DB');
  new Chart(document.getElementById('ch-depts').getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: DEPT_BREAKDOWN.map(d => d.dept),
      datasets: [{
        data: DEPT_BREAKDOWN.map(d => d.count),
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: false,
      cutout: '62%',
      plugins: {
        legend: { display: false },
        tooltip: {
          ...TT,
          callbacks: {
            label: c => ` ${c.label}: ${c.raw} чел. (${DEPT_BREAKDOWN[c.dataIndex].pct}%)`
          }
        }
      },
      animation: { duration: 800, easing: 'easeOutCubic' },
    }
  });

  // Legend
  const total = DEPT_BREAKDOWN.reduce((s,d)=>s+d.count,0);
  document.getElementById('dept-legend').innerHTML = DEPT_BREAKDOWN.map((d,i) => `
    <div class="dl-row" title="${d.dept}: ${d.count} чел.">
      <div class="dl-dot" style="background:${colors[i]}"></div>
      <span class="dl-name">${d.dept}</span>
      <span class="dl-val">${d.count}</span>
    </div>`).join('');
}

// ══════════════════════════════════════════════════════════
// DEPT BARS
// ══════════════════════════════════════════════════════════

function applyStaffStructure(){
  // «Структура персонала» — из STAFF (fetch_detali.py) и OPEN_VAC; статика в HTML только как fallback
  const ST=__D.STAFF; if(!ST) return;
  const openN=(OPEN_VAC||[]).length;
  const pct=Math.round(ST.hc/ST.plan*100);
  const S=(id,t)=>{const e=document.getElementById(id); if(e) e.textContent=t;};
  S('sp-pct',pct+'%');
  S('sp-active','Действующих: '+ST.hc);
  S('sp-plan','Штат: '+ST.plan+' · Открыто: '+openN);
  const f=document.getElementById('sp-fill'), em=document.getElementById('sp-empty');
  if(f) f.style.flex=pct; if(em) em.style.flex=100-pct;
  S('v-staff-sub',ST.hc+' из '+ST.plan+' по штату');
  S('v-mgr-sub',ST.managers+' руководителя / '+ST.ic+' ИК');
  S('rl-mgr-n',ST.managers); S('rl-ic-n',ST.ic);
  S('rl-mgr-pct',(ST.managers/ST.hc*100).toFixed(1)+'%');
  S('rl-ic-pct',(ST.ic/ST.hc*100).toFixed(1)+'%');
  const mb=document.getElementById('rl-mgr-bar'), ib=document.getElementById('rl-ic-bar');
  if(mb) mb.style.flex=ST.managers; if(ib) ib.style.flex=ST.ic;
}

function initStructureDonut(){
  // «Структура персонала» — круговая по отделам (DEPT_BREAKDOWN из живой ШТАТКИ)
  const cv=document.getElementById('ch-structure');
  if(!cv || !DEPT_BREAKDOWN || !DEPT_BREAKDOWN.length) return;
  const total=DEPT_BREAKDOWN.reduce((s,d)=>s+d.count,0);
  const S=(id,t)=>{const e=document.getElementById(id); if(e) e.textContent=t;};
  S('sp-total',total);
  const ST=__D.STAFF;
  if(ST){ S('sp-badge','укомплектованность '+Math.round(ST.hc/ST.plan*100)+'% ('+ST.hc+'/'+ST.plan+')'); }
  const colors=DEPT_BREAKDOWN.map((d,i)=>DEPT_COLORS[d.dept]||['#3B6FE0','#10B981','#F79009','#06B6D4','#8B5CF6','#EC4899','#F59E0B','#6B7280','#14B8A6','#EF4444','#84CC16','#A855F7'][i%12]);
  new Chart(cv.getContext('2d'),{
    type:'doughnut',
    data:{labels:DEPT_BREAKDOWN.map(d=>d.dept),
      datasets:[{data:DEPT_BREAKDOWN.map(d=>d.count),backgroundColor:colors,borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    options:{responsive:false,cutout:'66%',plugins:{legend:{display:false},
      tooltip:{...TT,callbacks:{label:c=>` ${c.label}: ${c.raw} чел. (${(c.raw/total*100).toFixed(1)}%)`}}},animation:{duration:700}},
  });
  const lg=document.getElementById('sp-legend');
  if(lg) lg.innerHTML=DEPT_BREAKDOWN.map((d,i)=>`
    <div style="display:flex;align-items:center;gap:8px;padding:4px 0">
      <div style="width:9px;height:9px;border-radius:50%;background:${colors[i]};flex-shrink:0"></div>
      <span style="font-size:12.5px;color:var(--text);flex:1">${d.dept}</span>
      <span style="font-size:13px;font-weight:800;color:var(--text)">${d.count}</span>
      <span style="font-size:11px;color:var(--micro);min-width:44px;text-align:right">${d.pct}%</span>
    </div>`).join('');
}

function renderDeptBars(){
  const el = document.getElementById('dept-bars');
  if(!el) return;
  const counts = {};
  HF_OPEN_VACS.forEach(v=>{ counts[v.dept]=(counts[v.dept]||0)+1; });
  const DEPT_COLOR = {
    'ИТ':'#3B6FE0','Маркетинг':'#06B6D4','Продукт':'#8B5CF6',
    'Забота':'#10B981','HR':'#EC4899','Финансы':'#F59E0B',
    'Юр.':'#F04438','АУП':'#6B7280','Другое':'#9CA3AF',
  };
  const rows = Object.entries(counts).sort((a,b)=>b[1]-a[1]);
  const max = rows[0][1];
  el.innerHTML = rows.map(([dept,cnt])=>{
    const color = DEPT_COLOR[dept]||'#9CA3AF';
    return `<div class="bar-row">
      <span class="bar-name">${dept}</span>
      <div class="bar-track"><div class="bar-fill" style="width:0;background:${color}" data-w="${Math.round(cnt/max*100)}"></div></div>
      <span class="bar-cnt">${cnt}</span>
    </div>`;
  }).join('');
  // animate
  el.querySelectorAll('.bar-fill').forEach((fill,i)=>{
    setTimeout(()=>{ fill.style.width=fill.dataset.w+'%'; }, 80*i);
  });
}

function animateBars(){ renderDeptBars(); }

// ══════════════════════════════════════════════════════════
// OPEN VACANCIES
// ══════════════════════════════════════════════════════════
function renderOpenList(){
  if(!document.getElementById('open-list')) return;
  const PRI_ORDER={Critical:0,High:1,Medium:2};
  const sorted=[...OPEN_VAC].sort((a,b)=>{
    const pd=PRI_ORDER[a.p]-PRI_ORDER[b.p];
    return pd!==0?pd:b.days-a.days;
  });
  const tc=v=>v.p==='Critical'?'tc':v.p==='High'?'th':'tm';
  const dayColor=d=>d>=30?'#F04438':d>=15?'#F79009':'#12B76A';
  const dayBg=d=>d>=30?'#FEE4E2':d>=15?'#FEF6E7':'#DCFAE6';
  document.getElementById('open-list').innerHTML=`
    <table style="width:100%;border-collapse:collapse">
      <thead><tr>
        <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:0 10px 10px;text-align:left;border-bottom:1px solid var(--border)">Вакансия</th>
        <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:0 10px 10px;text-align:left;border-bottom:1px solid var(--border)">Отдел</th>
        <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:0 10px 10px;text-align:left;border-bottom:1px solid var(--border)">Рекрутер</th>
        <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:0 10px 10px;text-align:center;border-bottom:1px solid var(--border)">Дней</th>
        <th style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--micro);padding:0 10px 10px;text-align:center;border-bottom:1px solid var(--border)">Приоритет</th>
      </tr></thead>
      <tbody>${sorted.map(v=>`
        <tr>
          <td style="padding:8px 10px;font-size:13px;font-weight:500;border-bottom:1px solid #F3F4F6">${v.name}</td>
          <td style="padding:8px 10px;font-size:12px;color:var(--muted);border-bottom:1px solid #F3F4F6;white-space:nowrap">${v.dept}</td>
          <td style="padding:8px 10px;font-size:12px;color:var(--muted);border-bottom:1px solid #F3F4F6;white-space:nowrap">${v.rec||'—'}</td>
          <td style="padding:8px 10px;text-align:center;border-bottom:1px solid #F3F4F6">
            <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:12px;color:${dayColor(v.days)};background:${dayBg(v.days)}">${v.days}д</span>
          </td>
          <td style="padding:8px 10px;text-align:center;border-bottom:1px solid #F3F4F6">
            <span class="tag ${tc(v)}">${v.p}</span>
          </td>
        </tr>`).join('')}
      </tbody>
    </table>`;
}

// ══════════════════════════════════════════════════════════
// CLOSED VACANCIES
// ══════════════════════════════════════════════════════════
const MONTH_NAMES={1:'Январь',2:'Февраль',3:'Март',4:'Апрель',5:'Май',6:'Июнь',7:'Июль',8:'Август',9:'Сентябрь',10:'Октябрь',11:'Ноябрь',12:'Декабрь'};
let closedFilter='all';
function renderClosed(){
  const rows=closedFilter==='all'?CLOSED_DATA:CLOSED_DATA.filter(r=>r.m===parseInt(closedFilter));
  const showMonth=closedFilter==='all';
  setTxt('closed-th-month',showMonth?'Месяц':'');
  document.getElementById('closed-body').innerHTML=rows.map(r=>{
    const dc=DEPT_COLORS[r.dept]||'#9CA3AF';
    const ttoCell = r.tto!=null
      ? (r.tto<=7?`<span style="color:#12B76A;font-weight:700">${r.tto}д</span>`:r.tto<=21?`<span style="color:#F79009;font-weight:700">${r.tto}д</span>`:`<span style="color:#F04438;font-weight:700">${r.tto}д</span>`)
      : `<span style="color:#9CA3AF">—</span>`;
    return `<tr>
      <td style="color:var(--muted);white-space:nowrap">${showMonth?MONTH_NAMES[r.m]:''}</td>
      <td style="font-weight:500">${r.vac}</td>
      <td><span class="dept-dot" style="background:${dc}"></span>${r.dept}</td>
      <td style="color:var(--muted)">${r.cand}</td>
      <td style="text-align:right">${ttoCell}</td>
    </tr>`;
  }).join('');
}
document.getElementById('closed-tabs').addEventListener('click',e=>{
  const btn=e.target.closest('.mtab');
  if(!btn) return;
  closedFilter=btn.dataset.m;
  document.querySelectorAll('.mtab').forEach(b=>b.classList.toggle('active',b===btn));
  renderClosed();
});

// ══════════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════════
// DEPT STAFFING
// ══════════════════════════════════════════════════════════
function renderDeptStaffing(){
  const el = document.getElementById('dept-staffing');
  if(!el) return;
  const openByDept = {};
  OPEN_VAC.forEach(v=>{ openByDept[v.dept]=(openByDept[v.dept]||0)+1; });
  const rows = [
    {dept:'ИТ',       color:'#3B6FE0'},
    {dept:'Маркетинг',color:'#06B6D4'},
    {dept:'Продукт',  color:'#EC4899'},
    {dept:'Забота',   color:'#10B981'},
  ];
  el.innerHTML = rows.map(r=>{
    const cur = (DEPT_BREAKDOWN.find(d=>d.dept===r.dept)||{count:0}).count;
    const op  = openByDept[r.dept]||0;
    const total = cur + op;
    const pct = total>0 ? Math.round(cur/total*100) : 100;
    const barColor = pct>=90?'#12B76A':pct>=70?'#F79009':'#F04438';
    return `<div class="dept-staff-row">
      <span class="dept-staff-name" style="color:${r.color}">${r.dept}</span>
      <div class="dept-staff-track"><div class="dept-staff-fill" style="width:${pct}%;background:${barColor}"></div></div>
      <span class="dept-staff-pct" style="color:${barColor}">${pct}%</span>
    </div>`;
  }).join('');
}

// ══════════════════════════════════════════════════════════
// RECRUITERS
// ══════════════════════════════════════════════════════════
function renderRecruiters(){
  const maxTTO=Math.max(...RECRUITERS.filter(r=>r.tto).map(r=>r.tto));
  const maxOpen=Math.max(...RECRUITERS.map(r=>r.open), 1);
  document.getElementById('rec-tbody').innerHTML=RECRUITERS.map((r,i)=>{
    const c=AVATAR_COLORS[i%AVATAR_COLORS.length];
    const ttoBar=r.tto?`<span style="display:inline-block;height:3px;width:${Math.round(r.tto/maxTTO*44)}px;background:var(--primary);border-radius:2px;margin-left:6px;vertical-align:middle"></span>`:'';
    const st=r.open>0?`<span style="color:var(--warning);font-weight:700">${r.open} акт.</span>`:`<span style="color:var(--micro)">—</span>`;
    // Нагрузка: открытых / (открытых + нанятых*0.05) — показывает соотношение
    const wlPct = r.open===0 ? 0 : Math.min(100, Math.round(r.open/maxOpen*100));
    const wlColor = wlPct>=80?'#F04438':wlPct>=50?'#F79009':'#12B76A';
    const wlLabel = wlPct>=80?'Высокая':wlPct>=50?'Средняя':'Низкая';
    const wlBar=`<span style="font-size:11px;color:${wlColor};font-weight:600">${wlLabel}</span><span class="wl-track"><span class="wl-fill" style="width:${wlPct}%;background:${wlColor}"></span></span>`;
    return `<tr>
      <td><div style="display:flex;align-items:center;gap:8px"><div class="av" style="background:${c}">${r.name[0]}</div><span style="font-weight:500">${r.name}</span></div></td>
      <td>${r.hired||'—'}</td>
      <td>${r.open||'—'}</td>
      <td style="text-align:left!important"><div style="display:flex;align-items:center;gap:4px">${wlBar}</div></td>
      <td>${r.tto?r.tto.toFixed(1):'—'}${ttoBar}</td>
      <td>${st}</td>
    </tr>`;
  }).join('');
}

// ══════════════════════════════════════════════════════════
// MODE SWITCH
// ══════════════════════════════════════════════════════════
document.querySelectorAll('.vtog').forEach(btn=>{
  btn.addEventListener('click',()=>{
    if(btn.dataset.mode===mode) return;
    mode=btn.dataset.mode;
    period='all';
    document.querySelectorAll('.vtog').forEach(b=>b.classList.toggle('active',b===btn));
    buildPeriodPills();
    buildMainChart();
    renderKPIs();
    updateWeeklyCharts();
  });
});

// ══════════════════════════════════════════════════════════
// QUALITY OF HIRE + WORK FORMAT + REFERRALS
// ══════════════════════════════════════════════════════════
function initQoH(){
  new Chart(document.getElementById('ch-qoh').getContext('2d'),{
    type:'doughnut',
    data:{labels:['Прошли ИС','На ИС','Нет данных'],datasets:[{data:[64,60,8],backgroundColor:['#12B76A','#F79009','#E5E7EB'],borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    options:{responsive:false,cutout:'68%',plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>`${c.label}: ${c.raw}`}}},animation:{duration:700}},
  });
}

const FMT_DATA = [
  {label:'Удалённо',     count:76, color:'#3B6FE0'},
  {label:'Офис Москва',  count:24, color:'#10B981'},
  {label:'Офис СПб',     count:22, color:'#8B5CF6'},
  {label:'Гибрид',       count:7,  color:'#F79009'},
  {label:'Не указано',   count:1,  color:'#E5E7EB'},
];
function initWorkFormat(){
  new Chart(document.getElementById('ch-fmt').getContext('2d'),{
    type:'doughnut',
    data:{labels:FMT_DATA.map(d=>d.label),datasets:[{data:FMT_DATA.map(d=>d.count),backgroundColor:FMT_DATA.map(d=>d.color),borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    options:{responsive:false,cutout:'62%',plugins:{legend:{display:false},tooltip:{...TT,callbacks:{label:c=>`${c.label}: ${c.raw} чел.`}}},animation:{duration:700}},
  });
  const total=FMT_DATA.reduce((s,d)=>s+d.count,0);
  document.getElementById('fmt-legend').innerHTML=FMT_DATA.map(d=>`
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:7px">
      <div style="width:8px;height:8px;border-radius:50%;background:${d.color};flex-shrink:0"></div>
      <span style="font-size:12px;color:var(--text);flex:1">${d.label}</span>
      <span style="font-size:12px;font-weight:700;color:var(--muted)">${Math.round(d.count/total*100)}%</span>
      <span style="font-size:12px;font-weight:700;color:var(--text);min-width:24px;text-align:right">${d.count}</span>
    </div>`).join('');
}

// блок «Реферальные сотрудники» удалён с дашборда по решению Екатерины (04.08.2026)

// ══════════════════════════════════════════════════════════
// INIT (after 800ms skeleton)
// ══════════════════════════════════════════════════════════
function removeSkeleton(){
  document.querySelectorAll('.skeleton').forEach(el=>el.classList.remove('skeleton'));
}

setTimeout(()=>{
  removeSkeleton();
  buildPeriodPills();
  buildMainChart();
  initSources();
  initRoles();
  buildWeeklyHC();
  buildWeeklyInterviews();
  initDeptsChart();
  initQoH();
  initWorkFormat();
  renderOpenList();
  renderClosed();
  renderRecruiters();
  animateBars();
  renderKPIs();
  initHuntflowCharts();
  renderHFOpenTable();
  renderHFFunnel();
  initClosedTabCounts();
  renderWeeklyTasks();
  renderStructureCard();
  renderVacanciesTable();
  renderSparklines();
  applyStaffStructure();
  initStructureDonut();
  initialized=true;
},800);

// ══════════════════════════════════════════════════════════
// HUNTFLOW DATA & CHARTS
// ══════════════════════════════════════════════════════════
// живая воронка из «Аналитики Хантфлоу» (апрель → сегодня): этап + сколько дошло + CR от предыдущего
const HF_FUNNEL = (() => {
  const f=(__D.HF||{}).funnel||[];
  if(!f.length) return [];
  const out=[{stage:'Оценка', count:f[0].in, cr:'100%'}];
  f.forEach(s=>{
    const nm=s.stage.split('→').pop().trim();
    out.push({stage:nm, count:s.out, cr:s.cr?Math.round(parseFloat(String(s.cr).replace(',','.'))*100)+'%':''});
  });
  return out;
})();

// живые данные: OPEN_VAC пересобирается fetch_detali.py из вкладки «Вакансии» при каждом обновлении
const HF_OPEN_VACS = (__D.OPEN_VAC||[]).map(v=>({name:v.name, dept:v.dept, recruiter:v.rec, days:v.days, priority:v.p}));


// ── Compute and inject closed-tab counts from actual CLOSED_DATA ──
function initClosedTabCounts(){
  const total = CLOSED_DATA.length;
  const byMonth = {};
  CLOSED_DATA.forEach(r=>{ byMonth[r.m]=(byMonth[r.m]||0)+1; });
  const el = id => document.getElementById(id);
  if(el('ctab-all'))  el('ctab-all').textContent  = total;
  [1,2,3,4,5,6,7,8,9,10,11,12].forEach(m=>{ if(el(`ctab-${m}`)) el(`ctab-${m}`).textContent = byMonth[m]||0; });
}

// ══════════════════════════════════════════════════════════
// SPARKLINES
// ══════════════════════════════════════════════════════════
function makeSpark(data, color, w=72, h=24){
  const min=Math.min(...data), max=Math.max(...data);
  const range=max-min||1;
  const xs=data.map((_,i)=>Math.round(i/(data.length-1)*(w-2)+1));
  const ys=data.map(v=>Math.round(h-1-(v-min)/range*(h-4)-1));
  const pts=xs.map((x,i)=>x+','+ys[i]).join(' ');
  const lastX=xs[xs.length-1], lastY=ys[ys.length-1];
  return `<svg class="kpi-spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" opacity=".7"/>
    <circle cx="${lastX}" cy="${lastY}" r="2.5" fill="${color}"/>
  </svg>`;
}

function renderSparklines(){
  const hireData=MONTH_ORDER.map(m=>MONTHS[m].hires||0);
  const hcData=MONTH_ORDER.map(m=>MONTHS[m].hc||0);
  const hireEl=document.querySelector('#kc5 .kpi-sub');
  if(hireEl && !document.querySelector('#kc5 .kpi-spark'))
    hireEl.insertAdjacentHTML('afterend', makeSpark(hireData,'#3B6FE0'));
  const hcEl=document.querySelector('#kc1 .kpi-sub');
  if(hcEl && !document.querySelector('#kc1 .kpi-spark'))
    hcEl.insertAdjacentHTML('afterend', makeSpark(hcData,'#12B76A'));
}

function renderHFFunnel(){
  if(!HF_FUNNEL.length){ const el=document.getElementById('hf-funnel'); if(el) el.innerHTML='<div style="font-size:12px;color:var(--micro);padding:20px 0">нет данных</div>'; return; }
  const max = HF_FUNNEL[0].count;
  document.getElementById('hf-funnel').innerHTML = HF_FUNNEL.map((s,i) => {
    const w = Math.max(2, Math.round(s.count/max*100));
    const color = i===0?'#3B6FE0':i<3?'#3B6FE0':i<4?'#10B981':'#F79009';
    const alpha = Math.max(0.35, 1 - i*0.12);
    const conv = s.cr || (i>0 ? Math.round(s.count/HF_FUNNEL[i-1].count*100)+'%' : '100%');
    return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">
      <span style="font-size:11px;color:var(--muted);width:170px;flex-shrink:0;text-align:right">${s.stage}</span>
      <div style="flex:1;height:20px;background:#F3F4F6;border-radius:4px;overflow:hidden;position:relative">
        <div style="height:100%;width:${w}%;background:${color};opacity:${alpha};border-radius:4px;transition:width .7s cubic-bezier(.22,1,.36,1)"></div>
        <span style="position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:11px;font-weight:700;color:#fff;line-height:1">${s.count.toLocaleString('ru')}</span>
      </div>
      <span style="font-size:11px;font-weight:600;color:var(--micro);width:36px;text-align:right;flex-shrink:0">${conv}</span>
    </div>`;
  }).join('');
}

function initHuntflowCharts(){
  const HF=__D.HF||{};
  // KPI-карточки секции
  const S=(id,t)=>{const e=document.getElementById(id); if(e) e.textContent=t;};
  if(HF.updated) S('hf-updated','данные Хантфлоу на '+HF.updated);
  const st=HF.vac_status||{};
  const tot=Object.values(st).reduce((s,v)=>s+v,0);
  if(tot){ S('hf-v-total',tot);
    S('hf-v-total-sub',(st['Открыта']||0)+' откр · '+(st['Закрыта']||0)+' закр · '+(st['На паузе']||0)+' пауза'); }
  if(HF.offers){
    if(HF.offers.tto_median!=null){ S('hf-v-tto',HF.offers.tto_median+'д'); S('hf-v-tto-sub','средн. '+HF.offers.tto_mean+'д по '+HF.offers.made+' офферам'); }
    S('hf-v-offers',HF.offers.made); S('hf-v-offers-sub','принято: '+HF.offers.accepted);
  }
  if(HF.oldest){ S('hf-v-oldest',HF.oldest.age+'д'); S('hf-v-oldest-sub',HF.oldest.vac); }
  const jm=(HF.months||{});
  const rec=jm['Интервью с рекрутером']||{}, tech=jm['Технические интервью']||{}, cust=jm['Интервью с заказчиком']||{};
  const mKeys=Object.keys(rec);
  if(mKeys.length){
    const m0=mKeys[0];
    S('hf-v-int',rec[m0]||'—');
    S('hf-v-int-sub','тех: '+(tech[m0]||0)+' · заказчик: '+(cust[m0]||0));
    const lbl=document.querySelector('#hf-kpi-row .kpi-card:nth-child(5) .kpi-lbl');
    if(lbl) lbl.textContent='Интервью, '+m0.toLowerCase();
  }
  // Типы интервью понедельно — отдельный график на каждого рекрутёра
  const rsw=HF.rec_stage_weekly||{};
  const rsGrid=document.getElementById('hf-rec-stage-grid');
  if(rsGrid && Object.keys(rsw).length){
    const totalOf=n=>Object.values(rsw[n]).reduce((s,w)=>s+w.rek+w.tech+w.cust,0);
    const names=Object.keys(rsw).sort((a,b)=>totalOf(b)-totalOf(a));
    const allWeeks=[...new Set(names.flatMap(n=>Object.keys(rsw[n])))].map(Number).sort((a,b)=>a-b);
    names.forEach((nm,idx)=>{
      const card=document.createElement('div');
      card.className='card p20';
      card.innerHTML=`<div class="ch"><span class="lbl mb0">${nm}</span><span class="badge">${totalOf(nm)} интервью</span></div>
        <div style="height:180px;position:relative"><canvas id="ch-rsw-${idx}"></canvas></div>`;
      rsGrid.appendChild(card);
      const get=(w,k)=>(rsw[nm][String(w)]||{})[k]||0;
      // хвостовые нули после последней активной недели → обрыв линии (не падаем в ноль)
      const trim=arr=>{
        let last=-1; arr.forEach((v,i)=>{ if(v) last=i; });
        return arr.map((v,i)=> i>last ? null : v);
      };
      new Chart(card.querySelector('canvas').getContext('2d'),{
        type:'line',
        data:{
          labels:allWeeks.map(w=>'Нед. '+w),
          datasets:[
            {label:'С HR',data:trim(allWeeks.map(w=>get(w,'rek'))),borderColor:'#3B6FE0',backgroundColor:'#3B6FE0',tension:.35,pointRadius:3,borderWidth:2.2,fill:false},
            {label:'Техническое',data:trim(allWeeks.map(w=>get(w,'tech'))),borderColor:'#F79009',backgroundColor:'#F79009',tension:.35,pointRadius:3,borderWidth:2.2,fill:false},
            {label:'С заказчиком',data:trim(allWeeks.map(w=>get(w,'cust'))),borderColor:'#10B981',backgroundColor:'#10B981',tension:.35,pointRadius:3,borderWidth:2.2,fill:false},
          ]
        },
        options:{
          responsive:true,maintainAspectRatio:false,
          plugins:{legend:{labels:{font:{size:10.5},boxWidth:9,usePointStyle:true}},
            tooltip:{...TT,callbacks:{label:c=>` ${c.dataset.label}: ${c.raw}`}}},
          scales:{
            x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:10.5}}},
            y:{grid:{color:'#F3F4F6'},border:{display:false},ticks:{color:'#9CA3AF',font:{size:10.5},stepSize:5},beginAtZero:true},
          },
          animation:{duration:700,easing:'easeOutCubic'},
        }
      });
    });
  }

  // План-факт интервью по рекрутёрам
  const pf=HF.plan_fact||[];
  const cv=document.getElementById('ch-ttf');
  if(!cv) return;
  if(!pf.length){ cv.parentElement.innerHTML='<div style="font-size:12px;color:var(--micro);padding:20px 0">нет данных</div>'; return; }
  const pfB=document.getElementById('hf-pf-badge');
  if(pfB) pfB.textContent='факт '+pf.reduce((s,p)=>s+(p.fact||0),0)+' из '+pf.reduce((s,p)=>s+(p.plan||0),0);
  new Chart(cv.getContext('2d'),{
    type:'bar',
    data:{
      labels:pf.map(p=>p.name.split(' ')[0]),
      datasets:[
        {label:'План',data:pf.map(p=>p.plan),backgroundColor:'#E5E7EB',borderRadius:5},
        {label:'Факт',data:pf.map(p=>p.fact),backgroundColor:'#3B6FE0',borderRadius:5},
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{font:{size:11},boxWidth:10,usePointStyle:true}},
        tooltip:{...TT,callbacks:{label:c=>` ${c.dataset.label}: ${c.raw}`}}},
      scales:{
        x:{grid:{display:false},border:{display:false},ticks:{color:'#9CA3AF',font:{size:11}}},
        y:{grid:{color:'#F3F4F6'},border:{display:false},ticks:{color:'#9CA3AF',font:{size:11}},beginAtZero:true},
      },
      animation:{duration:800,easing:'easeOutCubic'},
    }
  });
}

let hfRecFilter = 'all';

function renderHFOpenTable(){
  const tbody = document.getElementById('hf-open-tbody');
  if(!tbody) return;

  const PRIORITY = {
    Critical: {label:'Critical', color:'#F04438'},
    High:     {label:'High',     color:'#F79009'},
    Medium:   {label:'Medium',   color:'#3B6FE0'},
    Low:      {label:'Low',      color:'#12B76A'},
  };
  const ORDER = ['Critical','High','Medium','Low'];
  const dayColor = d => d>=30?'#F04438':d>=15?'#F79009':d>=7?'#F59E0B':'#12B76A';

  const source = hfRecFilter==='all'
    ? HF_OPEN_VACS
    : HF_OPEN_VACS.filter(v=>String(v.recruiter||'').includes(hfRecFilter));

  const badge = document.getElementById('hf-open-badge');
  if(badge) badge.textContent = source.length;

  const groups = {};
  ORDER.forEach(p => { groups[p] = source.filter(v=>v.priority===p); });

  let html = '';
  ORDER.forEach(pKey => {
    const list = groups[pKey];
    if(!list.length) return;
    const pr = PRIORITY[pKey];
    html += `<tr>
      <td colspan="3" style="padding:12px 20px 6px;background:#F9FAFB;border-top:1px solid #E5E7EB;border-bottom:1px solid #E5E7EB">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${pr.color};flex-shrink:0"></span>
          <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:${pr.color}">${pr.label}</span>
          <span style="font-size:10px;color:var(--micro);font-weight:500">${list.length} вак.</span>
        </div>
      </td>
    </tr>`;
    list.forEach(v => {
      const dc = dayColor(v.days);
      html += `<tr class="vac-row" style="border-left:3px solid ${pr.color}">
        <td style="padding:10px 16px 10px 14px;border-bottom:1px solid #F3F4F6">
          <span style="font-size:13px;font-weight:600;color:var(--text);display:block;line-height:1.3">${v.name}</span>
          <span style="font-size:11px;color:var(--micro);margin-top:1px;display:block">${v.dept}</span>
        </td>
        <td style="padding:10px 12px;border-bottom:1px solid #F3F4F6;font-size:12px;color:var(--muted);white-space:nowrap;vertical-align:middle">${v.recruiter}</td>
        <td style="padding:10px 20px 10px 12px;border-bottom:1px solid #F3F4F6;text-align:right;white-space:nowrap;vertical-align:middle">
          <span style="font-size:12px;font-weight:700;color:${dc};background:${dc}1A;padding:3px 9px;border-radius:20px">${v.days}д</span>
        </td>
      </tr>`;
    });
  });

  if(!html) html = `<tr><td colspan="3" style="padding:24px 20px;text-align:center;font-size:13px;color:var(--micro)">Нет вакансий</td></tr>`;
  tbody.innerHTML = html;

  tbody.querySelectorAll('.vac-row').forEach(tr=>{
    tr.addEventListener('mouseenter',()=>tr.style.background='#F9FAFB');
    tr.addEventListener('mouseleave',()=>tr.style.background='');
  });
}

document.addEventListener('click', e=>{
  const btn = e.target.closest('#hf-rec-filter .rfbtn');
  if(!btn) return;
  hfRecFilter = btn.dataset.rec;
  document.querySelectorAll('#hf-rec-filter .rfbtn').forEach(b=>b.classList.toggle('active', b===btn));
  renderHFOpenTable();
});
