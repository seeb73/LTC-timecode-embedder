# utils.py
# Version: 0.1.0

import datetime
import pytz

def parse_gopro_qr_timecode(qr_string: str) -> datetime.datetime:
    """Parses GoPro timecode from 'oT...' format to UTC datetime."""
    if not qr_string.startswith("oT"):
        raise ValueError("Invalid GoPro timecode format (missing 'oT' prefix).")

    time_part_end = qr_string.find("oTD")
    if time_part_end == -1:
        raise ValueError("Invalid GoPro timecode format (missing 'oTD').")
    
    time_part = qr_string[2:time_part_end]

    try:
        year_str = "20" + time_part[0:2]
        month_str = time_part[2:4]
        day_str = time_part[4:6]
        hour_str = time_part[6:8]
        minute_str = time_part[8:10]
        second_str = time_part[10:12]
        millisecond_str = time_part[13:]

        full_time_str = f"{year_str}-{month_str}-{day_str} {hour_str}:{minute_str}:{second_str}.{millisecond_str}"
        dt_naive = datetime.datetime.strptime(full_time_str, "%Y-%m-%d %H:%M:%S.%f")

        # Assume oTZ2 means UTC+2 as per user's experience
        # Using fixed offset timezone for simplicity. Consider 'Europe/Warsaw' for DST awareness.
        # pytz.timezone('Etc/GMT-2') means UTC+2
        cest_tz = pytz.timezone('Etc/GMT-2') 
        dt_aware_cest = cest_tz.localize(dt_naive)
        dt_utc = dt_aware_cest.astimezone(pytz.utc)
        
        return dt_utc
    except (ValueError, IndexError, pytz.exceptions.UnknownTimeZoneError) as e:
        raise ValueError(f"Error parsing GoPro time string '{time_part}': {e}")
