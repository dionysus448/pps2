import json
import os
import sys
import uuid

DATA_FILE = "dancers.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"dancers": [], "sessions": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def find_dancer(data, dancer_id):
    return next((d for d in data["dancers"] if d["id"] == dancer_id), None)


def run_web_ui():
    try:
        from flask import Flask, request, redirect, url_for, render_template_string
    except ImportError:
        print("Flask is not installed. Install it with: pip install flask")
        return

    app = Flask(__name__)

    base_css = '''
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#fafafa; margin:0; }
      .topbar { background:#fff; border-bottom:1px solid #dbdbdb; padding:12px 16px; position:sticky; top:0; z-index:10; display:flex; justify-content:space-between; align-items:center; }
      .topbar h1 { margin:0; font-size:22px; font-weight:600; letter-spacing:1px; }
      .container { max-width: 960px; margin: 22px auto; padding: 0 16px; }
      .row { display:flex; flex-wrap:wrap; margin:-8px; }
      .card { background:#fff; border:1px solid #dbdbdb; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.1); margin:8px; width:calc(33.333% - 16px); min-width:240px; }
      .card img { width:100%; border-bottom:1px solid #efefef; }
      .card .body { padding:12px; }
      .card h3 { margin:0 0 8px; font-size:18px; }
      .card p { margin:4px 0; color:#555; font-size:14px; }
      .btn { text-decoration:none; display:inline-block; padding:8px 14px; border:1px solid #dbdbdb; border-radius:6px; color:#262626; background:#fff; cursor:pointer; }
      .btn.primary { background:#3897f0; color:#fff; border:none; }
      .form-field { margin-bottom:10px; }
      .form-field label { display:block; font-size:14px; margin-bottom:4px; }
      .form-field input, .form-field textarea { width:100%; padding:8px; border:1px solid #dbdbdb; border-radius:6px; }
      .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap:14px; }
      @media (max-width: 880px) { .card { width:calc(50% - 16px); } }
      @media (max-width: 640px) { .card { width:100%; } }
    </style>
    '''

    @app.route("/")
    def home():
        data = load_data()
        return render_template_string(base_css + '''
            <div class="topbar">
                <h1>DanceBook</h1>
                <div>
                    <a class="btn" href="{{ url_for('add_dancer') }}">Add Dancer</a>
                    <a class="btn" href="{{ url_for('sessions') }}">Sessions</a>
                </div>
            </div>
            <div class="container">
                <h2>Discover Dancers</h2>
                <div class="grid">
                  {% for d in dancers %}
                    <div class="card">
                      <img src="https://source.unsplash.com/collection/3496975/500x300?sig={{ loop.index }}" alt="{{ d.name }}">
                      <div class="body">
                        <h3><a href="{{ url_for('profile', dancer_id=d.id) }}">{{ d.name }}</a></h3>
                        <p>{{ d.style }} · {{ d.experience_years }} yrs</p>
                        <p>Videos: {{ d.videos|length }} | Friends: {{ d.connections|length }}</p>
                      </div>
                    </div>
                  {% else %}
                    <p>No dancer profiles yet. Create one!</p>
                  {% endfor %}
                </div>
            </div>
        ''', dancers=data["dancers"])

    @app.route("/add", methods=["GET", "POST"])
    def add_dancer():
        if request.method == "POST":
            data = load_data()
            dancer = {
                "id": str(uuid.uuid4())[:8],
                "name": request.form.get("name", "").strip() or "Anonymous",
                "style": request.form.get("style", "").strip() or "Unknown",
                "experience_years": float(request.form.get("experience_years", 0) or 0),
                "videos": [],
                "accomplishments": [],
                "connections": []
            }
            data["dancers"].append(dancer)
            save_data(data)
            return redirect(url_for("home"))

        return render_template_string(base_css + '''
            <div class="topbar">
              <h1>DanceBook</h1>
              <a class="btn" href="{{ url_for('home') }}">Home</a>
            </div>
            <div class="container">
              <h2>Add Dancer Profile</h2>
              <form method="post">
                <div class="form-field"><label>Name</label><input name="name" required></div>
                <div class="form-field"><label>Dance Style</label><input name="style" required></div>
                <div class="form-field"><label>Years Experience</label><input type="number" min="0" step="0.1" name="experience_years" required></div>
                <button class="btn primary" type="submit">Create</button>
              </form>
            </div>
        ''')

    @app.route("/dancer/<dancer_id>", methods=["GET", "POST"])
    def profile(dancer_id):
        data = load_data()
        dancer = find_dancer(data, dancer_id)
        if not dancer:
            return "Dancer not found", 404

        message = ""

        if request.method == "POST":
            if request.form.get("action") == "video":
                title = request.form.get("video_title", "").strip()
                url = request.form.get("video_url", "").strip()
                if title and url:
                    dancer["videos"].append({"title": title, "url": url})
                    save_data(data)
                    return redirect(url_for('profile', dancer_id=dancer_id))
            elif request.form.get("action") == "accomplishment":
                text = request.form.get("accomplishment", "").strip()
                if text:
                    dancer["accomplishments"].append(text)
                    save_data(data)
                    return redirect(url_for('profile', dancer_id=dancer_id))
            elif request.form.get("action") == "connect":
                friend_id = request.form.get("friend_id", "").strip()
                friend = find_dancer(data, friend_id)
                if friend and friend_id != dancer_id and friend_id not in dancer["connections"]:
                    dancer["connections"].append(friend_id)
                    friend["connections"].append(dancer_id)
                    save_data(data)
                    return redirect(url_for('profile', dancer_id=dancer_id))
                message = "Could not connect. Check IDs or duplicate connection."

        friends = [find_dancer(data, c) for c in dancer["connections"] if find_dancer(data, c)]
        return render_template_string(base_css + '''
            <div class="topbar">
              <h1>DanceBook</h1>
              <a class="btn" href="{{ url_for('home') }}">Home</a>
            </div>
            <div class="container">
              <div class="card" style="margin-bottom:14px;">
                <div class="body">
                  <h2>{{ d.name }} ({{ d.style }})</h2>
                  <p>{{ d.experience_years }} years experience</p>
                  <p>Videos: {{ d.videos|length }} | Friends: {{ d.connections|length }}</p>
                </div>
              </div>

              <div class="card" style="margin-bottom:14px;">
                <div class="body">
                  <h3>Videos</h3>
                  <ul>{% for v in d.videos %}
                    <li><a href="{{ v.url }}" target="_blank">{{ v.title }}</a></li>
                  {% else %}<li>No videos yet</li>{% endfor %}</ul>
                  <form method="post">
                    <input type="hidden" name="action" value="video">
                    <div class="form-field"><label>Video Title</label><input name="video_title"></div>
                    <div class="form-field"><label>Video URL</label><input name="video_url"></div>
                    <button class="btn" type="submit">Add Video</button>
                  </form>
                </div>
              </div>

              <div class="card" style="margin-bottom:14px;">
                <div class="body">
                  <h3>Accomplishments</h3>
                  <ul>{% for a in d.accomplishments %}<li>{{ a }}</li>{% else %}<li>No accomplishments yet</li>{% endfor %}</ul>
                  <form method="post">
                    <input type="hidden" name="action" value="accomplishment">
                    <div class="form-field"><label>New accomplishment</label><textarea name="accomplishment"></textarea></div>
                    <button class="btn" type="submit">Add Accomplishment</button>
                  </form>
                </div>
              </div>

              <div class="card" style="margin-bottom:14px;">
                <div class="body">
                  <h3>Friends</h3>
                  <ul>{% for f in friends %}<li><a href="{{ url_for('profile', dancer_id=f.id) }}">{{ f.name }}</a></li>{% else %}<li>No friends yet</li>{% endfor %}</ul>
                  <form method="post">
                    <input type="hidden" name="action" value="connect">
                    <div class="form-field"><label>Friend dancer ID</label><input name="friend_id"></div>
                    <button class="btn" type="submit">Add Friend</button>
                  </form>
                </div>
              </div>

              <p style="color:red;">{{ message }}</p>
            </div>
        ''', d=dancer, friends=friends, message=message)

    @app.route("/sessions")
    def sessions():
        data = load_data()
        return render_template_string(base_css + '''
            <div class="topbar">
              <h1>DanceBook</h1>
              <a class="btn" href="{{ url_for('home') }}">Home</a>
            </div>
            <div class="container">
              <h2>Group Sessions</h2>
              <div class="grid">
                {% for s in sessions %}
                  <div class="card">
                    <div class="body">
                      <h3>{{ s.name }}</h3>
                      <p>ID: {{ s.id }}</p>
                      <p>Status: {{ s.status }}</p>
                      <p>Host: {{ s.host_name }}</p>
                      <p>Participants: {{ s.participants|length }}</p>
                    </div>
                  </div>
                {% else %}
                  <p>No sessions created yet.</p>
                {% endfor %}
              </div>
            </div>
        ''', sessions=[{
            **s,
            "host_name": (find_dancer(load_data(), s["host"])["name"] if find_dancer(load_data(), s["host"]) else "Unknown")
        } for s in load_data()["sessions"]])

    print("Starting web UI on http://127.0.0.1:5000")
    app.run(debug=False, port=5000)


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("web", "--web"):
        run_web_ui()
        return

    data = load_data()
    actions = {
        "1": ("List dancer profiles", lambda: list_dancers(data)),
        "2": ("Create dancer profile", lambda: add_dancer_cli(data)),
        "3": ("View dancer profile", lambda: view_dancer_cli(data)),
        "4": ("Add performance video", lambda: add_video_cli(data)),
        "5": ("Add accomplishment", lambda: add_accomplishment_cli(data)),
        "6": ("Connect dancers", lambda: connect_dancers_cli(data)),
        "7": ("Propose group session", lambda: propose_session_cli(data)),
        "8": ("List group sessions", lambda: list_sessions_cli(data)),
        "9": ("Quit", None)
    }

    while True:
        print("\n=== Dance Connect CLI ===")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        choice = input("Choose an option: ").strip()
        if choice not in actions:
            print("Invalid option.")
            continue
        if choice == "9":
            print("Bye!")
            break
        action = actions[choice][1]
        action()


