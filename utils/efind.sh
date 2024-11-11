#!/bin/bash
# Define the efind_within_dates function
efind_within_dates() {
    # find files created between dates 
    # Usage: efind -d1 2017-01-01 -d2 2017-01-31
    # default d2 is today
    # print the files created between d1 and d2
    d1=""
    d2=$(date +%Y-%m-%d)
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            -d1)
                d1="$2"
                shift 2
                ;;
            -d2)
                d2="$2"
                shift 2
                ;;
            *)
                echo "Invalid option: $1" >&2
                shift
                ;;
        esac
    done

    echo "Debug: d1=$d1, d2=$d2" # Debug statement

    if [ -z "$d1" ]; then
        echo "Start date (d1) is required."
        exit 1
    fi
    # print the date 
    echo "Finding files created between $d1 and $d2"
    # sort the ouput order from oldest to newest
    find . -type f -newermt "$d1" ! -newermt "$d2"
}

while getopts ":hd:" opt; do
    case $opt in
        h)
            echo "Usage:"
            echo -e "\tefind -d \"2017-01-01 2017-01-31\"\tfind files created between dates."
            exit 0
            ;;  
        d)
            IFS=' ' read -r d1 d2 <<< "$OPTARG"
            efind_within_dates -d1 "$d1" -d2 "$d2"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done
