import os
import time
import psycopg2
from sqlalchemy import create_engine, text, event
from massive_client import get_client

_engine = None
_postgres_password = None
_last_password_refresh = 0

def _get_connection_params():
    return {
        'host': os.environ['PGHOST'],
        'database': os.environ['PGDATABASE'],
        'user': os.environ['PGUSER'],
        'port': os.environ.get('PGPORT', 5432)
    }

def _refresh_token():
    global _postgres_password, _last_password_refresh
    client = get_client()
    endpoint = os.environ.get('LAKEBASE_ENDPOINT')
    if not endpoint:
        raise ValueError('LAKEBASE_ENDPOINT environment variable not set')
    cred = client.postgres.generate_database_credential(endpoint=endpoint)
    _postgres_password = cred.token
    _last_password_refresh = time.time()
    return _postgres_password

def get_connection():
    params = _get_connection_params()
    params['password'] = _refresh_token()
    params['sslmode'] = 'require'
    return psycopg2.connect(**params)

def get_engine():
    global _engine
    if _engine is None:
        params = _get_connection_params()
        conn_string = f"postgresql+psycopg2://{params['user']}:@{params['host']}:{params['port']}/{params['database']}"
        _engine = create_engine(conn_string)
        
        @event.listens_for(_engine, 'do_connect')
        def provide_token(dialect, conn_rec, cargs, cparams):
            global _postgres_password, _last_password_refresh
            if _postgres_password is None or time.time() - _last_password_refresh > 900:
                _refresh_token()
            cparams['password'] = _postgres_password
            cparams['sslmode'] = 'require'
    
    return _engine

def run_query(sql, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

def run_write(sql, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        conn.commit()
        return result.rowcount