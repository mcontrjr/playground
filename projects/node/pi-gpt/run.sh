docker build -t mypy-app .
docker run -d -p 3000:3000 --env-file .env --name mypy-app mypy-app
