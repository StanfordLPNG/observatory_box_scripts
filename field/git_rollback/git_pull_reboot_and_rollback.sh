#!/bin/bash -xe
sudo /home/pi/diagnostic_box_scripts/field/mount_readwrite.sh
git pull --ff-only
crontab /home/pi/diagnostic_box_scripts/field/initialization/user_cron_jobs
grep -v '/sbin/shutdown' /home/pi/diagnostic_box_scripts/field/initialization/root_cron_jobs > /tmp/newcrontab # put crontab lines that aren't shutdown into temp file
cat /home/pi/diagnostic_box_scripts/field/git_rollback/root_git_rollback_cron_job >> /tmp/newcrontab # add git rollback lines
sudo crontab /tmp/newcrontab
sudo reboot
