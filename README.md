MySQL2filetree
==============

This is a small console tool written in Python.
It allows to dump MySQL database into easy to edit files and directories 
and push it back to MySQL server with your changes. 

### USAGE:
sqltool.py [options] [operation [object_type [object_name]]]
#### Operations:
dump or restore (default - dump)

#### Object Types:
* table
* view
* proc
* fun
* structure
* all (default)

#### Options:
- `-h` - short help
- `-H` or `--host` - MySQL host (default: 127.0.0.1)
- `-u` or `--user` - MySQL username (default: root)
- `-p` or `--password` - MySQL password (default: yoursuperpassword)
- `-d` or `--database` - MySQL database name (default: test)
- `-D` or `--prefix` - path to structure files (default: ./db/)

You are welcome with questions and suggestions.
Please email Shvein Anton: t0hashvein@gmail.com
