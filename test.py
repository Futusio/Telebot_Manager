import telebot 
from telebot import types
from alchemy import *
import logging
from logging import config
from hashlib import sha256

from sqlalchemy.orm import sessionmaker

from conf import logger_config
from cipher import Cipher

logging.config.dictConfig(logger_config)

logger =logging.getLogger('logger')


session = sessionmaker(bind=engine)()

class Account():
    def __init__(self, u_id, g_id, s_id, name):
        self.u_id = u_id
        self.g_id = g_id
        self.s_id = s_id
        self.name = name
        self.login = None
        self.passw = None


class User():
    def __init__(self, chat_id):
        self.status = None # False is registration, True is authorization
        self.chat_id = chat_id
        self.id = None # ID In DataBase
        self.login = None
        self.passw = None
        self.markup = None # The message to choose Site/Group or accoun
        self.reply = None # The Message with keyboard buttons
        self.flag = True # Switch mode
        self.g_id = None # Current Group Id
        self.s_id = None # Current Site ID
        self.mode = 'normal' # normal \ group \ site \ account 
        self.account = None # For craete new account

    def set_data(self):
        self.groups   = session.query(Groups).filter_by(u_id=self.id)
        self.sites    = session.query(Sites).filter_by(u_id=self.id)
        self.accounts = session.query(Accounts).filter_by(u_id=self.id)

users = {}

token = "1130349206:AAGxwfku5VG8nYPdTpIvWiwGqsYj2I70xxs"

bot = telebot.TeleBot(token)

# WITH DATABASE
def check_login(message):
    """ Поиск логина по БД, в случае успеха 
    приписывает пользователю логин и возвращает True """
    for user in session.query(Users).all():
        if user.login.lower() == message.text.lower():
            users[message.from_user.id].login = message.text
            users[message.from_user.id].id = user.id
            return True
    return False

def check_password(message):
    for user in session.query(Users).all():
        if user.login.lower() == users[message.from_user.id].login:
            if sha256(bytes(message.text, encoding="UTF-8")).hexdigest() == user.password:
                return True
            else:
                return False
    return False

def free_login(message):
    for user in session.query(Users).all():
        if message.text == user.login:
            return False
    users[message.from_user.id].login = message.text
    return True

def create_password(message):
    new_user = Users(users[message.from_user.id].login, message.text)
    users[message.from_user.id].password = message.text
    session.add(new_user)
    session.commit()
    for user in session.query(Users).all():
        if users[message.from_user.id].login == user.login:
            users[message.from_user.id].id = user.id
    return True

# HANDLERS 

@bot.message_handler(commands=['start'])
def start_bot(message): # Стартуем 
    if message.chat.id not in users:
        text = "Hello, {} {}" if message.from_user.last_name is not None else "Hello, {}"
        bot.send_message(message.chat.id, text.format(message.from_user.first_name, message.from_user.last_name))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("authorization"))
        markup.add(types.KeyboardButton("registration"))
        
        users[message.from_user.id] = User(message.from_user.id)
        users[message.from_user.id].reply = bot.send_message(message.chat.id, "First, select authorization or registration?", reply_markup=markup).message_id
        logger.info("The user {} starts work with bot".format(message.from_user.id))
    else:
        bot.send_message(message.chat.id, 'You\'re working with bot, try <i>/quit</i> to start again', parse_mode='html')
        logger.warning("The user {} tired to /start after autho".format(message.chat.id))


@bot.message_handler(commands=['switch'])
def switch_mode(message): # Флаг отображения логина и пароля
    if message.chat.id in users: # Проверка существования пользователя 
        if users[message.chat.id].flag: # меняем флаг 
            users[message.chat.id].flag = False
        else: 
            users[message.chat.id].flag = True
    else: 
        logger.error("The user {} sends \"{}\"".format(message.from_user.id, message.text))
        bot.send_message(message.chat.id, 'Please send <i>/start</i> message to run the bot', parse_mode='html')
    logger.info('The user {} changed switch mode to {}'.format(message.chat.id, users[message.chat.id].flag))

    



