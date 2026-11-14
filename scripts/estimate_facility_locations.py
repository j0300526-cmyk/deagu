"""Derive *approximate* map points from administrative areas and OSM places.

This does not locate treatment-plant parcels. It only places a representative
point within the named ri/eup/myeon/dong or on the named road. Source geometry
is pinned and cached locally, and the output includes a basis and source URL.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import requests
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "06c7a3456dd82965bd29042130441515717519ab"
SOURCE_BASE = f"https://raw.githubusercontent.com/DevMinGeonPark/mapcn-kr/{COMMIT}/data"
GEODATA_CREDIT = "Statistics Korea SGIS / mapcn-kr (CC BY 4.0)"
OSM_CREDIT = "OpenStreetMap contributors (ODbL)"
OUTPUT = ROOT / "data" / "coordinates_estimated.csv"
PUBLIC = ROOT / "public" / "downloads" / "coordinates_estimated.csv"


def read_geojson(filename: str) -> dict:
    cached = ROOT / "data" / "raw" / "geography" / filename.replace("/", "_")
    if not cached.exists():
        response = requests.get(f"{SOURCE_BASE}/{filename}", timeout=30)
        response.raise_for_status()
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(response.content)
    return json.loads(cached.read_text(encoding="utf-8"))


def representative(feature: dict) -> tuple[float, float]:
    point = shape(feature["geometry"]).representative_point()
    return round(point.y, 6), round(point.x, 6)


def main() -> None:
    analysis = json.loads((ROOT / "public" / "data" / "analysis.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "data" / "map_location_overrides.json").read_text(encoding="utf-8"))
    by_id = {row["facility_id"]: row for row in overrides["locations"]}
    admin_by_id = {row["facility_id"]: row for row in overrides["administrative_matches"]}
    ri = read_geojson("ri/27.json")["features"]
    emd = read_geojson("emd.json")["features"]
    ri_source = f"{SOURCE_BASE}/ri/27.json"
    emd_source = f"{SOURCE_BASE}/emd.json"
    rows = []
    for facility in analysis["facilities"]:
        fid = facility["facility_id"]
        base = {"facility_id": fid, "facility_name": facility["name"],
                "source_address": facility["address"], "status": "estimated",
                "reference_year": 2026}
        if fid in by_id:
            place = by_id[fid]
            base.update({key: place[key] for key in ("latitude", "longitude", "area_name", "basis", "source_url")})
            base["attribution"] = OSM_CREDIT
            base["note"] = "공개 주소에 등장하는 지명·도로의 OSM 대표점. 시설 건물·부지 좌표 아님."
        else:
            ri_names = [token for token in facility["address"].split() if token.endswith("리")]
            if ri_names:
                name = ri_names[-1]
                district_code = "27720" if facility["district"] == "군위군" else "27710"
                matches = [feature for feature in ri if feature["properties"]["li_nm"] == name
                           and feature["properties"]["sgg"] == district_code]
                if len(matches) != 1:
                    raise ValueError(f"Unresolved ri for {facility['name']}: {name}, n={len(matches)}")
                lat, lon = representative(matches[0])
                base.update({"latitude": lat, "longitude": lon, "area_name": name,
                             "basis": "행정리 구역 내부 대표점", "source_url": ri_source,
                             "attribution": GEODATA_CREDIT,
                             "note": "주소의 리와 행정경계 이름을 일치시켜 구역 내부점을 계산. 시설 필지 좌표 아님."})
            else:
                admin = admin_by_id.get(fid)
                if not admin:
                    raise ValueError(f"Unresolved address for {facility['name']}: {facility['address']}")
                matches = [feature for feature in emd if feature["properties"]["sido"] == "27"
                           and feature["properties"]["sggnm"] == facility["district"]
                           and feature["properties"]["dong"] == admin["area_name"]]
                if len(matches) != 1:
                    raise ValueError(f"Unresolved administrative area for {facility['name']}: {admin['area_name']}")
                lat, lon = representative(matches[0])
                base.update({"latitude": lat, "longitude": lon,
                             "area_name": admin["area_name"], "basis": admin["basis"],
                             "source_url": emd_source, "attribution": GEODATA_CREDIT,
                             "note": admin["note"] + " 시설 부지 좌표 아님."})
        if not (35.5 <= base["latitude"] <= 36.5 and 128.1 <= base["longitude"] <= 128.9):
            raise ValueError(f"Coordinate outside Daegu/Gunwi: {base['facility_name']}")
        rows.append(base)
    if len(rows) != len(analysis["facilities"]) or len({row["facility_id"] for row in rows}) != len(rows):
        raise ValueError("Map coverage or facility uniqueness failed")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    PUBLIC.write_bytes(OUTPUT.read_bytes())
    print(f"Estimated locations: {len(rows)}; administrative ri: {sum(r['basis'].startswith('행정리') for r in rows)}")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
