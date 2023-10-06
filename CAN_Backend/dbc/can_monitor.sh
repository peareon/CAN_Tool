#!/bin/bash

export PYTHONPATH=".."
ssh $1 "candump -t a can0" | python3 can_monitor.py
