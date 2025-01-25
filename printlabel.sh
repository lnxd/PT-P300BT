#!/bin/bash

if [ $# -ne 2 ]
   then echo "Usage: $(basename $0)" '"label to print" /dev/ttyS_serial_port_number'
        echo "For multiple lines, separate text with | character (max 3 lines)"
        echo "Example: \"Line 1|Line 2|Line 3\""
        exit 1
fi

if [[ "$1" == *"|"* ]]; then
    if [[ "$1" =~ ^[A-Z0-9\ -|]+$ ]]; then
        echo "UPPERCASE MODE (bigger font) - Multiline"
        python3 printlabel.py "$2" "roboto.ttf" "$1" --multiline
    else
        echo "standard mode - Multiline"
        python3 printlabel.py "$2" "roboto.ttf" "$1" --multiline
    fi
else
    if [[ "$1" =~ ^[A-Z0-9\ -]+$ ]]; then
        echo "UPPERCASE MODE (bigger font)"
        python3 printlabel.py "$2" "roboto.ttf" "$1"
    else
        echo "standard mode"
        python3 printlabel.py "$2" "roboto.ttf" "$1"
    fi
fi

exit 0
