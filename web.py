from flask import Flask, request, render_template_string, send_file, jsonify
import yt_dlp
import os
import uuid
import re
from textblob import TextBlob

app = Flask(__name__)

# --- Configuration ---
# Directory to store downloaded files temporarily.
DOWNLOADS_DIR = "downloads"
# Create the directory if it doesn't exist.
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# --- Frontend HTML with Tailwind CSS ---
# The user interface is designed to be simple, modern, and responsive.
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts: Inter for a clean, modern look -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        /* Simple transition for better UX */
        .transition-all {
            transition: all 0.3s ease-in-out;
        }
    </style>
</head>
<body class="bg-gray-900 text-white flex items-center justify-center min-h-screen">
    <div class="w-full max-w-2xl mx-auto p-4 md:p-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl md:text-5xl font-bold mb-2">YouTube Video Downloader</h1>
            <p class="text-gray-400 text-lg">Quickly download YouTube videos as MP4 or just the audio as MP3.</p>
        </div>

        <!-- Main Form -->
        <div class="bg-gray-800 p-6 rounded-xl shadow-lg">
            <form id="download-form">
                <div class="flex flex-col sm:flex-row gap-4 mb-4">
                    <input type="url" id="youtube-url" name="url" class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="Paste YouTube URL here" required>
                    <select id="format" name="format" class="px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                        <option value="mp4">Video (MP4)</option>
                        <option value="mp3">Audio (MP3)</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-all">
                    Download
                </button>
            </form>
        </div>

        <!-- Status/Result Display Area -->
        <div id="status" class="text-center mt-6"></div>
        
        <!-- Explanation Section -->
        <div class="mt-12 text-left text-gray-400 max-w-xl mx-auto">
            <h3 class="font-semibold text-lg text-white mb-2">What's the difference?</h3>
            <p><strong class="text-gray-200">MP4:</strong> A versatile video file format that contains video, audio, and subtitles. It's the standard for web and mobile video, offering good quality with reasonable file sizes. Choose this if you want the full video.</p>
            <p class="mt-2"><strong class="text-gray-200">MP3:</strong> The most common audio file format. It contains only the sound from the video. Choose this if you just want to listen to the audio, like a song, podcast, or lecture.</p>
        </div>
    </div>

    <script>
        // JavaScript to handle form submission asynchronously
        const form = document.getElementById('download-form');
        const statusDiv = document.getElementById('status');
        const urlInput = document.getElementById('youtube-url');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = urlInput.value;
            const format = document.getElementById('format').value;
            
            if (!url) {
                statusDiv.innerHTML = `<p class="text-red-400">Please paste a YouTube URL.</p>`;
                return;
            }
            
            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                statusDiv.innerHTML = `<p class="text-red-400">Please enter a valid YouTube URL.</p>`;
                return;
            }

            // Show a loading message
            statusDiv.innerHTML = `
                <div class="flex items-center justify-center gap-2">
                    <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Processing your download... Please wait.</span>
                </div>`;

            try {
                // Send the request to the Flask backend
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, format: format }),
                });

                const result = await response.json();

                if (response.ok) {
                    // On success, create a download link
                    statusDiv.innerHTML = `
                        <div class="bg-gray-800 p-4 rounded-lg">
                            <p class="text-green-400 mb-3">Your file is ready!</p>
                            <p class="text-gray-300 mb-2">File: ${result.filename}</p>
                            <a href="/downloads/${result.filename}" class="inline-block bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition-all" download="${result.filename}">
                                Download ${result.filename.split('.').pop().toUpperCase()}
                            </a>
                        </div>
                    `;
                } else {
                    // On failure, display the error message
                    statusDiv.innerHTML = `<p class="text-red-400">Error: \${result.error}</p>`;
                }
            } catch (error) {
                // Handle network or unexpected errors
                statusDiv.innerHTML = `<p class="text-red-400">An unexpected error occurred. Please try again.</p>`;
                console.error('Fetch Error:', error);
            }
        });
    </script>
