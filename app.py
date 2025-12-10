"""Streamlit app to convert uploaded Excel files into downloadable CSV files."""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import streamlit as st

from df2notoin import upload_dataframe_to_notion_data_source 


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.rename(columns={"No.": "차트번호"}).iloc[:-1]
    df["예약일시"] = df.예약일 + " " + df.시간 + " (GMT+9)"
    df["등록일"] = df["등록일시"].str[:10]
    df["차트번호"] = df["차트번호"].astype(int)
    df = df.loc[:,["등록일", "예약일시", "차트번호", "고객명", "구분", "상태", "상담자", "원장", "성별", "나이", "핸드폰", "주소", "국가", "사진"]]
    
    return df

def read_excel(file) -> Optional[pd.DataFrame]:
    """Read the uploaded Excel file into a DataFrame with basic error handling."""
    try:
        return pd.read_excel(file)
    except Exception as exc:  # pragma: no cover - user facing
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {exc}")
        return None


def convert_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes without the index column."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode("utf-8")

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATA_SOURCE_ID = st.secrets["DATA_SOURCE_ID"]

def main() -> None:
    st.set_page_config(page_title="Excel to CSV Converter", page_icon="📁", layout="centered")
    st.title("📁 Plasys 데이터 변환기")
    st.write("Plasys에서 데이터를 다운받아 엑셀 파일을 업로드하세요.")

    uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요.", type=["xls", "xlsx"])
    if uploaded_file is None:
        st.info(".xls 또는 .xlsx 파일을 선택해주세요.")
        return

    df = read_excel(uploaded_file)
    if df is None:
        return

    st.subheader("업로드한 데이터 미리보기")
    st.dataframe(df.head())

    st.subheader("전처리된 데이터")
    processed_df = preprocess_dataframe(df.copy())
    st.dataframe(processed_df.head())

    csv_bytes = convert_to_csv(processed_df)

    st.download_button(
        label="CSV로 다운로드",
        data=csv_bytes,
        file_name="converted.csv",
        mime="text/csv",
        type="primary")

    st.subheader("Notion 업로드")
    st.info(f"전체 {len(processed_df)}개의 데이터가 Notion에 업로드 중 입니다.")

    page_ids = upload_dataframe_to_notion_data_source(
        processed_df,
        data_source_id = DATA_SOURCE_ID,
        token = NOTION_TOKEN)

    messege = f"전체 {len(processed_df)}개의 데이터가 Notion에 {len(page_ids)}개의 페이지로 업로드되었습니다."
    st.success(messege)

if __name__ == "__main__":
    main()
