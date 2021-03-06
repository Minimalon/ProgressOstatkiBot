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
                     "Здравствуйте <b>" + message.from_user.first_name + "</b>\n\n"
                     # "Чтобы получить остатки нажмите на кнопку <u><b>Получить остатки</b></u>\n\n"
                                                                         "Остатки формируются каждый день в 12:50. Компьютер обязательно должен быть <u><b>включен</b></u> и обязательно должен быть <u><b>интернет</b></u>\n\n"
                     # "Чтобы добавить себе штрихкод на компьютер нажмите на кнопку <u><b>Добавить штрихкод</b></u>\n\n"
                     # "Максимальное название товара не должно превышать 35 символов\n\n"
                                                                         "В случае любых вопросов обращайтесь к нам на WhatsApp по номеру <u>+7(960)048-43-66</u>",
                     parse_mode='html')
    start_select(message)


@bot.message_handler(content_types=['text'])
def catalog(message):
    if re.fullmatch(r".*Остатки.*|.*остатки.*", message.text):
        bot.send_message(message.chat.id, 'Вам нужно только нажимать на кнопки под текстом и следовать указанием')
        start_select(message)
    #
    # if message.text.lower() == 'получить остатки':
    #
    #
    # elif message.text.lower() == "последние остатки":
    #     logger.info("Кнопка 'последние остатки'")
    #
    #     msg = bot.send_message(message.chat.id, "Введите номер компьютера:", parse_mode="html")
    #     bot.register_next_step_handler(msg, send_last_file)
    #
    # elif message.text.lower() == "список по датам":
    #     logger.info("Кнопка 'список по датам'")
    #
    #     msg = bot.send_message(message.chat.id, "Введите номер компьютера:", parse_mode="html")
    #     bot.register_next_step_handler(msg, send_dates_files)
    #
    # elif message.text.lower() == "добавить штрихкод":
    #     logger.info("Кнопка 'добавить штрихкод'")
    #
    #     msg = bot.send_message(message.chat.id, "Введите номер компьютера:", parse_mode="html")
    #     bot.register_next_step_handler(msg, gen_bcode_start)
    else:
        logger.debug("Не понимаю данной команды - " + message.text)
        bot.send_message(message.chat.id, f"Не понимаю данной команды '{message.text}'")
        start_select(message)


