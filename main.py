#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
from telebot import types
import re
from loguru import logger
import io

import config
import functions
import cashInfo

bot = telebot.TeleBot(config.token)
logger.add(config.dir_path + 'logs/debug.log',
           level='DEBUG', rotation='10 MB', compression='zip')
logger.info("Начал работу")


@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Зашел {message.from_user.first_name}")
    bot.send_message(message.chat.id,
                     "Здравствуйте <b>" + message.from_user.first_name + "</b>\n"
                                                                         "Чтобы получить остатки нажмите на кнопку <u><b>Получить остатки</b></u>\n\n"
                                                                         "Остатки формируются каждый день в 12:50. Компьютер обязательно должен быть включен\n\n"
                                                                         "Чтобы добавить себе штрихкод на компьютер нажмите на кнопку <u><b>Добавить штрихкод</b></u>\n\n"
                                                                         "Максимальное название товара не должно превышать 35 символов\n\n"
                                                                         "В случае любых вопросов обращайтесь к нам на WhatsApp по номеру <u>+7(960)048-43-66</u>",
                     reply_markup=start_markup(), parse_mode='html')


@bot.message_handler(content_types=['text'])
@logger.catch
def catalog(message):
    if message.text.lower() == 'получить остатки':
        logger.info("Кнопка 'получить остатки'")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        button_lastOstatki = types.KeyboardButton("Последние остатки")
        button_listOstatki = types.KeyboardButton("Список по датам")
        markup.add(button_lastOstatki, button_listOstatki)
        bot.send_message(message.chat.id,
                         '<u><b>Последние остатки</b></u> - Получить последние сгенерированные остатки\n\n'
                         '<u><b>Список по датам</b></u> - Выведем даты последних 6 сгенерированных накладных',
                         reply_markup=markup, parse_mode='html')

    elif message.text.lower() == "последние остатки":
        logger.info("Кнопка 'последние остатки'")

        msg = bot.send_message(message.chat.id,
                               "Введите номер компьютера:",
                               parse_mode="html")

        bot.register_next_step_handler(msg, send_last_file)

    elif message.text.lower() == "список по датам":
        logger.info("Кнопка 'список по датам'")

        msg = bot.send_message(message.chat.id,
                               "Пример: <u><b>1798-1</b></u>\n"
                               "Где 1798 - это номер компьютера, а 1 - это номер кассы\n\n"
                               "Введите номер компьютера и номер кассы через дефиз:",
                               parse_mode="html")
        bot.register_next_step_handler(msg, send_dates_files)

    elif message.text.lower() == "добавить штрихкод":
        logger.info("Кнопка 'добавить штрихкод'")

        msg = bot.send_message(message.chat.id,
                               "Пример: <u><b>1798-1</b></u>\n"
                               "Где 1798 - это номер компьютера, а 1 - это номер кассы\n\n"
                               "Введите номер компьютера и номер кассы через дефиз:",
                               parse_mode="html")
        bot.register_next_step_handler(msg, gen_bcode_start)
    else:
        logger.debug("Не понимаю данной команды - " + message.text)
        bot.send_message(message.chat.id, "Не понимаю данной команды")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_send_email":
        try:
            msg = bot.send_message(call.message.chat.id, 'Введите почту: ')
            bot.register_next_step_handler(msg, send_email)
        except Exception as ex:
            bot.send_message(call.message.chat.id, 'Внутрення ошибка, попробуйте снова',
                             reply_markup=start_markup())
            logger.error(f'{ex} --- {cashInfo.cash_number}')


def start_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button_ostatki = types.KeyboardButton('Получить остатки')
    button_bcode = types.KeyboardButton('Добавить штрихкод')
    markup.add(button_ostatki, button_bcode)
    return markup


