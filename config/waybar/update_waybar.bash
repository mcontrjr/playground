#!/bin/bash

set -e

waybar_dir="$XDG_CONFIG_HOME/waybar"

mkdir -p "$waybar_dir/backup"
cp  "$waybar_dir/style.css" "$waybar_dir/config.jsonc" "$waybar_dir/backup/"
cp style.css config.jsonc $waybar_dir

echo "Copied waybar current waybar settings to $waybar_dir ✓"

pkill waybar
waybar &

sleep 0.5
echo "Restart Waybar 🗖"
