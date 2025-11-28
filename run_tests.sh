#!/bin/bash

# This script runs all unittests in the tests folder

# Exit immediately if a command exits with a non-zero status
set -e

# Discover and run unittests explicitly specifying the tests directory
python3 -m unittest discover -s ./tests -p "*.py"
