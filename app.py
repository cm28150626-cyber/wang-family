from flask import Flask, request, jsonify, send_from_directory
import os, time, psycopg2, psycopg2.extras, json

app = Flask(__name__, static_folder='static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            name TEXT,
            content TEXT,
            category TEXT,
            image TEXT,
            likes INTEGER DEFAULT 0,
            created_at BIGINT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            name TEXT,
            content TEXT,
            created_at BIGINT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'index.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    category = request.args.get('category', '')
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if category:
        cur.execute('SELECT * FROM posts WHERE category=%s ORDER BY created_at DESC', (category,))
    else:
        cur.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = [dict(r) for r in cur.fetchall()]
    for p in posts:
        cur.execute('SELECT * FROM comments WHERE post_id=%s ORDER BY created_at ASC', (p['id'],))
        p['comments'] = [dict(c) for c in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    d = request.json
    if not d.get('name') or not d.get('content') or not d.get('category'):
        return jsonify({'error': '請填寫所有欄位'}), 400
    post_id = str(int(time.time() * 1000))
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO posts (id, name, content, category, image, likes, created_at) VALUES (%s,%s,%s,%s,%s,0,%s)',
        (post_id, d['name'][:20], d['content'][:500], d['category'], d.get('image',''), int(time.time()))
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': post_id, 'name': d['name'], 'content': d['content'],
                    'category': d['category'], 'image': d.get('image',''),
                    'likes': 0, 'comments': [], 'created_at': int(time.time())})

@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE posts SET likes=likes+1 WHERE id=%s RETURNING likes', (post_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if row:
        return jsonify({'likes': row[0]})
    return jsonify({'error': '找不到貼文'}), 404

@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    d = request.json
    if not d.get('name') or not d.get('content'):
        return jsonify({'error': '請填寫暱稱和留言'}), 400
    cid = str(int(time.time() * 1000))
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO comments (id, post_id, name, content, created_at) VALUES (%s,%s,%s,%s,%s)',
        (cid, post_id, d['name'][:20], d['content'][:200], int(time.time()))
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': cid, 'name': d['name'], 'content': d['content'], 'created_at': int(time.time())})

if DATABASE_URL:
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
