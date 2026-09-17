from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import base64
from google import genai
from google.genai import types
import os
import re
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

client = genai.Client(api_key=GEMINI_API_KEY)

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",   # 경고 제거
    default_limits=[]
)

# ── DB 초기화 ──────────────────────────────────────────────
DB_PATH = os.environ.get("DB_PATH", "sikpan.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT UNIQUE NOT NULL,
                password  TEXT NOT NULL,
                class_name TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS records (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                mode       TEXT NOT NULL,
                score      INTEGER DEFAULT 0,
                calories   INTEGER DEFAULT 0,
                dish       TEXT DEFAULT '',
                detail     TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)

init_db()

# ── 유틸 ──────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def parse_image_data(image_data: str):
    if "," not in image_data:
        raise ValueError("올바른 이미지 데이터 형식이 아닙니다.")
    header, encoded = image_data.split(",", 1)
    mime_match = re.search(r"data:(image/[a-zA-Z+]+);base64", header)
    mime_type = mime_match.group(1) if mime_match else "image/jpeg"
    return mime_type, base64.b64decode(encoded)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return wrapper

# ── 페이지 라우트 ──────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html',
                           username=session.get('username'),
                           class_name=session.get('class_name', ''))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/ranking')
def ranking_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('ranking.html',
                           username=session.get('username'),
                           class_name=session.get('class_name', ''))

# ── 인증 API ───────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
@limiter.limit("1 per month")
def register():
    data = request.json or {}
    username   = (data.get('username') or '').strip()
    password   = data.get('password', '')
    class_name = (data.get('class_name') or '').strip()

    if class_name and (len(class_name) > 20 or not re.match(r'^\d+학년\s+\d+반$', class_name)):
        return jsonify({'error': '올바른 학급 형식(예: 1학년 2반)으로 입력해주세요.'}), 400
    if not username or not password:
        return jsonify({'error': '아이디와 비밀번호를 입력해주세요.'}), 400
    if len(username) < 2 or len(username) > 20:
        return jsonify({'error': '아이디는 2~20자로 입력해주세요.'}), 400
    if len(password) < 4:
        return jsonify({'error': '비밀번호는 4자 이상으로 입력해주세요.'}), 400

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password, class_name) VALUES (?, ?, ?)",
                (username, hash_pw(password), class_name)
            )
        return jsonify({'success': True, 'message': '회원가입 완료!'})
    except sqlite3.IntegrityError:
        return jsonify({'error': '이미 사용 중인 아이디입니다.'}), 409

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_pw(password))
        ).fetchone()

    if not user:
        return jsonify({'error': '아이디 또는 비밀번호가 틀렸습니다.'}), 401

    session['user_id']    = user['id']
    session['username']   = user['username']
    session['class_name'] = user['class_name']
    return jsonify({'success': True, 'username': user['username']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me')
@login_required
def me():
    with get_db() as conn:
        stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(AVG(CASE WHEN mode='after' THEN score END), 0) as avg_score,
                COALESCE(SUM(CASE WHEN mode='before' THEN calories END), 0) as total_cal,
                COUNT(CASE WHEN mode='after' AND score>=90 THEN 1 END) as perfect_days
            FROM records WHERE user_id=?
        """, (session['user_id'],)).fetchone()

    return jsonify({
        'username':   session['username'],
        'class_name': session.get('class_name', ''),
        'total':      stats['total'],
        'avg_score':  round(stats['avg_score'], 1),
        'total_cal':  stats['total_cal'],
        'perfect_days': stats['perfect_days']
    })

# ── 분석 API ───────────────────────────────────────────────
@app.route('/analyze-meal', methods=['POST'])
@login_required
def analyze_meal():
    data = request.json
    if not data:
        return jsonify({'error': '요청 데이터가 없습니다.'}), 400

    image_data = data.get('image')
    mode = data.get('mode')

    if not image_data:
        return jsonify({'error': '이미지가 없습니다.'}), 400
    if mode not in ("before", "after"):
        return jsonify({'error': 'mode는 "before" 또는 "after"여야 합니다.'}), 400

    try:
        mime_type, image_bytes = parse_image_data(image_data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    try:
        if mode == "before":
            prompt = """이 학교 급식 식판 사진을 분석해서 아래 JSON만 반환해. 코드블록 없이 순수 JSON만.
{
  "dish": "메뉴명들 쉼표로 구분",
  "calories": 숫자,
  "carb_g": 숫자,
  "protein_g": 숫자,
  "fat_g": 숫자,
  "comment": "한 줄 영양 코멘트"
}"""
        else:
            prompt = """이 다 먹고 남은 학교 급식 식판 사진을 분석해서 아래 JSON만 반환해. 코드블록 없이 순수 JSON만.
음식을 거의 다 먹어서 깨끗하면 100점, 많이 남길수록 점수를 깎아줘.
{
  "dish": "식단명",
  "score": 0에서100 사이 숫자,
  "leftover_pct": 남긴 비율 숫자(0에서100),
  "clean_slots": "예: 4/5",
  "eco_grade": "S 또는 A 또는 B 또는 C 또는 D",
  "comment": "남긴 음식에 대한 피드백이나 칭찬 한마디"
}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            ]
        )

        raw = response.text.strip()
        cleaned = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(cleaned)

        # DB 저장
        score    = result.get('score', 0) if mode == 'after' else 0
        calories = result.get('calories', 0) if mode == 'before' else 0
        with get_db() as conn:
            conn.execute(
                "INSERT INTO records (user_id, mode, score, calories, dish, detail) VALUES (?,?,?,?,?,?)",
                (session['user_id'], mode, score, calories, result.get('dish', ''), json.dumps(result, ensure_ascii=False))
            )

        return jsonify({'success': True, 'result': result})

    except json.JSONDecodeError as e:
        app.logger.error(f"JSON 파싱 오류: {e}")
        return jsonify({'error': 'AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.'}), 500
    except Exception as e:
        app.logger.error(f"Gemini API 오류: {e}")
        return jsonify({'error': 'AI 분석 중 오류가 발생했습니다.'}), 500

