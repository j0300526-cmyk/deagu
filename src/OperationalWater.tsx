import { useState } from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ArrowUpRight, CalendarDays, Database } from 'lucide-react';
import type { OperationalAPI } from './types';
import { DownloadLink, Empty, fmt, Note, Panel } from './components';

export default function OperationalWater({api}:{api:OperationalAPI}) {
 const[site,setSite]=useState(api.effluent_sites.includes('신천사업소')?'신천사업소':api.effluent_sites[0]??'');
 const[metric,setMetric]=useState('T-N');
 const rows=api.monthly.filter(x=>x.site===site&&x.metric===metric);
 const coverage=api.coverage.find(x=>x.site===site&&x.metric===metric);
 return <Panel title="일별 공공데이터로 보는 방류수의 계절 변화" subtitle={`${api.year}년 · API 운영일 ${api.operation_days}일 · 연간 에너지 비교와 별도 집계`} action={<DownloadLink file="hasu_effluent_monthly_2025.csv" label="월별 수질 CSV"/>}>
  <div className="filter-bar"><span className="filter-title"><CalendarDays size={16}/>실제 운영일 기준</span><label><span className="sr-only">API 사업소</span><select aria-label="수질 API 사업소" value={site} onChange={e=>setSite(e.target.value)}>{api.effluent_sites.map(x=><option key={x}>{x}</option>)}</select></label><label><span className="sr-only">방류 수질 항목</span><select aria-label="방류 수질 항목" value={metric} onChange={e=>setMetric(e.target.value)}>{['T-N','T-P','TOC','SS'].map(x=><option key={x}>{x}</option>)}</select></label><span className="muted">유효 관측 {coverage?.valid_days??0}/365일 · mg/L</span></div>
  <Note>일 관측값의 월별 단순 평균이며 유량 가중 평균이 아닙니다. 사업소명은 API 원문 표기이고, 전력 효율·감축 효과의 월별 변화로 해석하지 않습니다.</Note>
  {rows.some(x=>x.mean!=null)?<div className="chart" role="img" aria-label={`${api.year}년 ${site} 방류 ${metric} 월평균 mg/L`}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{top:15,right:25,left:0,bottom:10}}><CartesianGrid stroke="#E4EADD" vertical={false}/><XAxis dataKey="month" tick={{fontSize:10,fill:'#65786D'}} tickFormatter={x=>`${String(x).slice(-2)}월`} axisLine={false} tickLine={false}/><YAxis domain={[0,'auto']} tick={{fontSize:10,fill:'#65786D'}} tickFormatter={v=>fmt(v,metric==='T-P'?2:1)} axisLine={false} tickLine={false}/><Tooltip content={({active,payload})=>{if(!active||!payload?.length)return null;const x=payload[0].payload as OperationalAPI['monthly'][number];return <div className="custom-tooltip"><strong>{site} · {x.month}</strong><b>{metric} {fmt(x.mean,3)} mg/L</b><span>유효 {x.valid_days}/{x.calendar_days}일</span><span>관측 범위 {fmt(x.min,3)}–{fmt(x.max,3)} mg/L</span></div>}}/><Line type="linear" dataKey="mean" name={metric} connectNulls={false} stroke="#147D5A" strokeWidth={2} dot={{r:3,strokeWidth:1,fill:'#fff'}} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>:<Empty title="선택한 항목의 유효 관측값이 없습니다">다른 사업소 또는 항목을 선택해 주세요. 결측값을 0으로 대체하지 않았습니다.</Empty>}
  <p className="chart-caption">{site} · {metric} · 월별 mg/L · 유효 관측일만 집계. 결측 월은 선으로 연결하지 않습니다.</p>
  <details className="method-details"><summary>월별 유효 일수와 관측 범위 확인</summary><div className="table-wrap" tabIndex={0} role="region" aria-label="분석 결과 표"><table><thead><tr><th>관측월</th><th>단순 평균 mg/L</th><th>관측 최소 mg/L</th><th>관측 최대 mg/L</th><th>유효 / 달력 일수</th><th>관측률</th></tr></thead><tbody>{rows.map(x=><tr key={x.month}><td>{x.month}</td><td>{fmt(x.mean,3)}</td><td>{fmt(x.min,3)}</td><td>{fmt(x.max,3)}</td><td>{x.valid_days}/{x.calendar_days}</td><td>{fmt(x.coverage_pct,1)}%</td></tr>)}</tbody></table></div></details>
  <div className="source"><Database size={13}/><a href={api.source_url} target="_blank" rel="noreferrer">대구공공시설관리공단 하수 처리 현황 GW<ArrowUpRight size={12}/></a><span>{api.start_date}–{api.end_date} · 응답 opdate 기준</span></div>
 </Panel>;
}
