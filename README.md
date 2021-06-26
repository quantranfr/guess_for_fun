
First run:

```
python manage.py makemigrations football
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Import data before going live:
- Login with superuser account
- Go to `Teams` and upload `raw_data_euro2021_teams.csv`
- Go to `Matches` and upload `matches_group_phase.csv`

Datamart:

```
> crontab -e
* * * * * /absolute/path/to/clan_progression.sh /absolute/path/to/db.sqlite3 2> /absolute/path/to/log
```

## Ref

Access management: https://learndjango.com/tutorials/django-login-and-logout-tutorial
