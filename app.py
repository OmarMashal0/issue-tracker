import os
from flask import Flask, render_template, request, redirect, url_for, flash
from db import (
    init_db, add_item, get_items, get_item, update_item,
    delete_item, add_note, get_notes, get_task_shares,
    share_task, get_shared_items, get_db
)
from api import api
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt

app = Flask(__name__)
api.init_app(app)
app.secret_key = os.urandom(24).hex()  # Unique random key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.execute('SELECT id, username, role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    db.close()
    return User(user['id'], user['username'], user['role']) if user else None


# create database
with app.app_context():
    init_db()


@app.route('/')
@login_required
def index():
    """show all items with filtering and sorting"""
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    assignee_filter = request.args.get('assignee', '')

    my_items = get_items(current_user.id)
    shared_items = get_shared_items(current_user.id)
    items = my_items + shared_items

    if status_filter:
        items = [item for item in items if item['status'] == status_filter]
    if priority_filter:
        items = [item for item in items if str(item['priority']) == str(priority_filter)]
    if assignee_filter:
        items = [item for item in items if assignee_filter.lower() in (item['assignee'] or '').lower()]

    return render_template('list.html', items=items,
                           current_status=status_filter,
                           current_priority=priority_filter,
                           current_assignee=assignee_filter)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        item_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'assignee': request.form['assignee'],
            'status': request.form['status'],
            'priority': int(request.form['priority']),
            'user_id': current_user.id
        }
        add_item(item_data)
        flash('Item created!', 'success')
        return redirect(url_for('index'))
    return render_template('add.html')


@app.route('/edit/<item_id>', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    item = get_item(item_id, current_user.id)
    if not item:
        flash("You don't have access to this task.", "error")
        return redirect(url_for('index'))

    # owner has full control
    is_owner = item['user_id'] == current_user.id
    can_edit_status = bool(item.get('can_edit_status'))
    can_edit_assignee = bool(item.get('can_edit_assignee'))

    if not (is_owner or can_edit_status or can_edit_assignee):
        flash("You don’t have permission to edit this task.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        updated_data = {'id': item_id}

        # Always allow owner full edits
        if is_owner:
            updated_data.update({
                'title': request.form['title'],
                'description': request.form['description'],
                'assignee': request.form['assignee'],
                'status': request.form['status'],
                'priority': int(request.form['priority'])
            })
        else:
            # Shared user, apply only permitted edits
            updated_data['title'] = item['title']
            updated_data['description'] = item['description']
            updated_data['priority'] = item['priority']

            updated_data['status'] = request.form['status'] if can_edit_status else item['status']
            updated_data['assignee'] = request.form['assignee'] if can_edit_assignee else item['assignee']

        update_item(updated_data)
        flash('Item updated!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', item=item,
                           is_owner=is_owner,
                           can_edit_status=can_edit_status,
                           can_edit_assignee=can_edit_assignee)


@app.route('/view/<item_id>')
@login_required
def view(item_id):
    item = get_item(item_id, current_user.id)
    if not item:
        flash("You don't have access to this task.", "error")
        return redirect(url_for('index'))

    notes = get_notes(item_id)
    shares = []
    if item['user_id'] == current_user.id:
        shares = get_task_shares(item_id)

    return render_template('view.html', item=item, notes=notes, shares=shares)


@app.route('/delete/<item_id>')
@login_required
def delete(item_id):
    item = get_item(item_id, current_user.id)
    if not item or item['user_id'] != current_user.id:
        flash("You don’t have permission to delete this task.", "error")
        return redirect(url_for('index'))

    delete_item(item_id)
    flash('Item deleted!', 'success')
    return redirect(url_for('index'))


@app.route('/add_note', methods=['POST'])
@login_required
def add_comment():
    item_id = request.form['item_id']
    author = request.form['author']
    content = request.form['content']

    add_note(item_id, author, content)
    flash('Comment added!', 'success')
    return redirect(url_for('view', item_id=item_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db = get_db()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        db.commit()
        db.close()
        flash('Registered!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()
        if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
            login_user(User(user['id'], user['username'], 'user'))
            flash('Logged in!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/update_status/<item_id>', methods=['POST'])
@login_required
def update_status(item_id):
    new_status = request.form['status']
    item = get_item(item_id, current_user.id)

    if not item:
        flash("You don't have access to this task.", "error")
        return redirect(url_for('index'))

    if item['user_id'] == current_user.id or item['can_edit_status']:
        db = get_db()
        db.execute('UPDATE items SET status = ? WHERE id = ?', (new_status, item_id))
        db.commit()
        db.close()
        flash("Status updated!", "success")
    else:
        flash("You don't have permission to change status.", "error")

    return redirect(url_for('view', item_id=item_id))


@app.route('/update_assignee/<item_id>', methods=['POST'])
@login_required
def update_assignee(item_id):
    new_assignee = request.form['assignee']
    item = get_item(item_id, current_user.id)

    if not item:
        flash("You don't have access to this task.", "error")
        return redirect(url_for('index'))

    if item['user_id'] == current_user.id or item['can_edit_assignee']:
        db = get_db()
        db.execute('UPDATE items SET assignee = ? WHERE id = ?', (new_assignee, item_id))
        db.commit()
        db.close()
        flash("Assignee updated!", "success")
    else:
        flash("You don't have permission to change assignee.", "error")

    return redirect(url_for('view', item_id=item_id))


@app.route('/share/<item_id>', methods=['GET', 'POST'])
@login_required
def share(item_id):
    item = get_item(item_id, current_user.id)
    if not item or item['user_id'] != current_user.id:
        flash("You can only share tasks you own.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        can_edit_status = 1 if 'can_edit_status' in request.form else 0
        can_edit_assignee = 1 if 'can_edit_assignee' in request.form else 0

        db = get_db()
        cursor = db.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()

        if not user:
            flash("User not found.", "error")
            return redirect(url_for('share', item_id=item_id))

        share_task(item_id, user['id'], can_edit_status, can_edit_assignee)
        flash(f"Task shared with {username}", "success")
        return redirect(url_for('view', item_id=item_id))

    return render_template('share.html', item=item)


@app.route('/unshare/<task_id>/<user_id>', methods=['POST'])
@login_required
def unshare(task_id, user_id):
    item = get_item(task_id, current_user.id)
    if not item or item['user_id'] != current_user.id:
        flash("You don’t have permission to unshare this task.", "error")
        return redirect(url_for('index'))

    db = get_db()
    db.execute('DELETE FROM task_shares WHERE task_id = ? AND user_id = ?', (task_id, user_id))
    db.commit()
    db.close()

    flash("User access removed.", "success")
    return redirect(url_for('view', item_id=task_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
