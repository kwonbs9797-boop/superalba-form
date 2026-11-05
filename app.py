"""슈퍼알바 촬영 일정·USP 확인 — 광고주 작성 화면."""
from __future__ import annotations

from datetime import time

import streamlit as st

import common as c

st.set_page_config(page_title="슈퍼알바 촬영 일정·USP 확인", page_icon="📅", layout="centered")

c.hero(
    "촬영 일정 확인 및 광고주 USP 확인",
    "촬영 가능한 날짜와 시간을 체크하고, 브랜드와 매장 정보를 작성한 뒤 <b>제출하기</b>를 눌러주세요.",
)

ss = st.session_state


def _init_defaults() -> None:
    for d, _ in c.CANDIDATES:
        ss.setdefault(f"f_d{d}_on", False)
        ss.setdefault(f"f_d{d}_start", None)
        ss.setdefault(f"f_d{d}_end", None)
        ss.setdefault(f"f_d{d}_note", "")
    for k, _, kind, *_ in c.FIELDS:
        ss.setdefault(f"f_{k}", [] if kind == "multi" else (None if kind == "radio" else ""))


def _parse_time(v: str) -> time | None:
    try:
        h, m = v.split(":")
        return time(int(h), int(m))
    except Exception:
        return None


def _load_into_form(r: dict) -> None:
    for d, _ in c.CANDIDATES:
        s, e = _parse_time(r.get(f"d{d}_start", "")), _parse_time(r.get(f"d{d}_end", ""))
        ss[f"f_d{d}_on"] = bool(s and e)
        ss[f"f_d{d}_start"] = s
        ss[f"f_d{d}_end"] = e
        ss[f"f_d{d}_note"] = r.get(f"d{d}_note", "")
    for k, _, kind, *_ in c.FIELDS:
        v = r.get(k, "")
        if kind == "multi":
            ss[f"f_{k}"] = [x.strip() for x in v.split(",") if x.strip() in c.SALES_OPTIONS]
        elif kind == "radio":
            ss[f"f_{k}"] = v if v in c.TYPE_OPTIONS else None
        else:
            ss[f"f_{k}"] = v
    ss["rid"] = r["id"]
    ss["prev"] = r


_init_defaults()

# ---- 이전 제출 불러오기 ----
with st.expander("이미 제출했나요? 접수번호로 불러와서 수정하기"):
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    code = col1.text_input("접수번호", placeholder="예: SA-7K3QWX", key="load_code")
    if col2.button("불러오기", use_container_width=True):
        found = c.get_one(code) if code.strip() else None
        if found:
            _load_into_form(found)
            st.rerun()
        else:
            st.error("그 접수번호로 제출된 답변이 없어요. 번호를 다시 확인해주세요.")
    if ss.get("rid"):
        st.success(f"접수번호 {ss['rid']} 답변을 불러왔어요. 고친 뒤 제출하면 최신 답변으로 바뀝니다.")

if not c.using_sheets():
    st.info("테스트 모드: 구글 시트가 연결되지 않아 이 PC의 파일에 저장됩니다.", icon="🧪")

with st.form("answer", clear_on_submit=False, border=False):
    # ---- 01 일정 ----
    st.markdown('<div class="sa-sec"><b>01</b>일정 확인</div>', unsafe_allow_html=True)
    st.caption("2026년 11월 가능 일정 중 촬영 가능한 날짜를 체크하고, 시작·종료 시간을 입력해주세요.")
    for d, w in c.CANDIDATES:
        with st.container(border=True):
            st.checkbox(f"11월 {d}일 ({w})", key=f"f_d{d}_on")
            a, b = st.columns(2)
            a.time_input("시작 시간", key=f"f_d{d}_start", step=1800)
            b.time_input("종료 시간", key=f"f_d{d}_end", step=1800)
            st.text_input("비고 (선택)", key=f"f_d{d}_note", placeholder="이동 시간, 선호 사항 등")

    # ---- 02 USP ----
    st.markdown('<div class="sa-sec"><b>02</b>광고주 USP 확인</div>', unsafe_allow_html=True)
    for sec, tag in (("brand", "브랜드 창업 포인트"), ("owner", "촬영 매장 점주님(매니저님) 정보")):
        st.markdown(f'<span class="sa-tag">{tag}</span>', unsafe_allow_html=True)
        items = [f for f in c.FIELDS if f[3] == sec]
        cols = st.columns(2)
        i = 0
        for k, label, kind, _, ph, full in items:
            if full or kind == "area":
                target = st
            else:
                target = cols[i % 2]
                i += 1
            key = f"f_{k}"
            if kind == "text":
                target.text_input(label, key=key, placeholder=ph)
            elif kind == "area":
                target.text_area(label, key=key, placeholder=ph, height=100)
            elif kind == "multi":
                target.pills(label, c.SALES_OPTIONS, selection_mode="multi", key=key)
            elif kind == "radio":
                target.radio(label, c.TYPE_OPTIONS, key=key, horizontal=True)
            if full or kind == "area":
                cols = st.columns(2)
                i = 0

    st.divider()
    submitted = st.form_submit_button("제출하기", type="primary", use_container_width=True)

if submitted:
    errors = []
    record: dict = {}
    for d, w in c.CANDIDATES:
        s, e = ss[f"f_d{d}_start"], ss[f"f_d{d}_end"]
        if ss[f"f_d{d}_on"]:
            if not s or not e:
                errors.append(f"11월 {d}일({w}): 시작·종료 시간을 모두 입력해주세요.")
            elif e <= s:
                errors.append(f"11월 {d}일({w}): 종료 시간은 시작 시간보다 늦어야 해요.")
            else:
                record[f"d{d}_start"] = s.strftime("%H:%M")
                record[f"d{d}_end"] = e.strftime("%H:%M")
                record[f"d{d}_note"] = ss[f"f_d{d}_note"].strip()
    for k, _, kind, *_ in c.FIELDS:
        v = ss[f"f_{k}"]
        if kind == "multi":
            record[k] = ", ".join(v or [])
        else:
            record[k] = (v or "").strip()
    if not record["b_name"]:
        errors.append("브랜드명을 입력해주세요.")

    if errors:
        for msg in errors:
            st.error(msg)
    else:
        prev = ss.get("prev") or {}
        rid = ss.get("rid") or c.new_id()
        record.update(
            id=rid,
            submitted_at=prev.get("submitted_at") or c.now_kst(),
            updated_at=c.now_kst(),
            status=prev.get("status") or "new",
            memo=prev.get("memo", ""),
        )
        try:
            c.upsert(record)
        except Exception:
            st.error("제출하지 못했어요. 잠시 뒤 다시 눌러주세요. 계속 안 되면 아래 내용을 복사해 전달해주세요.")
            st.code(c.to_text(record), language=None)
        else:
            ss["rid"], ss["prev"] = rid, record
            st.success(
                f"제출했어요. 접수번호는 **{rid}** 입니다. 이 번호로 나중에 불러와서 수정할 수 있으니 꼭 적어두세요."
            )
            st.caption("제출한 내용 (오른쪽 위 아이콘으로 복사할 수 있어요)")
            st.code(c.to_text(record), language=None)