def send_last_file(message):
    try:
        functions.check_repeat_cash(message.text)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Отправить на почту', callback_data='cb_send_email'))
        cashInfo.cash_number = message.text
        xlsx = open(functions.get_last_file(cashInfo.cash_number), 'rb')
        cashInfo.current_path_file = functions.get_last_file(cashInfo.cash_number)
        logger.info(
            f'Отправил последние остатки "{functions.get_last_file(cashInfo.cash_number)}" --- {cashInfo.cash_number}')
        bot.send_document(message.chat.id, xlsx, reply_markup=markup)
        bot.send_message(message.chat.id, 'Нам очень приятно что пользуетесь нашим ботом\n\n'
                                          'Оставьте пожалуйста отзыв <u>https://forms.gle/CbUD1SLiNnWcYwz28</u> ',
                         reply_markup=start_markup(), parse_mode='html')
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_dates_files(message):
    try:
        regex = re.compile(r'[0-9]{1,4}-[0-9]{1,2}')
        if re.fullmatch(regex, message.text):
            cash_files = functions.get_last_files(message.text, 6)
            markup = types.ReplyKeyboardMarkup(row_width=3)
            cash_dates = [line.split("/")[-1] for line in cash_files]  # Берём только название файла
            # cash_dates = [line.split("/")[-1] for line in cash_files]  # Берём только даты
            cash_dates = [line.split("_")[0:3] for line in cash_dates]  # Берём только даты из названия файла
            for line in cash_dates:
                line.reverse()  # Переворачиваем чтобы даты были день-месяц-год
            cash_dates = ['-'.join(line) for line in cash_dates]  # Соединяем даты
            buttons = [types.KeyboardButton(line) for line in cash_dates]
            for i in buttons:
                markup.add(i)

            # Инфа для глобальных переменных
            cashInfo.cash_number = message.text
            cashInfo.path_to_files = cash_files
            cashInfo.dates_files = cash_dates

            send = bot.send_message(message.chat.id, 'Выберите одну из дат:', reply_markup=markup)
            bot.register_next_step_handler(send, send_file)
        else:
            logger.debug("Номер кассы введена не правильно - " + message.text)
            bot.send_message(message.chat.id, 'Номер кассы введена не правильно', reply_markup=start_markup())
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_file(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Отправить на потку', callback_data='cb_send_email'))
        path = cashInfo.path_to_files[cashInfo.dates_files.index(message.text)]

        # Инфа для глобальной переменной
        cashInfo.current_path_file = path
        logger.info(f'Отправил остатки по выбранной дате "{path}" --- {cashInfo.cash_number}')
        bot.send_document(message.chat.id, open(path, 'rb'), reply_markup=markup)
        bot.send_message(message.chat.id, 'Нам очень приятно что пользуетесь нашим ботом\n\n'
                                          'Оставьте пожалуйста отзыв <u>https://forms.gle/CbUD1SLiNnWcYwz28</u> ',
                         reply_markup=start_markup(), parse_mode='html')
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_email(message):
    try:
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

        if re.fullmatch(regex, message.text):
            functions.send_email(message.text, cashInfo.current_path_file)
            logger.info(f'Отправил {cashInfo.current_path_file} на почту {message.text} --- {cashInfo.cash_number}')
            bot.send_message(message.chat.id, 'Сообщение отправлено на почту\n\n'
                                              'Если сообщение не приходит, то оно возможно у вас в <b><u>спаме</u></b>',
                             reply_markup=start_markup(), parse_mode='html')
        else:
            logger.debug("Электронная почта введена не правильно - " + message.text + ' | cash-' + cashInfo.cash_number)
            bot.send_message(message.chat.id, 'Электронная почта введена не правильно', reply_markup=start_markup())
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.cash_number} or {cashInfo.bcode_cash_number}')


def gen_bcode_start(message):
    try:
        regex = re.compile(r'[0-9]{1,4}-[0-9]{1,2}')
        if re.fullmatch(regex, message.text):
            cashInfo.bcode_cash_number = message.text
            markup = types.ReplyKeyboardMarkup()
            alcohol = types.KeyboardButton('Крепкий алкоголь')
            beer = types.KeyboardButton('Пиво')
            cigarettes = types.KeyboardButton('Сигареты')
            other = types.KeyboardButton('Прочее')
            markup.add(alcohol, beer, cigarettes, other)

            msg = bot.send_message(message.chat.id, 'Выберите какой товар хотите добавить:\n\n'
                                                    '<u><b>Крепкий алкоголь</b></u> - всё что имеет акцизную марку\n\n'
                                                    '<u><b>Пиво</b></u> - любой вид пива\n\n'
                                                    '<u><b>Сигареты</b></u> - любой вид сигарет\n\n'
                                                    '<u><b>Прочее</b></u> - товары которые продаются как правило через ИП. Например: мыло, треугольник, хлеб',
                                   reply_markup=markup, parse_mode='html')
            bot.register_next_step_handler(msg, get_bcode_otdel)
        else:
            logger.debug("Номер кассы введена не правильно - " + message.text)
            bot.send_message(message.chat.id, 'Номер кассы введена не правильно', reply_markup=start_markup())
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.bcode_cash_number}')


