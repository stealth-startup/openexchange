install & initialization:

1 install django
2 install openexchangelib package
3 install bitcoin-python-api package
4 execute manage.py syncdb to initialize database for session support
5 execute manage.py initdata to initialize server's data
6 setup crontab or use process_block.sh to run "python manage.py processblock" for updating the server
