@echo off
set PYTHONPATH = C:/Path/To/Your/Python/Env

start powershell /k "python ./web/backend/main.py"
start powershell /k "python ./main.py"

cd "./web/frontend"
yarn run dev
