# 🍽️ 식판 스캐너
### AI 급식 분석 & 잔반 제로 챌린지

스마트폰으로 급식 식판을 촬영하면 **AI가 급식 메뉴와 영양 정보를 분석하고, 식사 후 남은 음식의 양을 분석해 잔반 점수를 제공하는 서비스**입니다.

단순한 AI 이미지 분석을 넘어 회원 시스템, 기록 저장, 랭킹 시스템을 결합하여 학생들이 자신의 식습관을 확인하고 잔반을 줄일 수 있도록 설계했습니다.

---

## 📌 프로젝트 개요

### 개발 기간
2026.06.13 ~ 2026.06.16

### 프로젝트 유형
- 개인 프로젝트
- Web Application
- AI 기반 이미지 분석 서비스

### 프로젝트 목표

학교 급식실에서 발생하는 음식물 쓰레기 문제에 주목했습니다.

학생들이 자신이 얼마나 음식을 남기는지 직관적으로 확인하기 어렵고, 급식의 영양 정보 역시 한눈에 파악하기 어렵다는 문제를 발견했습니다.

이를 해결하기 위해

> **"스마트폰으로 식판을 찍으면 AI가 바로 분석해주는 서비스를 만들면 어떨까?"**

라는 아이디어를 바탕으로 프로젝트를 제작했습니다.

### 기대 효과

- 학생 스스로 식습관을 확인하고 개선
- 잔반 감소를 통한 환경 보호
- 잔반 점수 및 랭킹을 활용한 참여 유도
- AI를 활용한 급식 및 영양 정보의 직관적인 제공

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.9.6 |
| Backend | Flask |
| Database | SQLite |
| Frontend | HTML / CSS / JavaScript |
| AI | Google Gemini 2.5 Flash API |
| Deployment | Railway |
| Application | PWA |

---

## 🏗️ System Architecture

```text
┌─────────────────────┐
│   Smartphone Camera │
└──────────┬──────────┘
           │
           │ 식판 촬영
           ▼
┌─────────────────────┐
│   Browser           │
│   HTML / JS         │
└──────────┬──────────┘
           │
           │ Base64 Image
           ▼
┌─────────────────────┐
│   Flask Server      │
│      Python         │
└──────────┬──────────┘
           │
           │ Image + Prompt
           ▼
┌─────────────────────┐
│ Gemini 2.5 Flash    │
│      AI API         │
└──────────┬──────────┘
           │
           │ JSON Analysis
           ▼
┌─────────────────────┐
│   Flask Server      │
│  DB 저장 및 처리    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Browser           │
│ 결과 시각화         │
└─────────────────────┘
```

---

## ✨ 주요 기능

### 1. 🥗 먹기 전 영양 분석

스마트폰으로 급식 식판을 촬영하면 AI가 식판 이미지를 분석합니다.

분석 결과를 통해 다음 정보를 제공합니다.

- 급식 메뉴 인식
- 칼로리
- 탄수화물
- 단백질
- 지방

분석 결과는 JSON 형태로 받아 프론트엔드에서 시각화합니다.

---

### 2. ♻️ 잔반 제로 점수

식사 후 식판을 다시 촬영하면 AI가 남은 음식의 양을 분석합니다.

분석 결과를 기반으로:

- 잔반 점수: `0 ~ 100점`
- 환경 등급: `S ~ D`

를 제공합니다.

이를 통해 사용자가 자신의 잔반량을 직관적으로 확인할 수 있도록 구현했습니다.

---

### 3. 👤 회원 시스템

회원가입 및 로그인 기능을 제공합니다.

사용자의 분석 기록을 데이터베이스에 저장하여 다음 정보를 관리합니다.

- 개인 분석 기록
- 평균 잔반 점수
- 완벽한 식사 횟수

---

### 4. 🏆 랭킹 시스템

사용자들의 잔반 점수를 기반으로 다양한 랭킹을 제공합니다.

