
import telebot


from db.DBTools import  DBWorker, State
from robotaparser.WorkProcessor import WorkProcessor

token_storage = open('tokenfile.txt','r')
token = token_storage.readline()
token_storage.close()



bot = telebot.TeleBot(token)

db_worker = DBWorker()


@bot.message_handler(commands=['start'])
def on_start(message):

    query_result = db_worker.get_user_by_id(chat_id=message.chat.id)

    if query_result is None:

        db_worker.create_new_user(chat_id=message.chat.id)


        bot.send_message(message.chat.id, "Привет.\nДавай познакомимся?\nЯ - jobsearcher.\n Подскажи мне свое имя.")
        db_worker.set_user_state(message.chat.id, State.S_ENTER_NAME.value)

    else:
        bot.send_message(message.chat.id,
                         "Привет, "
                         + query_result.name + "\nРад новой встрече. Подскажи город в котором будем искать работу")
        db_worker.set_user_state(message.chat.id, State.S_ENTER_CITY.value)
    #db_worker.session_close()


@bot.message_handler(commands=['urefresh'])
def on_refresh(message):
    db_worker.refresh_user(message.chat.id)
    #db_worker.session_close()
    bot.send_message(message.chat.id, "Привет.\nДавай познакомимся? Я jobsearcher. Подскажи мне свое имя.")
    db_worker.set_user_state(message.chat.id, State.S_ENTER_NAME.value)




@bot.callback_query_handler(func=lambda call: True)
def inline_button_handler(query):

    if query.data == 'change_request':
        bot.delete_message(query.message.chat.id, query.message.message_id)
        bot.send_message(query.message.chat.id, "В каком городе нужно искать вакансии?")
        db_worker.set_user_state(query.message.chat.id, State.S_ENTER_CITY.value)

    if query.data.find("pg") != -1:
        selected_page = int(query.data.split('-')[-1])

        user = db_worker.get_user_by_id(chat_id=query.message.chat.id)
        #db_worker.session_close()

        work_processor = WorkProcessor(user.city, user.query)
        job_list = work_processor.get_offer_list(page=selected_page)

        result = ''
        if len(job_list) != 0:
            result += "Всего найдено " + str(work_processor.get_offer_count()) + " вакансий\n"+"Вы находитесь на странице №" + str(selected_page+1) +"\n\n"
            for item in job_list:
                result += item['name'] + '\n' + item['publication_date'] + '\n' + item['vacancy_link'] + '\n' + '\n'
            keyboard = telebot.types.InlineKeyboardMarkup()
            change_button = telebot.types.InlineKeyboardButton('Изменить запрос', callback_data='change_request')

            if work_processor.has_next(selected_page) and work_processor.has_prev(selected_page):
                next_page = str(selected_page + 1)
                prev_page = str(selected_page - 1)
                keyboard.row(telebot.types.InlineKeyboardButton('Пред. страница', callback_data='pg-' + prev_page),
                             telebot.types.InlineKeyboardButton('След. страница', callback_data='pg-' + next_page))

            elif work_processor.has_prev(selected_page):
                prev_page = str(selected_page - 1)
                keyboard.row(telebot.types.InlineKeyboardButton('Пред. страница', callback_data='pg-' + prev_page))

            elif work_processor.has_next(selected_page):
                next_page = str(selected_page + 1)
                keyboard.row(telebot.types.InlineKeyboardButton('След. страница', callback_data='pg-'+next_page))

            keyboard.add(change_button)

            bot.edit_message_text(chat_id=query.message.chat.id,
                                  message_id=query.message.message_id,
                                  text=result,
                                  reply_markup=keyboard,
                                  disable_web_page_preview=True)

            db_worker.set_user_state(query.message.chat.id, State.S_ENTER_CITY.value)

        else:
            result = 'К сожалению, по Вашему запросу ничего не найдено'

            change_button = telebot.types.InlineKeyboardButton('Изменить запрос', callback_data='change_request')
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(change_button)
            bot.send_message(user.telegram_id, result, reply_markup=keyboard, disable_web_page_preview=True)


@bot.message_handler(func=lambda message: db_worker.get_user_state(chat_id=message.chat.id) == State.S_ENTER_NAME.value)
def get_name(message):

    db_worker.update_user(telegram_id=message.chat.id, name=message.text)
    user = db_worker.get_user_by_id(chat_id=message.chat.id)
    #db_worker.session_close()

    bot.send_message(user.telegram_id,
                     "Приятно познакомиться, " + user.name + "\n" + "В каком городе нужно искать вакансии?")

    db_worker.set_user_state(message.chat.id, State.S_ENTER_CITY.value)


@bot.message_handler(func=lambda message: db_worker.get_user_state(chat_id=message.chat.id) == State.S_ENTER_CITY.value )
def get_city(message):

    db_worker.update_user(telegram_id=message.chat.id, city=message.text)
    user = db_worker.get_user_by_id(chat_id=message.chat.id)
    #db_worker.session_close()
    bot.send_message(message.chat.id,
                     "Ищем вакансии в городе " + user.city + '\n' + user.name + ", какая работа тебя интересует?"  )
    db_worker.set_user_state(message.chat.id, State.S_ENTER_QUERY.value)


@bot.message_handler(func=lambda message: db_worker.get_user_state(chat_id=message.chat.id) == State.S_ENTER_QUERY.value)
def get_query(message):

    db_worker.update_user(telegram_id=message.chat.id, query=message.text)
    user = db_worker.get_user_by_id(chat_id=message.chat.id)
    bot.send_message(message.chat.id, "Ищем вакансии по запросу \n" + user.city + ', ' + user.query)
    #db_worker.session_close()
    work_processor = WorkProcessor(user.city, user.query)

    query_result = work_processor.get_offer_list()
    result = ''
    keyboard = telebot.types.InlineKeyboardMarkup()
    if len(query_result) == 0:
        result = 'По Вашему запросу ничего не найдено'
    else:
        result += "По вашему запросу найдено " + str(work_processor.get_offer_count()) + " вакансий\nВы находитесь на странице №1 \n\n"
        for item in query_result:
            result += item['name'] + '\n' + item['company_name']  +'\n'+item['publication_date'] + '\n' + item['vacancy_link'] + '\n' +'\n'
        keyboard.row(
            telebot.types.InlineKeyboardButton('Cлед. страница', callback_data='pg-1')
        )

    change_button = telebot.types.InlineKeyboardButton('Изменить запрос', callback_data='change_request')

    keyboard.add(change_button)
    bot.send_message(user.telegram_id, result, reply_markup=keyboard, disable_web_page_preview=True)


bot.polling()
