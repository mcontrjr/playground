#!/bin/bash
#
sudo chmod 777 logs/

uvicorn main:app --port 8000 --host 0.0.0.0
