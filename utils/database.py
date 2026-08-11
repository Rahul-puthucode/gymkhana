import sqlite3
import os
from flask import g, current_app

def get_db():
    """Get database connection - try MySQL first, fallback to SQLite if MySQL fails."""
    if 'db' not in g:
        # Check if MySQL can connect
        db_type = os.environ.get('DB_TYPE', 'mysql').lower()
        use_mysql = False
        
        if db_type == 'mysql':
            try:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=current_app.config['DB_HOST'],
                    port=current_app.config['DB_PORT'],
                    user=current_app.config['DB_USER'],
                    password=current_app.config['DB_PASSWORD'],
                    database=current_app.config['DB_NAME'],
                    autocommit=True
                )
                g.db = conn
                g.db_driver = 'mysql'
                use_mysql = True
            except Exception as e:
                # Log or print notice and fallback
                use_mysql = False

        if not use_mysql:
            # Fallback to local SQLite database in app directory
            db_path = os.path.join(current_app.root_path, 'gymkhana.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            g.db = conn
            g.db_driver = 'sqlite'

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return list of dictionaries."""
    db = get_db()
    driver = getattr(g, 'db_driver', 'sqlite')
    
    if driver == 'mysql':
        # MySQL uses %s placeholder
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, args)
        rv = cursor.fetchall()
        cursor.close()
        return (rv[0] if rv else None) if one else rv
    else:
        # SQLite uses ? placeholder - adjust %s to ?
        sqlite_query = query.replace('%s', '?')
        cursor = db.cursor()
        cursor.execute(sqlite_query, args)
        rv = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute INSERT/UPDATE/DELETE query and return lastrowid / affected rows."""
    db = get_db()
    driver = getattr(g, 'db_driver', 'sqlite')
    
    if driver == 'mysql':
        cursor = db.cursor()
        cursor.execute(query, args)
        db.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    else:
        sqlite_query = query.replace('%s', '?')
        cursor = db.cursor()
        cursor.execute(sqlite_query, args)
        db.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

def init_db(app):
    """Register database teardown with Flask app."""
    app.teardown_appcontext(close_db)
