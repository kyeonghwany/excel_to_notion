"""
Streamlit app to upload Excel files and push rows into a Notion database.
"""
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

NOTION_VERSION = "2022-06-28"


def get_secret(key: str) -> Optional[str]:
    """Fetch configuration from Streamlit secrets or environment variables."""
    if key in st.secrets:
        return str(st.secrets[key])
    return os.getenv(key)


def get_notion_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def fetch_database_properties(token: str, database_id: str) -> Dict[str, Any]:
    """Retrieve the database properties to map Excel columns to Notion fields."""
    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.get(url, headers=get_notion_headers(token), timeout=30)
    response.raise_for_status()
    database = response.json()
    return database.get("properties", {})


def resolve_title_property(properties: Dict[str, Any]) -> Optional[str]:
    for name, details in properties.items():
        if details.get("type") == "title":
            return name
    return None


def convert_value(value: Any, property_type: str) -> Optional[Any]:
    if pd.isna(value):
        return None

    if property_type in {"title", "rich_text"}:
        return [{"text": {"content": str(value)}}]

    if property_type == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    if property_type == "date":
        if isinstance(value, (datetime, pd.Timestamp)):
            return {"start": value.date().isoformat()}
        try:
            parsed = pd.to_datetime(value)
            return {"start": parsed.date().isoformat()}
        except (TypeError, ValueError):
            return None

    if property_type == "select":
        return {"name": str(value)}

    if property_type == "multi_select":
        options = [item.strip() for item in str(value).split(",") if item.strip()]
        return [{"name": option} for option in options]

    if property_type in {"email", "url", "phone_number"}:
        return str(value)

    return None


def build_notion_payload(row: pd.Series, properties: Dict[str, Any]) -> Dict[str, Any]:
    title_property = resolve_title_property(properties)
    payload: Dict[str, Any] = {}

    # Populate the title property first
    if title_property:
        if title_property in row:
            payload[title_property] = {
                "title": convert_value(row[title_property], "title") or [],
            }
        else:
            fallback_value = row.iloc[0] if len(row) else "Row"
            payload[title_property] = {
                "title": convert_value(fallback_value, "title") or [],
            }

    # Populate other properties when column names match
    for column, value in row.items():
        if column == title_property or column not in properties:
            continue
        property_type = properties[column].get("type")
        converted_value = convert_value(value, property_type)
        if converted_value is None:
            continue

        if property_type in {"title", "rich_text"}:
            payload[column] = {property_type: converted_value}
        elif property_type in {"number", "select", "multi_select", "email", "url", "phone_number"}:
            payload[column] = {property_type: converted_value}
        elif property_type == "date":
            payload[column] = {property_type: converted_value}

    return {"properties": payload}


def add_rows_to_notion(token: str, database_id: str, df: pd.DataFrame) -> List[str]:
    properties = fetch_database_properties(token, database_id)
    headers = get_notion_headers(token)
    endpoint = "https://api.notion.com/v1/pages"

    errors: List[str] = []
    for index, row in df.iterrows():
        payload = build_notion_payload(row, properties)
        payload["parent"] = {"database_id": database_id}

        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if response.status_code >= 400:
            message = response.text
            errors.append(f"Row {index + 1}: {message}")
    return errors


def render_credentials_section() -> Optional[Dict[str, str]]:
    st.sidebar.header("Notion 연결 설정")
    st.sidebar.write(
        "환경 변수 또는 Streamlit secrets에 NOTION_TOKEN과 NOTION_DATABASE_ID를 설정해주세요."
    )

    token = get_secret("NOTION_TOKEN")
    database_id = get_secret("NOTION_DATABASE_ID")

    if token and database_id:
        st.sidebar.success("Notion 자격 증명이 설정되었습니다.")
        return {"token": token, "database_id": database_id}

    st.sidebar.error("필요한 자격 증명이 설정되지 않았습니다.")
    return None


def main() -> None:
    st.set_page_config(page_title="Excel to Notion", page_icon="📒", layout="centered")
    st.title("📒 Excel → Notion 업로드")
    st.write(
        "엑셀 파일을 업로드하면 행 데이터를 지정된 Notion 데이터베이스로 전송합니다."
    )

    creds = render_credentials_section()

    uploaded = st.file_uploader("엑셀 파일을 업로드하세요", type=["xls", "xlsx"])
    if not uploaded:
        st.info(".xls 또는 .xlsx 파일을 선택해주세요.")
        return

    try:
        df = pd.read_excel(uploaded)
    except Exception as exc:  # pragma: no cover - user facing
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {exc}")
        return

    st.subheader("미리보기")
    st.dataframe(df.head())

    if not creds:
        st.warning("Notion 자격 증명 설정 후 다시 시도해주세요.")
        return

    if st.button("Notion으로 보내기", type="primary"):
        with st.spinner("Notion으로 데이터를 전송 중입니다..."):
            errors = add_rows_to_notion(creds["token"], creds["database_id"], df)

        if errors:
            st.error("일부 행이 업로드되지 않았습니다:")
            for error in errors:
                st.write(f"- {error}")
        else:
            st.success(f"총 {len(df)}개의 행을 성공적으로 전송했습니다!")


if __name__ == "__main__":
    main()
