#!/bin/bash
set -e

echo "Pulling from repositories"
git pull origin master

echo "Installing dependencies..."
./.venv/bin/pip3 install -r requirements.txt
npm ci --dev

echo "Setting up django..."
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
./.venv/bin/python3 manage.py collectstatic --noinput
./.venv/bin/python3 manage.py migrate --noinput

echo "Restarting daemons..."
systemctl restart starburger-server.service

echo "Reporting to Rollbar..."
HASH=$(git rev-parse HEAD)
MESSAGE=$(git log -1 --pretty=%B)
POST_SERVER_ACCESS_TOKEN=823f6b168ba940c480e4b79c1a76eef8
ENVIRONMENT=production-yukari
curl -H "X-Rollbar-Access-Token: ${POST_SERVER_ACCESS_TOKEN}" -H "Content-Type: application/json" -X POST "https://api.rollbar.com/api/1/deploy" -d "{\"environment\": \"${ENVIRONMENT}\", \"revision\": \"${HASH}\", \"comment\": \"${MESSAGE}\", \"status\": \"succeeded\"}"

echo "Done."



