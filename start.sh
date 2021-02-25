#!/bin/bash
if ! [ -f $1 ]
then
	exit 1
fi
source venv/bin/activate
python3 run.py > $1
