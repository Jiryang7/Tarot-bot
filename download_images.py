"""
라이더-웨이트 타로 카드 이미지 다운로드 스크립트
공개 도메인 이미지를 images/ 폴더에 저장합니다.
실행: python download_images.py
"""

import os
import urllib.request
import time

# images 폴더 생성
os.makedirs("images", exist_ok=True)

# 라이더-웨이트 메이저 아르카나 이미지 URL 목록
# (Wikipedia Commons - 공개 도메인)
CARD_URLS = {
    0:  "https://upload.wikimedia.org/wikipedia/commons/9/90/RWS_Tarot_00_Fool.jpg",
    1:  "https://upload.wikimedia.org/wikipedia/commons/d/de/RWS_Tarot_01_Magician.jpg",
    2:  "https://upload.wikimedia.org/wikipedia/commons/8/88/RWS_Tarot_02_High_Priestess.jpg",
    3:  "https://upload.wikimedia.org/wikipedia/commons/d/d2/RWS_Tarot_03_Empress.jpg",
    4:  "https://upload.wikimedia.org/wikipedia/commons/c/c3/RWS_Tarot_04_Emperor.jpg",
    5:  "https://upload.wikimedia.org/wikipedia/commons/8/8d/RWS_Tarot_05_Hierophant.jpg",
    6:  "https://upload.wikimedia.org/wikipedia/commons/3/3a/TheLovers.jpg",
    7:  "https://upload.wikimedia.org/wikipedia/commons/9/9b/RWS_Tarot_07_Chariot.jpg",
    8:  "https://upload.wikimedia.org/wikipedia/commons/f/f5/RWS_Tarot_08_Strength.jpg",
    9:  "https://upload.wikimedia.org/wikipedia/commons/4/4d/RWS_Tarot_09_Hermit.jpg",
    10: "https://upload.wikimedia.org/wikipedia/commons/3/3c/RWS_Tarot_10_Wheel_of_Fortune.jpg",
    11: "https://upload.wikimedia.org/wikipedia/commons/e/e0/RWS_Tarot_11_Justice.jpg",
    12: "https://upload.wikimedia.org/wikipedia/commons/2/2b/RWS_Tarot_12_Hanged_Man.jpg",
    13: "https://upload.wikimedia.org/wikipedia/commons/d/d7/RWS_Tarot_13_Death.jpg",
    14: "https://upload.wikimedia.org/wikipedia/commons/f/f8/RWS_Tarot_14_Temperance.jpg",
    15: "https://upload.wikimedia.org/wikipedia/commons/5/55/RWS_Tarot_15_Devil.jpg",
    16: "https://upload.wikimedia.org/wikipedia/commons/5/53/RWS_Tarot_16_Tower.jpg",
    17: "https://upload.wikimedia.org/wikipedia/commons/d/db/RWS_Tarot_17_Star.jpg",
    18: "https://upload.wikimedia.org/wikipedia/commons/7/7f/RWS_Tarot_18_Moon.jpg",
    19: "https://upload.wikimedia.org/wikipedia/commons/1/17/RWS_Tarot_19_Sun.jpg",
    20: "https://upload.wikimedia.org/wikipedia/commons/d/dd/RWS_Tarot_20_Judgement.jpg",
    21: "https://upload.wikimedia.org/wikipedia/commons/f/ff/RWS_Tarot_21_World.jpg",
}

def download_images():
    print("📥 타로 카드 이미지 다운로드 시작...\n")
    success = 0
    fail = 0

    for card_num, url in CARD_URLS.items():
        filename = f"images/{card_num:02d}.jpg"

        if os.path.exists(filename):
            print(f"✅ {card_num:02d}번 이미 있음 - 스킵")
            success += 1
            continue

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(filename, "wb") as f:
                    f.write(response.read())
            print(f"✅ {card_num:02d}번 카드 다운로드 완료")
            success += 1
            time.sleep(0.5)  # 서버 부하 방지
        except Exception as e:
            print(f"❌ {card_num:02d}번 카드 실패: {e}")
            fail += 1

    # 22번은 0번(바보) 복사
    if os.path.exists("images/00.jpg") and not os.path.exists("images/22.jpg"):
        import shutil
        shutil.copy("images/00.jpg", "images/22.jpg")
        print("✅ 22번 카드 (바보 복사본) 생성 완료")

    print(f"\n🎉 완료! 성공: {success}개, 실패: {fail}개")

if __name__ == "__main__":
    download_images()
