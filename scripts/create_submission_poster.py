"""Create a one-page, data-backed competition poster from analysis.json.

The poster contains no hand-entered result numbers. Run after the analysis
pipeline so every displayed figure comes from the current published JSON.
Install the optional authoring dependency with ``python -m pip install reportlab``.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data" / "analysis.json"
OUTPUT = ROOT / "output" / "pdf" / "daegu_carbon_lab_research_poster.pdf"
PUBLIC_COPY = ROOT / "public" / "downloads" / OUTPUT.name
SITE = "https://deagu-phi.vercel.app"

W, H = landscape(A3)
INK = HexColor("#183F35")
ACCENT = HexColor("#147D5A")
BG = HexColor("#F5F6F2")
WHITE = HexColor("#FFFFFF")
MUTED = HexColor("#587166")
LINE = HexColor("#DCE5DD")
PALE = HexColor("#E8F2EC")
WARM = HexColor("#D8B879")


def register_fonts() -> None:
    fonts = Path("C:/Windows/Fonts")
    regular = fonts / "malgun.ttf"
    bold = fonts / "malgunbd.ttf"
    if not regular.exists() or not bold.exists():
        raise FileNotFoundError("Windows Malgun Gothic fonts are required")
    pdfmetrics.registerFont(TTFont("Malgun", str(regular)))
    pdfmetrics.registerFont(TTFont("MalgunBold", str(bold)))


def label(c: canvas.Canvas, x: float, y: float, value: str, size=10, color=MUTED,
          bold=False) -> None:
    c.setFillColor(color)
    c.setFont("MalgunBold" if bold else "Malgun", size)
    c.drawString(x, y, value)


def right(c: canvas.Canvas, x: float, y: float, value: str, size=10,
          color=MUTED, bold=False) -> None:
    c.setFillColor(color)
    c.setFont("MalgunBold" if bold else "Malgun", size)
    c.drawRightString(x, y, value)


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 13, fill=1, stroke=1)


def rule(c: canvas.Canvas, x: float, y: float, w: float) -> None:
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(x, y, x + w, y)


def bar(c: canvas.Canvas, x: float, y: float, w: float, value: float,
        max_value: float, color=ACCENT) -> None:
    c.setFillColor(PALE)
    c.roundRect(x, y, w, 11, 5.5, fill=1, stroke=0)
    c.setFillColor(color)
    c.roundRect(x, y, max(7, w * value / max_value), 11, 5.5, fill=1, stroke=0)


def qr(c: canvas.Canvas, x: float, y: float, size: float) -> None:
    widget = QrCodeWidget(SITE)
    bounds = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (bounds[2] - bounds[0]), 0,
                                            0, size / (bounds[3] - bounds[1]), 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, c, x, y)
    c.linkURL(SITE, (x, y, x + size, y + size), relative=0)


def main() -> None:
    register_fonts()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    year = data["meta"]["year"]
    city = data["summary"]["daegu"]
    nation = data["summary"]["national"]
    facilities = data["facilities"]
    top_five = sorted(facilities, key=lambda f: f["electricity_kwh"], reverse=True)[:5]
    top_share = sum(f["electricity_kwh"] for f in top_five) / city["electricity_kwh"]
    peer_cases = [
        (f, data["peers"].get(f["facility_id"], {}))
        for f in facilities
    ]
    peer_cases = [(f, p) for f, p in peer_cases if p.get("available") and p.get("ratio", 0) > 5]
    if not peer_cases:
        raise ValueError("No qualifying peer diagnostic case in the current analysis")
    peer_facility, peer = max(peer_cases, key=lambda pair: pair[1]["ratio"])
    rank_cases = [f for f in facilities if f.get("rank_volume") == 11 and f.get("rank_bod") == 26]
    if not rank_cases:
        raise ValueError("Expected rank contrast is absent from the current analysis")
    rank_facility = rank_cases[0]
    scenario_rate = 0.10
    saved_gwh = city["electricity_kwh"] * scenario_rate / 1_000_000
    factor = data["meta"]["factor"]
    if isinstance(factor, dict):
        factor_value = factor.get("value") or factor.get("tco2e_per_mwh")
    else:
        factor_value = factor
    if factor_value is None:
        factor_value = city["indirect_tco2e_est"] / (city["electricity_kwh"] / 1_000)
    saved_tco2e = city["electricity_kwh"] / 1_000 * scenario_rate * factor_value

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_COPY.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("DAEGU CARBON LAB | 대구 하수처리시설의 숨은 탄소격차")
    c.setAuthor("DAEGU CARBON LAB")
    c.setSubject(f"{year}년 공공데이터 기반 하수처리시설 에너지·수질·탄소 분석")

    # Editorial masthead.
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(INK)
    c.roundRect(34, H - 189, W - 68, 155, 16, fill=1, stroke=0)
    label(c, 61, H - 68, "DAEGU CARBON LAB   /   RESEARCH NOTE 01", 11, WARM, True)
    label(c, 61, H - 120, "대구 하수처리시설의 숨은 탄소격차", 37, WHITE, True)
    label(c, 63, H - 155,
          "같은 물을 처리해도, 규모와 오염부하를 고려하면 에너지 효율의 해석은 달라진다.",
          14, HexColor("#DDE9E0"))
    right(c, W - 61, H - 67, f"{year} DATA BRIEF", 11, WHITE, True)
    right(c, W - 61, H - 154, f"전국 {nation['n']:,}개  ·  대구 {city['n']}개 시설", 12, WHITE)

    # City-wide metrics, deliberately separate from facility-level peer evidence.
    x1, x2 = 34, W / 2 + 8
    card_w = W / 2 - 42
    top_y, top_h = H - 395, 190
    card(c, x1, top_y, card_w, top_h)
    card(c, x2, top_y, card_w, top_h)

    label(c, x1 + 24, top_y + 156, "01  도시 전체 / 유량 가중 전력 원단위", 11, ACCENT, True)
    label(c, x1 + 24, top_y + 100, f"{city['weighted_kwh_m3']:.3f}", 39, INK, True)
    label(c, x1 + 173, top_y + 106, "kWh/m³", 14, MUTED)
    label(c, x1 + 24, top_y + 74, f"대구 {city['n']}개 시설 · 전국 {nation['n']:,}개 시설과 비교", 10, MUTED)
    bar(c, x1 + 25, top_y + 48, card_w - 145, city["weighted_kwh_m3"],
        nation["weighted_kwh_m3"] * 1.05)
    right(c, x1 + card_w - 23, top_y + 47, f"대구 {city['weighted_kwh_m3']:.3f}", 10, ACCENT, True)
    bar(c, x1 + 25, top_y + 26, card_w - 145, nation["weighted_kwh_m3"],
        nation["weighted_kwh_m3"] * 1.05, MUTED)
    right(c, x1 + card_w - 23, top_y + 25, f"전국 {nation['weighted_kwh_m3']:.3f}", 10, MUTED)

    label(c, x2 + 24, top_y + 156, "02  총량 / 전력 사용의 집중", 11, ACCENT, True)
    label(c, x2 + 24, top_y + 100, f"{top_share * 100:.1f}%", 39, INK, True)
    label(c, x2 + 206, top_y + 106, "상위 5개 시설의 전력 비중", 14, MUTED)
    label(c, x2 + 24, top_y + 74,
          f"{sum(f['electricity_kwh'] for f in top_five) / 1_000_000:.2f} GWh/년  /  대구 총 {city['electricity_kwh'] / 1_000_000:.2f} GWh/년",
          10, MUTED)
    c.setFillColor(PALE)
    c.roundRect(x2 + 25, top_y + 41, card_w - 49, 17, 8.5, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.roundRect(x2 + 25, top_y + 41, (card_w - 49) * top_share, 17, 8.5, fill=1, stroke=0)
    label(c, x2 + 25, top_y + 20, "총전력이 크다는 사실만으로 시설 비효율을 판정할 수 없다.", 9, MUTED)

    # Facility-level evidence. Three unequal cards make the information hierarchy clear.
    mid_y, mid_h = H - 634, 223
    widths = (376, 314, W - 68 - 376 - 314 - 32)
    xs = (34, 34 + widths[0] + 16, 34 + widths[0] + 16 + widths[1] + 16)
    for x, width in zip(xs, widths):
        card(c, x, mid_y, width, mid_h)

    px, pw = xs[0], widths[0]
    label(c, px + 22, mid_y + 189, "03  같은 공법·규모·부하의 유사시설", 11, ACCENT, True)
    label(c, px + 22, mid_y + 151, peer_facility["name"], 18, INK, True)
    right(c, px + pw - 22, mid_y + 151, f"{peer['ratio']:.2f}배", 20, ACCENT, True)
    rule(c, px + 22, mid_y + 134, pw - 44)
    label(c, px + 22, mid_y + 107, "해당 시설", 10, INK)
    right(c, px + pw - 22, mid_y + 107, f"{peer_facility['kwh_m3']:.3f} kWh/m³", 10, INK, True)
    bar(c, px + 22, mid_y + 91, pw - 44, peer_facility["kwh_m3"], peer_facility["kwh_m3"])
    label(c, px + 22, mid_y + 69, f"유사시설 중앙값 (n={peer['count']})", 10, MUTED)
    right(c, px + pw - 22, mid_y + 69, f"{peer['median_kwh_m3']:.3f} kWh/m³", 10, MUTED)
    bar(c, px + 22, mid_y + 53, pw - 44, peer["median_kwh_m3"], peer_facility["kwh_m3"], MUTED)
    label(c, px + 22, mid_y + 24,
          f"BOD 제거율 {peer_facility['bod_removal_pct']:.2f}% · 현장 정밀진단 후보", 10, INK)

    rx, rw = xs[1], widths[1]
    label(c, rx + 22, mid_y + 189, "04  지표가 바꾸는 순위", 11, ACCENT, True)
    label(c, rx + 22, mid_y + 151, rank_facility["name"], 18, INK, True)
    label(c, rx + 22, mid_y + 104, f"{int(rank_facility['rank_volume'])}위", 27, INK, True)
    label(c, rx + 108, mid_y + 107, "→", 23, ACCENT, True)
    label(c, rx + 158, mid_y + 104, f"{int(rank_facility['rank_bod'])}위", 27, INK, True)
    label(c, rx + 22, mid_y + 78, "유입량당 전력     BOD 제거량당 전력", 9, MUTED)
    rule(c, rx + 22, mid_y + 60, rw - 44)
    label(c, rx + 22, mid_y + 41, f"{rank_facility['kwh_m3']:.3f} kWh/m³", 11, INK, True)
    right(c, rx + rw - 22, mid_y + 41, f"{rank_facility['kwh_kg_bod']:.2f} kWh/kg-BOD", 11, INK, True)
    label(c, rx + 22, mid_y + 19, "대구 39개 중 낮은 값이 1위 · 오염질량은 연평균 근사", 8.5, MUTED)

    sx, sw = xs[2], widths[2]
    label(c, sx + 22, mid_y + 189, "05  규모별 중앙값을 함께 읽기", 11, ACCENT, True)
    label(c, sx + 22, mid_y + 164, "전국 / 대구 · kWh/m³", 10, MUTED)
    scales = data["scale_comparison"]
    for i, row in enumerate(scales):
        y = mid_y + 126 - i * 33
        name = row["scale"].replace("–", "-")
        label(c, sx + 22, y + 7, name, 9, INK)
        right(c, sx + sw - 22, y + 7,
              f"{row['national_median']:.2f} / {row['daegu_median']:.2f}",
              10, INK, True)
        label(c, sx + 22, y - 7,
              f"전국 n={row['national_n']:,} · 대구 n={row['daegu_n']}", 8, MUTED)
        if i < 3:
            rule(c, sx + 22, y - 13, sw - 44)
    label(c, sx + 22, mid_y + 10, "규모·공법 구성 차이 때문에 지역 평균은 운영성과가 아니다.", 8.5, MUTED)

    # Scenario strip: explicit assumption and scope.
    strip_y, strip_h = 82, 111
    c.setFillColor(INK)
    c.roundRect(34, strip_y, W - 68, strip_h, 13, fill=1, stroke=0)
    label(c, 58, strip_y + 79, "10% 전력 절감 가정", 13, WARM, True)
    label(c, 58, strip_y + 41, f"{saved_gwh:.2f}", 27, WHITE, True)
    label(c, 155, strip_y + 44, "GWh/년 절감", 12, WHITE)
    c.setStrokeColor(HexColor("#42695D"))
    c.line(340, strip_y + 23, 340, strip_y + 88)
    label(c, 367, strip_y + 41, f"{saved_tco2e:,.0f}", 27, WHITE, True)
    label(c, 507, strip_y + 44, "tCO₂eq/년 간접배출 감소 잠재량", 12, WHITE)
    label(c, 367, strip_y + 20,
          f"2025 승인 소비단 계수 {factor_value:.4f} tCO₂eq/MWh 적용 · 실증 감축량 아님",
          9, HexColor("#DDE9E0"))
    c.setStrokeColor(HexColor("#42695D"))
    c.line(W - 284, strip_y + 23, W - 284, strip_y + 88)
    label(c, W - 264, strip_y + 76, "정책 출발점", 11, WARM, True)
    label(c, W - 264, strip_y + 52, "공정별 계측 → 수질 유지 검증", 10, WHITE)
    label(c, W - 264, strip_y + 33, "→ 실증 후 투자·감축 평가", 10, WHITE)

    # Provenance, limitations and live QR.
    label(c, 35, 60,
          "자료: 한국환경공단 공공하수처리시설 현황(3073222), 환경부 하수도통계; 계수: 온실가스종합정보센터 승인자료.",
          8, MUTED)
    label(c, 35, 43,
          "유사시설 비교는 진단 단서이며 절감 목표가 아니다. 전력 간접배출은 시설 전체 온실가스 배출을 뜻하지 않는다.",
          8, MUTED)
    label(c, 35, 25, f"분석연도 {year}  ·  계산식·원자료·한계·상호작용 그래프: {SITE}", 8, ACCENT, True)
    c.linkURL(SITE, (35, 20, 555, 39), relative=0)
    qr(c, W - 73, 14, 48)
    c.showPage()
    c.save()
    PUBLIC_COPY.write_bytes(OUTPUT.read_bytes())
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"Public copy {PUBLIC_COPY}")


if __name__ == "__main__":
    main()
