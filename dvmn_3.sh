#!/bin/bash

set -e # stop script execution on any error
set -o pipefail # consider errors in the pipeline

# Загрузка переменных окружения из файла .env
if [[ -f .env ]]; then
  source .env
fi

function deploy_failed {
  echo "Deployment failed! Notifying Rollbar..."
  curl https://api.rollbar.com/api/1/item/ \
    -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" \
    -d environment=production \
    -d level=error \
    -d framework=bash \
    -d language=bash \
    -d body="Deployment failed"
  exit 1
}

function deploy_succeeded {
  echo "Deployment succeeded! Notifying Rollbar..."
  curl https://api.rollbar.com/api/1/deploy/ \
    -F access_token=$ROLLBAR_ACCESS_TOKEN \
    -F environment=production \
    -F revision=$(git log -n 1 --pretty=format:"%H") \
    -F local_username=$(whoami)
}

trap 'deploy_failed' ERR

# Переходим в директорию с проектом
cd /home/wombatoff/dvmn_3

# Обновляем репозиторий
git pull --no-edit

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем зависимости
yes | python -m pip install --upgrade pip && yes | pip install -r requirements.txt --no-cache-dir

# Накатываем миграции БД
python manage.py migrate

# Собираем статику
python manage.py collectstatic --no-input

# Установливаем пакеты Node.js
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

# Перезапускаем gunicorn (убедитесь, что у вас настроена системная служба для gunicorn)
sudo systemctl restart gunicorn

# Отправляем уведомление о успешном деплое
deploy_succeeded
