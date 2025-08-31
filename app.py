from flask import Flask, render_template, request, redirect, url_for, flash
from db import init_db, add_item, get_items, get_item, update_item, delete_item, add_note, get_notes

app = Flask(__name__)
app.secret_key = 'secret'

# create database
with app.app_context():
    init_db()

@app.route('/')
def index():
    """show all items with filtering and sorting"""
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    assignee_filter = request.args.get('assignee', '')
    
    items = get_items()
    
    # apply filters
    if status_filter:
        items = [item for item in items if item['status'] == status_filter]
    if priority_filter:
        items = [item for item in items if item['priority'] == int(priority_filter)]
    if assignee_filter:
        items = [item for item in items if assignee_filter.lower() in (item['assignee'] or '').lower()]
    
    return render_template('list.html', items=items,
                         current_status=status_filter,
                         current_priority=priority_filter,
                         current_assignee=assignee_filter)

@app.route('/add', methods=['GET', 'POST'])
def add():
    """add new item"""
    if request.method == 'POST':
        item_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'assignee': request.form['assignee'],
            'status': request.form['status'],
            'priority': int(request.form['priority'])
        }
        
        add_item(item_data)
        flash('item created!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit(item_id):
    """edit item"""
    if request.method == 'POST':
        item_data = {
            'id': item_id,
            'title': request.form['title'],
            'description': request.form['description'],
            'assignee': request.form['assignee'],
            'status': request.form['status'],
            'priority': int(request.form['priority'])
        }
        
        update_item(item_data)
        flash('item updated!', 'success')
        return redirect(url_for('index'))
    
    item = get_item(item_id)
    return render_template('edit.html', item=item)

@app.route('/view/<item_id>')
def view(item_id):
    """view item details"""
    item = get_item(item_id)
    notes = get_notes(item_id)
    return render_template('view.html', item=item, notes=notes)

@app.route('/delete/<item_id>')
def delete(item_id):
    """delete item"""
    delete_item(item_id)
    flash('item deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/add_note', methods=['POST'])
def add_comment():
    """add comment"""
    item_id = request.form['item_id']
    author = request.form['author']
    content = request.form['content']
    
    add_note(item_id, author, content)
    flash('comment added!', 'success')
    return redirect(url_for('view', item_id=item_id))

if __name__ == '__main__':
    app.run(debug=True)
