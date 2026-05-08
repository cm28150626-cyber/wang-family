from flask import Flask, request, jsonify, send_from_directory
import json, os, time

app = Flask(__name__, static_folder='static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'posts': []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'index.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    category = request.args.get('category', '')
    data = load_data()
    posts = data['posts']
    if category:
        posts = [p for p in posts if p['category'] == category]
    return jsonify(sorted(posts, key=lambda x: x['time'], reverse=True))

@app.route('/api/posts', methods=['POST'])
def create_post():
    d = request.json
    if not d.get('name') or not d.get('content') or not d.get('category'):
        return jsonify({'error': '請填寫所有欄位'}), 400
    data = load_data()
    post = {
        'id': str(int(time.time() * 1000)),
        'name': d['name'][:20],
        'content': d['content'][:500],
        'category': d['category'],
        'time': int(time.time()),
        'likes': 0,
        'comments': []
    }
    data['posts'].insert(0, post)
    save_data(data)
    return jsonify(post)

@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    data = load_data()
    for p in data['posts']:
        if p['id'] == post_id:
            p['likes'] += 1
            save_data(data)
            return jsonify({'likes': p['likes']})
    return jsonify({'error': '找不到貼文'}), 404

@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    d = request.json
    if not d.get('name') or not d.get('content'):
        return jsonify({'error': '請填寫暱稱和留言'}), 400
    data = load_data()
    for p in data['posts']:
        if p['id'] == post_id:
            comment = {
                'id': str(int(time.time() * 1000)),
                'name': d['name'][:20],
                'content': d['content'][:200],
                'time': int(time.time())
            }
            p['comments'].append(comment)
            save_data(data)
            return jsonify(comment)
    return jsonify({'error': '找不到貼文'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
