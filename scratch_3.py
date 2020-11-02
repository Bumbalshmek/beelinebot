import requests
import telebot
import json
import random
import re
import sqlite3
import cherrypy
import config
users_dictionary = dict()
employee_dict = dict()
# eto v konfig
telegram_token = config.telegram_token
bot = telebot.TeleBot(telegram_token)
Api_Auth_Token = config.Api_Auth_Token
Sms_ru_api_Token = config.Sms_ru_api_Token
table_name = config.table_name
database_name = config.database_name
webhook_ip = config.webhook_ip
webhook_ssl_certificate = config.webhook_ssl_certificate
webhook_ssl_private = config.webhook_ssl_private
side_numbers_forwarding = config.side_numbers_forwarding
class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
    def new_row(self, user_id):
        """Добавление новой строки в таблицу(все ячейки кроме айди = Null)"""
        with self.connection:
            self.cursor.execute('INSERT INTO ' + table_name + ' ("user_id") VALUES ("' + str(user_id) + '")')
    def check_row(self,user_id):
        """Проверяет таблицу на наличие определенного айди в ней"""
        with self.connection:
            result = self.cursor.execute('SELECT count(user_id)>0 FROM '+ table_name +' WHERE user_id = "'+str(user_id)+'"').fetchall()
            return result
    def state_update(self, user_id, new_state):
        with self.connection:
            self.cursor.execute(
                'UPDATE ' + table_name + ' SET user_state = ' + str(new_state) + ' WHERE user_id  = "' + str(user_id) + '"')
    def add_to_row(self,user_id,column_name,text):
        """ Добавление контента в определенную строку таблицы """
        with self.connection:
            roflinochka = self.cursor.execute('UPDATE ' +table_name + ' SET '+column_name+' = '+str(text)+' WHERE user_id  = "'+str(user_id)+'"')
            return roflinochka
    def show_info(self,user_id):
        """Выдача данных из одной строки таблицы списком"""
        with self.connection:
            information = self.cursor.execute('SELECT * FROM ' + table_name +' WHERE user_id = "'+str(user_id)+ '"').fetchall()
            if len(information) == 0:
                pass
            else:
                information[0] = list(information[0])
                information = (sum(information, []))
                return information
    def id_list_full(self):
        with self.connection:
            ids = self.cursor.execute('SELECT user_id FROM '+table_name+'').fetchall()
            if len(ids) == 0:
                pass
            else:
                ids[0] = list(ids[0])
                ids = (sum(ids, []))
                return ids
    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM ' + table_name ).fetchall()
            return len(result)
