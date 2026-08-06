import os
from flask import Flask, request, jsonify, render_template
import lakebase

app = Flask(__name__)

def get_schema_name():
    app_name = 'support_ticket_system'
    client_id = os.environ['DATABRICKS_CLIENT_ID']
    return f"{app_name}_schema_{client_id}"

def init_database():
    schema = get_schema_name()
    
    lakebase.run_write(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    
    lakebase.run_write(f"""
        CREATE TABLE IF NOT EXISTS {schema}.tickets (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_by TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    lakebase.run_write(f"""
        CREATE TABLE IF NOT EXISTS {schema}.ticket_messages (
            id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES {schema}.tickets(id),
            message TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    try:
        schema = get_schema_name()
        tickets = lakebase.run_query(f"""
            SELECT id, title, status, created_by, created_at
            FROM {schema}.tickets
            ORDER BY created_at DESC
        """)
        return jsonify(tickets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    try:
        data = request.json
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        schema = get_schema_name()
        created_by = data.get('created_by', 'anonymous')
        
        lakebase.run_write(f"""
            INSERT INTO {schema}.tickets (title, created_by)
            VALUES (:title, :created_by)
        """, {'title': data['title'], 'created_by': created_by})
        
        tickets = lakebase.run_query(f"""
            SELECT id, title, status, created_by, created_at
            FROM {schema}.tickets
            ORDER BY id DESC
            LIMIT 1
        """)
        
        return jsonify(tickets[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    try:
        schema = get_schema_name()
        tickets = lakebase.run_query(f"""
            SELECT id, title, status, created_by, created_at
            FROM {schema}.tickets
            WHERE id = :ticket_id
        """, {'ticket_id': ticket_id})
        
        if not tickets:
            return jsonify({'error': 'Ticket not found'}), 404
        
        return jsonify(tickets[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    try:
        data = request.json
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        schema = get_schema_name()
        rowcount = lakebase.run_write(f"""
            UPDATE {schema}.tickets
            SET status = :status
            WHERE id = :ticket_id
        """, {'status': data['status'], 'ticket_id': ticket_id})
        
        if rowcount == 0:
            return jsonify({'error': 'Ticket not found'}), 404
        
        tickets = lakebase.run_query(f"""
            SELECT id, title, status, created_by, created_at
            FROM {schema}.tickets
            WHERE id = :ticket_id
        """, {'ticket_id': ticket_id})
        
        return jsonify(tickets[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/messages', methods=['GET'])
def get_ticket_messages(ticket_id):
    try:
        schema = get_schema_name()
        messages = lakebase.run_query(f"""
            SELECT id, ticket_id, message, author, created_at
            FROM {schema}.ticket_messages
            WHERE ticket_id = :ticket_id
            ORDER BY created_at ASC
        """, {'ticket_id': ticket_id})
        
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/messages', methods=['POST'])
def add_ticket_message(ticket_id):
    try:
        data = request.json
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        schema = get_schema_name()
        author = data.get('author', 'anonymous')
        
        lakebase.run_write(f"""
            INSERT INTO {schema}.ticket_messages (ticket_id, message, author)
            VALUES (:ticket_id, :message, :author)
        """, {'ticket_id': ticket_id, 'message': data['message'], 'author': author})
        
        messages = lakebase.run_query(f"""
            SELECT id, ticket_id, message, author, created_at
            FROM {schema}.ticket_messages
            WHERE ticket_id = :ticket_id
            ORDER BY id DESC
            LIMIT 1
        """, {'ticket_id': ticket_id})
        
        return jsonify(messages[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=8000)