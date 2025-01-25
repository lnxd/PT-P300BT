#!/bin/bash

if [ $# -lt 2 ] || [ $# -gt 4 ]
   then echo "Usage: $(basename $0)" '"label to print" /dev/ttyS_serial_port_number [width_in_mm] [align]'
        echo "For multiple lines, separate text with | character (max 3 lines)"
        echo "Example: \"Line 1|Line 2|Line 3\""
        echo "Optional: Specify the printed text width in millimeters (e.g., 35 for 35mm width)"
        echo "Optional: Specify text alignment (left, center, right) - default: center"
        exit 1
fi

WIDTH_PARAM=""
if [ $# -ge 3 ]; then
    WIDTH_PARAM="--text-size $3"
fi

ALIGN_PARAM=""
if [ $# -eq 4 ]; then
    ALIGN_PARAM="--align $4"
fi

if [[ "$1" == *"|"* ]]; then
    if [[ "$1" =~ ^[A-Z0-9\ -|]+$ ]]; then
        echo "UPPERCASE MODE (bigger font) - Multiline"
        python3 printlabel.py "$2" "roboto.ttf" "$1" --multiline $WIDTH_PARAM $ALIGN_PARAM
    else
        echo "standard mode - Multiline"
        python3 printlabel.py "$2" "roboto.ttf" "$1" --multiline $WIDTH_PARAM $ALIGN_PARAM
    fi
else
    if [[ "$1" =~ ^[A-Z0-9\ -]+$ ]]; then
        echo "UPPERCASE MODE (bigger font)"
        python3 printlabel.py "$2" "roboto.ttf" "$1" $WIDTH_PARAM $ALIGN_PARAM
    else
        echo "standard mode"
        python3 printlabel.py "$2" "roboto.ttf" "$1" $WIDTH_PARAM $ALIGN_PARAM
    fi
fi

exit 0