@bot.message_handler(commands=['quit'])
def quit_user(message):
    if message.chat.id in users:
        text = "Goodbye, {} {}" if message.from_user.last_name is not None else "Goodbye, {}"
        bot.send_message(message.chat.id, text.format(message.from_user.first_name, message.from_user.last_name))
        # Correct below code
        try: 
            bot.delete_message(message.chat.id, users[message.from_user.id].reply)
        except:
            pass
        try:
            bot.delete_message(message.chat.id, users[message.from_user.id].markup)
        except:
            pass
        try:
            bot.delete_message(message.chat.id, users[message.from_user.id].message)
        except:
            pass

        logger.info("The user {} quit from the bot".format(message.from_user.id))
        users.pop(message.from_user.id)
    else:
        logger.error("The user {} sends \"{}\"".format(message.from_user.id, message.text))
        bot.send_message(message.chat.id, 'Please send <i>/start</i> message to run the bot', parse_mode='html')

def show_groups(message): # Show user's groups
    logger.debug("The user {} got groups list".format(message.from_user.id))
    markup = types.InlineKeyboardMarkup(row_width=1)
    for group in users[message.from_user.id].groups:
        markup.add(types.InlineKeyboardButton(group.name, callback_data='s.' + group.name))
    markup.add(types.InlineKeyboardButton('New Group', callback_data='new_group'))
    # The bellow is message to change with actions 
    users[message.chat.id].markup = bot.send_message(message.chat.id, 'Choose the group', reply_markup=markup).message_id

