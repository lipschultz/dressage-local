#!/bin/bash

scp -P 122 pi@192.168.1.49:projects/dressage-local/dressage.sqlite ./dressage.sqlite

python scripts/clean_files.py dressage.sqlite /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/ready/ --destination /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/bad/ --threshold 2
python scripts/clean_files.py dressage.sqlite /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/ready/ --destination /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/stars3/ --threshold 3
python scripts/clean_files.py dressage.sqlite /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/ready/ --destination /media/michael/OS/Users/Michael/Desktop/Backup-Organized/horses/great --threshold 6
