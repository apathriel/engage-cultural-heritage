#!/usr/bin/bash

python3 -m pip install --user virtualenv

python3 -m virtualenv env

source ./env/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

deactivate