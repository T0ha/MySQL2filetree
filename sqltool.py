#!/usr/bin/env python2
# -*-coding: utf-8 -*-
# -*- mode: python -*-

from MySQLdb import connect
from os.path import abspath
import os, shutil, argparse, sys, csv

def tablelist(db):
    cur = db.cursor()
    cur.execute("SHOW TABLES")
    return [t for (t,) in cur.fetchall()]

def filelist(db):
    files = [f[0:-4] for f in os.listdir(db)]
    return [f for f in set(files)]


def proclist(db, base):
    cur = db.cursor()
    cur.execute("SHOW PROCEDURE STATUS WHERE db='%s'" % base)
    return [t[1] for t in cur.fetchall()]

def funlist(db, base):
    cur = db.cursor()
    cur.execute("SHOW FUNCTION STATUS WHERE db='%s'" % base)
    return [t[1] for t in cur.fetchall()]

def viewlist(db):
    cur = db.cursor()
    cur.execute("SHOW FULL TABLES WHERE TABLE_TYPE LIKE 'VIEW'")
    return [t[0] for t in cur.fetchall()]

def apply_all(db, fun, objs, args):
    cur = db.cursor()
    for t in objs:
        fun(cur, t, **args)

def dump_table(cur, table, host="127.0.0.1", user="root", passwd="yoursuperpasswd", database="test", **args):
    os.system("mysqldump -h%s -u%s -p%s -d -r%stables/%s.sql %s %s" % (host, user, passwd, args['prefix'], table, database, table))
    cur.execute("""DESCRIBE %s""" % table)
    fields = [f[0] for f in cur.fetchall()]
    cur.execute("""SELECT * FROM %s""" % table)
    with open(args['prefix'] + "tables/%s.csv" % table, "w") as f:
        writer = csv.writer(f,lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(fields)
        writer.writerows(cur.fetchall())

def dump_view(cur, table, host="127.0.0.1", user="root", passwd="yoursuperpasswd", database="test", **args):
    os.system("mysqldump -h%s -u%s -p%s -d -r%sviews/%s.sql %s %s" % (host, user, passwd, args['prefix'], table, database, table))

def restore_table(cur, table, host="127.0.0.1", user="root", passwd="yoursuperpasswd", database="test", **args):
    try:
        os.system("mysql -h%s -u%s -p%s -D%s < %stables/%s.sql" %(host, user, passwd, database, args['prefix'], table))
        fname = "%s/tables/%s.csv" % (args['prefix'], table)
        with open(fname, 'r') as f:
            fields = ",".join([c for c in f.readline()[1:-2].split('","')])
            cur.execute("""LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '\' IGNORE 1 LINES (%s)""" % (abspath(fname), table, fields))
    except:
        print "Not all tables restored"
        print "Upgrade codebase before deploy"

def dump_proc(cur, proc, **args):
    cur.execute("""SHOW CREATE PROCEDURE `%s`""" % proc)
    pdef = "DROP PROCEDURE IF EXISTS `%s`;\nDELIMITER $$\n" % proc + cur.fetchall()[0][2] + "\n$$"
    with open(args['prefix'] + "procs/%s.sql" % proc, "w") as f:
        f.write(pdef)

def dump_fun(cur, fun, **args):
    cur.execute("""SHOW CREATE FUNCTION `%s`""" % fun)
    pdef = "DROP FUNCTION IF EXISTS `%s`;\nDELIMITER $$\n" % fun + cur.fetchall()[0][2] + "\n$$"
    with open(args['prefix'] + "funs/%s.sql" % fun, "w") as f:
        f.write(pdef)

def restore(_cur, obj, host="127.0.0.1", user="root", passwd="yoursuperpasswd", database="test", **args):
    #try:
        os.system("mysql -h%s -u%s -p%s -D%s < %ss/%s.sql" %(host, user, passwd, database, args['prefix'] + args['object'], obj))




def arg_parser(args):
    argparser = argparse.ArgumentParser(description = 'MySQL deployment tool')
    argparser.add_argument('action', type=str, choices=['dump', 'restore'], default='dump')
    argparser.add_argument('object', type=str, nargs='?', choices=['all', 'structure', 'table', 'proc', 'view', 'fun'], default='all')
    argparser.add_argument('name', type=str, nargs='?', default='*')
    argparser.add_argument('--host', '-H', type=str, default='127.0.0.1')
    argparser.add_argument('--user', '-u', type=str, default='root')
    argparser.add_argument('--passwd', '-p', type=str, default='yoursuperpasswd')
    argparser.add_argument('--database', '-d', type=str, default='test')
    argparser.add_argument('--prefix', '-D', type=str, default='./db/')
    return argparser.parse_args(sys.argv[1:])

if __name__ == '__main__':
    args = arg_parser(sys.argv[1:])
    print args
    db = connect(host=args.host, user=args.user, passwd=args.passwd, db=args.database)
    if args.action == 'dump':
        if args.object == 'all':
            apply_all(db, dump_table, tablelist(db), vars(args))
            apply_all(db, dump_view, viewlist(db), vars(args))
            apply_all(db, dump_proc, proclist(db, args.database), vars(args))
            apply_all(db, dump_fun, funlist(db, args.database), vars(args))
        elif args.object == 'structure':
            apply_all(db, dump_view, tablelist(db), vars(args))
            apply_all(db, dump_view, viewlist(db), vars(args))
            apply_all(db, dump_proc, proclist(db, args.database), vars(args))
            apply_all(db, dump_fun, funlist(db, args.database), vars(args))
        elif args.object == 'table':
            if args.name == '*':
                apply_all(db, dump_table, tablelist(db), vars(args))
            else:
                apply_all(db, dump_table, [args.name], vars(args))
        elif args.object == 'proc':
            if args.name == '*':
                apply_all(db, dump_proc, proclist(db, args.database), vars(args))
            else:
                apply_all(db, dump_proc, [args.name], vars(args))
        elif args.object == 'fun':
            if args.name == '*':
                apply_all(db, dump_fun, funlist(db, args.database), vars(args))
            else:
                apply_all(db, dump_fun, [args.name], vars(args))
        elif args.object == 'view':
            if args.name == '*':
                apply_all(db, dump_view, viewlist(db), vars(args))
            else:
                apply_all(db, dump_view, [args.name], vars(args))

    elif args.action == 'restore':
        if args.object == 'all':
            apply_all(db, restore_table, filelist('./tables'), vars(args))
            apply_all(db, restore, filelist('./views'), vars(args))
            apply_all(db, restore, filelist('./procs'), vars(args))
            apply_all(db, restore, filelist('./funs'), vars(args))
        elif args.object == 'structure':
            apply_all(db, restore, filelist('./tables'), vars(args))
            apply_all(db, restore, filelist('./views'), vars(args))
            apply_all(db, restore, filelist('./procs'), vars(args))
            apply_all(db, restore, filelist('./funs'), vars(args))
        elif args.object == 'table':
            if args.name == '*':
                apply_all(db, restore_table, filelist('./tables'), vars(args))
            else:
                apply_all(db, restore_table, [args.name], vars(args))
        elif args.object == 'proc':
            if args.name == '*':
                apply_all(db, restore, filelist('./procs'), vars(args))
            else:
                apply_all(db, restore, [args.name], vars(args))
        elif args.object == 'fun':
            if args.name == '*':
                apply_all(db, restore, filelist('./funs'), vars(args))
            else:
                apply_all(db, restore, [args.name], vars(args))
        elif args.object == 'view':
            if args.name == '*':
                apply_all(db, restore, filelist('./views'), vars(args))
            else:
                apply_all(db, restore, [args.name], vars(args))

    db.commit()
