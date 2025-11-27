# Excel to Notion Streamlit 앱

업로드한 엑셀 파일을 Notion 데이터베이스에 저장하는 간단한 Streamlit 앱입니다.

## 실행 방법
1. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```
2. 환경 변수 또는 `.streamlit/secrets.toml`에 아래 값을 설정합니다.
   - `NOTION_TOKEN`: Notion 통합(Integration) 시크릿 토큰
   - `NOTION_DATABASE_ID`: 데이터를 추가할 데이터베이스 ID

3. 앱을 실행합니다.
   ```bash
   streamlit run app.py
   ```

## 사용 방법
- xls/xlsx 파일을 업로드하면 상단에 미리보기 데이터가 표시됩니다.
- 사이드바에서 Notion 자격 증명이 올바르게 설정되었는지 확인하세요.
- "Notion으로 보내기" 버튼을 클릭하면 각 행이 지정된 데이터베이스에 추가됩니다.

## 주의사항
- 데이터베이스의 컬럼 이름이 엑셀 컬럼과 일치해야 합니다.
- Title 속성이 존재해야 하며, 엑셀에 동일한 이름의 컬럼이 없을 경우 첫 번째 컬럼 값으로 대체됩니다.
