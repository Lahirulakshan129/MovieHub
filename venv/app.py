# app.py
from flask import Flask, render_template, jsonify, request, redirect
import subprocess, json, os, threading

app = Flask(__name__)
DATA_FILE = "data_1337x.json"
SCRAPING_STATUS = {}  

def load_data():
    if not os.path.exists(DATA_FILE):
        run_scraper_async(1)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content: return {}
            data = json.loads(content)
            return data if isinstance(data, dict) else {"1": data}
    except:
        run_scraper_async(1)
        return {}

def run_scraper_async(page):
    if SCRAPING_STATUS.get(page) == "running" or page < 1:
        return
    SCRAPING_STATUS[page] = "running"
    def task():
        print(f"Scraping page {page}...")
        env = os.environ.copy()
        env["SCRAPER_PAGE"] = str(page)
        try:
            subprocess.run(["python", "scraper.py"], env=env, check=True, cwd="venv")
            print(f"Page {page} saved")
        except Exception as e:
            print(f"Scrape failed: {e}")
        finally:
            SCRAPING_STATUS[page] = "done"
    threading.Thread(target=task, daemon=True).start()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    return render_template('index.html', page=page)

@app.route('/player')
def player():
    stream = request.args.get('stream')
    title = request.args.get('title', 'Movie Player')
    if not stream: return redirect('/')
    return render_template('player.html', stream=stream, title=title)

@app.route('/api/movies')
def get_movies():
    data = load_data()
    page = request.args.get('page', 1, type=int)
    page_key = str(page)

    movies = data.get(page_key, [])
    status = SCRAPING_STATUS.get(page, "done")

    
    if not movies:
        run_scraper_async(page)
        status = "running"

  
    next_page = page + 1
    next_key = str(next_page)
    if next_key not in data or not data[next_key]:
        run_scraper_async(next_page)

    return jsonify({
        "movies": movies,
        "status": status,
        "count": len(movies),
        "next_status": SCRAPING_STATUS.get(next_page, "none")
    })

@app.route('/api/refresh/<int:page>')
def refresh(page):
    run_scraper_async(page)
    return jsonify({"status": "started"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)