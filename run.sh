#!/bin/bash
python3 main.py --input "v4l2src device=/dev/video0 ! video/x-raw, format= GRAY8 ! videoconvert ! appsink max-buffers=1 drop=true " --ext_output > result.txt 