import asyncio
import sqlite3
from asyncio import tasks

import disnake
from disnake.ext import commands, tasks
import json
import time
from datetime import datetime
import pytz

from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import aiosqlite


def initialize_database():
    conn = sqlite3.connect('discord.db')
    c = conn.cursor()

    # User table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        avatar TEXT,
        messages_sent INTEGER DEFAULT 0,
        reactions_sent INTEGER DEFAULT 0,
        time_spent_in_voice_channels INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0,
        birthday DATE,
        exp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )''')

    # Message table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        author_id INTEGER,
        content TEXT,
        timestamp INTEGER,
        edited_timestamp INTEGER
    )''')

    # Reaction table
    c.execute('''CREATE TABLE IF NOT EXISTS reactions (
        reaction_id INTEGER PRIMARY KEY,
        emoji_id TEXT,
        message_id INTEGER,
        user_id INTEGER,
        emoji TEXT
    )''')

    # Voice channels table
    c.execute('''CREATE TABLE IF NOT EXISTS voice_channels (
        voice_channel_id INTEGER PRIMARY KEY,
        name TEXT,
        bitrate INTEGER,
        user_limit INTEGER,
        time_spent_in_channel INTEGER DEFAULT 0
    )''')

    # Role changes table
    c.execute('''CREATE TABLE IF NOT EXISTS role_changes (
        user_id INTEGER,
        old_roles TEXT,
        new_roles TEXT,
        timestamp INTEGER
    )''')

    # Verifications table
    c.execute('''CREATE TABLE IF NOT EXISTS verifications (
         member_id INTEGER,
         inviter_id INTEGER,
         PRIMARY KEY (member_id)
    )''')

    # Shop table
    c.execute('''CREATE TABLE IF NOT EXISTS shop (
        role_id INTEGER,
        price INTEGER
    )''')

    # Cases table
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
        case_name TEXT,
        role_id INTEGER,
        drop_chance REAL,
        price INTEGER
    )''')

    # Case roles table
    c.execute('''CREATE TABLE IF NOT EXISTS case_roles (
        case_name TEXT,
        role_id INTEGER,
        drop_chance REAL
    )''')

    # User roles table
    c.execute('''CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER,
        role_id INTEGER,
        expire_date TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS shop_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        role_name TEXT NOT NULL,
        duration TEXT NOT NULL,
        price INTEGER NOT NULL
    )''')

    # Commit changes to database
    conn.commit()
    conn.close()


# Create bot with specified prefix and intents
intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


def setup(bot):
    try:
        with open('config.json') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Файл 'config.json' не найден.")
        return
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON в файле 'config.json'.")
        return

    myserver = config['guild']

    voice_states = {}
    verification_role_id = {760998034845728780, 760998034792251411}
    invites = {}
    initialize_database()
    inviter_data = {}

    @bot.event
    async def on_ready():
        print('Бот запущен!')
        try:
            print('Вношу данные о пользователях в базу данных')
            guild = await bot.fetch_guild(myserver)
            if guild:
                members = await guild.fetch_members().flatten()
                for member in members:
                    if not member.bot:
                        with sqlite3.connect('discord.db') as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT OR IGNORE INTO users (user_id, username, avatar, messages_sent, "
                                "reactions_sent, time_spent_in_voice_channels, coins, birthday) VALUES (?, ?, ?, 0, "
                                "0, 0, 0, NULL)",
                                (member.id, member.name, str(member.avatar))
                            )
                print('База данных заполнена, и работает исправно')
            else:
                print(f'Не удалось найти гильдию с ID {myserver}.')
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    inviter_data = {}  # Создаем словарь для хранения данных

    @bot.event
    async def on_member_join(member):
        try:
            with sqlite3.connect('discord.db') as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE user_id = ?", (member.id,))
                result = c.fetchone()

                if result:
                    user_id, username, avatar, messages_sent, reactions_sent, time_spent_in_voice_channels, coins, birthday, exp, level, roles = result

                    # Восстановление ролей
                    if roles:
                        saved_roles = [
                            member.guild.get_role(int(role_id)) for role_id in roles.split(",")
                            if member.guild.get_role(int(role_id)) and int(role_id) not in [role.id for role in
                                                                                            member.roles]
                        ]
                        if saved_roles:
                            await member.add_roles(*saved_roles)

                # Выдача стартовых ролей
                roles_to_exclude_1 = [760998034845728780, 760998034792251411]
                role_to_skip_1 = 1288865862232703096

                roles_to_exclude_2 = [
                    760998034792251406, 1132210261487525939, 1298522245446238249,
                    1298522215976796170, 1132209830711545856, 1132210249911246848
                ]
                role_to_skip_2 = 760998034792251406

                roles_to_give = []

                # Проверка для первой стартовой роли
                if not any(role.id in roles_to_exclude_1 for role in member.roles):
                    role_1 = member.guild.get_role(role_to_skip_1)
                    if role_1 and role_1 not in member.roles:
                        roles_to_give.append(role_1)

                # Проверка для второй стартовой роли
                if not any(role.id in roles_to_exclude_2 for role in member.roles):
                    role_2 = member.guild.get_role(role_to_skip_2)
                    if role_2 and role_2 not in member.roles:
                        roles_to_give.append(role_2)

                if roles_to_give:
                    await member.add_roles(*roles_to_give)

                # Приветственное сообщение в канал
                channel = bot.get_channel(1117872265556676728)  # Указанный канал
                if channel:
                    # Сообщение с упоминанием участника и его ID
                    await channel.send(f"{member.mention} **залетел на сервер!** ({member.id})")
                    # Упоминание роли
                    role = member.guild.get_role(760998034850709535)
                    if role:
                        await channel.send(role.mention)

        except Exception as e:
            print(f"Ошибка: {e}")

    async def find_inviter(member):
        try:
            guild_invites = await member.guild.invites()  # Получаем текущие приглашения
            old_invites = invites.get(member.guild.id, [])  # Получаем старые приглашения, если они есть

            if not old_invites:
                print(f"Нет сохранённых приглашений для сервера {member.guild.id}.")
                return None

            # Поиск изменившегося приглашения
            for invite in guild_invites:
                for old_invite in old_invites:
                    if invite.code == old_invite.code and invite.uses > old_invite.uses:
                        return invite.inviter

            print(f"Пригласитель не найден для {member}. Возможно, использовано одноразовое приглашение.")
            return None
        except Exception as e:
            print(f"Ошибка при получении пригласителя для {member}: {e}")
            return None

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        msg = message.content.lower()
        excluded_channel_ids = [760998035483262977, 1123513070870863932, 1297662275196424334]  # ID исключенных каналов

        # Логика начисления опыта за сообщение
        if message.channel.id not in excluded_channel_ids:
            await add_exp(message.author.id, 10)  # Добавлено await перед вызовом
            await check_level_up(message.author)  # Здесь добавляем await

        greeting_words = ["hello", "hi", "привет", "хай"]
        censored_words = [
            "дурак", "идиот", "тупой", "урод", "придурок", "дебил", "глупец", "сволочь", "подлец", "идиотка",
            "тупица", "жалкий", "бестолочь", "козёл", "гадина", "лжец", "олуx", "бес", "мразь", "тупица",
            "ничтожество", "никчёмный", "скотина", "чёрт", "ничтожный", "убогий", "неудачник", "мямля",
            "паршивец", "дура", "злобный", "тупица", "ничтожество", "уродина", "никчёмность", "лицемер",
            "крыса", "лентяй", "позор", "неадекват", "баран", "лох", "идиотизм", "бездарь", "тупорылый",
            "недоумок", "засранец", "болван", "шизик", "больной", "профан", "клоун", "закомплексованный",
            "псих", "убожество", "пиявка", "отвратительный", "придурковатый", "наглец", "трусишка", "лгун",
            "обуза", "бездушный", "жадина", "подставщик", "манипулятор", "ублюдок", "жалобник", "обормот",
            "пустышка", "подонок", "мерзость", "чучело", "дезинформатор", "паскуда", "хлюпик", "выскочка",
            "истерик", "самовлюбленный", "подкаблучник", "лживый", "никудышный", "попрошайка", "хамло",
            "сутенер", "наглец", "паразит", "нытик", "смегма", "безумец"
        ]

        if msg in greeting_words:
            await message.channel.send(f"{message.author.name}, приветствую тебя!")

        # Фильтр нецензурных слов
        for bad_content in msg.split(" "):
            if bad_content in censored_words:
                await message.channel.send(f"{message.author.mention}, Будьте вежливее человечишка!")

        # Логика сохранения сообщений и начисления монет
        if message.channel.id not in excluded_channel_ids:
            save_message(message)
            update_balance(message.author.id, 4)
            increment_message_count(message.author.id)

        # Продолжаем обработку команд
        await bot.process_commands(message)

    # Функция для обновления баланса
    def update_balance(user_id, amount):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result:
                new_balance = result[0] + amount
                c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, user_id))
            else:
                c.execute("INSERT INTO users (user_id, coins) VALUES (?, ?)", (user_id, amount))

            conn.commit()

    # Функция для сохранения сообщения в базу данных
    def save_message(message):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO messages (message_id, channel_id, author_id, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (
                    message.id, message.channel.id, message.author.id, message.content,
                    int(message.created_at.timestamp())
                )
            )
            conn.commit()

    # Функция для обновления количества сообщений
    def increment_message_count(user_id):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT messages_sent FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result:
                new_message_count = result[0] + 1
                c.execute("UPDATE users SET messages_sent = ? WHERE user_id = ?", (new_message_count, user_id))
            else:
                c.execute("INSERT INTO users (user_id, messages_sent) VALUES (?, 1)", (user_id,))

            conn.commit()

    role_multipliers = {
        "760998034850709535": 2,  # Роль 1: 2x монеты
        "1291461515467296808": 2,  # Роль 2: 2x монеты
        "760998034845728786": 2,  # Роль 2: 2x монеты
        "1123262857614721104": 3,  # Роль 2: 3x монеты
        # Добавьте больше ролей по мере необходимости
    }

    @bot.event
    async def on_voice_state_update(member, before, after):
        log_channel_id = 1298466797615317044
        skip_coin_channel_id = 760998036125384774

        try:
            async with aiosqlite.connect('discord.db') as conn:
                c = await conn.cursor()

                if before.channel is None and after.channel is not None:
                    print(f"{member.name} присоединился к голосовому каналу {after.channel.name}")
                    voice_states[member.id] = int(time.time())

                    await c.execute(
                        "INSERT OR IGNORE INTO voice_channels (voice_channel_id, name, bitrate, user_limit, "
                        "time_spent_in_channel) VALUES (?, ?, ?, ?, 0)",
                        (after.channel.id, after.channel.name, after.channel.bitrate, after.channel.user_limit)
                    )
                    await conn.commit()

                elif before.channel is not None and after.channel is None:
                    print(f"{member.name} покинул голосовой канал {before.channel.name}")
                    joined_at = voice_states.pop(member.id, None)
                    if joined_at:
                        time_spent = int(time.time()) - joined_at
                        exp_gained = (time_spent // 60) * 10
                        await add_exp(member.id, exp_gained)
                        await check_level_up(member)

                        if before.channel.id != skip_coin_channel_id:
                            base_coins = time_spent // 60 * 20
                            multiplier = max([role_multipliers[role_id] for role_id in role_multipliers if
                                              any(role.id == int(role_id) for role in member.roles)], default=1)
                            coins_earned = base_coins * multiplier
                            await c.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?',
                                            (coins_earned, member.id))

                        await c.execute(
                            'UPDATE users SET time_spent_in_voice_channels = time_spent_in_voice_channels + ? WHERE user_id = ?',
                            (time_spent, member.id))
                        await c.execute(
                            'UPDATE voice_channels SET time_spent_in_channel = time_spent_in_channel + ? WHERE voice_channel_id = ?',
                            (time_spent, before.channel.id))
                        await conn.commit()

                    log_channel = bot.get_channel(log_channel_id)
                    if log_channel:
                        try:
                            joined_at_str = time.strftime('%H:%M:%S', time.localtime(joined_at))
                            left_at_str = time.strftime('%H:%M:%S', time.localtime(int(time.time())))
                            await log_channel.send(
                                f"{member.name} вошел в канал {before.channel.mention} в {joined_at_str}, провел там {time_spent // 60} минут и вышел в {left_at_str}."
                            )
                        except Exception as log_err:
                            print(f"Ошибка отправки лога: {log_err}")
        except aiosqlite.Error as db_err:
            print(f"Ошибка базы данных: {db_err}")
        except aiohttp.ClientConnectorError as conn_err:
            print(f"Ошибка подключения к Discord API: {conn_err}")
            await asyncio.sleep(5)  # Повтор через 5 секунд
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    async def add_exp(user_id, exp_gained):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT exp, level FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result:
                current_exp, current_level = result
            else:
                current_exp, current_level = 0, 1
                c.execute("INSERT INTO users (user_id, exp, level) VALUES (?, ?, ?)", (user_id, 0, 1))

            new_exp = current_exp + exp_gained
            c.execute("UPDATE users SET exp = ? WHERE user_id = ?", (new_exp, user_id))
            conn.commit()

            return new_exp, current_level

    emoji = "<:fam_coin:1295370513383948339>"

    async def check_level_up(member):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT exp, level, coins FROM users WHERE user_id = ?", (member.id,))
            result = c.fetchone()

            if result:
                exp, level, coins = result  # Извлекаем количество монет
                new_level = level
                level_up_messages = []  # Список для хранения сообщений о повышении уровня

                while True:
                    exp_to_next_level = 100 * (new_level ** 2)
                    if exp >= exp_to_next_level:
                        new_level += 1
                        level_up_messages.append(new_level)  # Сохраняем новый уровень для отправки сообщений
                    else:
                        break

                # Обновляем уровень и монеты только если есть повышения
                if level < new_level:
                    # Обновляем уровень и добавляем 500 монет за каждый новый уровень
                    c.execute("UPDATE users SET level = ?, coins = coins + 500 * ? WHERE user_id = ?",
                              (new_level, new_level - level, member.id))
                    conn.commit()

                    # Уведомляем пользователя о повышении уровней в личные сообщения
                    for level_up in level_up_messages:
                        await member.send(f"Поздравляем! Ты достиг {level_up} уровня и получил 500 {emoji}!")

                    # Канал для уведомлений о получении ролей
                    notification_channel_id = 760998035483262976  # ID канала для уведомлений
                    channel = member.guild.get_channel(notification_channel_id)  # Получаем канал по ID

                    # Автовыдача ролей за достижение уровней
                    roles_to_give = {
                        10: 1132210261487525939,
                        20: 1298522245446238249,
                        30: 1298522215976796170,
                        40: 1132209830711545856,
                        50: 1132210249911246848
                    }

                    # Роли, которые нужно снять при выдаче новых
                    roles_to_remove = {
                        10: 760998034792251406,
                        20: 1132210261487525939,
                        30: 1298522245446238249,
                        40: 1298522215976796170,
                        50: 1132209830711545856
                    }

                    # Проверяем, нужно ли выдать новую роль
                    for level in range(level + 1, new_level + 1):
                        if level in roles_to_give:
                            new_role_id = roles_to_give[level]
                            new_role = member.guild.get_role(new_role_id)

                            if new_role:
                                await member.add_roles(new_role)

                                # Проверяем, нужно ли снять старую роль
                                if level in roles_to_remove:
                                    old_role_id = roles_to_remove[level]
                                    old_role = member.guild.get_role(old_role_id)

                                    if old_role and old_role in member.roles:
                                        await member.remove_roles(old_role)

                                # Отправляем уведомление в канал
                                if channel:
                                    await channel.send(
                                        f"{member.mention}, ты получил роль {new_role.mention} за достижение {level} уровня!"
                                    )

    async def fetch_avatar_image(url):
        # Функция для загрузки аватара пользователя
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        return None

    async def generate_level_image(user: disnake.User, level: int, exp: int, exp_to_next: int):
        try:
            background = Image.open("background_level.jpg").resize((750, 250)).convert("RGB")
        except FileNotFoundError:
            raise Exception("Фоновое изображение не найдено. Убедитесь, что вы указали правильный путь.")

        # Загрузка шрифтов
        font_name = ImageFont.truetype("BubblegumSans-Regular.ttf", 40)
        font_level = ImageFont.truetype("PTSans-Regular.ttf", 24)

        # Загрузка эмодзи
        try:
            santa_hat = Image.open("santa_hat.png").resize((40, 40)).convert("RGBA")
        except FileNotFoundError:
            raise Exception("Файл santa_hat.png не найден. Убедитесь, что он находится в директории.")

        # Аватар пользователя
        avatar_url = user.display_avatar.url
        avatar_data = await fetch_avatar_image(avatar_url)
        if avatar_data:
            avatar = Image.open(io.BytesIO(avatar_data)).resize((150, 150)).convert("RGB")
            mask = Image.new("L", (150, 150), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
            background.paste(avatar, (50, 50), mask=mask)

        # Текст: никнейм
        draw = ImageDraw.Draw(background)
        username_width, _ = draw.textsize(user.name, font=font_name)
        draw.text((250, 50), f"{user.name}", font=font_name, fill="black")

        # Добавление эмодзи рядом с ником
        emoji_x = 250 + username_width + 10  # Смещение эмодзи от конца текста
        emoji_y = 50  # По высоте с ником
        background.paste(santa_hat, (emoji_x, emoji_y), mask=santa_hat)

        # Положение полоски уровня
        bar_y = 160
        text_y = bar_y - 40

        # Текст: уровень и опыт
        draw.text((250, text_y), f"Уровень: {level}", font=font_level, fill="black")
        draw.text((580, text_y), f"{exp} / {exp_to_next}", font=font_level, fill="black", anchor="ra")

        # Прогресс-бар
        bar_x, bar_width, bar_height = 250, 400, 30
        exp_previous_level = 100 * ((level - 1) ** 2) if level > 1 else 0
        progress = (exp - exp_previous_level) / (exp_to_next - exp_previous_level)
        progress = max(0, min(1, progress))

        bar = Image.new("RGB", (bar_width, bar_height))
        draw_bar = ImageDraw.Draw(bar)
        draw_bar.rounded_rectangle((0, 0, bar_width, bar_height), radius=15, fill=(200, 200, 200))
        draw_bar.rounded_rectangle((0, 0, int(bar_width * progress), bar_height), radius=15, fill=(50, 50, 50))
        background.paste(bar, (bar_x, bar_y))

        # Сохранение изображения
        output = io.BytesIO()
        background.save(output, format="PNG")
        output.seek(0)

        return output

    # Команда для Discord бота
    @bot.command(name="level")
    async def check_level(ctx, member: disnake.Member = None):
        member = member or ctx.author  # Если участник не указан, используется автор команды
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT exp, level FROM users WHERE user_id = ?", (member.id,))
            result = c.fetchone()

            if result:
                exp, level = result
                exp_to_next_level = 100 * (level ** 2)  # Формула для опыта
                image = await generate_level_image(member, level, exp, exp_to_next_level)

                # Отправляем картинку в чат
                await ctx.send(file=disnake.File(image, "level.png"))
            else:
                await ctx.send(f"{member.mention}, у тебя пока нет опыта.")

    @bot.command(name="give_exp")
    @commands.has_permissions(administrator=True)  # Только для администраторов
    async def give_exp(ctx, member: disnake.Member, amount: int):
        """Добавить опыт участнику."""
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT exp FROM users WHERE user_id = ?", (member.id,))
            result = c.fetchone()

            if result:
                current_exp = result[0]
                new_exp = current_exp + amount
                c.execute("UPDATE users SET exp = ? WHERE user_id = ?", (new_exp, member.id))
                conn.commit()

                await ctx.send(
                    f"{ctx.author.mention}, вы добавили {amount} опыта {member.mention}. Новый опыт: {new_exp}.")
                # Проверка повышения уровня
                await check_level_up(member)
            else:
                await ctx.send(f"{member.mention} не найден в базе данных.")

    @bot.command(name="remove_exp")
    @commands.has_permissions(administrator=True)  # Только для администраторов
    async def remove_exp(ctx, member: disnake.Member, amount: int):
        """Удалить опыт у участника."""
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT exp, level FROM users WHERE user_id = ?", (member.id,))
            result = c.fetchone()

            if result:
                current_exp, current_level = result
                new_exp = max(0, current_exp - amount)  # Не даем опуститься ниже 0

                # Проверка на новый уровень
                new_level = current_level
                while True:
                    exp_to_next_level = 100 * (new_level ** 2)
                    if new_exp < exp_to_next_level:  # Условие для уменьшения уровня
                        break
                    new_level += 1

                # Уменьшаем уровень, если текущий уровень больше нового
                while new_level > 1 and new_exp < (100 * (new_level - 1) ** 2):
                    new_level -= 1

                # Обновляем данные в базе, если уровень изменился
                if new_level != current_level:
                    c.execute("UPDATE users SET level = ?, exp = ? WHERE user_id = ?",
                              (new_level, new_exp, member.id))
                    conn.commit()

                    await ctx.send(
                        f"{ctx.author.mention}, вы убрали {amount} опыта у {member.mention}. "
                        f"Новый уровень: {new_level}, новый опыт: {new_exp}.")

                    # Уведомляем пользователя о снижении уровня
                    await member.send(f"Ваш уровень понижен до {new_level} из-за уменьшения опыта.")
                else:
                    # Обновляем только опыт, если уровень не изменился
                    c.execute("UPDATE users SET exp = ? WHERE user_id = ?", (new_exp, member.id))
                    conn.commit()

                    await ctx.send(
                        f"{ctx.author.mention}, вы убрали {amount} опыта у {member.mention}. "
                        f"Новый опыт: {new_exp}.")
            else:
                await ctx.send(f"{member.mention} не найден в базе данных.")

    @bot.command(name="set_level")
    @commands.has_permissions(administrator=True)  # Только для администраторов
    async def set_level(ctx, member: disnake.Member, level: int):
        """Установить уровень участнику."""
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            # Получаем текущий опыт пользователя
            c.execute("SELECT exp FROM users WHERE user_id = ?", (member.id,))
            result = c.fetchone()

            if result:
                current_exp = result[0]
                # Вычисляем необходимый опыт для нового уровня
                exp_to_next_level = 100 * (level ** 2)
                # Устанавливаем новый уровень и обновляем опыт
                c.execute("UPDATE users SET level = ?, exp = ? WHERE user_id = ?",
                          (level, min(current_exp, exp_to_next_level - 1), member.id))
                conn.commit()

                await ctx.send(f"{ctx.author.mention}, уровень {member.mention} установлен на {level}.")
                # Проверка повышения уровня
                await check_level_up(member)
            else:
                await ctx.send(f"{member.mention} не найден в базе данных.")

    @bot.event
    async def on_raw_reaction_add(payload):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO reactions (reaction_id, message_id, user_id, emoji_id) VALUES (NULL, ?, ?, ?)",
                (payload.message_id, payload.user_id, payload.emoji.name)
            )
            c.execute(
                "UPDATE users SET reactions_sent = reactions_sent + 1 WHERE user_id = ?",
                (payload.user_id,)
            )

    emoji = "<:fam_coin:1295370513383948339>"

    @bot.event
    async def on_member_update(before, after):
        added_roles = set(after.roles) - set(before.roles)
        for role in added_roles:
            if role.id in verification_role_id:
                inviter = inviter_data.get(after.id)
                if inviter:
                    try:
                        with sqlite3.connect('discord.db') as conn:
                            c = conn.cursor()

                            # Проверка, не приглашал ли уже этот человек данного пользователя
                            c.execute("SELECT inviter_id FROM verifications WHERE member_id = ?", (after.id,))
                            result = c.fetchone()

                            if not result:
                                c.execute("INSERT INTO verifications (member_id, inviter_id) VALUES (?, ?)",
                                          (after.id, inviter.id))
                                conn.commit()

                                # Начисление монет только если человек не был приглашён ранее
                                c.execute("SELECT COUNT(*) FROM verifications WHERE inviter_id = ? AND member_id = ?",
                                          (inviter.id, after.id))
                                count = c.fetchone()[0]

                                if count == 0:
                                    await add_coins_to_user(inviter, 2000)
                                    await inviter.send(
                                        f"Ты получил 2000 {emoji} за приглашение {after.name}, который прошел верификацию!"
                                    )

                                    # Логирование
                                    log_channel_id = 1298472332993630260
                                    log_channel = bot.get_channel(log_channel_id)
                                    if log_channel is not None:
                                        await log_channel.send(
                                            f"{inviter.name} пригласил {after.mention}, прошедшего верификацию, и получил 2000 {emoji}"
                                        )

                                    print(
                                        f"{after.name} получил верификационную роль {role.name}, пригласил: {inviter.name}")
                            else:
                                print(f"Монеты за {after.name} уже начислены.")
                    except Exception as e:
                        print(f"Ошибка при начислении монет {inviter.name}: {e}")



    @bot.command()
    async def set_birthday(ctx, date: str):
        """Команда для установки дня рождения (один раз). Формат: DD-MM-YYYY"""
        user_id = ctx.author.id

        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT birthday FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result and result[0]:
                await ctx.send("Вы уже установили свой день рождения, его нельзя изменить.")
                return

            try:
                birthday = datetime.strptime(date, "%d-%m-%Y").date()
            except ValueError:
                await ctx.send("Неверный формат даты. Пожалуйста, используйте формат DD-MM-YYYY.")
                return

            c.execute("INSERT OR IGNORE INTO users (user_id, birthday) VALUES (?, ?)", (user_id, birthday))
            c.execute("UPDATE users SET birthday = ? WHERE user_id = ?", (birthday, user_id))
            conn.commit()

            await ctx.send(f"Ваш день рождения успешно установлен на {birthday.strftime('%d-%m-%Y')}.")

    @tasks.loop(minutes=1)
    async def birthday_check():
        print("Running 'birthday_check' task.")
        current_date = datetime.now().date()

        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, birthday FROM users WHERE birthday IS NOT NULL")
            birthday_users = c.fetchall()

        for user_id, birthday in birthday_users:
            try:
                birthday_date = datetime.strptime(birthday, "%d-%m-%Y").date()

                if birthday_date.day == current_date.day and birthday_date.month == current_date.month:
                    user = await bot.fetch_user(user_id)
                    guild = bot.get_guild(760998034821349436)
                    channel = guild.get_channel(760998035483262976)  # Birthday announcement channel
                    role = guild.get_role(760998034845728786)  # Birthday role
                    member = guild.get_member(user_id)

                    if member and channel and role:
                        await channel.send(f"Happy Birthday, {user.mention}! 🎉")
                        await member.add_roles(role)

                        # Remove role after 24 hours
                        asyncio.create_task(remove_role_after_delay(member, role, 86400))

                        # Add coins
                        with sqlite3.connect('discord.db') as conn:
                            c = conn.cursor()
                            c.execute("UPDATE users SET coins = coins + 10000 WHERE user_id = ?", (user_id,))
                            conn.commit()

                        await channel.send(f"{user.mention}, you have received 10,000 coins as a birthday gift! 🎁")

            except Exception as e:
                print(f"Error processing user {user_id}: {e}")

    async def remove_role_after_delay(member, role, delay):
        await asyncio.sleep(delay)
        await member.remove_roles(role)

    @bot.command()
    async def birthdays(ctx):
        """Команда для отображения списка ближайших дней рождений."""
        current_date = datetime.now().date()

        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT user_id, birthday FROM users WHERE birthday IS NOT NULL''')
            birthday_data = c.fetchall()

        if not birthday_data:
            await ctx.send("Не найдено ни одного пользователя с установленной датой дня рождения.")
            return

        upcoming_birthdays = []
        for user_id, birthday in birthday_data:
            birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()
            days_left = (birthday_date.replace(year=current_date.year) - current_date).days

            if days_left < 0:
                next_birthday = birthday_date.replace(year=current_date.year + 1)
                days_left = (next_birthday - current_date).days

            upcoming_birthdays.append((user_id, birthday_date, days_left))

        upcoming_birthdays.sort(key=lambda x: x[2])
        upcoming_birthdays = upcoming_birthdays[:5]

        embed = disnake.Embed(title="🎊Ближайшие дни рождения🎊", color=0x2F3136)

        for user_id, birthday_date, days_left in upcoming_birthdays:
            user = await bot.fetch_user(user_id)
            embed.add_field(
                name=f"{user}",
                value=f"Дата: {birthday_date.strftime('%d-%m-%Y')} (через {days_left} дней)",
                inline=False
            )

        await ctx.send(embed=embed)
