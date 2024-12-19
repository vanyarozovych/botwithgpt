
import datetime
import disnake
from disnake.ext import commands, tasks
import pytz
import asyncio

# Декоратор для проверки ролей
role_check = commands.check_any(
    commands.has_role(1123262857614721104),
    commands.has_role(1123263812884234360),
    commands.has_role(760998034850709540)
)


def setup(bot):
    # Общая функция для отправки сообщений об ивентах
    async def send_event_message(ctx, title, description, image_url):
        channel_id = 1291935428227760210  # ID текстового канала
        target_channel = ctx.bot.get_channel(channel_id) if ctx else bot.get_channel(channel_id)

        if target_channel:
            embed = disnake.Embed(title=title, description=description, color=0x323232)
            embed.set_image(url=image_url)
            await target_channel.send(embed=embed)
        else:
            if ctx:
                await ctx.send("Канал не найден.")

    # Команды для запуска ивентов
    @bot.command()
    @role_check
    async def event_among_us(ctx):
        await send_event_message(ctx, "AMONG US!",
                                 "<@&1291935144827031647> Начинается ивент по игре Among Us!\nЗаходите все в "
                                 "голосовой канал!",
                                 "https://media.tenor.com/BGQHhBwbYNwAAAAC/among-us.gif")

    @bot.command()
    @role_check
    async def event_puzzle(ctx):
        await send_event_message(ctx, "Puzzle!",
                                 "<@&1291935144827031647> Начинается ивент по игре Puzzle!\nЗаходите все в голосовой "
                                 "канал!",
                                 "https://i.gifer.com/BgeK.gif")

    @bot.command()
    @role_check
    async def event_film(ctx):
        await send_event_message(ctx, "Film!",
                                 "<@&1291935144827031647> Начинается ивент по просмотру Кино-фильмов!\nЗаходите все в "
                                 "голосовой канал!",
                                 "https://i.gifer.com/7FAC.gif")

    @bot.command()
    @role_check
    async def event_minecraft(ctx):
        await send_event_message(ctx, "MINECRAFT!",
                                 "<@&1291935144827031647> Начинается ивент по игре Minecraft!\n\n- IP: "
                                 "vanyarozovych.aternos.me:56613\n- Version: 1.16.5 \n- Режим игры: выживание\n-"
                                 "Давайте развиваться вместе!\n\n- (Если вы впервые заходите на сервер, "
                                 "попросите одного из ивентёров добавить вас в whitelist, чтобы у вас был доступ к "
                                 "заходу на сервер)",
                                 "https://media.tenor.com/c8zAMfdwlDgAAAAC/dwdsd.gif")

    @bot.command()
    @role_check
    async def event_brawlstars(ctx):
        await send_event_message(ctx, "BRAWLSTARS!",
                                 "<@&1291935144827031647> Начинается ивент по игре BrawlStars!",
                                 "https://media.tenor.com/7-endVMZbCoAAAAi/eshkere-edgar.gif")

    @bot.command()
    @role_check
    async def event_mafia(ctx):
        await send_event_message(ctx, "MAFIA!",
                                 "<@&1291935144827031647> Начинается ивент по игре Mafia!",
                                 "https://media1.tenor.com/m/DHR-LGMxXqYAAAAC/mafia.gif")

    @bot.command()
    @role_check
    async def event_alias(ctx):
        await send_event_message(ctx, "ALIAS!",
                                 "<@&1291935144827031647> Начинается ивент по игре Alias!",
                                 "https://media1.tenor.com/m/gWT2QqylI7gAAAAC/word-funny.gif")

    @bot.command()
    @role_check
    async def event_gartic(ctx):
        await send_event_message(ctx, "GARTIC PHONE!",
                                 "<@&1291935144827031647> Начинается ивент по игре Gartic Phone!",
                                 "https://media1.tenor.com/m/9u4aLvK2ZDcAAAAC/garticphone.gif")

    @bot.command()
    @role_check
    async def event_bunker(ctx):
        await send_event_message(ctx, "Бункер!",
                                 "<@&1291935144827031647> Начинается ивент по игре Бункер! Заходите в голосовой канал!",
                                 "https://media1.tenor.com/m/0md5xJfu43gAAAAd/hiding-bunker.gif")

    @bot.command()
    @role_check
    async def event_monopoly(ctx):
        await send_event_message(ctx, "Монополия!",
                                 "<@&1291935144827031647> Начинается ивент по игре Монополия! Собираемся в голосовой "
                                 "канал!",
                                 "https://media1.tenor.com/m/akLtEJPULVIAAAAC/flip-monopoly.gif")

    @bot.command()
    @role_check
    async def event_durak_online(ctx):
        await send_event_message(ctx, "Дурак Онлайн!",
                                 "<@&1291935144827031647> Начинается ивент по игре Дурак Онлайн! Присоединяйтесь к "
                                 "голосовому каналу!",
                                 "https://media1.tenor.com/m/3D9hAwFbegYAAAAC/cards-game.gif")

    @bot.command()
    @role_check
    async def event_goose_goose_duck(ctx):
        await send_event_message(ctx, "Goose Goose Duck!",
                                 "<@&1291935144827031647> Начинается ивент по игре Goose Goose Duck! Заходите в "
                                 "голосовой канал!",
                                 "https://media1.tenor.com/m/BRfKDZEC_7MAAAAC/goosegooseduck-ggd.gif")

    @bot.command()
    @role_check
    async def event_supermarket_together(ctx):
        await send_event_message(ctx, "Supermarket Together!",
                                 "<@&1291935144827031647> Начинается ивент по игре Supermarket Together! Встречаемся "
                                 "в голосовом канале!",
                                 "https://media1.tenor.com/m/37QecuowWqwAAAAC/epik-high-grocery-shopping.gif")


