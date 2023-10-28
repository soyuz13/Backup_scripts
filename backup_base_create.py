#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from ftplib import FTP_TLS
from datetime import datetime
import pytz
from backup_settings import Log
from pathlib import Path
#from google_API import GoogleDrive
import datetime as dtime
import yadisk
from dotenv import load_dotenv
import os
import telebot

load_dotenv()
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
TLG_TOKEN = os.getenv('TLG_TOKEN')
TLG_CHAT_ID = os.getenv('TLG_CHAT_ID')
BASE_HOST_IP = os.getenv('BASE_HOST_IP')
BASE_HOST_PORT = os.getenv('BASE_HOST_PORT')
BASE_HOST_USER = os.getenv('BASE_HOST_USER')
BASE_HOST_PASS = os.getenv('BASE_HOST_PASS')


def send_tlg_message(msg):
    bot = telebot.TeleBot(token=TLG_TOKEN)
    msg_id = bot.send_message(os.getenv('TLG_CHAT_ID'), msg, parse_mode='HTML').message_id
    return msg_id


def copy_base(base_filename, path_to_save):
    Log.logger.info('Соединяемся по FTP и копируем базу на сервер...')
    try:
        ftp = FTP_TLS()
        ftp.connect(BASE_HOST_IP, int(BASE_HOST_PORT), 10)
        ftp.login(BASE_HOST_USER, BASE_HOST_PASS)
        ftp.prot_p()
        Log.logger.debug(str(path_to_save))
        with open(path_to_save, 'wb') as f:
            ftp.retrbinary('RETR ' + str(base_filename), f.write)
        filesize = round((float(os.path.getsize(path_to_save)))/1024/1024, 2)
        msg = f'Бэкап базы создан на сервере, размер {filesize} Мб'
        Log.logger.info(msg)
        send_tlg_message(msg)
        return True
    except Exception as ex:
        print(ex)
        send_tlg_message('Ошибка при копировании базы на сервер: ' + str(ex))
        Log.logger.error(ex)


def main():
#    copy_base(1,2)
#    return

    base_filename = Path('BASE/VREMYA_CH.DBX')
    backup_path = Path('/backups/slsbase')
    now_date = datetime.strftime(datetime.now(), '%y%m%d_%H%M')

    if not backup_path.exists():
        backup_path.mkdir(parents=True)

    filename = f'{base_filename.stem}_{now_date}{base_filename.suffix}'
    copy_result = copy_base(base_filename, backup_path / filename)

    return
    if copy_result:
        print(filename)
        y = yadisk.YaDisk(token=YANDEX_TOKEN) 
        #print('Токен принят')
        path_local = str(backup_path / filename)
        #print(f'Локальный путь: {path_local}')
        path_yandex= '/Бэкапы/' + filename
        #print(f'Путь на yandex: {path_yandex}')
        try:
            y.upload(path_local, path_yandex, timeout=(10, 290))
            #print(f'Загрузка на yandex - OK')
            msg = 'Бэкап базы загружен в облако Yandex'
            Log.logger.debug(msg) 
            send_tlg_message(msg)
        except Exception as ex:
            send_tlg_message('Ошибка загрузки базы в облако Yandex: ' + str(ex))
            Log.logger.error(ex)

        # utc = pytz.UTC
        now_minus_30_days =dtime.datetime.now(tz=dtime.timezone.utc) + dtime.timedelta(days=-30)

        try:
            files_to_delete = [x['path'] for x in list(y.listdir("disk:/Бэкапы/")) if x['created'] < now_minus_30_days and x['type'] == 'file' and x['name'].startswith('VREMYA')]
        except Exception as ex:
            files_to_delete = None
            Log.logger.error(ex)

        if files_to_delete:
            for item in files_to_delete:
                y.remove(item)
                Log.logger.debug(f'{item["name"]} удален')
        else:
            Log.logger.debug('Список для удаления пуст')


if __name__ == '__main__':
    main()
