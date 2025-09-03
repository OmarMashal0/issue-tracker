import sqlite3
from datetime import datetime

DATABASE = 'items.db'


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            priority INTEGER DEFAULT 3,
            assignee TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            author TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT "user"
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS task_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            can_edit_status INTEGER DEFAULT 0,
            can_edit_assignee INTEGER DEFAULT 0,
            FOREIGN KEY(task_id) REFERENCES items(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    db.close()


def add_item(item_data):
    db = get_db()
    db.execute('''
        INSERT INTO items (title, description, status, priority, assignee, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        item_data['title'], item_data['description'],
        item_data['status'], item_data['priority'],
        item_data['assignee'], item_data['user_id']
    ))
    db.commit()
    db.close()


def get_items(user_id):
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM items
        WHERE user_id = ?
        ORDER BY 
            CASE status
                WHEN 'Open' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Done' THEN 3
                ELSE 4
            END,
            priority ASC
    ''', (user_id,))
    items = [dict(row) for row in cursor.fetchall()]
    db.close()
    return items


def get_item(item_id, user_id=None):
    db = get_db()
    if user_id:
        cursor = db.execute('''
            SELECT items.*,
                   COALESCE(task_shares.can_edit_status, 0) AS can_edit_status,
                   COALESCE(task_shares.can_edit_assignee, 0) AS can_edit_assignee
            FROM items
            LEFT JOIN task_shares 
                ON items.id = task_shares.task_id AND task_shares.user_id = ?
            WHERE items.id = ? AND (items.user_id = ? OR task_shares.user_id = ?)
        ''', (user_id, item_id, user_id, user_id))
    else:
        cursor = db.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    db.close()
    return dict(item) if item else None


def update_item(item_data):
    db = get_db()
    db.execute('''
        UPDATE items 
        SET title = ?, description = ?, status = ?, priority = ?, assignee = ?
        WHERE id = ?
    ''', (
        item_data['title'], item_data['description'], item_data['status'],
        item_data['priority'], item_data['assignee'],
        item_data['id']
    ))
    db.commit()
    db.close()


def delete_item(item_id, user_id):
    db = get_db()
    db.execute('DELETE FROM notes WHERE item_id = ?', (item_id,))
    rows = db.execute('DELETE FROM items WHERE id = ? AND user_id = ?', (item_id, user_id)).rowcount
    db.commit()
    db.close()
    return rows > 0


def add_note(item_id, author, content):
    db = get_db()
    db.execute('''
        INSERT INTO notes (item_id, author, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (item_id, author, content, datetime.now().isoformat()))
    db.commit()
    db.close()


def get_notes(item_id):
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM notes 
        WHERE item_id = ? 
        ORDER BY timestamp DESC
    ''', (item_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    db.close()
    return notes


def share_task(task_id, user_id, can_edit_status=0, can_edit_assignee=0):
    db = get_db()
    db.execute('''
        INSERT INTO task_shares (task_id, user_id, can_edit_status, can_edit_assignee)
        VALUES (?, ?, ?, ?)
    ''', (task_id, user_id, can_edit_status, can_edit_assignee))
    db.commit()
    db.close()


def get_shared_items(user_id):
    db = get_db()
    cursor = db.execute('''
        SELECT items.*, 
               task_shares.can_edit_status, 
               task_shares.can_edit_assignee,
               users.username AS owner_username
        FROM items
        JOIN task_shares ON items.id = task_shares.task_id
        JOIN users ON items.user_id = users.id
        WHERE task_shares.user_id = ?
    ''', (user_id,))
    items = [dict(row) for row in cursor.fetchall()]
    db.close()
    return items


def get_task_shares(task_id):
    db = get_db()
    cursor = db.execute('''
        SELECT users.username, task_shares.user_id,
               task_shares.can_edit_status, task_shares.can_edit_assignee
        FROM task_shares
        JOIN users ON users.id = task_shares.user_id
        WHERE task_shares.task_id = ?
    ''', (task_id,))
    shares = [dict(row) for row in cursor.fetchall()]
    db.close()
    return shares
