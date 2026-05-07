# 🃏 타로 운명 카드 텔레그램 봇

생년월일로 타로 메이저 아르카나 운명 카드를 계산하고,
Google 스프레드시트와 연동해 사람 정보를 저장/검색하는 텔레그램 봇입니다.

---

## ✨ 기능

| 기능 | 설명 |
|------|------|
| 🃏 운명 카드 보기 | 생년월일 입력 → 수비학 계산 → 카드 이미지 + 설명 |
| 🔍 이름 검색 | 저장된 이름으로 카드 조회 |
| 💞 궁합 보기 | 두 사람의 카드 비교 및 궁합 분석 |

---

## 📁 파일 구조

```
tarot_bot/
├── bot.py              # 텔레그램 봇 메인
├── tarot.py            # 수비학 계산 + 카드 정보
├── sheets.py           # Google 스프레드시트 연동
├── download_images.py  # 카드 이미지 자동 다운로드
├── requirements.txt    # 패키지 목록
├── .env.example        # 환경변수 예시
├── .env                # 실제 환경변수 (직접 생성)
├── credentials.json    # Google 서비스 계정 키 (직접 추가)
└── images/             # 카드 이미지 폴더 (자동 생성)
    ├── 00.jpg  (바보)
    ├── 01.jpg  (마법사)
    └── ...
```

---

## 🚀 설치 및 실행 방법

### 1단계: 패키지 설치

```bash
cd tarot_bot
pip install -r requirements.txt
```

### 2단계: 텔레그램 봇 토큰 발급

1. 텔레그램에서 **@BotFather** 검색
2. `/newbot` 명령어 실행
3. 봇 이름 및 username 설정
4. 발급된 **토큰** 복사

### 3단계: Google 스프레드시트 연동

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성
3. **Google Sheets API** 활성화
4. **서비스 계정** 생성 → JSON 키 다운로드 → `credentials.json`으로 저장
5. 구글 스프레드시트 새로 만들기
6. 스프레드시트를 서비스 계정 이메일과 **공유** (편집자 권한)
7. URL에서 스프레드시트 ID 복사

```
https://docs.google.com/spreadsheets/d/[이 부분이 ID]/edit
```

### 4단계: 환경변수 설정

`.env.example`을 복사해 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 편집:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
GOOGLE_CREDENTIALS_PATH=credentials.json
```

### 5단계: 카드 이미지 다운로드

```bash
python download_images.py
```

### 6단계: 봇 실행

```bash
python bot.py
```

---

## 🔢 수비학 계산법

생년월일의 각 자리 숫자를 모두 더해서 1~22 범위로 줄입니다.

```
예시: 1990년 5월 23일
→ 1+9+9+0+0+5+2+3 = 29
→ 29 > 22이므로 → 2+9 = 11
→ 운명 카드: 11번 (정의)
```

---

## 📊 Google 스프레드시트 구조

| A열 (이름) | B열 (생년월일) | C열 (카드번호) | D열 (등록일) |
|-----------|--------------|--------------|------------|
| 홍길동     | 1990-05-23   | 11           | 2024-01-15 |

---

## 💞 궁합 시스템

카드를 4가지 원소 그룹으로 분류하여 궁합을 분석합니다:

- 🔥 **불** (1, 4, 7, 10, 13, 16, 19번): 활동, 열정
- 💧 **물** (2, 5, 8, 11, 14, 17, 20번): 감성, 직관  
- 💨 **바람** (3, 6, 9, 12, 15, 18, 21번): 지성, 변화
- 🌱 **흙** (0/22번 바보): 순수 에너지

---

## 🛠️ VSCode에서 개발하기

### 디버그 실행 (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "타로봇 실행",
      "type": "python",
      "request": "launch",
      "program": "bot.py",
      "cwd": "${workspaceFolder}/tarot_bot",
      "envFile": "${workspaceFolder}/tarot_bot/.env"
    }
  ]
}
```

---

## ⚠️ 주의사항

- `.env` 파일과 `credentials.json`은 **절대 GitHub에 올리지 마세요**
- `.gitignore`에 반드시 추가하세요:
  ```
  .env
  credentials.json
  images/
  ```