def get_bcode_otdel(message):
    try:
        if message.text.lower() == 'крепкий алкоголь':
            cashInfo.bcode_otdel = '1'
            bcode = bot.send_message(message.chat.id, 'Введите штрихкод товара:')
            bot.register_next_step_handler(bcode, set_barcode)
        elif message.text.lower() == 'пиво':
            cashInfo.bcode_otdel = '2'
            bcode = bot.send_message(message.chat.id, 'Введите штрихкод товара:')
            bot.register_next_step_handler(bcode, set_barcode)
        elif message.text.lower() == 'сигареты':
            cashInfo.bcode_otdel = '3'
            bcode = bot.send_message(message.chat.id, 'Введите штрихкод товара:')
            bot.register_next_step_handler(bcode, set_barcode)
        elif message.text.lower() == 'прочее':
            cashInfo.bcode_otdel = '4'
            cashInfo.bcode = functions.get_valid_barcode(cashInfo.bcode_cash_number)
            msg = bot.send_message(message.chat.id, "Введите короткое название товара:")
            bot.register_next_step_handler(msg, get_bcode_send)
        else:
            bot.send_message(message.chat.id, "Не понимаю данной команды")


    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.bcode_cash_number}')


def set_barcode(message):
    regex = re.compile('^\d+$')
    if re.fullmatch(regex, message.text):
        cashInfo.bcode = message.text

        msg = bot.send_message(message.chat.id, "Введите короткое название товара:")
        bot.register_next_step_handler(msg, get_bcode_send)
    else:
        logger.debug(
            f"Штрихкод неверен {message.text} - длина штрихкода({len(message.text)}) --- {cashInfo.bcode_cash_number}")
        bot.send_message(message.chat.id, 'Штрихкод должен быть только из цифр. Попробуйте всё с начала',
                         reply_markup=start_markup())


def get_bcode_send(message):
    try:
        regex = re.compile(r'.{1,35}')
        if re.fullmatch(regex, message.text):
            name = message.text
            cashInfo.bcode_name = name
            functions.generate_barcode(cashInfo.bcode)
            cashInfo.current_path_file = config.dir_path + 'logs/barcode.png'
            functions.resize_canvas(config.dir_path + 'logs/barcode.png', name)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Отправить на почту', callback_data='cb_send_email'))
            bot.send_photo(message.chat.id, open(config.dir_path + 'logs/barcode.png', 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, 'Товар в скором времени будет добавлен к вам на кассу\n\n'
                                              'Касса обязательно должна быть <u><b>включена</b></u> и должен быть <u><b>интернет</b></u>',
                             reply_markup=start_markup(), parse_mode='html')
            with open(f'{config.server_path}telegram_barcode.txt',
                      'a') as barcodes_file:  # Инфа для скрипта, который будет добавлять на компы штрихкода
                barcodes_file.write(
                    'cash-' + cashInfo.bcode_cash_number + "|" + cashInfo.bcode + '|' + cashInfo.bcode_otdel + '|' + cashInfo.bcode_name + '\n')
                logger.info(
                    'Добавил: cash-' + cashInfo.bcode_cash_number + "|" + cashInfo.bcode + '|' + cashInfo.bcode_otdel + '|' + cashInfo.bcode_name + '\n')
        else:
            logger.debug(
                f"Штрихкод неверен {message.text} - длина штрихкода({len(message.text)}) --- {cashInfo.bcode_cash_number}")
            bot.send_message(message.chat.id, 'Название товара введено не верно. Максимальная длина 35 символов',
                             reply_markup=start_markup())
    except Exception as ex:
        bot.send_message(message.chat.id, 'Внутрення ошибка, попробуйте снова',
                         reply_markup=start_markup())
        logger.error(f'{ex} --- {cashInfo.bcode_cash_number}')


bot.polling()
