// Real-data React rendering smoke check. This does not replace a browser interaction test.
import { build } from 'esbuild';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import React from 'react';
import { renderToString } from 'react-dom/server';

await mkdir('tmp', { recursive: true });
await build({entryPoints:['src/pages.tsx'],outfile:'tmp/render-pages.mjs',bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic'});
const pages=await import(pathToFileURL(resolve('tmp/render-pages.mjs')).href);
const data=JSON.parse(await readFile('public/data/analysis.json','utf8'));
const names=['Overview','Benchmark','AIInsights','CarbonSimulator','PolicyInsights','DataQuality'];
const results=[];
for(const name of names){
 const html=renderToString(React.createElement(pages[name],{data,onSelect:()=>{},go:()=>{}}));
 if(!html.includes('2025')||html.includes('NaN')||html.includes('undefined'))throw new Error(`${name}: invalid real-data rendering`);
 if(name==='AIInsights' && data.model.shap?.available){
  if(!html.includes('XGBoost')||!html.includes('SHAP')||!html.includes('log(kWh/m³)'))throw new Error('AIInsights: missing model or SHAP scale');
  if(!html.includes('평균 절대 SHAP 수치 확인')||!html.includes('기준값에서 예측까지'))throw new Error('AIInsights: missing global or local explanation');
  for(const row of data.model.shap.predictions){
   if(!html.includes(`value="${row.facility_id}"`))throw new Error('AIInsights: missing real facility option');
  }
 }
 results.push({page:name,rendered:true,htmlBytes:Buffer.byteLength(html)});
}
await writeFile('tmp/render-smoke.json',JSON.stringify(results,null,2));
console.log(JSON.stringify(results,null,2));
await build({entryPoints:['src/AIInsights.tsx'],outfile:'tmp/render-ai.mjs',bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic'});
const {modelPrediction}=await import(pathToFileURL(resolve('tmp/render-ai.mjs')).href);
for(const row of data.model.predictions){
 for(const [algorithm,field] of [['Ridge 기준모델','baseline_predicted'],['Random Forest','rf_predicted'],['XGBoost','xgb_predicted']]){
  if(!data.model.evaluations.some(item=>item.name===algorithm))continue;
  if(modelPrediction(row,algorithm)!==row[field])throw new Error(`Wrong plotted prediction: ${algorithm} / ${row.facility_id}`);
 }
}
console.log('Real-data model selection checks passed.');
await build({entryPoints:['src/scenario.ts'],outfile:'tmp/scenario-check.mjs',bundle:true,platform:'node',format:'esm'});
const {calculateScenario,scenarioCsv}=await import(pathToFileURL(resolve('tmp/scenario-check.mjs')).href);
for(const rate of [0,1,10,30]){
 const city=calculateScenario(data.summary.daegu.electricity_kwh,rate,data.meta.factor.value);
 const parts=data.facilities.map(f=>calculateScenario(f.electricity_kwh,rate,data.meta.factor.value));
 const sum=parts.reduce((total,p)=>total+p.carbon,0);
 if(Math.abs(city.carbon-sum)>1e-8)throw new Error('Scenario facility/city mismatch');
 if(Math.abs(city.carbon-city.saving/1000*data.meta.factor.value)>1e-8)throw new Error('Scenario unit mismatch');
}
for(const rate of [-1,31,NaN]){
 let rejected=false;try{calculateScenario(1000,rate,.433);}catch{rejected=true;}
 if(!rejected)throw new Error('Invalid scenario input accepted');
}
if(scenarioCsv([['a,b','a"b']])!=='\uFEFF"a,b","a""b"\r\n')throw new Error('CSV escaping failed');
console.log('Scenario units, boundaries, facility totals and CSV escaping passed.');
