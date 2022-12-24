repo2sqlite
==
Simple tool for loading git repo commit informaiton to an SQLite database

Usage
==

In a git managed directory, run:

```python3 repo2sqlite.py [/path/to/file.sqlite3]```

If no value is passed for the path to the SQLite file, it will create it in your home directory.

NOTES
==

This currently only works for git repos that have a remote defined.  I frequently rename a repository locally when I clone it, so to get the repository name, it will use the value of:

```git remote get-url --push origin``` 

So, for ```git@github.com:slmcmahon/repo2sqlite.git```, it will extract ```repo2sqlite```.

If the target database already exists, it will attempt to add to it.  Before runing ```git log```, it first checks the database to see if there are already entries for the current repository.  If so, it will get the date of the last recorded entry and use that as the ```--after``` argument to ```git log```.

CREDITS
==
This is loosly based on examples from the following blog post by [Will Schenk](https://github.com/wschenk) - [gitlog in sqlite](https://willschenk.com/articles/2020/gitlog_in_sqlite/)