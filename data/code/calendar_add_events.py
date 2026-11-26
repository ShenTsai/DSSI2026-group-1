"""Add Tier 1 & Tier 2 campus/venue events to calendar_2024.csv and calendar_2025.csv,
and fill empty `day_off_reason` entries with "0" for clean programmatic handling.

Columns added (no-event rows encoded as 0):
  - event       : int 0/1 indicator (1 = Tier 1 or Tier 2 event, 0 = none)
  - event_tier  : int 0/1/2 (1 = Tier 1 core high-impact, 2 = Tier 2 major exam/venue/campus, 0 = none)
  - event_scope : str ("campus", "venue", "both", or "0")
  - event_name  : str descriptive label (or "0")

Existing columns preserved verbatim (`date`, `day_of_week`, `weekday`, `semester`);
`day_off_reason` retains all existing non-empty labels and encodes non-day-off rows as "0".
The script is idempotent (re-running produces identical files).

Run from anywhere inside the project:
  python3 data/code/calendar_add_events.py
"""

from pathlib import Path
import hashlib
import pandas as pd


def find_project_root(start: Path = Path(__file__).resolve()) -> Path:
    for p in [start, *start.parents]:
        if (p / "AGENTS.md").exists() and (p / "templates").is_dir():
            return p
    raise FileNotFoundError("Project root (AGENTS.md + templates/) not found.")


