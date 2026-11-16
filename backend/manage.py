"""Explicit local operator provisioning; never exposed through HTTP."""
import argparse
import os
from pathlib import Path
from backend.engine import Engine, identifier
import time


def set_staff(engine, email, enabled):
    with engine.transaction():
        user = engine.db.execute('SELECT id FROM users WHERE email=?', (email.strip().lower(),)).fetchone()
        if not user:
            raise ValueError('No registered user has that email.')
        if enabled:
            engine.db.execute('INSERT OR IGNORE INTO staff VALUES(?)', (user['id'],))
        else:
            engine.db.execute('DELETE FROM staff WHERE user_id=?', (user['id'],))
        engine.db.execute('INSERT INTO admin_audit VALUES(?,?,?,?,?)',
                          (identifier(), 'local_operator', 'staff_grant' if enabled else 'staff_revoke', user['id'], time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['grant-staff', 'revoke-staff'])
    parser.add_argument('email')
    parser.add_argument('--db', default=os.environ.get('NORTHSTAR_DB', str(Path(__file__).resolve().parent.parent / 'data/northstar.sqlite3')))
    args = parser.parse_args()
    if not Path(args.db).is_file():
        parser.error('Database does not exist. Start the app and register first.')
    engine = Engine(args.db)
    try:
        set_staff(engine, args.email, args.action == 'grant-staff')
        print('Staff permission updated and audited.')
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        engine.db.close()


if __name__ == '__main__':
    main()
