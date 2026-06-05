from flask import Flask, request, session, redirect, render_template_string
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "brainbattle_pro_secret"

# ---------------- DB ----------------
conn = sqlite3.connect("brain.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
username TEXT,
password TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS scores(
id INTEGER PRIMARY KEY,
username TEXT,
score INTEGER,
total INTEGER,
level TEXT
)""")

conn.commit()

# ---------------- QUESTIONS ----------------
def generate_questions(level):
    qs = []

    for i in range(100):
        if level == "easy":
            a, b = random.randint(1, 10), random.randint(1, 10)
            op = "+"
            ans = a + b

        else:
            a, b = random.randint(10, 50), random.randint(1, 20)
            op = random.choice(["+", "-", "*"])

            if op == "+":
                ans = a + b
            elif op == "-":
                ans = a - b
            else:
                ans = a * b

        qs.append((f"{a} {op} {b}", ans))

    return qs


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
    body{
        margin:0;
        font-family:Arial;
        background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
        text-align:center;
        color:white;
    }

    h1{
        margin-top:80px;
        font-size:50px;
        color:#00ffcc;
        text-shadow:0 0 20px #00ffcc;
    }

    button{
        padding:15px;
        width:80%;
        max-width:250px;
        margin:10px;
        border:none;
        border-radius:10px;
        font-size:18px;
        cursor:pointer;
    }

    .a{background:#00ffcc;}
    .b{background:#ffcc00;}
    .c{background:#ff4444;}
    </style>
    </head>

    <body>
    <h1>🧠 Brain Battle</h1>
    <p>Learn • Play • Win</p>

    <a href="/login"><button class="a">Login</button></a>
    <a href="/signup"><button class="b">Signup</button></a>
    <a href="/leaderboard"><button class="c">Leaderboard</button></a>

    <hr>

    <p>👨‍💻 Creator: Soham Lokhande</p>
    <p>🌐 Brain Battle</p>
    </body>
    </html>
    """)


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        c.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
        conn.commit()

        return redirect("/login")

    return """
    <h2>Signup</h2>
    <form method="post">
    Username: <input name="username"><br><br>
    Password: <input type="password" name="password"><br><br>
    <button>Signup</button>
    </form>
    """


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user = c.fetchone()

        if user:
            session["user"] = u
            return redirect("/quiz")

    return """
    <h2>Login</h2>
    <form method="post">
    Username: <input name="username"><br><br>
    Password: <input type="password" name="password"><br><br>
    <button>Login</button>
    </form>
    """


# ---------------- QUIZ SETUP ----------------
@app.route("/quiz", methods=["GET","POST"])
def quiz():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        session["level"] = request.form["level"]
        session["total"] = int(request.form["total"])
        session["questions"] = generate_questions(session["level"])
        session["q_index"] = 0
        session["score"] = 0

        return redirect("/play")

    return """
    <body style="text-align:center;background:#111;color:white;font-family:Arial;">
    <h1>Choose Mode</h1>

    <form method="post">

    <h3>Difficulty</h3>
    <select name="level">
        <option value="easy">🟢 Easy</option>
        <option value="hard">🔴 Hard</option>
    </select>

    <h3>Questions</h3>
    <select name="total">
        <option value="10">10</option>
        <option value="20">20</option>
        <option value="30">30</option>
        <option value="50">50</option>
        <option value="100">100</option>
    </select>

    <br><br>
    <button>Start</button>
    </form>
    </body>
    """


# ---------------- LIVE QUIZ (KAHOOT STYLE) ----------------
@app.route("/play", methods=["GET","POST"])
def play():

    if request.method == "POST":
        ans = request.form["ans"]

        q_index = session["q_index"]
        q = session["questions"][q_index]

        if ans and int(ans) == q[1]:
            session["score"] += 1

        session["q_index"] += 1

        if session["q_index"] >= session["total"]:
            return redirect("/result")

    q_index = session["q_index"]
    q = session["questions"][q_index]

    return f"""
    <body style="background:#000;color:#00ffcc;text-align:center;font-family:Arial;">
    <h2>Question {q_index+1}</h2>

    <h1>{q[0]}</h1>

    <form method="post">
    <input name="ans" style="padding:10px;font-size:18px;">
    <br><br>
    <button>Next</button>
    </form>
    </body>
    """


# ---------------- RESULT ----------------
@app.route("/result")
def result():
    u = session["user"]
    score = session["score"]
    total = session["total"]
    level = session["level"]

    c.execute("INSERT INTO scores(username,score,total,level) VALUES(?,?,?,?)",
              (u,score,total,level))
    conn.commit()

    return f"""
    <body style="text-align:center;background:#111;color:white;font-family:Arial;">
    <h1>🏆 Result</h1>

    <h2>{u}</h2>
    <h2>{score}/{total}</h2>

    <h3>Level: {level}</h3>

    <div style="border:2px solid #00ffcc;width:300px;margin:auto;padding:20px;">
        <h2>📜 Certificate</h2>
        <p>{u} completed Brain Battle</p>
        <h3>Score: {score}/{total}</h3>
    </div>

    <br>
    <a href="/quiz">Play Again</a>
    </body>
    """


# ---------------- LEADERBOARD ----------------
@app.route("/leaderboard")
def leaderboard():

    c.execute("""
    SELECT username, SUM(score)
    FROM scores
    GROUP BY username
    ORDER BY SUM(score) DESC
    """)

    data = c.fetchall()

    html = """
    <body style="background:#000;color:#00ffcc;text-align:center;font-family:Arial;">
    <h1>🏆 Global Leaderboard</h1>
    """

    i = 1
    for d in data:
        html += f"<h3>{i}. {d[0]} - {d[1]}</h3>"
        i += 1

    html += "<br><a href='/'>Home</a></body>"
    return html


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)