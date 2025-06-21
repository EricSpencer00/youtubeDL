from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>YouTubeDL Web</title>
<h2>Download YouTube Video</h2>
<form method=post>
  YouTube URL: <input type=text name=url size=60>
  <input type=submit value=Download>
</form>
{% if error %}
  <p style="color:red;">{{ error }}</p>
{% endif %}
{% if filename %}
  <a href="{{ url_for('download_file', filename=filename) }}">Download your file</a>
{% endif %}
"""

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    filename = None
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            error = "Please provide a YouTube URL."
        else:
            unique_id = str(uuid.uuid4())
            output_path = os.path.join(DOWNLOADS_DIR, f"{unique_id}.%(ext)s")
            ydl_opts = {
                "outtmpl": output_path,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "quiet": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    ext = info.get("ext", "mp4")
                    filename = f"{unique_id}.{ext}"
            except Exception as e:
                error = f"Error: {e}"
    return render_template_string(HTML_FORM, error=error, filename=filename)

@app.route("/downloads/<filename>")
def download_file(filename):
    path = os.path.join(DOWNLOADS_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)