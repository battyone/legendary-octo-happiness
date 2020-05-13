#!/usr/bin/env bash

project=${1}

set -x

ags-prune-database $project

root=$HOME/data/logs/akamai/"$project"/incoming
mkdir -p $root

# Delete files that are older than a week.
#find "$root" -mtime +10080 | xargs -I fname rm fname

# Get any new log files.
ags-get-akamai-logs $project

# Process files just recently downloaded
files_to_process=$(find "$root" -mmin -60 -name "*.gz" | sort -t "-" -k 3,3n -k4,4 -k5,5n)

for logfile in $files_to_process
do
	ags-parse-logs $project --infile $logfile
done

ags-produce-graphics $project

