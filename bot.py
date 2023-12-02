import cfg
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, types, executor
from sqlighter import SQLighter
from stopgame import StopGame

# logging
logging.basicConfig(level=logging.INFO)

# initializing bot
bot = Bot(token=cfg.API_TOKEN)
dp = Dispatcher(bot)

# connect DB
db = SQLighter('db.db')

# инициализируем парсер
sg = StopGame('lastkey.txt')

# subs activation
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        #add user
        db.add_subscriber(message.from_user.id)
    else:
        #renew user
        db.update_subscription(message.from_user.id, True)
    await message.answer("Вы успешно подписались")
# subs deactivate
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        #add user with inactive status
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы и так не подписаны")
    else:
        #Если он есть в бд, то обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы успешно отписались")

#check new games and mailings
async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        # check new games
        new_games = sg.new_games()
        if (new_games):
            #if there's a new game, turn the list over.
            new_games.reverse()
            for ng in new_games:
                #parse info about new game
                nfo = sg.game_info(ng)

                #bot subscriber list
                subscriptions = db.get_subscriptions()

                #newsletter
                with open(sg.download_image(nfo['image']), 'rb') as photo:
                    for s in subscriptions:
                        await bot.send_photo(
                            s[1],
                            photo,
                            caption=nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n" + nfo['excerpt'] + "\n\n" +
                                    nfo['link'],
                            disable_notification=True
                        )

                #update key
                sg.update_lastkey(nfo['id'])


# long polling
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(10))
    executor.start_polling(dp, skip_updates=True)
