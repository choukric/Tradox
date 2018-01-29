#!/usr/bin/env bash
export py_dir="/Users/Chafik/workspace/python/my_projects/crypto_currency/tradox"

while true; do
    python $py_dir/historizer.py -z $py_dir/data/histo/ -q ZEUR
    next=$(date -v +2H)
    echo "Relaunching at : $next"
    #sleep for 2h
    sleep 7200
done