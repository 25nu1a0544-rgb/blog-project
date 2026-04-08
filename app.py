from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
import json, os, uuid

app = Flask(__name__)
app.secret_key = 'blogsecretkey2024'

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'users': {}, 'posts': []}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

QUOTES = [
    "The journey of a thousand miles begins with one step. — Lao Tzu",
    "Education is the most powerful weapon which you can use to change the world. — Nelson Mandela",
    "Not all those who wander are lost. — J.R.R. Tolkien",
    "Life is either a daring adventure or nothing at all. — Helen Keller",
    "The world is a book, and those who do not travel read only one page. — St. Augustine",
    "In learning you will teach, and in teaching you will learn. — Phil Collins",
    "Every experience, good or bad, is a priceless collector's item. — Isaac Marion",
]

@app.route('/')
def home():
    data = load_data()
    posts = data['posts']
    education = [p for p in posts if p['category'] == 'Education'][:3]
    experience = [p for p in posts if p['category'] == 'Personal Experience'][:3]
    travel = [p for p in posts if p['category'] == 'Traveling'][:3]
    return render_template('home.html', education=education, experience=experience, travel=travel)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = load_data()
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if username in data['users']:
            flash('Username already exists!', 'error')
        else:
            data['users'][username] = {
                'email': email,
                'password': password,
                'joined': str(date.today()),
                'streak': 0,
                'last_post_date': None
            }
            save_data(data)
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = load_data()
        username = request.form['username']
        password = request.form['password']
        user = data['users'].get(username)
        if user and user['password'] == password:
            session['user'] = username
            return redirect(url_for('home'))
        flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    username = session['user']
    user_posts = [p for p in data['posts'] if p['author'] == username]
    user = data['users'][username]
    total_likes = sum(len(p.get('likes', [])) for p in user_posts)
    total_comments = sum(len(p.get('comments', [])) for p in user_posts)
    return render_template('profile.html', user=user, username=username,
                           posts=user_posts, total_likes=total_likes,
                           total_comments=total_comments)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = load_data()
        username = session['user']
        today = str(date.today())
        user = data['users'][username]
        # Update streak
        if user['last_post_date'] == today:
            pass
        elif user['last_post_date'] and (date.today() - date.fromisoformat(user['last_post_date'])).days == 1:
            user['streak'] = user.get('streak', 0) + 1
        else:
            user['streak'] = 1
        user['last_post_date'] = today

        post = {
            'id': str(uuid.uuid4()),
            'title': request.form['title'],
            'category': request.form['category'],
            'content': request.form['content'],
            'author': username,
            'date': str(datetime.now().strftime('%B %d, %Y')),
            'likes': [],
            'comments': []
        }
        data['posts'].insert(0, post)
        save_data(data)
        flash('Post published!', 'success')
        return redirect(url_for('view_post', post_id=post['id']))
    return render_template('create_post.html')

@app.route('/post/<post_id>')
def view_post(post_id):
    data = load_data()
    post = next((p for p in data['posts'] if p['id'] == post_id), None)
    if not post:
        return redirect(url_for('home'))
    import random
    quote = random.choice(QUOTES)
    related = [p for p in data['posts'] if p['category'] == post['category'] and p['id'] != post_id][:3]
    return render_template('view_post.html', post=post, quote=quote, related=related)

@app.route('/like/<post_id>', methods=['POST'])
def like_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    for p in data['posts']:
        if p['id'] == post_id:
            user = session['user']
            if user in p['likes']:
                p['likes'].remove(user)
            else:
                p['likes'].append(user)
            break
    save_data(data)
    return redirect(request.referrer or url_for('view_post', post_id=post_id))

@app.route('/comment/<post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    thought = request.form.get('thought', '').strip()
    if thought:
        for p in data['posts']:
            if p['id'] == post_id:
                p['comments'].append({
                    'user': session['user'],
                    'text': thought,
                    'date': str(datetime.now().strftime('%b %d, %Y'))
                })
                break
        save_data(data)
    return redirect(url_for('view_post', post_id=post_id))

if __name__ == '__main__':
    app.run(debug=True)