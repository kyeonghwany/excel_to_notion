"""Streamlit app to convert uploaded Excel files into downloadable CSV files."""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import streamlit as st


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder preprocessing for uploaded Excel data.

    Update this function to include the exact cleaning or transformation steps
    needed for your workflow. The current implementation demonstrates a simple
    pattern of trimming whitespace and dropping empty rows.
    """

    # Trim surrounding whitespace from string columns
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].astype("string").str.strip()

    # Drop rows that are fully empty
    df = df.dropna(how="all").reset_index(drop=True)

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
        type="primary",
    )

    st.download_button(
        label="XLSX로 다운로드",
        data=csv_bytes,
        file_name="converted.csv",
        mime="text/csv",
        type="primary",
    )

if __name__ == "__main__":
    main()
