"""슈퍼알바 응답 관리 — 관리자 전용 (비밀번호 보호)."""
from __future__ import annotations

import csv
import hmac
import io

import pandas as pd
import streamlit as st

import common as c

st.set_page_config(page_title="슈퍼알바 응답 관리", page_icon="🗂️", layout="wide")
c.hero("응답 관리", "광고주가 제출한 촬영 일정과 USP 답변을 확인하고, 진행 상태와 메모를 관리합니다.")

ss = st.session_state

# ---- 로그인 ----
try:
    PASSWORD = st.secrets.get("admin_password", "")
except Exception:
    PASSWORD = ""

if not PASSWORD:
    st.error("관리자 비밀번호가 설정되지 않았어요. secrets에 admin_password를 넣어주세요. (README 참고)")
    st.stop()

if not ss.get("admin_ok"):
    with st.form("login"):
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.form_submit_button("들어가기", type="primary"):
            if hmac.compare_digest(pw, PASSWORD):
                ss["admin_ok"] = True
                st.rerun()
            else:
                st.error("비밀번호가 맞지 않아요.")
    st.stop()

# ---- 데이터 ----
top = st.columns([1, 1, 4])
if top[0].button("새로고침", use_container_width=True):
    st.rerun()
if top[1].button("로그아웃", use_container_width=True):
    ss["admin_ok"] = False
    st.rerun()

try:
    rows = c.load_all()
except Exception as e:  # noqa: BLE001
    st.error(f"응답을 불러오지 못했어요. 구글 시트 연결 설정을 확인해주세요. ({type(e).__name__})")
    st.stop()

rows.sort(key=lambda r: r.get("updated_at") or r.get("submitted_at") or "", reverse=True)
if not c.using_sheets():
    st.info("테스트 모드: 이 PC의 파일(data/responses.csv)을 보고 있어요.", icon="🧪")

# ---- 요약 ----
counts = {k: 0 for k in c.STATUS}
for r in rows:
    counts[r.get("status") or "new"] = counts.get(r.get("status") or "new", 0) + 1
m = st.columns(len(c.STATUS) + 1)
m[0].metric("전체 응답", len(rows))
for i, (k, label) in enumerate(c.STATUS.items(), start=1):
    m[i].metric(label, counts.get(k, 0))

st.markdown('<span class="sa-tag">날짜별 촬영 가능 응답 수</span>', unsafe_allow_html=True)
demand = pd.DataFrame(
    {
        "날짜": [f"11/{d}({w})" for d, w in c.CANDIDATES],
        "응답 수": [sum(1 for r in rows if r.get(f"d{d}_start")) for d, _ in c.CANDIDATES],
    }
)
st.bar_chart(demand, x="날짜", y="응답 수", color="#E5202A", horizontal=True, height=220)

# ---- 내려받기 ----
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(c.HEADERS)
for r in rows:
    w.writerow([c.STATUS.get(r.get(k), r.get(k, "")) if k == "status" else r.get(k, "") for k in c.KEYS])
st.download_button(
    "CSV 내려받기 (엑셀용)",
    data=buf.getvalue().encode("utf-8-sig"),
    file_name=f"슈퍼알바_응답_{c.now_kst()[:10]}.csv",
    mime="text/csv",
    disabled=not rows,
)

# ---- 목록 ----
st.markdown('<span class="sa-tag">제출된 응답</span>', unsafe_allow_html=True)
labels = {"all": f"전체 {len(rows)}"} | {k: f"{v} {counts.get(k, 0)}" for k, v in c.STATUS.items()}
flt = st.segmented_control("상태로 거르기", list(labels), format_func=labels.get, default="all", key="flt") or "all"
shown = [r for r in rows if flt == "all" or (r.get("status") or "new") == flt]

if not rows:
    st.info("아직 제출된 응답이 없어요. 광고주가 제출하기를 누르면 여기에 나타납니다.")
elif not shown:
    st.caption("이 상태의 응답이 없어요.")

for r in shown:
    rid = r["id"]
    st_key = r.get("status") or "new"
    dates = [f"11/{d}({w}) {r[f'd{d}_start']}~{r[f'd{d}_end']}" for d, w in c.CANDIDATES if r.get(f"d{d}_start")]
    title = f"[{c.STATUS.get(st_key, '신규')}] {r.get('b_name') or '(브랜드명 없음)'} · {r.get('o_store') or '-'} · {r.get('updated_at') or r.get('submitted_at')}"
    with st.expander(title):
        st.caption(f"접수번호 {rid} · 가능 일정: " + (", ".join(dates) if dates else "없음"))

        a, b = st.columns([1, 2])
        with a:
            new_status = st.selectbox(
                "진행 상태", list(c.STATUS), index=list(c.STATUS).index(st_key) if st_key in c.STATUS else 0,
                format_func=c.STATUS.get, key=f"st_{rid}",
            )
        with b:
            memo = st.text_area("내부 메모 (광고주에게 보이지 않음)", value=r.get("memo", ""), key=f"memo_{rid}", height=80)
        if st.button("상태·메모 저장", key=f"save_{rid}", type="primary"):
            try:
                c.update_fields(rid, {"status": new_status, "memo": memo})
                st.toast("저장했어요.")
                st.rerun()
            except Exception:
                st.error("저장하지 못했어요. 새로고침 후 다시 시도해주세요.")

        t1, t2, t3 = st.tabs(["촬영 일정", "브랜드 창업 포인트", "점주님 정보"])
        with t1:
            st.table(pd.DataFrame(
                [{"날짜": f"11월 {d}일 ({w})",
                  "가능 시간": f"{r[f'd{d}_start']} ~ {r[f'd{d}_end']}" if r.get(f"d{d}_start") else "미선택",
                  "비고": r.get(f"d{d}_note", "")} for d, w in c.CANDIDATES]
            ).set_index("날짜"))
        for tab, sec in ((t2, "brand"), (t3, "owner")):
            with tab:
                st.table(pd.DataFrame(
                    [{"항목": label, "답변": r.get(k) or "-"} for k, label, _, s, *_ in c.FIELDS if s == sec]
                ).set_index("항목"))

        st.code(c.to_text(r), language=None)

        confirm = st.checkbox("이 응답을 영구 삭제합니다", key=f"delok_{rid}")
        if st.button("삭제", key=f"del_{rid}", disabled=not confirm):
            try:
                c.delete(rid)
                st.toast("삭제했어요.")
                st.rerun()
            except Exception:
                st.error("삭제하지 못했어요. 잠시 뒤 다시 시도해주세요.")
