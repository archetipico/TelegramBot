#!/bin/sh

echo "> Initialization"

# Create files
touch ./orders/utility/admins
touch ./orders/utility/mali
touch ./orders/utility/secrets
touch ./orders/utility/superadmins
touch ./orders/utility/usage.csv
echo "> Files created"

# Set permissions
chmod 755 ./orders/utility/superadmins ./orders/utility/admins ./orders/utility/usage.csv ./orders/utility/mali
chmod 644 ./orders/utility/secrets
echo "> Permissions set"

# Populate files
echo -e "meets a dragon and wins\nmeets a dragon and loses" > ./orders/utility/mali
echo "> Mali populated"

echo -e "CMD;USER;TIME;OUT;FULL_CMD;ERR" > ./orders/utility/usage.csv
echo "> Usage initialized"

# Download yolov4-tiny files
wget -q -N -P ./orders/utility https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/coco.names
wget -q -N -P ./orders/utility https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights
wget -q -N -P ./orders/utility https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg
echo "> Downloaded yolov4-tiny files"

echo "> Finished"