def add_dancer_cli(data):
    name = input("Name: ").strip() or "Anonymous"
    style = input("Dance style: ").strip() or "Unknown"
    exp = input("Years of experience: ").strip() or "0"
    try:
        exp = float(exp)
    except ValueError:
        exp = 0
    data["dancers"].append({
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "style": style,
        "experience_years": exp,
        "videos": [],
        "accomplishments": [],
        "connections": []
    })
    save_data(data)
    print("Dancer added.")


def view_dancer_cli(data):
    dancer_id = input("Enter dancer ID: ").strip()
    dancer = find_dancer(data, dancer_id)
    if not dancer:
        print("Dancer not found.")
        return
    print(JSON_PRETTY(dancer))


def add_video_cli(data):
    dancer_id = input("Enter dancer ID: ").strip()
    dancer = find_dancer(data, dancer_id)
    if not dancer:
        print("Dancer not found.")
        return
    title = input("Video title: ").strip()
    url = input("Video URL: ").strip()
    dancer["videos"].append({"title": title, "url": url})
    save_data(data)
    print("Video saved.")


def add_accomplishment_cli(data):
    dancer_id = input("Enter dancer ID: ").strip()
    dancer = find_dancer(data, dancer_id)
    if not dancer:
        print("Dancer not found.")
        return
    text = input("Accomplishment: ").strip()
    dancer["accomplishments"].append(text)
    save_data(data)
    print("Accomplishment added.")


