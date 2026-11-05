"""Shared definitions and storage for the 슈퍼알바 촬영 일정·USP 앱.

Storage: Google Sheets when `gcp_service_account` and `sheet_id` are in
st.secrets, otherwise a local CSV (for testing on your own PC only —
Streamlit Cloud wipes local files on every restart).
"""
from __future__ import annotations

import csv
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

KST = timezone(timedelta(hours=9))

# Candidate shooting dates (2026-11)
CANDIDATES = [(16, "월"), (17, "화"), (19, "목"), (23, "월"), (24, "화")]

# (key, label, kind, section, placeholder, full_width)
FIELDS = [
    ("b_name", "브랜드명", "text", "brand", "", False),
    ("b_launch", "브랜드 론칭일(1호점)", "text", "brand", "예: 2020.03", False),
    ("b_stores", "현재 매장 수", "text", "brand", "", False),
    ("b_bi", "BI 및 브랜드 소개", "area", "brand", "", False),
    ("b_signature", "시그니처 메뉴 (노출을 원하는 메뉴)", "area", "brand", "", False),
    ("b_cooktime", "평균 조리 시간 (노출을 원하는 메뉴)", "text", "brand", "예: 약 5분", False),
    ("b_newcycle", "신메뉴 출시 주기", "text", "brand", "예: 분기 1회", False),
    ("b_sales", "주요 영업 형태 (홀/배달/포장)", "multi", "brand", "", True),
    ("b_ratio", "전체적인 매출 비율 (홀/배달/포장)", "text", "brand", "예: 홀 00% / 배달 00% / 포장 00%", False),
    ("b_logistics", "물류 주기", "text", "brand", "예: 주 1회", False),
    ("b_pack", "재고 및 조리 과정 (원팩 및 배송 형태)", "area", "brand", "", True),
    ("b_system", "차별화된 조리 시스템", "area", "brand", "", True),
    ("b_super", "슈퍼바이저 관리 포인트 (배달 플랫폼, 순수익 계산 등)", "area", "brand", "", True),
    ("b_cost", "창업 비용", "text", "brand", "", False),
    ("b_benefit", "창업 혜택", "text", "brand", "", False),
    ("o_store", "촬영 매장명", "text", "owner", "", False),
    ("o_name", "성함", "text", "owner", "", False),
    ("o_gender", "성별/나이", "text", "owner", "", False),
    ("o_start", "창업 시기", "text", "owner", "예: 2025.06", False),
    ("o_type", "업종변경 / 첫창업 여부", "radio", "owner", "", True),
    ("o_area", "상권 특성", "text", "owner", "", False),
    ("o_sales", "최근 3개월 매출(8~10개월) - 수익률", "text", "owner", "", False),
    ("o_staff", "매장 운영 수 (인건비)", "text", "owner", "", False),
    ("o_peak", "피크 시간", "text", "owner", "예: 점심 11:30~13:30", False),
    ("o_story", "점주님의 사연", "area", "owner", "", True),
]
SALES_OPTIONS = ["홀", "배달", "포장"]
TYPE_OPTIONS = ["첫창업", "업종변경"]

STATUS = {"new": "신규", "review": "검토중", "confirmed": "촬영 확정", "hold": "보류"}

# Sheet columns: (key, header shown in Google Sheets)
COLUMNS: list[tuple[str, str]] = [
    ("id", "접수번호"),
    ("submitted_at", "최초 제출"),
    ("updated_at", "최근 수정"),
    ("status", "진행 상태"),
    ("memo", "내부 메모"),
]
for _d, _w in CANDIDATES:
    COLUMNS += [
        (f"d{_d}_start", f"11/{_d}({_w}) 시작"),
        (f"d{_d}_end", f"11/{_d}({_w}) 종료"),
        (f"d{_d}_note", f"11/{_d}({_w}) 비고"),
    ]
COLUMNS += [(k, label) for k, label, *_ in FIELDS]
KEYS = [k for k, _ in COLUMNS]
HEADERS = [h for _, h in COLUMNS]
SHEET_NAME = "responses"
LOCAL_CSV = Path(__file__).parent / "data" / "responses.csv"


def now_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")


def new_id() -> str:
    # Short, hard-to-guess code the respondent keeps to edit later
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "SA-" + "".join(secrets.choice(alphabet) for _ in range(6))


def using_sheets() -> bool:
    try:
        return "gcp_service_account" in st.secrets and "sheet_id" in st.secrets
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _worksheet():
    import gspread

    gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    sh = gc.open_by_key(st.secrets["sheet_id"])
    try:
        ws = sh.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=200, cols=len(HEADERS))
    if ws.row_values(1) != HEADERS:
        ws.update(range_name="A1", values=[HEADERS])
    return ws


