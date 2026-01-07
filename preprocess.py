import pandas as pd

def preprocess_reservation(df: pd.DataFrame) -> pd.DataFrame:  # noqa: F811
    
    state_code = {
        1: "예약",
        3: "부도",
        4: "취소",
        5: "완료",
        7: "변경",
        9: "당일",
        10: "결정",
        13: "재상담",
        16: "동행",
        17: "비대면",
        21: "모델"
    }

    df = df.rename(columns={"챠트": "차트번호", "분류": "구분"})
    df["reservation_id"] = df["지점"].notna().cumsum()
    df["시간"] = df["시간"].ffill()
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df["예약일시"] = pd.to_datetime(
        today + " " +
        df["시간"]
        .str.replace("오전", "AM")
        .str.replace("오후", "PM"),
        format="%Y-%m-%d %p %H:%M"
    )

    df = df.drop_duplicates(subset=["reservation_id"], keep="first").loc[:,["차트번호", "고객명", "reservation_id", "구분", "상태", "예약일시", "등록일시", "생년월일", "핸드폰", "원장", "상담자", "메모"]]
    df["차트번호"] = df["차트번호"].astype(int)
    df["상태"] = df["상태"].astype(int)
    df["상태"] = df["상태"].map(state_code)
    df["핸드폰"] = "\""+ df["핸드폰"].astype("string") + "\""
    df["생년월일"] = "\""+ df["생년월일"].astype("string") + "\""

    return df

def preprocess_event(df: pd.DataFrame) -> pd.DataFrame:
    events = ["내원", "진행", "완료", "퇴원"]
    df = (
        df.merge(pd.DataFrame({"event_name": events}), how="cross")
        .assign(event_id=lambda x: x.groupby("reservation_id").cumcount() + 1)
        )
    df["event_time"] = pd.NaT
    df["event_exp_time"] = pd.NaT
    df["event_params"] = None
    df = df.loc[:,["차트번호", "고객명", "reservation_id", "구분", "상태", "예약일시", "등록일시", "event_id", "event_name", "event_time", "event_exp_time", "event_params"]]
    
    return df

def preprocess_customer(df: pd.DataFrame) -> pd.DataFrame:
    
    exclude_status = {"취소", "변경", "부도"}

    df_summary = (
        df[~ df["상태"].isin(exclude_status)]
        .groupby("차트번호", as_index=False)
        .agg({
            "고객명": "first",
            "reservation_id": "first",
            "구분": lambda s: ">".join(pd.unique(s.dropna().astype(str))),
            "상태": "first",
            "예약일시": "first",
            "등록일시": "first",
            "생년월일": "first",
            "핸드폰": "first",
            "원장": "first",
            "상담자": "first"
            }))
    
    df_summary["예약일시"] = df_summary["예약일시"].astype(str) + ".000+09:00"

    return df_summary
    