"""
Google 스프레드시트 연동 모듈
컬럼 구조: 이름 | 양력생일 | 양력카드 | 음력생일 | 음력카드 | 등록일
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 컬럼 인덱스
COL_NAME       = 0
COL_SOLAR_DATE = 1
COL_SOLAR_CARD = 2
COL_LUNAR_DATE = 3
COL_LUNAR_CARD = 4
COL_REG_DATE   = 5


def _get_sheet():
    try:
        import gspread
        import json
        from google.oauth2.service_account import Credentials

        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id:
            logger.warning("GOOGLE_SHEET_ID 환경변수가 없습니다.")
            return None

        # Railway 등 환경변수로 credentials JSON을 직접 주입한 경우
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            info = json.loads(creds_json)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            # 로컬 개발: credentials.json 파일 사용
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id).sheet1

    except Exception as e:
        logger.error(f"Google Sheets 연결 실패: {e}")
        return None


def save_person(
    name: str,
    solar_date: str,
    solar_card: int,
    lunar_date: str = "",
    lunar_card: int = None,
) -> bool:
    """사람 정보 저장 (이름+양력생일 기준으로 중복 체크 후 upsert)"""
    try:
        from datetime import datetime
        sheet = _get_sheet()
        if not sheet:
            return False

        today    = datetime.now().strftime("%Y-%m-%d")
        all_rows = sheet.get_all_values()

        for i, row in enumerate(all_rows):
            if len(row) >= 2 and row[COL_NAME] == name and row[COL_SOLAR_DATE] == solar_date:
                # 업데이트
                sheet.update(
                    f"A{i+1}:F{i+1}",
                    [[name, solar_date, solar_card, lunar_date, lunar_card or "", today]]
                )
                logger.info(f"업데이트: {name} ({solar_date})")
                return True

        # 새로 추가
        sheet.append_row([name, solar_date, solar_card, lunar_date, lunar_card or "", today])
        logger.info(f"저장: {name} | 양력 {solar_date}({solar_card}) | 음력 {lunar_date}({lunar_card})")
        return True

    except Exception as e:
        logger.error(f"저장 실패: {e}")
        return False


def find_person_by_name(name: str) -> list:
    """이름으로 검색 (부분 일치)"""
    try:
        sheet = _get_sheet()
        if not sheet:
            return []

        results = []
        for row in sheet.get_all_values():
            if len(row) >= 3 and name in row[COL_NAME]:
                try:
                    results.append({
                        "name":       row[COL_NAME],
                        "solar_date": row[COL_SOLAR_DATE],
                        "solar_card": int(row[COL_SOLAR_CARD]),
                        "lunar_date": row[COL_LUNAR_DATE] if len(row) > COL_LUNAR_DATE else "",
                        "lunar_card": int(row[COL_LUNAR_CARD]) if len(row) > COL_LUNAR_CARD and row[COL_LUNAR_CARD] else None,
                    })
                except (ValueError, IndexError):
                    continue
        return results

    except Exception as e:
        logger.error(f"검색 실패: {e}")
        return []
