#!/bin/bash

MOUNT_POINT=/home/michael/pi
REMOTE_IMAGE_DIRECTORY="$MOUNT_POINT/media/pi/76612328-6719-4441-8a40-d4894bf66cd0/"
LOCAL_IMAGE_ROOT_DIRECTORY=/media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses

# Mount the Pi's share drive to $MOUNT_POINT
sshfs -p 122 -o idmap=user pi@192.168.1.49:/ $MOUNT_POINT

scp -P 122 pi@192.168.1.49:projects/dressage-local/dressage.sqlite ./dressage.sqlite

python scripts/clean_files.py dressage.sqlite $LOCAL_IMAGE_ROOT_DIRECTORY/ready/ --destination $LOCAL_IMAGE_ROOT_DIRECTORY/bad/ --threshold 2
python scripts/clean_files.py dressage.sqlite $LOCAL_IMAGE_ROOT_DIRECTORY/ready/ --destination $LOCAL_IMAGE_ROOT_DIRECTORY/stars3/ --threshold 3
python scripts/clean_files.py dressage.sqlite $LOCAL_IMAGE_ROOT_DIRECTORY/ready/ --destination $LOCAL_IMAGE_ROOT_DIRECTORY/great --threshold 6

python scripts/remove_rated.py dressage.sqlite $REMOTE_IMAGE_DIRECTORY --verbose

python scripts/send_files.py $LOCAL_IMAGE_ROOT_DIRECTORY/ready/ $REMOTE_IMAGE_DIRECTORY -v --replace-existing --resize-over 1048576
