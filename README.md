### Virtual Environment

Generate venv folder
```
python3 -m venv venv
```

Activate virtual environment
```
source venv/bin/activate 
```

### How to install 

```
pip install -r requirements.txt
```


#### Generate migrations
alembic revision --autogenerate -m "Initial migration"

#### Run  Migrations
```
alembic upgrade head
```

### How to start app

```
uvicorn app.main:app --reload
```


### Codebase structure

```
cowabunga_ai/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── companies.py
│   │   ├── projects.py
│   │   ├── auth.py
│   │   ├── test_cases.py
│   ├── utils.py
├── alembic/
│   ├── ...
├── .env
├── requirements.txt

```