# ── 랭킹 API ───────────────────────────────────────────────
@app.route('/api/ranking/personal')
@login_required
def ranking_personal():
    """전체 개인 랭킹 (잔반 평균 점수 기준)"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT u.username, u.class_name,
                   ROUND(AVG(r.score), 1) as avg_score,
                   COUNT(r.id) as total,
                   COUNT(CASE WHEN r.score>=90 THEN 1 END) as perfect
            FROM users u
            JOIN records r ON u.id = r.user_id AND r.mode='after'
            GROUP BY u.id
            HAVING total >= 1
            ORDER BY avg_score DESC
            LIMIT 50
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ranking/class')
@login_required
def ranking_class():
    """학급별 랭킹"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT u.class_name,
                   ROUND(AVG(r.score), 1) as avg_score,
                   COUNT(DISTINCT u.id) as members,
                   COUNT(r.id) as total_records
            FROM users u
            JOIN records r ON u.id = r.user_id AND r.mode='after'
            WHERE u.class_name != ''
            GROUP BY u.class_name
            HAVING total_records >= 1
            ORDER BY avg_score DESC
            LIMIT 20
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ranking/today')
@login_required
def ranking_today():
    """오늘의 잔반 점수 랭킹"""
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT u.username, u.class_name,
                   MAX(r.score) as score, r.dish
            FROM users u
            JOIN records r ON u.id = r.user_id AND r.mode='after'
            WHERE DATE(r.created_at) = ?
            GROUP BY u.id
            ORDER BY score DESC
            LIMIT 30
        """, (today,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/history')
@login_required
def history():
    """내 기록 조회"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT mode, score, calories, dish, created_at
            FROM records WHERE user_id=?
            ORDER BY created_at DESC LIMIT 20
        """, (session['user_id'],)).fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', debug=debug_mode, port=port)


def validate_class_name(class_name: str) -> bool:
    if not class_name:
        return True  # 빈 값은 허용 (기존 기획 유지)
    
    # '숫자+학년+공백+숫자+반' 형식 검사
    # ^\d+ : 시작은 1개 이상의 숫자
    # 학년\s+ : '학년' 글자 뒤에 1개 이상의 공백
    # \d+반$ : 1개 이상의 숫자 뒤에 '반'으로 끝남
    if not re.match(r'^\d+학년\s+\d+반$', class_name):
        return False
        
    return True