#### 오늘의 랭킹
당일 잔반 점수를 기준으로 순위를 표시합니다.

#### 개인 전체 랭킹
전체 기간 동안의 평균 점수를 기준으로 표시합니다.

#### 학급별 랭킹
학급 단위로 평균 점수를 비교할 수 있도록 구성했습니다.

---

## 🔐 보안 설계

단순히 기능을 구현하는 것에서 끝내지 않고 기본적인 보안 요소도 적용했습니다.

### 비밀번호 보호

비밀번호를 평문으로 저장하지 않고 해시 처리하여 데이터베이스에 저장했습니다.

```text
사용자 비밀번호
       ↓
    SHA-256
       ↓
Hash 값 저장
```

### API Key 보호

Gemini API Key를 소스 코드에 직접 작성하지 않고 환경변수로 분리했습니다.

```text
GEMINI_API_KEY
```

실제 API Key가 GitHub 저장소에 노출되지 않도록 구성했습니다.

### Rate Limiting

`flask-limiter`를 사용하여 무분별한 요청을 제한했습니다.

- 회원가입: IP 기준 하루 5회
- 로그인: 분당 10회

### 입력값 검증

학급명 입력값에 정규식 검증을 적용하여 악의적인 입력을 방지했습니다.

---

## 🧩 Troubleshooting

### 1. Google Gemini API 라이브러리 마이그레이션

개발 중 기존 `google.generativeai` 패키지에서 새로운 `google.genai` 방식으로 변경해야 하는 상황이 발생했습니다.

#### 기존 방식

```python
import google.generativeai as genai

genai.configure(api_key=KEY)

model = genai.GenerativeModel("gemini-1.5-flash")
```

#### 변경 후

```python
from google import genai

client = genai.Client(api_key=KEY)

client.models.generate_content(
    model="gemini-2.5-flash",
    ...
)
```

공식 문서를 확인하고 새로운 `Client` 방식으로 직접 마이그레이션했습니다.

---

### 2. Railway 배포 오류

배포 과정에서 발생한 오류를 로그를 확인하며 단계적으로 해결했습니다.

#### `ModuleNotFoundError`

필요한 패키지가 설치되지 않은 문제였습니다.

**해결**

`requirements.txt`를 작성하여 필요한 패키지를 명시했습니다.

---

#### `ValueError: GEMINI_API_KEY`

Gemini API Key 환경변수가 설정되지 않은 문제였습니다.

**해결**

Railway 환경변수 설정에 API Key를 등록했습니다.

---

#### `AssertionError: overwriting endpoint`

Flask에서 동일한 endpoint가 중복 정의된 문제였습니다.

**해결**

중복된 함수 및 endpoint 구조를 수정했습니다.

---

## 📚 프로젝트를 통해 배운 점

### Backend

- Flask를 이용한 REST API 설계
- 프론트엔드와 백엔드 통신
- JSON 데이터 처리
- 데이터베이스 CRUD
- SQLite 활용

### AI

- AI API를 이용한 이미지 분석
- 프롬프트 설계
- AI 응답을 JSON 형태로 구조화
- AI 분석 결과를 실제 서비스에 연결

### Security

- 비밀번호 해싱
- 환경변수 관리
- Rate Limiting
- 사용자 입력값 검증
- 기본적인 웹 보안 개념

### Deployment

- 로컬 개발 환경 구성
- 환경변수 설정
- 배포 환경에서 발생하는 오류 분석
- Railway를 이용한 서비스 배포

---

## 💡 가장 큰 문제 해결 경험

이 프로젝트에서 가장 의미 있었던 경험은 단순히 기능을 구현한 것이 아니라 **실제 서비스가 배포되는 과정에서 발생한 문제를 직접 분석하고 해결한 것**입니다.

배포 과정에서 발생한 오류 로그를 확인하고,

```text
오류 발생
   ↓
로그 확인
   ↓
원인 추적
   ↓
관련 코드/설정 확인
   ↓
수정
   ↓
재배포
   ↓
정상 동작 확인
```

