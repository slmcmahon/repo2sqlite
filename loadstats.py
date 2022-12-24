import os
import sys
import sqlite3
import re
import subprocess
from datetime import datetime, timedelta

DEFAULT_DB_PATH = os.path.join(os.path.expanduser('~'), 'commits.sqlite3')
COMMITS_TABLE = """create table if not exists commits (
    id text unique, 
    repo_name text, 
    summary text, 
    author_name text, 
    author_email text, 
    committed_on datetime    
);
"""
FILES_TABLE = """create table if not exists commit_files (
    id text, 
    name text, 
    added int, 
    deleted int,
    constraint fk_id
        foreign key (id)
        references commits (id)
        on delete cascade
);
"""


def add_commit(csr, id, repo_name, summary, author_name, author_email, committed_on):
    csr.execute("insert into commits (id, repo_name, summary, author_name, author_email, committed_on) values (?, ?, ?, ?, ?, ?)",
                (id, repo_name, summary, author_name, author_email, committed_on))


def add_commit_file(csr, id, name, added, deleted):
    csr.execute("insert into commit_files (id, name, added, deleted) values (?, ?, ?, ?)",
                (id, name, added, deleted))


def get_repo_name():
    if not os.path.exists(".git"):
        return None

    s = os.popen("git remote get-url --push origin")
    url = s.read().strip().split('/')
    return url[-1].split('.')[0]


def create_tables(csr):
    csr.execute(COMMITS_TABLE)
    csr.execute(FILES_TABLE)


def get_db_path():
    if len(sys.argv) == 1:
        return DEFAULT_DB_PATH
    else:
        actual_path = None
        proposed_path = sys.argv[1]
        try:
            with open(proposed_path, 'x') as tempfile:
                actual_path = proposed_path
        except:
            print(f'The proposed path {proposed_path} is not a valid path.')
            return None
        return actual_path


def get_last_modified(conn, repo_name):
    csr = conn.cursor()
    csr.execute(
        "select max(committed_on) from commits where repo_name = ?", (repo_name,))
    last_mod = csr.fetchone()[0]
    if not last_mod:
        return None
    else:
        dt = datetime.strptime(last_mod, '%Y-%m-%dT%H:%M:%S')
        return dt + timedelta(seconds=1)


def main():
    repo_name = get_repo_name()
    if not repo_name:
        exit(1)

    db_path = get_db_path()
    if not db_path:
        print(f'{sys.argv[1]} is not a valid path.  Exiting')
        exit(1)

    commit_pattern = re.compile("\|(.*?)\|\|(.*?)\|\|(.*?)\|\|(.*?)\|\|(.*)")
    file_pattern = re.compile("([\d|-]*)\s*([\d|-]*)\s*(.*)")

    print(f'Using DB Path: {db_path}')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_tables(cursor)

    last_modified = get_last_modified(conn, repo_name)
    procArgs = ["git", "log", "--date=local",
                "--pretty=format:|%h||%s||%an||%ae||%aI", "--numstat"]
    if last_modified:
        # if last_modified actually contains a date, then we want to add new records
        # after that date, so we insert that arg here.
        procArgs.insert(3, f'--after={last_modified}')

    # print(f'Executing: {" ".join(procArgs)}')
    log_data = subprocess.Popen(
        procArgs, stdout=subprocess.PIPE, encoding="utf-8")

    commit = None
    for line in log_data.stdout.readlines():
        line = line.strip()

        if len(line) == 0:
            continue

        if line[0] == '|':
            m = commit_pattern.match(line)
            commit = m[1]
            print(f'Writing data for {commit} for {repo_name}.')
            ts = m[5][:-6]
            add_commit(cursor, commit, repo_name, m[2], m[3], m[4], ts)
        else:
            m = file_pattern.match(line)
            add_commit_file(cursor, commit, m[3], m[1], m[2])
        
    print(f'Database is up to date for {repo_name}.')
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