@bot.callback_query_handler(func=lambda call: True)
@logger.catch()
def callback_query(call):
    # Barcodes
    if call.data == 'cb_generate_barcodes':
        logger.info(f"Кнопка 'Добавить штрихкод' --- {call.message.chat.first_name}")
        msg = bot.send_message(call.message.chat.id, 'Напишите номер компьютера:\n'
                                                     'Нужны только цифры. Например: <b><u>902</u></b>',
                               parse_mode='html')
        bot.register_next_step_handler(msg, gen_bcode_start)

    if call.data == 'cb_barcodes_alcohol':
        logger.info(f"Кнопка 'Крепкий алкоголь' --- {call.message.chat.first_name}")
        cashInfo.bcode_otdel = '1'
        bcode = bot.send_message(call.message.chat.id, 'Напишите штрихкод товара:')
        bot.register_next_step_handler(bcode, set_barcode)

    if call.data == 'cb_barcodes_beer':
        logger.info(f"Кнопка 'Пиво' --- {call.message.chat.first_name}")
        cashInfo.bcode_otdel = '2'
        bcode = bot.send_message(call.message.chat.id, 'Напишите штрихкод товара:')
        bot.register_next_step_handler(bcode, set_barcode)

    if call.data == 'cb_barcodes_cigaretes':
        logger.info(f"Кнопка 'Сигареты' --- {call.message.chat.first_name}")
        cashInfo.bcode_otdel = '3'
        bcode = bot.send_message(call.message.chat.id, 'Напишите штрихкод товара:')
        bot.register_next_step_handler(bcode, set_barcode)

    if call.data == 'cb_barcodes_other':
        logger.info(f"Кнопка 'Прочее' --- {call.message.chat.first_name}")
        cashInfo.bcode_otdel = '4'
        cashInfo.bcode = functions.get_valid_barcode(cashInfo.bcode_cash_number)
        msg = bot.send_message(call.message.chat.id, "Напишите короткое название товара:")
        bot.register_next_step_handler(msg, get_bcode_send)

    # Ostatki
    if call.data == 'cb_get_ostatki':
        logger.info(f"Кнопка 'получить остатки' --- {call.message.chat.first_name}")
        markup = types.InlineKeyboardMarkup()
        button_lastOstatki = types.InlineKeyboardButton("Последние остатки", callback_data='cb_last_ostatki')
        button_listOstatki = types.InlineKeyboardButton("Список по датам", callback_data='cb_list_ostatki')
        markup.add(button_lastOstatki, button_listOstatki)
        bot.send_message(call.message.chat.id,
                         '<u><b>Последние остатки</b></u> - Получить последние сгенерированные остатки\n\n'
                         '<u><b>Список по датам</b></u> - Выведем даты последних 6 сгенерированных накладных',
                         reply_markup=markup, parse_mode='html')
    if call.data == 'cb_choose_date_1':
        logger.info(f"Выбрали остатки: 1")
        cashInfo.select_index_date = 1
        send_file(call.message)
    if call.data == 'cb_choose_date_2':
        logger.info(f"Выбрали остатки: 2")
        cashInfo.select_index_date = 2
        send_file(call.message)
    if call.data == 'cb_choose_date_3':
        logger.info(f"Выбрали остатки: 3")
        cashInfo.select_index_date = 3
        send_file(call.message)
    if call.data == 'cb_choose_date_4':
        logger.info(f"Выбрали остатки: 4")
        cashInfo.select_index_date = 4
        send_file(call.message)
    if call.data == 'cb_choose_date_5':
        logger.info(f"Выбрали остатки: 5")
        cashInfo.select_index_date = 5
        send_file(call.message)
    if call.data == 'cb_choose_date_6':
        logger.info(f"Выбрали остатки: 6")
        cashInfo.select_index_date = 6
        send_file(call.message)
    if call.data == 'cb_last_ostatki':
        logger.info(f"Кнопка 'Последние остатки' --- {call.message.chat.first_name}")
        msg = bot.send_message(call.message.chat.id, 'Напишите номер компьютера:\n'
                                                     'Нужны только цифры. Например: <b><u>902</u></b>',
                               parse_mode='html')
        bot.register_next_step_handler(msg, send_last_file)

    if call.data == 'cb_list_ostatki':
        logger.info(f"Кнопка 'Список остатков' --- {call.message.chat.first_name}")
        msg = bot.send_message(call.message.chat.id, 'Напишите номер компьютера:\n'
                                                     'Нужны только цифры. Например: <b><u>902</u></b>',
                               parse_mode='html')
        bot.register_next_step_handler(msg, send_dates_files)
    # send email
    if call.data == "cb_send_email":
        try:
            msg = bot.send_message(call.message.chat.id, 'Введите почту: ')
            bot.register_next_step_handler(msg, send_email)
        except Exception as ex:
            bot_error_send(call.message)
            logger.error(f'{ex} --- {cashInfo.cash_number}')
    # MarkUP
    if call.data == 'cb_click_form':
        logger.info(f"Кнопка 'Оставить отзыв' --- {call.message.chat.first_name}")
    if call.data == 'cb_WhatsApp_markup':
        logger.info(f"Кнопка 'Тех.Поддержка' --- {call.message.chat.first_name}")


def start_select(message):
    # markup = types.InlineKeyboardMarkup()
    # ostatki = types.InlineKeyboardButton("Получить остатки", callback_data='cb_get_ostatki')
    # barcodes = types.InlineKeyboardButton("Добавить штрихкод", callback_data='cb_generate_barcodes')
    # markup.add(ostatki, barcodes)
    # bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

    markup = types.InlineKeyboardMarkup()
    button_lastOstatki = types.InlineKeyboardButton("Последние остатки", callback_data='cb_last_ostatki')
    button_listOstatki = types.InlineKeyboardButton("Список по датам", callback_data='cb_list_ostatki')
    markup.add(button_lastOstatki, button_listOstatki)
    bot.send_message(message.chat.id,
                     '<u><b>Последние остатки</b></u> - Получить последние сгенерированные остатки\n\n'
                     '<u><b>Список по датам</b></u> - Выведем даты последних 6 сгенерированных накладных',
                     reply_markup=markup, parse_mode='html')
    return markup


def markup_WhatsApp():
    markup_WhatsApp = types.InlineKeyboardMarkup()
    markup_WhatsApp.add(types.InlineKeyboardButton('Тех.Поддержка', url='https://wa.me/79600484366',
                                                   callback_data='cb_WhatsApp_markup'))
    return markup_WhatsApp


def check_valid_cash(message, cash):
    if cash == '--':
        logger.error(f'Данной кассы не найдено "{message.text}"')

        bot.send_message(message.chat.id, "Данной кассы не найдено \n\n"
                                          "Обратитесь в тех. поддержку",
                         parse_mode='html', reply_markup=markup_WhatsApp())
        return False
    elif cash == '---':
        logger.error(f'Нашлось больше одной кассы "{message.text}"')
        bot.send_message(message.chat.id, "Нашлось больше одной кассы\n\n"
                                          "Обратитесь в тех. поддержку",
                         parse_mode='html', reply_markup=markup_WhatsApp())
        return False


