#!/bin/bash
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade virtualenv
python3 -m venv --clear venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
