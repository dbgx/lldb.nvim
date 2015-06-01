#!/bin/bash

set -e

TEST_DIR=$( dirname "${BASH_SOURCE[0]}" )
cd "$TEST_DIR"
gcc -g -o ab ab.c
nvim -c 'e term://python2\ -i\ test.py'
