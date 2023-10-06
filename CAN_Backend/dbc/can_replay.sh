#!/bin/bash

export PYTHONPATH=".."
cat $1 | python3 can_monitor.py
