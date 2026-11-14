import { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from 'react-leaflet';
import { MapPin, Search, ShieldCheck } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import type { Analysis, Facility, MapCoordinate } from './types';
import { fmt, Note, Source, Takeaway } from './components';

type MapGroup = { key: string; latitude: number; longitude: number; locations: MapCoordinate[]; facilities: Facility[] };

function FitMapToLocations({ groups }: { groups: MapGroup[] }) {
  const map = useMap();
  const points = useMemo(() => groups.map(group => [group.latitude, group.longitude] as [number, number]), [groups]);
  useEffect(() => {
    if (points.length) map.fitBounds(points, { padding: [38, 38], maxZoom: 12, animate: false });
  }, [map, points]);
  return null;
}

export default function FacilityMap({ data, onSelect }: { data: Analysis; onSelect: (facility: Facility) => void }) {
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const rows = useMemo(
    () => data.facilities.filter(facility => `${facility.name} ${facility.district}`.includes(search.trim())),
    [data.facilities, search],
  );
  const locationById = useMemo(() => new Map(data.coordinates.map(location => [location.facility_id, location])), [data.coordinates]);
  const groups = useMemo(() => {
    const grouped = new Map<string, MapGroup>();
    for (const facility of rows) {
      const location = locationById.get(facility.facility_id);
      if (!location) continue;
      // Identical administrative representative points are one map place, not separate invented sites.
      const key = `${location.latitude.toFixed(6)},${location.longitude.toFixed(6)}`;
      const existing = grouped.get(key);
      if (existing) {
        existing.locations.push(location);
        existing.facilities.push(facility);
      } else {
        grouped.set(key, { key, latitude: location.latitude, longitude: location.longitude,
          locations: [location], facilities: [facility] });
      }
    }
    return [...grouped.values()];
  }, [rows, locationById]);
  const verified = data.quality.coordinates_verified_n;
  const estimated = data.quality.coordinates_estimated_n;

  return <>
    <Note tone="warning">
      주소 기반 추정 위치 {estimated}개 · 공식 검증 위치 {verified}개. 지도상의 점은 시설 부지 좌표가 아니라
      주소가 속한 행정구역 또는 동·도로의 대표점입니다. 위치를 길찾기나 현장 방문에 사용하지 마세요.
    </Note>
    <div className="map-layout">
      <section className="map-list panel">
        <div className="panel-head"><div><h2>대구 하수처리시설</h2><p>운영 지표 {data.meta.year}년 · {rows.length}개 시설</p></div><MapPin size={19}/></div>
        <label className="search map-search"><Search size={16}/><input value={search} onChange={event => setSearch(event.target.value)} aria-label="지도 시설 검색" placeholder="시설명 또는 구군 검색"/></label>
        <div className="map-items">
          {rows.map(facility => {
            const location = locationById.get(facility.facility_id);
            return <button className="map-item" key={facility.facility_id} onClick={() => onSelect(facility)}>
              <div><strong>{facility.name}</strong><span>{facility.district} · {facility.method}</span>
                <span className="map-item-location">{location ? `${location.status === 'verified' ? '공식 좌표' : '추정 위치'} · ${location.area_name || location.basis}` : '위치 미확인'}</span>
              </div><b>{fmt(facility.kwh_m3, 3)}<small>kWh/m³</small></b>
            </button>;
          })}
          {!rows.length && <p className="map-no-results">검색 결과가 없습니다.</p>}
        </div>
      </section>
      <div className="map-canvas">
        <MapContainer center={[35.95, 128.6]} zoom={9} scrollWheelZoom={false} style={{ width: '100%', height: '100%' }}>
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"/>
          <FitMapToLocations groups={groups}/>
          {groups.map(group => {
            const primary = group.locations[0];
            const isVerified = group.locations.some(location => location.status === 'verified');
            return <CircleMarker key={group.key} center={[group.latitude, group.longitude]}
              radius={group.facilities.length > 1 ? 11 : 8}
              pathOptions={isVerified
                ? { color: '#FFFFFF', fillColor: '#147D5A', fillOpacity: 1, weight: 2 }
                : { color: selectedKey === group.key ? '#8C5E20' : '#A77631', fillColor: '#FFFFFF', fillOpacity: .84, weight: 3 }}
              eventHandlers={{ click: () => setSelectedKey(group.key) }}>
              {group.facilities.length > 1 && <Tooltip permanent direction="top" offset={[0, -8]}>{group.facilities.length}개</Tooltip>}
              <Popup minWidth={240}>
                <div className="map-popup">
                  <span className="map-popup-status">{isVerified ? '공식 좌표' : '추정 위치'} · {primary.basis}</span>
                  <strong>{primary.area_name || '주소 기준 위치'}</strong>
                  <p>표시점은 시설 부지 좌표가 아닙니다. 같은 대표점을 사용하는 시설은 함께 표시합니다.</p>
                  {group.facilities.map(facility => <div className="map-popup-facility" key={facility.facility_id}>
                    <b>{facility.name}</b>
                    <span>{fmt(facility.kwh_m3, 3)} kWh/m³ · 전력 {fmt(facility.electricity_kwh, 0)} kWh/년</span>
                    <span>BOD 제거 {fmt(facility.bod_removal_pct, 1)}% · 간접배출 {fmt(facility.indirect_tco2e_est, 1)} tCO₂eq/년</span>
                    <button onClick={() => onSelect(facility)}>시설 상세 보기</button>
                  </div>)}
                  <a href={primary.source_url} target="_blank" rel="noreferrer">위치 추정 근거 ↗</a>
                </div>
              </Popup>
            </CircleMarker>;
          })}
        </MapContainer>
        <div className="map-status"><ShieldCheck size={19}/><div><strong>주소 기반 추정 {estimated}개</strong><span>공식 좌표 {verified}개 · 현재 {groups.length}개 지도점</span></div></div>
        <div className="map-year">운영 지표 {data.meta.year}년 · 위치 기준 2026년</div>
        <div className="map-legend"><i/>추정 대표점 <span>· 시설 부지 위치 아님</span></div>
      </div>
    </div>
    <Takeaway source={`${data.meta.year}년 운영 지표 · 2026년 주소 기반 추정 위치 · 한국환경공단 / SGIS / OpenStreetMap`}>지도의 점은 시설이 속한 지역을 찾는 단서입니다. 옆의 kWh/m³는 시설별 유입량당 전력이므로 위치가 가까운 시설의 수치 차이를 살펴볼 수 있지만, 공간적 원인을 증명하지는 않습니다.</Takeaway>
    <div className="note"><MapPin size={17}/><div>
      추정점은 2026년 행정리·읍면동 경계 또는 OpenStreetMap 동·도로 객체에서 얻었습니다.
      <a href="/downloads/coordinates_estimated.csv" download> 시설별 위치 유형·원주소·근거 CSV ↓</a>
      <br/>행정경계: Statistics Korea SGIS / mapcn-kr (CC BY 4.0). 지도·동·도로: © OpenStreetMap contributors (ODbL).
    </div></div>
    <Source data={data}/>
  </>;
}
