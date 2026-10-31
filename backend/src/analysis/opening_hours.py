from datetime import datetime, time
from typing import Dict, Any, Optional, Tuple
import re
import zoneinfo

TIJUANA_TZ = zoneinfo.ZoneInfo("America/Tijuana")

DAY_MAP = {
    0: ["mo", "mon", "lunes", "lu"],
    1: ["tu", "tue", "martes", "ma"],
    2: ["we", "wed", "miercoles", "miércoles", "mi"],
    3: ["th", "thu", "jueves", "ju"],
    4: ["fr", "fri", "viernes", "vi"],
    5: ["sa", "sat", "sabado", "sábado", "sa"],
    6: ["su", "sun", "domingo", "do"]
}


def parse_time_str(t_str: str) -> Optional[time]:
    t_str = t_str.strip().lower()
    m = re.match(r"^(\d{1,2}):(\d{2})$", t_str)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h < 24 and 0 <= mn < 60:
            return time(h, mn)
    
    # 12-hour format e.g. 5 p.m., 5:30 pm
    m12 = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)$", t_str)
    if m12:
        h = int(m12.group(1))
        mn = int(m12.group(2)) if m12.group(2) else 0
        meridiem = m12.group(3).replace(".", "")
        if "p" in meridiem and h < 12:
            h += 12
        elif "a" in meridiem and h == 12:
            h = 0
        if 0 <= h < 24 and 0 <= mn < 60:
            return time(h, mn)
    return None


def evaluate_opening_hours(raw_hours: Optional[str]) -> Tuple[bool, str]:
    now = datetime.now(TIJUANA_TZ)
    current_weekday = now.weekday()  # 0=Monday, 6=Sunday
    current_time = now.time()

    # 1. Check if raw_hours explicitly says Open / Closed
    if raw_hours:
        lower = raw_hours.lower()
        if "abierto las 24 horas" in lower:
            return True, "Abierto 24 horas"
        
        # Check text starting with 'Abierto'
        if re.search(r"\babierto\b", lower) and not re.search(r"\bcerrado\b", lower):
            # Check if closing soon (e.g. closes in less than 60 mins)
            m_close = re.search(r"cierra a las?\s+([\d:]+\s*[ap]\.?m\.?)", lower)
            if m_close:
                close_t = parse_time_str(m_close.group(1))
                if close_t:
                    now_mins = current_time.hour * 60 + current_time.minute
                    close_mins = close_t.hour * 60 + close_t.minute
                    diff = close_mins - now_mins
                    if 0 < diff <= 60:
                        return True, "Por cerrar pronto"
            return True, "Abierto ahora"
        
        if re.search(r"\bcerrado\b", lower):
            return False, "Cerrado en este momento"

        # Check OSM pattern like 'Mo-Fr 09:00-18:00; Sa 09:00-14:00'
        parts = lower.split(";")
        for p in parts:
            p = p.strip()
            # Match day range and hours
            m_osm = re.search(r"([a-z,-]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", p)
            if m_osm:
                days_spec = m_osm.group(1)
                open_str = m_osm.group(2)
                close_str = m_osm.group(3)

                applies_today = False
                if "mo-fr" in days_spec and current_weekday in (0, 1, 2, 3, 4):
                    applies_today = True
                elif "mo-sa" in days_spec and current_weekday in (0, 1, 2, 3, 4, 5):
                    applies_today = True
                elif "sa" in days_spec and current_weekday == 5:
                    applies_today = True
                elif "su" in days_spec and current_weekday == 6:
                    applies_today = True

                if applies_today:
                    t_open = parse_time_str(open_str)
                    t_close = parse_time_str(close_str)
                    if t_open and t_close:
                        if t_open <= current_time <= t_close:
                            now_m = current_time.hour * 60 + current_time.minute
                            close_m = t_close.hour * 60 + t_close.minute
                            if 0 < (close_m - now_m) <= 60:
                                return True, "Por cerrar pronto"
                            return True, "Abierto ahora"
                        else:
                            return False, "Cerrado en este momento"

    # 2. Standard commercial business hours for professional services (Dentistas, Contadores)
    # Mon-Fri: 09:00 - 18:00, Sat: 09:00 - 14:00, Sun: Closed
    if current_weekday in (0, 1, 2, 3, 4):
        # Mon-Fri
        if time(9, 0) <= current_time <= time(18, 0):
            if current_time >= time(17, 0):
                return True, "Por cerrar pronto"
            return True, "Abierto ahora"
        return False, "Cerrado en este momento"
    elif current_weekday == 5:
        # Sat
        if time(9, 0) <= current_time <= time(14, 0):
            if current_time >= time(13, 0):
                return True, "Por cerrar pronto"
            return True, "Abierto ahora"
        return False, "Cerrado en este momento"
    else:
        # Sun
        return False, "Cerrado en este momento"
