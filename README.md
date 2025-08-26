# Fakturama DB backup
Used to backup the IPV Fakturama database.

## Use
Intended to be used as a shell script for a cron job.
```bash
python3 fakturama_backup.py [options]
```

## Dependencies
1. [`mysqldump`](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html) must be installed and in the `PATH` environement variable.
2. Install python dependencies using `pip install -r requirements.txt`.

## Windows Task Scheduler
In Windows Task Scheduler, create a basic task whose action is to start a program. Set the
1. Program to run to the absolute path to Python. This can be found in `cmd` with the `where python` command. (The file selector may not work. It's best to just paste the path into the input.)
2. Arguments to `fakturama_backup.py` along with any arguments to pass to the script. e.g. `fakturama_backup.py -u <username> -p <password> -db <db>`.
3. Location to the directory containing the `fakturama_backup.py` script.
