from flask import Flask, request, jsonify
from threading import Thread
import queue

# URL 큐
url_queue = queue.Queue()

flask_app = Flask(__name__)

@flask_app.route('/api/add-url', methods=['POST'])
def add_url():
    """브라우저 확장에서 URL 받기"""
    data = request.json
    url_queue.put(data)
    return jsonify({"status": "received"})

def run_flask():
    flask_app.run(host='127.0.0.1', port=8502, debug=False, use_reloader=False)

def start_api():
    """API 서버 시작"""
    Thread(target=run_flask, daemon=True).start()