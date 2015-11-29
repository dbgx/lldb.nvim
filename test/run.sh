#!/bin/bash

set -e

TEST_DIR=$( python2 -c "from os.path import realpath
print realpath(\"$(dirname "$0")\")" ) # resolve symlinks
cd "$TEST_DIR"
gcc -g -o ab ab.c
nvim -c 'e term://python2\ -i\ test.py'
