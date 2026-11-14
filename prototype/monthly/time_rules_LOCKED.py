"""星めぐり天文暦：JST表示時刻 共通仕様（表示のみ分単位四捨五入）."""
from datetime import datetime, timedelta

def round_to_minute(dt: datetime) -> datetime:
    """Aware datetime (JST) -> nearest minute, exactly 30s rounds up."""
    if dt.tzinfo is None or dt.utcoffset() != timedelta(hours=9):
        raise ValueError("Timezone-aware JST (+09:00) datetime required")
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0)

def display_minute(dt: datetime) -> str:
    return round_to_minute(dt).strftime("%Y-%m-%d %H:%M")

def root_source_time(dt: datetime) -> str:
    """Keep original timing to microseconds; never round the source."""
    if dt.tzinfo is None:
        raise ValueError("Timezone-aware datetime required")
    return dt.isoformat()
