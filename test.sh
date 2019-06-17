#!/usr/bin/env zsh

for f in $(ls test/*.m);
do
  echo "running $f";
  ./marshal < $f > ${f%.m}.c;
done

