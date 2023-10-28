#!/bin/bash

find /backups/dumps/ -type f -mtime +30 -exec rm -f {} \;
echo "Файлы удалены"
