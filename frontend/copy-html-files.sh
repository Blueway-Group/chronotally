#!/bin/bash

find ../chronotally/public/frontend -type f -name "*.html" -print0 | while IFS= read -r -d $'\0' file; do
    # Calculate the relative path
    relative_path="${file#../chronotally/public/frontend/}"

    # Define the destination path
    dest="../chronotally/www/chronotally/$relative_path"

    # Create necessary subdirectories in www
    mkdir -p "$(dirname "$dest")"

    # Move the file
    mv -- "$file" "$dest"
done