EVENTS_TIER12 = [
    # ==================== 2024 Tier 1 (17 days) ====================
    ("2024-02-24", 1, "venue",  "CWT-66台灣同人誌販售會D1"),
    ("2024-02-25", 1, "venue",  "CWT-66台灣同人誌販售會D2"),
    ("2024-03-02", 1, "campus", "2024臺大校園徵才博覽會"),
    ("2024-03-09", 1, "both",   "2024臺大杜鵑花節D1＋社團博覽會"),
    ("2024-03-10", 1, "both",   "2024臺大杜鵑花節D2"),
    ("2024-03-30", 1, "both",   "112學年度臺大校園馬拉松＋企排19總冠軍賽D1"),
    ("2024-03-31", 1, "venue",  "企業19年排球聯賽總冠軍賽D2"),
    ("2024-05-25", 1, "both",   "2024臺大112學年度畢業典禮＋臺科大畢業典禮"),
    ("2024-06-02", 1, "venue",  "NVIDIA黃仁勳COMPUTEX臺大體育館主題演講"),
    ("2024-08-10", 1, "venue",  "CWT-67台灣同人誌販售會D1"),
    ("2024-08-11", 1, "venue",  "CWT-67台灣同人誌販售會D2"),
    ("2024-08-29", 1, "both",   "2024臺大新生書院D3（新生音樂祭／大型集會）"),
    ("2024-08-30", 1, "campus", "2024臺大新生書院D4（結業＋社團市集）"),
    ("2024-09-01", 1, "both",   "2024臺大113學年度開學典禮＋宿舍搬入高峰"),
    ("2024-11-15", 1, "both",   "2024臺大96週年校慶"),
    ("2024-12-14", 1, "venue",  "CWT-68台灣同人誌販售會D1"),
    ("2024-12-15", 1, "venue",  "CWT-68台灣同人誌販售會D2"),

    # ==================== 2024 Tier 2 (23 days) ====================
    ("2024-02-03", 2, "campus", "113學年度臺大碩士班筆試D1"),
    ("2024-02-04", 2, "campus", "113學年度臺大碩士班筆試D2"),
    ("2024-04-21", 2, "venue",  "Jessica鄭秀妍演唱會"),
    ("2024-06-22", 2, "venue",  "臺大EMBA110級聯合畢典＋KARA見面會"),
    ("2024-06-28", 2, "venue",  "avantgardey台灣巡演D1"),
    ("2024-06-29", 2, "both",   "avantgardey台灣巡演D2＋2024臺大轉學考＋臺北親水節開幕"),
    ("2024-06-30", 2, "venue",  "avantgardey台灣巡演D3"),
    ("2024-07-07", 2, "venue",  "2024JLPT日本語能力試驗第一回"),
    ("2024-07-27", 2, "venue",  "EPIK HIGH亞洲巡演演唱會"),
    ("2024-08-27", 2, "campus", "2024臺大新生書院D1"),
    ("2024-08-28", 2, "campus", "2024臺大新生書院D2"),
    ("2024-09-07", 2, "campus", "2024上學期社團聯展"),
    ("2024-10-05", 2, "venue",  "南優鉉演唱會"),
    ("2024-10-06", 2, "venue",  "李起光演唱會"),
    ("2024-10-19", 2, "venue",  "2024司法官律師考試第二試D1"),
    ("2024-10-20", 2, "venue",  "2024司法官律師考試第二試D2"),
    ("2024-11-22", 2, "both",   "2024臺大校慶運動會D1"),
    ("2024-11-23", 2, "both",   "2024臺大校慶運動會D2＋BoA寶兒演唱會"),
    ("2024-11-30", 2, "venue",  "CRAVITY FAN-CON＋2024公館聖誕季開幕"),
    ("2024-12-01", 2, "venue",  "2024JLPT日本語能力試驗第二回"),
    ("2024-12-07", 2, "campus", "2024地方特考D1"),
    ("2024-12-08", 2, "campus", "2024地方特考D2"),
    ("2024-12-09", 2, "campus", "2024地方特考D3"),

    # ==================== 2025 Tier 1 (20 days) ====================
    ("2025-02-08", 1, "both",   "CWT-69D1＋114學年度臺大碩士班筆試D1"),
    ("2025-02-09", 1, "both",   "CWT-69D2＋114學年度臺大碩士班筆試D2"),
    ("2025-03-08", 1, "both",   "2025臺大校園徵才博覽會＋企排20挑戰賽"),
    ("2025-03-15", 1, "both",   "2025臺大杜鵑花節D1＋社團博覽會"),
    ("2025-03-16", 1, "both",   "2025臺大杜鵑花節D2"),
    ("2025-03-22", 1, "venue",  "企業20年排球聯賽總冠軍賽D1"),
    ("2025-03-23", 1, "venue",  "企業20年排球聯賽總冠軍賽D2"),
    ("2025-03-29", 1, "both",   "113學年度臺大校園馬拉松＋台北市召會萬人青年大會D1"),
    ("2025-05-24", 1, "both",   "2025臺大113學年度畢業典禮＋臺科大畢業典禮"),
    ("2025-06-08", 1, "venue",  "2025臺大電機資訊學院電機學群畢業典禮"),
    ("2025-08-16", 1, "venue",  "CWT-70台灣同人誌販售會D1"),
    ("2025-08-17", 1, "venue",  "CWT-70台灣同人誌販售會D2"),
    ("2025-08-28", 1, "both",   "2025臺大新生書院核心日（實境臺大）"),
    ("2025-08-31", 1, "both",   "2025臺大114學年度開學典禮＋宿舍搬入高峰"),
    ("2025-11-15", 1, "both",   "2025臺大97週年校慶＋校慶園遊會"),
    ("2025-11-22", 1, "both",   "2025臺大校慶運動會D2＋LisAni LIVE TAIPEI D1"),
    ("2025-11-23", 1, "venue",  "LisAni LIVE TAIPEI 2025 D2"),
    ("2025-12-13", 1, "venue",  "CWT-71台灣同人誌販售會D1"),
    ("2025-12-14", 1, "venue",  "CWT-71台灣同人誌販售會D2"),
    ("2025-12-27", 1, "venue",  "第23屆拳願明星格鬥賽＋李俊昊見面會D1"),

    # ==================== 2025 Tier 2 (17 days) ====================
    ("2025-01-18", 2, "both",   "2025學測D1＋GENBLUE幻藍小熊演唱會"),
    ("2025-02-22", 2, "venue",  "李俊昊FAN-CON Midnight Sun D1"),
    ("2025-02-23", 2, "venue",  "李俊昊FAN-CON Midnight Sun D2"),
    ("2025-03-30", 2, "venue",  "台北市召會萬人青年大會D2"),
    ("2025-04-12", 2, "venue",  "BTOB FAN-CON MELympic"),
    ("2025-06-07", 2, "both",   "國北教大113畢業典禮＋臺大各院系撥穗週末"),
    ("2025-06-28", 2, "both",   "2025臺大暑假轉學考＋臺北親水節開幕"),
    ("2025-07-06", 2, "venue",  "2025JLPT日本語能力試驗第一回"),
    ("2025-08-27", 2, "campus", "2025臺大新生書院D1"),
    ("2025-08-29", 2, "both",   "2025臺大新生書院D3（新生音樂祭）"),
    ("2025-09-06", 2, "campus", "2025上學期社團聯展"),
    ("2025-10-18", 2, "both",   "2025司法官律師考試第二試D1＋BTOB延長賽"),
    ("2025-11-21", 2, "both",   "2025臺大校慶運動會D1"),
    ("2025-12-06", 2, "both",   "國北教大130週年校慶園遊會＋2025地方特考D1"),
    ("2025-12-07", 2, "both",   "2025JLPT第二回＋2025地方特考D2"),
    ("2025-12-08", 2, "campus", "2025地方特考D3"),
    ("2025-12-20", 2, "venue",  "Kep1er巡迴演唱會"),
]


