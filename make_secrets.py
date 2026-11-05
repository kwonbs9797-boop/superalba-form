"""Streamlit Secrets 내용을 만들어 클립보드에 복사합니다.

사용법:  .venv\\Scripts\\python make_secrets.py  <서비스계정키.json 경로>
- 구글 시트 주소와 관리자 비밀번호를 물어봅니다.
- 결과를 .streamlit/secrets.toml 에 저장하고(깃에 안 올라감) 클립보드에 복사합니다.
- 그대로 Streamlit > Settings > Secrets 칸에 붙여넣으면 됩니다.
"""
from __future__ import annotations

import getpass
import json
import re
import subprocess
import sys
from pathlib import Path


def q(v) -> str:
    # JSON string escapes are valid TOML basic-string escapes
    return json.dumps(str(v), ensure_ascii=False)


def main() -> None:
    if len(sys.argv) >= 2:
        raw = sys.argv[1]
    else:
        raw = input("서비스 계정 키(.json) 파일을 이 창에 끌어다 놓고 Enter: ")
    key_path = Path(raw.strip().strip("'\"").lstrip("& ").strip("'\""))
    if not key_path.is_file():
        print(f"파일을 찾지 못했어요: {key_path}")
        sys.exit(1)
    key = json.loads(key_path.read_text(encoding="utf-8"))
    if key.get("type") != "service_account":
        print("서비스 계정 키(JSON)가 아닌 것 같아요. 다시 확인해주세요.")
        sys.exit(1)

    url = input("구글 시트 주소(브라우저 주소창 그대로): ").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    sheet_id = m.group(1) if m else url
    pw = getpass.getpass("관리자 비밀번호(입력해도 화면에 안 보입니다): ")
    if not pw:
        print("비밀번호가 비어 있어요.")
        sys.exit(1)

    lines = [f"admin_password = {q(pw)}", f"sheet_id = {q(sheet_id)}", "", "[gcp_service_account]"]
    lines += [f"{k} = {q(v)}" for k, v in key.items()]
    text = "\n".join(lines) + "\n"

    out = Path(__file__).parent / ".streamlit" / "secrets.toml"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    try:
        subprocess.run("clip", input=text.encode("utf-16le"), check=True, shell=True)
        copied = True
    except Exception:
        copied = False

    print()
    print(f"완료: {out} 에 저장했어요.")
    print("클립보드에 복사했어요. Streamlit Secrets 칸에 Ctrl+V 로 붙여넣으세요." if copied
          else "클립보드 복사는 실패했어요. 위 파일을 메모장으로 열어 내용을 복사하세요.")
    print(f"시트 공유 대상(편집자로 추가할 이메일): {key.get('client_email')}")


if __name__ == "__main__":
    main()
