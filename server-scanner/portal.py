from flask import Flask, render_template, send_from_directory, url_for
import sqlite3, json
import os

app = Flask(__name__)

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}


@app.route('/')
def index():
    conn = sqlite3.connect(settings["db_path"])
    cursor = conn.cursor()
    cursor.execute("SELECT filename, thumbnail_path FROM pictures")
    images = cursor.fetchall()
    conn.close()
    return render_template('index.html', images=images)

@app.route('/thumbnails/<filename>')
def thumbnails(filename):
    return send_from_directory(os.path.abspath(settings["thumbnail_dir"]), filename)

if __name__ == '__main__':
    app.run(debug=True)