def bot_error_send(message):
    bot.send_message(message.chat.id, 'Внутреняя ошибка, попробуйте снова')
    start_select(message)


def send_last_file(message):
    try:
        regex = re.compile(r'[0-9]{1,4}')
        if re.fullmatch(regex, message.text):
            logger.info(f"Ввели номер компьютера '{message.text}'")
            cash = functions.check_repeat_cash(message.text)
            logger.info(f'check_repeat_cash нашел "{cashInfo.cash_number}"')
            check_valid_cash(message, cash)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Отправить на почту', callback_data='cb_send_email'))
            xlsx = open(functions.get_last_file(cashInfo.cash_number), 'rb')
            cashInfo.current_path_file = functions.get_last_file(cashInfo.cash_number)

            logger.info(
                f'Отправил последние остатки "{functions.get_last_file(cashInfo.cash_number)}" --- {cashInfo.cash_number}')
            bot.send_document(message.chat.id, xlsx, reply_markup=markup)

            # Block WhatsApp
            cash_dates = cashInfo.current_path_file.split('/')[-1]  # Берём только название файла
            cash_times = ":".join(cash_dates.split("_")[4:6]).split(".")[0]  # Берём только  время из названия файла
            cash_dates = cash_dates.split("_")[0:3]
            cash_dates.reverse()
            cash_dates = '-'.join(cash_dates)  # Берём только даты из названия файла
            cash_datesAndTimes = cash_dates + " " + cash_times
            bot.send_message(message.chat.id, f'Остатки <b><u>{cash_datesAndTimes}</u></b>\n\n'
                                              f'Чтобы получить более свежие остатки, обратитесь к нам в тех.поддержку',
                             reply_markup=markup_WhatsApp(), parse_mode="html")

            # Block Google Form
            markup_Form = types.InlineKeyboardMarkup()
            markup_Form.add(types.InlineKeyboardButton('Оставить отзыв', callback_data='cb_click_form',
                                                       url='https://forms.gle/CbUD1SLiNnWcYwz28'))
            bot.send_message(message.chat.id, 'Оставьте пожалуйста отзыв', reply_markup=markup_Form, parse_mode='html')

            # Block continue
            start_select(message)
        else:
            logger.debug("Номер компьютера введен не правильно - " + message.text)
            bot.send_message(message.chat.id, 'Номер кассы введена не правильно')
            start_select(message)
    except Exception as ex:
        bot_error_send(message)
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_dates_files(message):
    try:
        regex = re.compile(r'[0-9]{1,4}')
        if re.fullmatch(regex, message.text):
            logger.info(f"Ввели номер компьютера '{message.text}'")
            cash = functions.check_repeat_cash(message.text)
            logger.info(f'check_repeat_cash нашел "{cashInfo.cash_number}"')
            check_valid_cash(message, cash)
            cash_files = functions.get_last_files(cashInfo.cash_number, 6)
            markup = types.InlineKeyboardMarkup()
            cash_dates = [line.split("/")[-1] for line in cash_files]  # Берём только название файла
            # cash_dates = [line.split("/")[-1] for line in cash_files]  # Берём только даты
            cash_times = [":".join(line.split("_")[4:6]).split('.')[0] for line in
                          cash_dates]  # Берём только даты из названия файла
            cash_dates = [line.split("_")[0:3] for line in cash_dates]  # Берём только даты из названия файла
            for line in cash_dates:
                line.reverse()  # Переворачиваем чтобы даты были день-месяц-год
            cash_dates = ['-'.join(line) + " " + cash_times[count] for count, line in
                          enumerate(cash_dates)]  # Соединяем даты
            logger.info(f"Список остатков {cash_dates}")
            buttons = [types.InlineKeyboardButton(line, callback_data=f'cb_choose_date_{count}') for count, line in
                       enumerate(cash_dates)]

            for i in buttons:
                markup.add(i)

            # Инфа для глобальных переменных
            cashInfo.path_to_files = cash_files
            cashInfo.dates_files = cash_dates

            bot.send_message(message.chat.id, 'Выберите нужную дату остатков:', reply_markup=markup)
        else:
            logger.debug("Номер кассы введена не правильно - " + message.text)
            bot.send_message(message.chat.id, 'Номер кассы введена не правильно')
            start_select(message)
    except Exception as ex:
        bot_error_send(message)
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_file(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Отправить на почту', callback_data='cb_send_email'))
        path = cashInfo.path_to_files[cashInfo.select_index_date]

        # Инфа для глобальной переменной
        cashInfo.current_path_file = path
        logger.info(f'Отправил остатки по выбранной дате "{path}" --- {cashInfo.cash_number}')
        bot.send_document(message.chat.id, open(path, 'rb'), reply_markup=markup)
        # Block WhatsApp
        bot.send_message(message.chat.id, f'Чтобы получить более свежие остатки, обратитесь к нам в тех.поддержку',
                         reply_markup=markup_WhatsApp())

        # Block Google Form
        markup_Form = types.InlineKeyboardMarkup()
        markup_Form.add(types.InlineKeyboardButton('Оставить отзыв', callback_data='cb_click_form',
                                                   url='https://forms.gle/CbUD1SLiNnWcYwz28'))
        bot.send_message(message.chat.id, 'Оставьте пожалуйста отзыв', reply_markup=markup_Form, parse_mode='html')

        # Block continue
        start_select(message)
    except Exception as ex:
        bot_error_send(message)
        logger.error(f'{ex} --- {cashInfo.cash_number}')


def send_email(message):
    try:
        regex = re.compile(r'.+@.+\..+')

        if re.fullmatch(regex, message.text):
            functions.send_email(message.text, cashInfo.current_path_file)
            logger.info(f'Отправил {cashInfo.current_path_file} на почту {message.text} --- {cashInfo.cash_number}')
            bot.send_message(message.chat.id, 'Сообщение отправлено на почту\n\n'
                                              'Если сообщение не приходит, то оно возможно у вас в <b><u>спаме</u></b>',
                             parse_mode='html')
            start_select(message)
        else:
            logger.debug("Электронная почта введена не правильно - " + message.text + ' | cash-' + cashInfo.cash_number)
            bot.send_message(message.chat.id, 'Электронная почта введена не правильно')
            start_select(message)
    except Exception as ex:
        bot_error_send(message)
        logger.error(f'{ex} --- {cashInfo.cash_number} or {cashInfo.bcode_cash_number}')


def gen_bcode_start(message):
    try:
        regex = re.compile(r'[0-9]{1,4}')
        if re.fullmatch(regex, message.text):
            logger.info(f"Ввели номер компьютера '{message.text}'")
            cash = functions.check_repeat_cash(message.text)
            if check_valid_cash(message, cash) == False:
                start_select(message)
                return False
            cash_number = functions.check_repeat_cash(message.text).split('-')
            logger.info(f'check_repeat_cash нашел "cash-{cash_number[1]}-{cash_number[2]}"')
            cashInfo.bcode_cash_number = f'{cash_number[1]}-{cash_number[2]}'
            markup = types.InlineKeyboardMarkup()
            alcohol = types.InlineKeyboardButton('Крепкий алкоголь', callback_data='cb_barcodes_alcohol')
            beer = types.InlineKeyboardButton('Пиво', callback_data='cb_barcodes_beer')
            cigarettes = types.InlineKeyboardButton('Сигареты', callback_data='cb_barcodes_cigaretes')
            other = types.InlineKeyboardButton('Прочее', callback_data='cb_barcodes_other')
            markup.add(alcohol, beer, cigarettes, other)

            msg = bot.send_message(message.chat.id, 'Выберите какой товар хотите добавить:\n\n'
                                                    '<u><b>Крепкий алкоголь</b></u> - всё что имеет акцизную марку\n\n'
                                                    '<u><b>Пиво</b></u> - любой вид пива\n\n'
                                                    '<u><b>Сигареты</b></u> - любой вид сигарет\n\n'
                                                    '<u><b>Прочее</b></u> - товары которые продаются как правило через ИП. Например: мыло, треугольник, хлеб',
                                   reply_markup=markup, parse_mode='html')
        else:
            logger.debug("Номер кассы введена не правильно - " + message.text)
            bot.send_message(message.chat.id, 'Номер кассы введена не правильно')
            start_select(message)
    except Exception as ex:
        bot_error_send(message)
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
        bot.send_message(message.chat.id, 'Штрихкод должен быть только из цифр. Попробуйте всё с начала')
        start_select(message)


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
                             parse_mode='html')
            start_select(message)
            with open(f'{config.server_path}telegram_barcode.txt',
                      'a') as barcodes_file:  # Инфа для скрипта, который будет добавлять на компы штрихкода
                barcodes_file.write(
                    'cash-' + cashInfo.bcode_cash_number + "|" + cashInfo.bcode + '|' + cashInfo.bcode_otdel + '|' + cashInfo.bcode_name + '\n')
                logger.info(
                    'Добавил: cash-' + cashInfo.bcode_cash_number + "|" + cashInfo.bcode + '|' + cashInfo.bcode_otdel + '|' + cashInfo.bcode_name + '\n')
        else:
            logger.debug(
                f"Штрихкод неверен {message.text} - длина штрихкода({len(message.text)}) --- {cashInfo.bcode_cash_number}")
            bot.send_message(message.chat.id, 'Название товара введено не верно. Максимальная длина 35 символов')
            start_select(message)
    except Exception as ex:
        bot_error_send(message)
        logger.error(f'{ex} --- {cashInfo.bcode_cash_number}')


bot.polling()
