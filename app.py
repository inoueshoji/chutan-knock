# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"


# -----------------------------------
# DB 初期化
# -----------------------------------
def init_db():
    conn = sqlite3.connect("chutan.db")
    cur = conn.cursor()

    # users テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        );
    """)

    # progress テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER PRIMARY KEY,
            total INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            last_play TEXT
        );
    """)

    conn.commit()
    conn.close()


# -----------------------------------
# DBユーティリティ
# -----------------------------------
def get_user(username):
    conn = sqlite3.connect("chutan.db")
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user


def get_progress(user_id):
    conn = sqlite3.connect("chutan.db")
    cur = conn.cursor()
    cur.execute("SELECT total, correct, last_play FROM progress WHERE user_id=?", (user_id,))
    data = cur.fetchone()
    conn.close()
    if data is None:
        return (0, 0, "-")
    return data


def update_progress(user_id, add_total, add_correct):
    conn = sqlite3.connect("chutan.db")
    cur = conn.cursor()

    cur.execute("SELECT total, correct FROM progress WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if row:
        new_total = row[0] + add_total
        new_correct = row[1] + add_correct
        cur.execute("""
            UPDATE progress SET total=?, correct=?, last_play=?
            WHERE user_id=?
        """, (new_total, new_correct, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id))
    else:
        cur.execute("""
            INSERT INTO progress (user_id, total, correct, last_play)
            VALUES (?, ?, ?, ?)
        """, (user_id, add_total, add_correct, datetime.now().strftime("%Y-%m-%d %H:%M")))

    conn.commit()
    conn.close()


# -----------------------------------
# トップページ
# -----------------------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    total, correct, last_play = get_progress(session["user_id"])
    username = session["username"]

    return render_template("index.html",
                           username=username,
                           total=total,
                           correct=correct,
                           last_play=last_play)


# -----------------------------------
# 新規登録
# -----------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        pw_hash = generate_password_hash(password)

        conn = sqlite3.connect("chutan.db")
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, pw_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="すでに存在するユーザー名です")

        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------------
# ログイン
# -----------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="ユーザー名またはパスワードが違います")

    return render_template("login.html")


# -----------------------------------
# ログアウト
# -----------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------------
# クイズ開始
# -----------------------------------
@app.route("/quiz", methods=["GET"])
def quiz():
    if "user_id" not in session:
        return redirect(url_for("login"))

    df = pd.read_excel("static/Chutan.xlsx")

    # 10問ランダム抽出
    questions = df.sample(n=10).reset_index(drop=True)

    session["questions"] = questions.to_dict(orient="records")
    session["q_num"] = 0
    session["score"] = 0

    return redirect(url_for("question"))


# -----------------------------------
# 問題画面
# -----------------------------------
@app.route("/question")
def question():
    if "user_id" not in session:
        return redirect(url_for("login"))

    q_num = session["q_num"]
    questions = session["questions"]

    if q_num >= len(questions):
        return redirect(url_for("result"))

    row = questions[q_num]

    # Excel列名に完全対応
    word = row["語句"]
    pos = row["品詞"]
    correct = row["意味"]

    # 全データ読み込み（候補用）
    df = pd.read_excel("static/Chutan.xlsx")

    # 同じ品詞の候補を取得
    candidates = df[df["品詞"] == pos]

    # 3件未満なら補完
    if len(candidates) < 3:
        extra = df.sample(n=3 - len(candidates))
        candidates = pd.concat([candidates, extra])

    candidates = candidates.sample(n=3)

    choices = list(candidates["意味"])

    # 正解が含まれない場合は補強
    if correct not in choices:
        choices[random.randint(0, 2)] = correct

    random.shuffle(choices)

    return render_template("quiz.html",
                           q_num=q_num + 1,
                           total=len(questions),
                           word=word,
                           choices=choices,
                           correct=correct)


# -----------------------------------
# 回答処理
# -----------------------------------
@app.route("/answer", methods=["POST"])
def answer():
    selected = request.form["selected"]
    correct = request.form["correct"]

    if selected == correct:
        session["score"] += 1

    session["q_num"] += 1

    return redirect(url_for("question"))


# -----------------------------------
# 結果画面
# -----------------------------------
@app.route("/result")
def result():
    score = session["score"]
    total = len(session["questions"])

    # 成績記録
    update_progress(session["user_id"], total, score)

    return render_template("result.html", score=score, total=total)


# -----------------------------------
# メイン
# -----------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