과정을 반복하면서 문제 해결 능력을 키웠습니다.

---

## 🚀 향후 발전 방향

### 1. 급식 메뉴 DB 연동

학교 급식 메뉴 데이터베이스와 연동하여 AI가 이미지를 분석할 때 메뉴 정보를 함께 활용하도록 개선할 예정입니다.

### 2. 관리자 페이지

선생님이 학급 전체의 잔반 통계를 확인할 수 있는 관리자 페이지를 추가할 수 있습니다.

### 3. 모바일 앱

PWA 기반 서비스를 발전시켜 Flutter를 이용한 네이티브 앱으로 확장할 수 있습니다.

### 4. 식습관 리포트

사용자의 기록을 기반으로 주간/월간 식습관 리포트를 제공할 수 있습니다.

---

## 🎯 프로젝트 의의

이 프로젝트는 **학교에서 실제로 발생하는 문제를 발견하고 AI와 웹 기술을 이용해 해결하는 것**을 목표로 제작했습니다.

```text
학교의 문제 발견
      ↓
아이디어 구상
      ↓
서비스 설계
      ↓
AI + Backend 개발
      ↓
보안 적용
      ↓
배포
      ↓
실제 동작하는 서비스 완성
```

단순한 AI 모델 실험이 아니라 **AI API + Backend + Database + Frontend + Deployment + Security**를 하나의 서비스로 연결해본 프로젝트입니다.



## 🚀 실행 방법

### 1. 웹사이트로 이용

배포된 웹사이트에 접속하면 별도의 설치 없이 바로 사용할 수 있습니다.

**배포 URL:**  
https://siu-production-a23c.up.railway.app/login

---

### 2. GitHub에서 다운로드하여 직접 실행

GitHub Repository에서 프로젝트를 다운로드하여 로컬 환경에서 직접 실행할 수 있습니다.

#### ① 프로젝트 다운로드

GitHub Repository에서

**Code → Download ZIP**

을 클릭하여 프로젝트를 다운로드합니다.

압축을 해제한 후 프로젝트 폴더로 이동합니다.

#### ② Python 환경 확인

Python 3.9.6 환경을 권장합니다.

```bash
python --version
```

#### ③ 필요한 라이브러리 설치

프로젝트 폴더에서 다음 명령어를 실행합니다.

```bash
pip install -r requirements.txt
```

#### ④ Gemini API Key 설정

이 프로젝트는 Google Gemini API를 사용하므로 실행 전에 API Key를 환경변수로 설정해야 합니다.

**macOS / Linux**

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export SECRET_KEY="YOUR_SECRET_KEY"
```

**Windows PowerShell**

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:SECRET_KEY="YOUR_SECRET_KEY"
```

> ⚠️ 실제 Gemini API Key를 GitHub에 업로드하지 마세요.
> 
> API Key는 반드시 환경변수로 관리하는 것을 권장합니다.

#### ⑤ 서버 실행

```bash
python app.py
```

정상적으로 실행되면 브라우저에서 다음 주소로 접속합니다.

```text
http://127.0.0.1:8080
```

로그인 페이지:

```text
http://127.0.0.1:8080/login
```

---

### 3. 프로젝트 폴더 구조

```text
cafeteria-scanner/
├── app.py
├── requirements.txt
├── Procfile
├── .gitignore
├── templates/
│   ├── index.html
│   ├── login.html
│   └── ranking.html
└── static/
    ├── icon-192.png
    ├── icon-512.png
    ├── manifest.json
    └── service-worker.js
```

---

### 📱 PWA 설치

이 프로젝트는 PWA(Progressive Web App)를 지원합니다.

웹사이트에 접속한 후 브라우저에서 제공하는

**홈 화면에 추가 / 앱 설치**

기능을 이용하면 모바일에서 앱처럼 사용할 수 있습니다.

별도의 앱스토어 설치 없이 웹사이트를 앱 형태로 사용할 수 있습니다.
