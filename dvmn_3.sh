#!/bin/bash

# Переходим в директорию с проектом
cd /home/wombatoff/dvmn_3

# Обновляем репозиторий
git pull

# Уведомление Rollbar о деплое
curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=c2eedbf883b644dca14781524e20688d \
  -F environment=production \
  -F revision=$(git log -n 1 --pretty=format:"%H") \
  -F local_username=$(whoami)

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем зависимости
python -m pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

# Накатываем миграции БД
python manage.py migrate

# Собираем статику
python manage.py collectstatic --no-input

# Установливаем пакеты Node.js
npm ci --dev
./node_modules/.bin/parcel watch bundles-src/index.js --dist-dir bundles --public-url="./"

# Перезапускаем gunicorn (убедитесь, что у вас настроена системная служба для gunicorn)
sudo systemctl restart gunicorn

# Перезапускаем Nginx
sudo systemctl restart nginx
