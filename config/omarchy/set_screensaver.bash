#!/bin/bash

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  echo "Usage: $0 <screensaver_file>"
  echo "Replaces the current screensaver with the specified file."
  exit 0
fi

new_screensaver=$1
screensaver_dir="$XDG_CONFIG_HOME/omarchy/branding"

cp "$screensaver_dir/screensaver.txt" "$screensaver_dir/screensaver.txt.bk"

cp "$new_screensaver" "$screensaver_dir/screensaver.txt"

echo "Copied $new_screensaver to $screensaver_dir"
