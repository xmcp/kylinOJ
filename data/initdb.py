#coding=utf-8
import sqlite3
import os
import const

db=sqlite3.connect(os.path.join('..',const.DBFILE))
cur=db.cursor()
cur.executescript('''

CREATE TABLE IF NOT EXISTS problems (
    id integer primary key,
    title TEXT not null,
    subtitle TEXT,
    acuser INT not null default 0,
    alluser INT not null default 0,
    description TEXT,
    memory int not null,
    time int not null
);

CREATE TABLE IF NOT EXISTS solutions (
  id integer primary key,
  uid int not null,
  pid int not null,
  accepted int not null,
  status text,
  time int not null,
  acpoint int not null,
  allpoint int not null
);

CREATE TABLE IF NOT EXISTS users (
  id integer primary key,
  username text unique not null,
  password text not null,
  nick text not null,
  description text default '',
  acprob int not null default 0,
  allprob int not null default 0,
  disabled int not null default 0
);

''')
db.commit()
print('=== done')