# Обработчик ввода пользователя
@bot.message_handler(content_types=['text'])
def text_handler(message):
    try: 
        user = users[message.from_user.id]
    except KeyError:
        bot.send_message(message.chat.id, 'Please send <i>/start</i> message to run the bot', parse_mode='html')
        return

    if message.from_user.id in users and user.status is None: # If the user already send /start message
        if message.text == 'authorization': # 
            user.status = True
            bot.send_message(message.chat.id, 'First, send your <b>login</b>', parse_mode='html')
            logger.info("The user {} starts authorization proccess".format(message.from_user.id))
            bot.delete_message(message.chat.id, user.reply)
        elif message.text == 'registration':
            logger.info("The user {} starts registration proccess".format(message.from_user.id))
            user.status = False
            bot.send_message(message.chat.id, 'First, create your <b>login</b>', parse_mode='html')
            bot.delete_message(message.chat.id, user.reply)
        else: 
            logger.error("The user {} sends \"{}\"".format(message.from_user.id, message.text))
            bot.send_message(message.chat.id, 'Please, choose between two variants', parse_mode='html')
        


    elif message.from_user.id in users and user.status is False: # Registration new user
        if user.login is None:# Проверка занят ли логин или нет
            if free_login(message): # Если свободен
                logger.debug("The user {} sent correct registration login".format(message.from_user.id))
                bot.send_message(message.chat.id, 'The login is <i>free</i>', parse_mode='html')
                bot.send_message(message.chat.id, 'Now, please create your password')
                user.login = message.text
            else: # В противном случае
                logger.debug("The user {}sent incorrect reg. login".format(message.from_user.id))
                bot.send_message(message.chat.id, 'The login is already in use')
                bot.send_message(message.chat.id, 'Try use any other login')
        elif user.passw is None: # Создание пароля
            if create_password(message):
                logger.info('New Account was created . Login is {} by user {}'.format(user.login, message.from_user.id))
                bot.send_message(message.chat.id, 'The password is correct. Your account was created!')
                user.passw = message.text
                user.status = True
                user.set_data()
                show_groups(message)
            else:
                bot.send_message(message.chat.id, 'The password is incorrect')
                bot.send_message(message.chat.id, 'Try again. Create your password')
    

    elif message.from_user.id in users and user.status is True: # Authorization old users


        if user.mode == 'group': # ADding new group
            bot.send_message(message.chat.id, 'The new group was created')
            session.add(Groups(user.id, message.text)) # Group Created 
            session.commit() # Group Created 

            bot.delete_message(message.from_user.id, user.markup)
            show_groups(message)
            logger.info("The user {} created new group \"{}\"".format(message.from_user.id, message.text))
            # Change mode
            user.mode = 'normal'
            return

        elif user.mode == 'site':
            bot.send_message(message.chat.id, 'The new site was created')
            session.add(Sites(user.id, user.g_id, message.text))
            session.commit()

            bot.delete_message(message.from_user.id, user.markup)
            show_groups(message)
            logger.info("The user {} created new site \"{}\"".format(message.from_user.id, message.text))
            user.mode = 'normal'
            return


        elif user.mode == 'account':
            if user.account is None:
                user.account = Account(user.id, user.g_id, user.s_id, message.text)
                bot.send_message(message.chat.id, 'Ok, now send a login')
            elif user.account.login is None:
                user.account.login = message.text
                bot.send_message(message.chat.id, 'Ok, now send a password')
            elif user.account.passw is None:
                user.account.passw = message.text
                bot.send_message(message.chat.id, 'New account was created')
                session.add(Accounts(user.account.u_id, user.account.g_id, user.account.s_id,
                                        user.account.name, user.account.login, user.account.passw, user.passw))
                session.commit()

            
                bot.delete_message(message.from_user.id, user.markup)
                show_groups(message)
                logger.info("The user {} created new account \"{}\"".format(message.from_user.id, user.account.name))
                user.mode = 'normal'
                user.account = None
                return


        if users[message.from_user.id].login == None and user.mode == 'normal': # If not login
            if check_login(message): # Try find inputted login
                logger.debug("The user {} send correct auth. login".format(message.from_user.id))
                bot.send_message(message.chat.id, 'The login is <i>correct</i>', parse_mode='html')
                bot.send_message(message.chat.id, 'Now, please send your <b>password</b>', parse_mode='html')
            else:
                logger.debug("The user {} incorrect auth.login ".format(message.from_user.id))
                bot.send_message(message.chat.id, 'The login is <i>incorrect</i>', parse_mode='html')
                bot.send_message(message.chat.id, 'Try again. Send your login')
        elif user.passw == None and user.mode == 'normal':
            if check_password(message): # Try find inputted login
                users[message.from_user.id].reply = bot.send_message(message.chat.id, 'The password is <i>correct</i>', parse_mode='html').message_id
                logger.info("The user {} entered into {} account".format(message.from_user.id, user.login))
                users[message.from_user.id].passw = message.text
                users[message.from_user.id].set_data()
                show_groups(message)
            else:
                logger.debug("The user {} send incorrect auth. passw".format(message.from_user.id))
                bot.send_message(message.chat.id, 'The password is <i>incorrect</i>', parse_mode='html')
                bot.send_message(message.chat.id, 'Try again. Send your password')
        else:
            if user.mode == 'normal':
                logger.error("The user {} sends \"{}\"".format(message.from_user.id, message.text))
                bot.send_message(message.chat.id, "I do not know what to do")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try: 
        user = users[call.message.chat.id]
        if call.message:
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            if call.data == 'groups': # Back to Groups menu
                logger.debug("The user {} returns to group list".format(call.message.from_user.id))
                markup = types.InlineKeyboardMarkup(row_width=1)
                for group in users[call.message.chat.id].groups:
                    markup.add(types.InlineKeyboardButton(group.name, callback_data='s.'+group.name))
                markup.add(types.InlineKeyboardButton('new group', callback_data='new_group'))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                    text='Groups:', reply_markup=markup)
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif call.data == 'sites': # Back to Sites menu
                logger.debug("The user {} returns to site list".format(call.message.from_user.id))
                markup = types.InlineKeyboardMarkup(row_width=1)
                for site in users[call.message.chat.id].sites:
                    if site.g_id == users[call.message.chat.id].g_id:
                        markup.add(types.InlineKeyboardButton(site.name, callback_data='a.'+site.name))
                markup.add(types.InlineKeyboardButton('new site', callback_data='new_site'))        
                markup.add(types.InlineKeyboardButton('back', callback_data='groups'))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                    text='Sites:', reply_markup=markup)
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            
            elif call.data == 'new_group':
                logger.debug("The user {} clicked NEW GROUP".format(call.message.from_user.id))
                bot.send_message(call.message.chat.id, "Enter a group name")
                user.mode = 'group'

            elif call.data == 'new_site':
                logger.debug("The user {} clicked NEW SITE".format(call.message.from_user.id))
                bot.send_message(call.message.chat.id, "Enter a site name")
                user.mode = 'site'
                
            elif call.data == "new_account":
                logger.debug("The user {} clicked NEW ACCOUNT".format(call.message.from_user.id))
                bot.send_message(call.message.chat.id, "Enter an account name")
                user.mode = 'account'

            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif call.data[:2] == 's.': # s. is sites
                markup = types.InlineKeyboardMarkup(row_width=1)
                for group in users[call.message.chat.id].groups: # Ищем ID Группы
                    if group.name == call.data[2:]: # Когда находим нужную группу
                        logger.debug("The user {} opened {} site".format(call.message.from_user.id, group.name))
                        user.g_id = group.id
                        for site in users[call.message.chat.id].sites: # Проходим по всем сайтам 
                            if site.g_id == group.id: # И если g_id сайта совпадает с id группы
                                markup.add(types.InlineKeyboardButton(site.name, callback_data='a.'+site.name)) # ВЫчисленно
                        break
                markup.add(types.InlineKeyboardButton('new site', callback_data='new_site'))   
                markup.add(types.InlineKeyboardButton('back', callback_data='groups')) # Back to groups list
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                    text='Sites:', reply_markup=markup)

            
            elif call.data[:2] == 'a.': # a. is accounts 
                markup = types.InlineKeyboardMarkup(row_width=1)
                for site in users[call.message.chat.id].sites:
                    if site.name == call.data[2:]:
                        logger.debug("The user {} opened {} site".format(call.message.from_user.id, site.name))
                        user.s_id = site.id
                        for account in users[call.message.chat.id].accounts:
                            if account.s_id == site.id:
                                markup.add(types.InlineKeyboardButton(account.name, callback_data='l.'+account.name))
                markup.add(types.InlineKeyboardButton('new account', callback_data='new_account'))   
                markup.add(types.InlineKeyboardButton('back', callback_data='sites')) # Back to groups list
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                    text='Accounts:', reply_markup=markup)

            elif call.data[:2] == 'l.':
                name, login, passw = None, None, None
                for account in users[call.message.chat.id].accounts:
                    if call.data[2:] == account.name: # Data must be decrypt

                        name = account.name
                        login = Cipher.decrypt(account.login, users[call.message.chat.id].passw).decode()
                        passw = Cipher.decrypt(account.password, users[call.message.chat.id].passw).decode()
                logger.warning("The user {} shows data from account {}".format(call.message.chat.id, name))
                # Flag is the /switch mode
                if users[call.message.chat.id].flag:
                    try: 
                        bot.edit_message_text(chat_id=call.message.chat.id, message_id=users[call.message.chat.id].message,  text='{}\nLogin: {}\nPassword: {}'.format(name.title(), login, passw))
                    except AttributeError:
                        users[call.message.chat.id].message = bot.send_message(call.message.chat.id, '{}\nLogin: {}\nPassword: {}'.format(name.title(), login, passw)).message_id
                else: 
                    bot.answer_callback_query(call.id, '{}\nLogin: {}\nPassword: {}'.format(name.title(), login, passw),True)

    except Exception:
        pass


bot.polling(none_stop=True)