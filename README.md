# 슈퍼알바 촬영 일정·USP 확인

광고주가 로그인 없이 링크만으로 촬영 가능 일정과 USP를 작성·제출하고,
담당자는 **응답 관리** 페이지(비밀번호 보호)에서 상태·메모·삭제·CSV 다운로드로 관리하는 Streamlit 앱입니다.
응답은 구글 시트에 쌓이므로 시트에서 직접 봐도 됩니다.

| 화면 | 파일 | 누가 |
|---|---|---|
| 작성 화면 | `app.py` | 광고주 (링크만 있으면 누구나) |
| 응답 관리 | `pages/1_응답_관리.py` | 담당자 (`admin_password` 필요) |

광고주는 제출 후 받는 **접수번호**(예: `SA-7K3QWX`)로 답변을 다시 불러와 수정할 수 있습니다.

---

## 배포 순서 (처음 한 번)

### 1. 구글 시트 + 서비스 계정 만들기 (응답 저장소)

1. 구글 드라이브에서 빈 스프레드시트를 하나 만듭니다. 주소의 `/d/` 와 `/edit` 사이 문자열이 **sheet_id** 입니다.
2. https://console.cloud.google.com 에서 프로젝트를 만들고
   **API 및 서비스 → 라이브러리**에서 `Google Sheets API`, `Google Drive API` 를 사용 설정합니다.
3. **IAM 및 관리자 → 서비스 계정 → 서비스 계정 만들기** → 만든 계정의 **키 → 키 추가 → JSON** 으로 키 파일을 받습니다.
4. 1번 시트의 **공유** 버튼에서 키 파일 안의 `client_email` 주소를 **편집자**로 추가합니다.

> 키 파일(JSON)은 비밀번호와 같습니다. 깃허브에 올리거나 메신저로 보내지 마세요. (`.gitignore` 가 `*.json` 을 막아둡니다.)

### 2. 깃허브에 올리기

1. https://github.com/new 에서 저장소를 만듭니다. (이름 예: `superalba-form`, **Private** 권장, README 추가 체크 해제)
2. 이 폴더에서:

```bash
git remote add origin https://github.com/<아이디>/superalba-form.git
git push -u origin main
```

처음 push 할 때 깃허브 로그인 창이 뜨면 로그인합니다.

### 3. Streamlit Community Cloud 에 배포

1. https://share.streamlit.io 에 깃허브 계정으로 로그인 → **Create app → Deploy a public app from GitHub**.
2. Repository: 위 저장소, Branch: `main`, Main file path: `app.py`.
3. **Advanced settings → Secrets** 칸에 `.streamlit/secrets.toml.example` 내용을 붙여넣고 값을 채웁니다.
   - `admin_password`: 응답 관리 페이지 비밀번호
   - `sheet_id`: 1-1의 값
   - `[gcp_service_account]`: 1-3 JSON 키의 각 값을 그대로 옮김 (`private_key` 의 `\n` 은 그대로 둡니다)
4. **Deploy** → 몇 분 뒤 `https://<이름>.streamlit.app` 주소가 생깁니다. 이 주소를 광고주에게 보내면 됩니다.

이후에는 깃허브에 push 하면 Streamlit 앱이 자동으로 새 버전으로 바뀝니다.

---

## 내 PC에서 실행해 보기

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

`.streamlit/secrets.toml` 이 없거나 구글 시트 설정이 없으면 **테스트 모드**로 `data/responses.csv` 에 저장합니다.
응답 관리 페이지를 열려면 최소한 `admin_password` 한 줄은 `.streamlit/secrets.toml` 에 있어야 합니다.

## 일정·항목 바꾸기

`common.py` 의 `CANDIDATES`(촬영 가능 날짜)와 `FIELDS`(USP 질문)를 고치면 작성 화면, 관리 화면, 시트 열이 함께 바뀝니다.
항목을 바꾼 뒤에는 시트 첫 줄(머리글)이 자동으로 새 순서로 덮어써지므로, 이미 응답이 쌓인 시트라면 새 시트를 쓰는 편이 안전합니다.
