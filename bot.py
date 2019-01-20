'''
Бот должен понимать следующие команды:
near_lesson GROUP_NUMBER - ближайшее занятие для указанной группы;
DAY WEEK_NUMBER GROUP_NUMBER - расписание занятий в указанный день (monday, thuesday, ...). Неделя может быть четной (1), нечетной (2) или же четная и нечетная (0);
tommorow GROUP_NUMBER - расписание на следующий день (если это воскресенье, то выводится расписание на понедельник, учитывая, что неделя может быть четной или нечетной);
all WEEK_NUMBER GROUP_NUMBER - расписание на всю неделю.
??? день когда нет пар
'''


import telebot

access_token = "278609498:AAEGcVz87gUs6OEafjEjWyrOZoQOn7-qa2I"
# Создание бота с указанным токеном доступа
bot = telebot.TeleBot(access_token)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Hello! I'm ScheduleBot.\n"
    )

# Бот будет отвечать только на текстовые сообщения
#@bot.message_handler(content_types=['text'])
#def echo(message):
#bot.send_message(message.chat.id, message.text)


import requests
import config
import time
from time import strftime

clock = strftime("%A %H %U")
_, hour, num_week = clock.split()
print(hour)
print(num_week)

def week_number(num_week):
    if int(num_week) % 2 == 0:
        return 1
    else: return 2

week_day = {"monday": "1day",
            "thuesday":"2day",
            "wensday": "3day",
            "thursday": "4day",
            "friday":"5day",
            "saturday": "6day"
            }

def get_page(group, week = ''):
    if week:
        week = str(week) + '/'
    url = '{domain}/{group}/{week}raspisanie_zanyatiy_{group}.htm'.format(
        domain=config.domain, 
        week=week, 
        group=group)
    response = requests.get(url)
    web_page = response.text
    return web_page

from bs4 import BeautifulSoup

def get_schedule(web_page,day = ""):
    soup = BeautifulSoup(web_page)

    # Получаем таблицу с расписанием на понедельник
    schedule_table = soup.find("table", attrs={"id": day})
    if schedule_table is None:
        times_list, locations_list, lessons_list = '0','0','0'
        return times_list, locations_list, lessons_list
    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий и номер аудитории
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.text.split('\n\n') for room in locations_list]
    locations_list = [', '.join([info for info in room_info if info]) for room_info in locations_list]

    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
    lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]

    return times_list, locations_list, lessons_list

#day_rasp возвращает распиасние на желаемый день(работает)

@bot.message_handler(commands=["monday", "thuesday", "wensday", "thursday", "friday", "saturday"])
def get_day(message):
    _, group, week, day = message.text.split()
    day = week_day[day]
    web_page = get_page(group,week)
   
    times_lst, locations_lst, lessons_lst = get_schedule(web_page,day)
    if  times_lst == '0' and locations_lst== '0' and lessons_lst == '0':
        error = 'No lesson today'
        bot.send_message(message.chat.id, error, parse_mode='HTML')
    else:
        resp = ''
        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)

        bot.send_message(message.chat.id, resp, parse_mode='HTML')


           
# allrasp возвращает расписание на всю неделю с возможностью выбора четности недели(с ошибкой)
@bot.message_handler(commands=['allrasp'])
def get_all_rasp(message):
    _, group, week = message.text.split()
    web_page = get_page(group,week)
    
    for day in ["1day","2day","3day","4day","5day","6day"] :
        times_lst, locations_lst, lessons_lst = get_schedule(web_page,day)
        if  times_lst == '0' and locations_lst== '0' and lessons_lst == '0':
            error = 'No lesson today'
            bot.send_message(message.chat.id, error, parse_mode='HTML')
        else:
            resp = ''
            for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
                resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)

            bot.send_message(message.chat.id, resp, parse_mode='HTML')
 
 
#tommorow_rasp возвращает расписание на завтра(работает)
@bot.message_handler(commands=['tommorow_rasp'])
def get_tommorow_rasp(message):
    _, group = message.text.split()
    day = strftime("%A")
    day = day.lower()

    day = week_day[day]
    if int(day[0]) < 6:
        day = str(int(day[0])+int(1)) + "day"
    elif int(day[0]) == 6:
        day = str(int(day[0])-int(5)) + "day"
    week = week_number(num_week)
    web_page = get_page(group,week)
    times_lst, locations_lst, lessons_lst = get_schedule(web_page,day)
    
    resp = ''
    for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)
    
    bot.send_message(message.chat.id, resp, parse_mode='HTML')
# near_lesson возвращает ближайщую пару для указанной группы(работает)
@bot.message_handler(commands=['near_lesson'])
def get_near_les(message):
    #print("Today is",strftime("%A, %d %b %Y %H:%M:%S %U"))
    _, group = message.text.split()
    day = strftime("%A")
    day = day.lower()
    day = week_day[day]

    web_page = get_page(group,week = week_number(num_week))
    times_lst, locations_lst, lessons_lst = get_schedule(web_page,day)
    if  times_lst == '0' and locations_lst== '0' and lessons_lst == '0':
        error = 'No lesson today'
        bot.send_message(message.chat.id, error, parse_mode='HTML')
    else:
        j=0
        resp = ''
        for i in times_lst:
            h=times_lst[j]
            if int(hour) <= int(h.split(":")[0]):
                time,location,lesson = times_lst[j],locations_lst[j],lessons_lst[j]
                resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)
                break
            elif int(hour) > int(h.split(":")[0]):
                day = str(int(day[0])+int(1)) + "day"
                times_lst, locations_lst, lessons_lst = get_schedule(web_page,day)
                time,location,lesson = times_lst[j],locations_lst[j],lessons_lst[j]
                resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)
                break
            j=j+1

        bot.send_message(message.chat.id, resp, parse_mode='HTML')



if __name__ == '__main__':
    bot.polling(none_stop=True)