def connect_dancers_cli(data):
    id1 = input("Your dancer ID: ").strip()
    id2 = input("Friend dancer ID: ").strip()
    d1 = find_dancer(data, id1)
    d2 = find_dancer(data, id2)
    if not d1 or not d2 or id1 == id2:
        print("Invalid dancer IDs.")
        return
    if id2 not in d1["connections"]:
        d1["connections"].append(id2)
    if id1 not in d2["connections"]:
        d2["connections"].append(id1)
    save_data(data)
    print("Friend added.")


def propose_session_cli(data):
    name = input("Session name: ").strip()
    host_id = input("Host dancer ID: ").strip()
    host = find_dancer(data, host_id)
    if not host:
        print("Host not found.")
        return
    parts = input("Participants IDs comma sep: ").split(",")
    participants = [host_id] + [p.strip() for p in parts if p.strip() and find_dancer(data, p.strip())]
    participants = list(dict.fromkeys(participants))
    data["sessions"].append({"id": str(uuid.uuid4())[:8], "name": name, "host": host_id, "participants": participants, "status": "planned"})
    save_data(data)
    print("Session created.")


def list_sessions_cli(data):
    if not data["sessions"]:
        print("No sessions.")
        return
    for s in data["sessions"]:
        host = find_dancer(data, s["host"])
        print(f"- {s['id']} | {s['name']} | host: {host['name'] if host else 'Unknown'} | {len(s['participants'])} participants")


def JSON_PRETTY(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
