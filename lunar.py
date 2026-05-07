"""
양력 → 음력 변환 모듈
korean-lunar-calendar 라이브러리 사용
설치: pip install korean-lunar-calendar
"""

import logging

logger = logging.getLogger(__name__)


def solar_to_lunar(year: int, month: int, day: int):
    """
    양력 날짜를 음력으로 변환
    반환: {"year": int, "month": int, "day": int, "is_leap": bool}
    실패 시: None
    """
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        cal = KoreanLunarCalendar()
        cal.setSolarDate(year, month, day)

        lunar_str = cal.LunarIsoFormat()   # 예: "1990-04-26"
        if not lunar_str:
            return None

        parts = lunar_str.split("-")
        return {
            "year":    int(parts[0]),
            "month":   int(parts[1]),
            "day":     int(parts[2]),
            "is_leap": cal.isIntercalation,  # 윤달 여부
        }

    except ImportError:
        logger.error(
            "korean-lunar-calendar 라이브러리가 없습니다.\n"
            "설치: pip install korean-lunar-calendar"
        )
        return None
    except Exception as e:
        logger.error(f"음력 변환 실패 ({year}-{month:02d}-{day:02d}): {e}")
        return None


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False):
    """
    음력 날짜를 양력으로 변환 (반대 방향)
    반환: {"year": int, "month": int, "day": int}
    실패 시: None
    """
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        cal = KoreanLunarCalendar()
        cal.setLunarDate(year, month, day, is_leap)

        solar_str = cal.SolarIsoFormat()   # 예: "1990-05-20"
        if not solar_str:
            return None

        parts = solar_str.split("-")
        return {
            "year":  int(parts[0]),
            "month": int(parts[1]),
            "day":   int(parts[2]),
        }

    except ImportError:
        logger.error("korean-lunar-calendar 라이브러리가 없습니다.")
        return None
    except Exception as e:
        logger.error(f"양력 변환 실패 ({year}-{month:02d}-{day:02d}): {e}")
        return None


# ─────────────────────────────────────────────
# 테스트용
# ─────────────────────────────────────────────
if __name__ == "__main__":
    result = solar_to_lunar(1990, 5, 20)
    print(f"1990-05-20 (양력) → {result}")

    result2 = solar_to_lunar(1967, 2, 20)
    print(f"1967-02-20 (양력) → {result2}")