def main() -> None:
    root = find_project_root()
    events_df = pd.DataFrame(
        EVENTS_TIER12, columns=["date", "event_tier", "event_scope", "event_name"]
    )

    assert not events_df["date"].duplicated().any(), "Duplicate event dates found."
    assert events_df["event_tier"].isin([1, 2]).all()
    assert events_df["event_scope"].isin(["campus", "venue", "both"]).all()
    assert not events_df["event_name"].str.contains(",").any(), "Event names must not contain commas."

    for rel_path in ["data/processed/calendar_2024.csv", "data/processed/calendar_2025.csv"]:
        path = root / rel_path
        orig = pd.read_csv(path, dtype=str, keep_default_na=False)
        base = orig[["date", "day_of_week", "weekday", "semester", "day_off_reason"]].copy()

        base["day_off_reason"] = base["day_off_reason"].str.strip().replace("", "0")
        merged = base.merge(events_df, on="date", how="left")
        merged["event"] = merged["event_tier"].notna().astype(int)
        merged["event_tier"] = merged["event_tier"].fillna(0).astype(int)
        merged["event_scope"] = merged["event_scope"].fillna("0")
        merged["event_name"] = merged["event_name"].fillna("0")

        out_cols = [
            "date", "day_of_week", "weekday", "semester", "day_off_reason",
            "event", "event_tier", "event_scope", "event_name",
        ]
        merged = merged[out_cols]
        merged.to_csv(path, index=False, lineterminator="\n")

        # Re-read and strictly verify
        reread = pd.read_csv(path, dtype=str, keep_default_na=False)
        assert list(reread.columns) == out_cols
        assert len(reread) == len(orig)
        for col in ["date", "day_of_week", "weekday", "semester"]:
            assert (reread[col] == orig[col]).all(), f"Column {col} mutated unexpectedly."
        for col in out_cols:
            assert (reread[col] != "").all(), f"Blank value found in {col}."
        assert set(reread["event"]).issubset({"0", "1"})
        assert set(reread["event_tier"]).issubset({"0", "1", "2"})
        assert ((reread["event"] == "0") == (reread["event_tier"] == "0")).all()
        assert ((reread["event"] == "0") == (reread["event_scope"] == "0")).all()
        assert ((reread["event"] == "0") == (reread["event_name"] == "0")).all()

        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        t1 = int((reread["event_tier"] == "1").sum())
        t2 = int((reread["event_tier"] == "2").sum())
        dayoff_n = int((reread["day_off_reason"] != "0").sum())
        print(
            f"{rel_path}: {len(reread)} rows x {len(reread.columns)} cols | "
            f"day_off_reason != 0: {dayoff_n} | event == 1: {t1 + t2} (T1={t1}, T2={t2}) | "
            f"sha256={sha}"
        )


if __name__ == "__main__":
    main()
