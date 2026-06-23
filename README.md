# sportsfacts

minimal django app for a sports facts feed.

## setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata seed
python manage.py createsuperuser
python manage.py runserver
```

open http://127.0.0.1:8000/ for the feed.

use http://127.0.0.1:8000/admin/ to insert facts, records, and tags.

each feed card has upvote/downvote buttons and share links for x, facebook, linkedin, whatsapp, plus a direct png image link.

you can also seed with the management command:

```bash
python manage.py seed_db
```

## tests

```bash
python manage.py test
```