def forwarding_status(number,api_token = Api_Auth_Token):
    headers = {
        'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
    }

    response = requests.get('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(number)+'/cfb', headers=headers)
    return json.loads(response.text)
def absolute_forwarding_change(forward_number,new_number,api_token = Api_Auth_Token):
    headers = {
    'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
    'Content-Type': 'application/json',
        }
    data = ' { "forwardAllCallsPhone" : "'+str(new_number)+'" } '
    response = requests.put('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(forward_number)+'/cfb', headers=headers, data=data)
    return response
def forwarding_disable(phone_number,api_token = Api_Auth_Token):
    headers = {
            'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
    }

    response = requests.delete('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(phone_number)+'/cfb', headers=headers)
    return response
def something(api_token = Api_Auth_Token):
    headers = {
        'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
    }

    response = requests.get('https://cloudpbx.beeline.ru/apis/portal/abonents', headers=headers)
    return response.text
def forwarding_while_not_anwsering(forwarding_number,new_number,timeout,api_token = Api_Auth_Token):
    headers = {
        'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
        'Content-Type': 'application/json',
    }
    kerpa = forwarding_status(forwarding_number)
    if kerpa['status'] == "OFF" or "forwardAllCallsPhone" in kerpa["forward"]:
        data = ' { "forwardNotAnswerPhone" : "'+str(new_number)+'", "forwardNotAnswerTimeout": '+str(timeout)+' } '
    else:
        data = ' { '
        if 'forwardUnavailablePhone' in kerpa["forward"]:
            data += '"forwardUnavailablePhone" : "' + str(kerpa["forward"]["forwardUnavailablePhone"]) + '", '
        if 'forwardBusyPhone' in kerpa["forward"]:
            data += '"forwardBusyPhone" : "' + str(kerpa["forward"]["forwardBusyPhone"]) + '", '
        data += '"forwardNotAnswerPhone" : "'+str(new_number)+'", "forwardNotAnswerTimeout": '+str(timeout)+' } '
    response = requests.put('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(forwarding_number)+'/cfb', headers=headers,
                            data=data)
    return response.ok
def busy_forwarding(forwarding_number,new_number,api_token = Api_Auth_Token):
    headers = {
    'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
    'Content-Type': 'application/json',
    }
    kerpa = forwarding_status(forwarding_number)
    data =  ''
    if kerpa['status'] == "OFF" or "forwardAllCallsPhone" in kerpa["forward"]:
        data = ' {"forwardBusyPhone" : "' + str(new_number) + '" } '
    else:
        data = ' { '
        if 'forwardUnavailablePhone' in kerpa["forward"]:
            data+= '"forwardUnavailablePhone" : "' +str(kerpa["forward"]["forwardUnavailablePhone"]) +'", '
        if 'forwardNotAnswerPhone' in kerpa["forward"]:
            data+= '"forwardNotAnswerPhone" : "' + str(kerpa["forward"]["forwardNotAnswerPhone"]) + '", '
            data+= '"forwardNotAnswerTimeout" : ' + str(kerpa["forward"]["forwardNotAnswerTimeout"]) +', '
        data += '"forwardBusyPhone" : "' + str(new_number) + '" } '


    response = requests.put('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(forwarding_number)+'/cfb', headers=headers, data=data)
    return response.ok
def unavailable_forwarding(forwarding_number,new_number,api_token = Api_Auth_Token):
    headers = {
        'X-MPBX-API-AUTH-TOKEN': ''+api_token+'',
        'Content-Type': 'application/json',
    }
    kerpa = forwarding_status(forwarding_number)
    if kerpa['status'] == "OFF" or "forwardAllCallsPhone" in kerpa["forward"]:
        data = ' {"forwardUnavailablePhone" : "' + str(new_number) + '" } '
    else:
        data = ' { '
        if 'forwardBusyPhone' in kerpa["forward"]:
            data+= '"forwardBusyPhone" : "' +str(kerpa["forward"]["forwardBusyPhone"]) +'", '
        if 'forwardNotAnswerPhone' in kerpa["forward"]:
            data+= '"forwardNotAnswerPhone" : "' + str(kerpa["forward"]["forwardNotAnswerPhone"]) + '", '
            data+= '"forwardNotAnswerTimeout" : ' + str(kerpa["forward"]["forwardNotAnswerTimeout"]) +', '
        data += '"forwardUnavailablePhone" : "' + str(new_number) + '" } '
    response = requests.put('https://cloudpbx.beeline.ru/apis/portal/abonents/'+str(forwarding_number)+'/cfb', headers=headers, data=data)
    return response
def numberinbase(contacts,number):
    for i in range(len(contacts)):
        if contacts[i]['phone'] == number:
            return True
    return False
def send_sms(number,auth_code,Sms_ru_api_token = Sms_ru_api_Token ):
    checkbalance = requests.get('https://sms.ru/my/balance?api_id='+Sms_ru_api_token+'&json=1')
    checkbalance = checkbalance.json()
    check_limit = requests.get('https://sms.ru/my/limit?api_id='+Sms_ru_api_token+'&json=1')
    check_limit = check_limit.json()
    if float(checkbalance["balance"]) - 2.89 < 0:
        return "Извините, смс не может быть отправлена из-за отсутствия денег на балансе"
    elif int(check_limit["total_limit"]) - int(check_limit["used_today"]) == 0:
        return "Изините, суточный лимит смс исчерпан"
    else:
        responsee = requests.get(
        'https://sms.ru/sms/send?api_id='+Sms_ru_api_token+'&to=7'+str(number)+'&msg='+str(auth_code)+'&json=1')
        return "Enter sms code"
def randadadad(sms_ru_api_token = Sms_ru_api_Token):
    response = requests.get('https://sms.ru/my/balance?api_id='+sms_ru_api_token+'&json=1')
WEBHOOK_HOST = webhook_ip
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = webhook_ssl_certificate  # Путь к сертификату

WEBHOOK_SSL_PRIV = webhook_ssl_private   # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (telegram_token)
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

db_worker = SQLighter(database_name)
for i in range(db_worker.count_rows()):
    users_dictionary.update({db_worker.id_list_full()[i]:db_worker.show_info(db_worker.id_list_full()[i])})
    del users_dictionary[(db_worker.id_list_full()[i])][0]
@bot.message_handler(commands=["start"])
def starting_message(message):
    db_worker = SQLighter(database_name)
    db_worker.show_info(message.chat.id)
    var = db_worker.check_row(message.chat.id)
    if message.chat.id not in users_dictionary and var[0] != (1,):
        bot.send_message(message.chat.id,'Здравствуйте, введите свой номер телефона')
        users_dictionary.update({message.chat.id : []})
        users_dictionary[message.chat.id].append(1)
    else:
        bot.send_message(message.chat.id, 'Неверный ответ')
@bot.message_handler(content_types=["text"])
def send_message(message):
    if message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 1:
        if message.text.isdigit() and len(message.text) == 10:
            contacts = json.loads(something())
            if numberinbase(contacts, message.text):
                users_dictionary[message.chat.id][0] = 2
                users_dictionary[message.chat.id].append(random.randint(100000,999999))
                users_dictionary[message.chat.id].append(message.text)
                bot.send_message(message.chat.id, send_sms(users_dictionary[message.chat.id][2],users_dictionary[message.chat.id][1]))
            else:
                bot.send_message(message.chat.id,'Номера нет в базе')
        else:
            bot.send_message(message.chat.id,'Неверный номер')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 2:
        if str(message.text) == str(users_dictionary[message.chat.id][1]):
            db_worker = SQLighter(database_name)
            bot.send_message(message.chat.id,'Вы авторизованы')
            users_dictionary[message.chat.id][0] = 3
            db_worker.new_row(message.chat.id)
            db_worker.state_update(message.chat.id, 3)
            db_worker.add_to_row(message.chat.id, "sms_code", users_dictionary[message.chat.id][1])
            db_worker.add_to_row(message.chat.id, "phone_number", users_dictionary[message.chat.id][2])
            bot.send_message(message.chat.id, 'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
        else:
            bot.send_message(message.chat.id,'Неверный код')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 3 and message.text == str(1):
        if forwarding_status(users_dictionary[message.chat.id][2])['status'] == 'OFF':
            bot.send_message(message.chat.id, 'Переадресация уже отключена')
        else:

            forwarding_disable(users_dictionary[message.chat.id][2])
            bot.send_message(message.chat.id, 'Переадресация была отключена')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 3 and message.text == str(2):
        users_dictionary[message.chat.id][0] = 4
        bot.send_message(message.chat.id,'Выберите режим переадресации\n1.Безусловная переадресация\n2.Переадресация когда номер не отвечает\n3.Переадресация когда номер занят\n4.Переадресация когда номер недоступен')
        dictic = dict()
        somethingg = json.loads(something())
        for i in range(len(somethingg)):
            if somethingg[i-1]["phone"] == users_dictionary[message.chat.id][2]:
                somethingg.pop(i-1)
        for i in range(len(somethingg)):
            if "firstName" in somethingg[i] and somethingg[i]["phone"] != users_dictionary[message.chat.id][2]:
                dictic.update({i+1: str(somethingg[i]['firstName'])})
            if "lastName" in somethingg[i] and somethingg[i]["phone"] != users_dictionary[message.chat.id][2]:
                if i+1 not in dictic:
                    dictic.update({i+1:' '+str(somethingg[i]['lastName'])})
                else:
                    dictic.update({i+1:dictic[i+1]+' '+str(somethingg[i]['lastName'])})

        for i in range(len(somethingg)):
            dictic.update({i+1 : dictic[i+1]+' : '+somethingg[i]["phone"]})
        mama = ''
        for i in range(len(somethingg)):
            mama += str(i+1)+'.'+str(dictic[i+1]) +'\n'

        if mama not in users_dictionary[message.chat.id]:
            users_dictionary[message.chat.id].append(mama)
        if dictic not in users_dictionary[message.chat.id]:
            users_dictionary[message.chat.id].append(dictic)
        #bot.send_message(message.chat.id, mama)
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 3 and message.text == str(3):
        kerpa = forwarding_status(users_dictionary[message.chat.id][2])

        if kerpa['status'] == 'ON':
            if len(kerpa["forward"]) == 1 and "forwardAllCallsPhone" in kerpa["forward"]:
                bot.send_message(message.chat.id, 'Все звонки переадресованы на '+str(kerpa["forward"]["forwardAllCallsPhone"])+'')
            #dopisal vrode
            else:
                text = 'Ваш статус переадресации \n'
                if 'forwardBusyPhone' in kerpa["forward"]:
                    text += 'Переадресация когда номер занят : '+str(kerpa["forward"]['forwardBusyPhone'])+'\n'

                if 'forwardUnavailablePhone' in kerpa["forward"]:
                    text += 'Переадресация когда номер недоступен : '+str(kerpa["forward"]['forwardUnavailablePhone'])+'\n'

                if 'forwardNotAnswerPhone' in kerpa["forward"]:
                    text += 'Переадресация когда номер не отвечает : '+str(kerpa["forward"]['forwardNotAnswerPhone'])+'\n'
                    text += 'Количество гудков до переадресации : '+str(kerpa["forward"]['forwardNotAnswerTimeout'])
                bot.send_message(message.chat.id,text)
            bot.send_message(message.chat.id,
                             'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')

        else:
            bot.send_message(message.chat.id, 'Переадресация отключена')
            bot.send_message(message.chat.id,
                             'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 4 and message.text == str(1):
        if side_numbers_forwarding:
            bot.send_message(message.chat.id, 'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3] +''+str(len(users_dictionary[message.chat.id][4])+1) +'. Для переадресации на сторонний номер')
        else:
            bot.send_message(message.chat.id, 'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3])
        users_dictionary[message.chat.id][0] = 5
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 5 and int(message.text) in users_dictionary[message.chat.id][4]:
        pip = re.sub("\D", "", users_dictionary[message.chat.id][4][int(message.text)])
        pip = pip[-10:]
        pip = int(pip)
        users_dictionary[message.chat.id].append(pip)
        absolute_forwarding_change(users_dictionary[message.chat.id][2],users_dictionary[message.chat.id][5])
        users_dictionary[message.chat.id].pop()
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 5 and int(message.text) == len(users_dictionary[message.chat.id][4]) + 1 and side_numbers_forwarding:
        users_dictionary[message.chat.id][0] = 6
        bot.send_message(message.chat.id,'Введите номер')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 6 and message.text.isdigit() and len(message.text) == 10 and message.text != users_dictionary[message.chat.id][2]:
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,
                         'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
        absolute_forwarding_change(users_dictionary[message.chat.id][2], int(message.text))
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 4 and message.text == str(2):
        if side_numbers_forwarding:
            bot.send_message(message.chat.id,
                             'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3] + '' + str(len(
                                 users_dictionary[message.chat.id][4])+1) + '. Для переадресации на сторонний номер')
        else:
            bot.send_message(message.chat.id, 'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3])
        users_dictionary[message.chat.id][0] = 7
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 7 and int(message.text) in users_dictionary[message.chat.id][4]:
        pip = re.sub("\D", "", users_dictionary[message.chat.id][4][int(message.text)])
        pip = pip[-10:]
        pip = int(pip)
        users_dictionary[message.chat.id].append(pip)
        bot.send_message(message.chat.id,'Введите количество гудков до переадресации')
        users_dictionary[message.chat.id][0] = 8
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 7 and int(message.text) == len(
            users_dictionary[message.chat.id][4]) + 1 and side_numbers_forwarding:
        bot.send_message(message.chat.id,'Введите номер')
        users_dictionary[message.chat.id][0] = 9
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 9 and message.text.isdigit() and len(message.text) == 10 and message.text != users_dictionary[message.chat.id][2]:
        users_dictionary[message.chat.id].append(int(message.text))
        bot.send_message(message.chat.id, 'Введите количество гудков до переадресации')
        users_dictionary[message.chat.id][0] = 8
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 8 and message.text.isdigit() and int(message.text) <= 10 :
        forwarding_while_not_anwsering(users_dictionary[message.chat.id][2], users_dictionary[message.chat.id][5],int(message.text))
        users_dictionary[message.chat.id].pop()
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 4 and message.text == str(3):
        if side_numbers_forwarding:
            bot.send_message(message.chat.id,
                             'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3] + '' + str(len(
                                 users_dictionary[message.chat.id][4] )+1) + '. Для переадресации на сторонний номер')
        else:
            bot.send_message(message.chat.id, 'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3])
        users_dictionary[message.chat.id][0] = 10
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 10 and int(message.text) in users_dictionary[message.chat.id][4]:
        pip = re.sub("\D", "", users_dictionary[message.chat.id][4][int(message.text)])
        pip = pip[-10:]
        pip = int(pip)
        users_dictionary[message.chat.id].append(pip)
        busy_forwarding(users_dictionary[message.chat.id][2],users_dictionary[message.chat.id][-1])
        users_dictionary[message.chat.id].pop()
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,
                         'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 10 and int(message.text) == len(users_dictionary[message.chat.id][4]) + 1 and side_numbers_forwarding:
         users_dictionary[message.chat.id][0] = 11
         bot.send_message(message.chat.id, 'Введите номер')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 11 and message.text.isdigit() and len(message.text) == 10 and message.text != users_dictionary[message.chat.id][2]:
        busy_forwarding(users_dictionary[message.chat.id][2],int(message.text))
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 4 and message.text == str(4):
        if side_numbers_forwarding:
            bot.send_message(message.chat.id,
                             'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3] +''+ str(len(
                                 users_dictionary[message.chat.id][4] )+1)  + '. Для переадресации на сторонний номер')
        else:
            bot.send_message(message.chat.id, 'Выберите номер для переадресации\n' + users_dictionary[message.chat.id][3])
        users_dictionary[message.chat.id][0] = 12
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 12 and int(message.text) in users_dictionary[message.chat.id][4]:
        pip = re.sub("\D", "", users_dictionary[message.chat.id][4][int(message.text)])
        pip = pip[-10:]
        pip = int(pip)
        users_dictionary[message.chat.id].append(pip)
        unavailable_forwarding(users_dictionary[message.chat.id][2], users_dictionary[message.chat.id][5])
        users_dictionary[message.chat.id].pop()
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id, 'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 12 and int(message.text) == len(users_dictionary[message.chat.id][4]) + 1 and side_numbers_forwarding:
        users_dictionary[message.chat.id][0] = 13
        bot.send_message(message.chat.id, 'Введите номер')
    elif message.chat.id in users_dictionary and users_dictionary[message.chat.id][0] == 13 and message.text.isdigit() and len(message.text) == 10 and message.text != users_dictionary[message.chat.id][2]:
        unavailable_forwarding(users_dictionary[message.chat.id][2], int(message.text))
        users_dictionary[message.chat.id][0] = 3
        bot.send_message(message.chat.id,'Что вы хотите сделать? \n1. Убрать переадресацию с моего номера\n2. Установить переадресацию с моего номера на другой\n3. Показать статус переадресации на моем номере')
    else:
        bot.send_message(message.chat.id, 'Неверный ответ')

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})