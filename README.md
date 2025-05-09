# wedding_tg_bot

Wedding tg bot

# installation

```shell
git clone git@github.com:AsseylumVA/wedding_tg_bot.git
```

# settings

```shell
cp settings.dev.py settings.py
```

Now settings are located in the file `settings.py`
You need to configure `API Token` and `DB` Constants

# run on Docker

You need to install Docker before start.

```shell
docker compose up --build
```

# run locally

```shell
#linux
sudo apt update
sudo apt install redis-server
```

Configure `REDIS_DB` and `REDIS_USER_DATA_DB` in settings.py.\
Example:

```python
REDIS_DB = 'redis://localhost:6379/1'
REDIS_USER_DATA_DB = 'redis://localhost:6379/0'
```

```shell
cd wedding_tg_bot/
python3 -m venv env
. env/bin/activate
pip install -U pip
pip install -r requirements.txt

python3 aiogram_run.py
```