</body>
</html>
"""

# --- NLP + Cleaning Logic ---
def clean_title(title):
    return re.sub(r'[<>:"/\\|?*]', '', title)

def extract_metadata(title):
    parts = title.split("-")
    if len(parts) == 2:
        artist, song = parts[0].strip(), parts[1].strip()
    else:
        blob = TextBlob(title)
        words = blob.words
        if len(words) > 2:
            artist, song = words[0], " ".join(words[1:])
        else:
            artist, song = "Unknown", title
    return artist, song

# --- Flask Backend Logic ---

@app.route("/", methods=["GET"])
def index():
    """
    Handles the initial page load (GET).
    """
    # For GET requests, just render the main HTML page
    return render_template_string(HTML_TEMPLATE)

@app.route("/download", methods=["POST"])
def download():
    """
    Handles the form submission (POST).
    Downloads the video/audio based on the provided URL and format.
    """
    # Get data from the JSON request body sent by our JavaScript
    data = request.get_json()
    url = data.get("url")
    file_format = data.get("format", "mp4") # Default to mp4 if not specified

    if not url:
        return jsonify({"error": "Please provide a YouTube URL."}), 400

    # Generate a unique ID for the file to prevent conflicts
    unique_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOADS_DIR, f"{unique_id}.%(ext)s")

    ydl_opts = {
        "quiet": True, # Suppress console output
        "nocheckcertificate": True,
        "outtmpl": output_path,
    }

    try:
        # --- Configure options based on selected format ---
        if file_format == "mp3":
            # Options for extracting audio only
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192", # 192 kbps quality
                }],
            })
            ext = "mp3"
        else: # Default to mp4
            # Options for downloading video + audio and merging
            ydl_opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            })
            ext = "mp4"

        # --- Download using yt-dlp ---
        # Using a with statement ensures resources are managed properly.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({"error": "Could not retrieve video information."}), 500
                
            raw_title = info.get("title", "downloaded_file")
            artist, song = extract_metadata(raw_title)
            cleaned_title = clean_title(raw_title)

        # Rename downloaded file to cleaned title
        downloaded_file = os.path.join(DOWNLOADS_DIR, f"{unique_id}.{ext}")
        final_filename = clean_title(f"{cleaned_title}.{ext}")
        final_path = os.path.join(DOWNLOADS_DIR, final_filename)
        
        # Check if the downloaded file exists before trying to rename it
        if not os.path.exists(downloaded_file):
            # If the file doesn't exist with the expected name, try to find it with a similar name
            # This can happen with some videos due to yt-dlp's naming conventions
            potential_files = [f for f in os.listdir(DOWNLOADS_DIR) if f.startswith(unique_id)]
            if potential_files:
                downloaded_file = os.path.join(DOWNLOADS_DIR, potential_files[0])
            else:
                return jsonify({"error": "Download failed: File not found."}), 500
                
        os.rename(downloaded_file, final_path)

        return jsonify({
            "filename": final_filename,
            "artist": artist,
            "song": song
        })
    except yt_dlp.utils.DownloadError as e:
        # Handle specific download errors (e.g., video unavailable)
        return jsonify({"error": "Failed to download video. Please check the URL and try again."}), 500
    except Exception as e:
        # Handle other unexpected errors
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/downloads/<filename>")
def download_file(filename):
    """
    Serves the downloaded file to the user for download.
    It's crucial to sanitize the filename to prevent security issues.
    """
    # Sanitize filename to prevent directory traversal attacks
    if ".." in filename or "/" in filename:
        return "Invalid filename", 400
        
    path = os.path.join(DOWNLOADS_DIR, filename)
    
    # Check if the file actually exists before trying to send it
    if os.path.exists(path):
        # as_attachment=True prompts the browser to download the file
        return send_file(path, as_attachment=True, download_name=filename)
    
    return "File not found.", 404

if __name__ == "__main__":
    # Running in debug mode is useful for development.
    # For production, use a proper WSGI server like Gunicorn or Waitress.
    app.run(debug=True)
