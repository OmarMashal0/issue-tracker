import sqlite3
from datetime import datetime

DATABASE = 'items.db'

def get_db():
    """get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """create tables"""
    db = get_db()
    
    # create items table with auto-incrementing id
    db.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            priority INTEGER DEFAULT 3,
            assignee TEXT
        )
    ''')
    
    # create notes table
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
    
    db.commit()
    db.close()

def add_item(item_data):
    """add new item"""
    db = get_db()
    cursor = db.execute('''
        INSERT INTO items (title, description, status, priority, assignee)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        item_data['title'], item_data['description'], 
        item_data['status'], item_data['priority'], item_data['assignee']
    ))
    db.commit()
    db.close()

def get_items():
    """get all items"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM items 
        ORDER BY 
            CASE status
                WHEN 'Open' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Done' THEN 3
                ELSE 4
            END,
            priority ASC
    ''')
    items = [dict(row) for row in cursor.fetchall()]
    db.close()
    return items

def get_item(item_id):
    """get single item"""
    db = get_db()
    cursor = db.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    db.close()
    
    if item:
        return dict(item)
    return None

def update_item(item_data):
    """update item"""
    db = get_db()
    db.execute('''
        UPDATE items 
        SET title = ?, description = ?, status = ?, priority = ?, assignee = ?
        WHERE id = ?
    ''', (
        item_data['title'], item_data['description'], item_data['status'],
        item_data['priority'], item_data['assignee'], item_data['id']
    ))
    db.commit()
    db.close()

def delete_item(item_id):
    """delete item"""
    db = get_db()
    
    # delete notes first
    db.execute('DELETE FROM notes WHERE item_id = ?', (item_id,))
    
    # delete item
    db.execute('DELETE FROM items WHERE id = ?', (item_id,))
    
    db.commit()
    db.close()

def add_note(item_id, author, content):
    """add comment"""
    db = get_db()
    db.execute('''
        INSERT INTO notes (item_id, author, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (item_id, author, content, datetime.now().isoformat()))
    db.commit()
    db.close()

def get_notes(item_id):
    """get comments for item"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM notes 
        WHERE item_id = ? 
        ORDER BY timestamp DESC
    ''', (item_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    db.close()
    return notes
