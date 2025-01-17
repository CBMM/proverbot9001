#!/usr/bin/env bash

set -e

[ "$#" -ne 1 ] || cd $1

comm -12 <(find -name "*.vo" -not -path "./_opam/*" | sed 's/.vo/.v/' | sort) <(find -name "*.v" -not -path "./_opam/*" | sort) > files.txt
