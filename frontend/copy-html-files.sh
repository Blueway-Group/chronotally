#!/bin/bash

find ../enerlinq_timesheets/public/frontend -type f -name "*.html" -print0 | while IFS= read -r -d $'\0' file; do
    # Calculate the relative path
    relative_path="${file#../enerlinq_timesheets/public/frontend/}"

    # Define the destination path
    dest="../enerlinq_timesheets/www/chronotally/$relative_path"

    # Create necessary subdirectories in www
    mkdir -p "$(dirname "$dest")"

    # Move the file
    mv -- "$file" "$dest"
done