def _rows_to_dicts(values: list[list[str]]) -> list[dict]:
    out = []
    for row in values[1:]:
        if not any(row):
            continue
        row = list(row) + [""] * (len(KEYS) - len(row))
        out.append(dict(zip(KEYS, row)))
    return out


def load_all() -> list[dict]:
    if using_sheets():
        return _rows_to_dicts(_worksheet().get_all_values())
    if not LOCAL_CSV.exists():
        return []
    with LOCAL_CSV.open(encoding="utf-8-sig", newline="") as f:
        return _rows_to_dicts(list(csv.reader(f)))


def _write_local(rows: list[dict]) -> None:
    LOCAL_CSV.parent.mkdir(exist_ok=True)
    with LOCAL_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        for r in rows:
            w.writerow([r.get(k, "") for k in KEYS])


def get_one(rid: str) -> dict | None:
    rid = rid.strip().upper()
    for r in load_all():
        if r["id"] == rid:
            return r
    return None


def upsert(record: dict) -> None:
    """Insert or replace a response by its id (keeps status/memo unless given)."""
    values = [str(record.get(k, "")) for k in KEYS]
    if using_sheets():
        ws = _worksheet()
        cell = ws.find(record["id"], in_column=1)
        if cell:
            ws.update(range_name=f"A{cell.row}", values=[values])
        else:
            ws.append_row(values, value_input_option="RAW")
        return
    rows = load_all()
    for i, r in enumerate(rows):
        if r["id"] == record["id"]:
            rows[i] = {k: record.get(k, "") for k in KEYS}
            break
    else:
        rows.append({k: record.get(k, "") for k in KEYS})
    _write_local(rows)


def update_fields(rid: str, patch: dict) -> None:
    current = get_one(rid)
    if not current:
        raise KeyError(rid)
    current.update(patch)
    current["updated_at"] = current.get("updated_at") or now_kst()
    upsert(current)


def delete(rid: str) -> None:
    if using_sheets():
        ws = _worksheet()
        cell = ws.find(rid, in_column=1)
        if cell:
            ws.delete_rows(cell.row)
        return
    _write_local([r for r in load_all() if r["id"] != rid])


def to_text(r: dict) -> str:
    lines = ["[슈퍼알바 촬영 일정 확인]"]
    for d, w in CANDIDATES:
        s, e, n = r.get(f"d{d}_start"), r.get(f"d{d}_end"), r.get(f"d{d}_note")
        if s and e:
            lines.append(f"- 11월 {d}일({w}) 가능 {s} ~ {e}" + (f" / {n}" if n else ""))
        else:
            lines.append(f"- 11월 {d}일({w}) 미선택")
    lines += ["", "[광고주 USP 확인]", "1) 브랜드 창업 포인트"]
    for k, label, _, sec, *_ in FIELDS:
        if sec == "brand":
            lines.append(f"- {label}: {r.get(k) or '-'}")
    lines += ["", "2) 촬영 매장 점주님(매니저님) 정보"]
    for k, label, _, sec, *_ in FIELDS:
        if sec == "owner":
            lines.append(f"- {label}: {r.get(k) or '-'}")
    return "\n".join(lines)


BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html, body, [class*="css"], .stMarkdown, input, textarea, button { font-family: "Noto Sans KR", "Malgun Gothic", sans-serif; }
.sa-hero { background:#FFB202; border:3px solid #1E1B16; border-radius:18px; padding:22px 22px 18px; margin-bottom:18px; box-shadow:0 5px 0 #1E1B16; }
.sa-logo { font-family:"Black Han Sans",sans-serif; font-size:44px; line-height:1; color:#E5202A;
  text-shadow:3px 3px 0 #1E1B16,-1px -1px 0 #1E1B16,1px -1px 0 #1E1B16,-1px 1px 0 #1E1B16,1px 1px 0 #1E1B16; }
.sa-logo span { color:#fff; }
.sa-hero h1 { font-family:"Black Han Sans",sans-serif; font-weight:400; font-size:26px; margin:12px 0 6px; color:#1E1B16; padding:0; }
.sa-hero p { margin:0; color:#1E1B16; }
.sa-sec { font-family:"Black Han Sans",sans-serif; font-size:24px; color:#1E1B16; margin:8px 0 2px; }
.sa-sec b { color:#E5202A; font-weight:400; margin-right:8px; }
.sa-tag { display:inline-block; background:#FFB202; border:2px solid #1E1B16; border-radius:999px; padding:2px 14px;
  font-family:"Black Han Sans",sans-serif; font-size:16px; margin:14px 0 6px; color:#1E1B16; }
.sa-date { font-family:"Black Han Sans",sans-serif; font-size:19px; }
</style>
"""


def hero(title: str, body: str) -> None:
    st.markdown(BRAND_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="sa-hero"><div class="sa-logo"><span>슈퍼</span>알바</div>'
        f"<h1>{title}</h1><p>{body}</p></div>",
        unsafe_allow_html=True,
    )
