import asyncio
import io
import disnake
from disnake.ext import commands
from disnake.ui import View, Button
from discord.utils import get

import requests as requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import threading
import datetime
from datetime import datetime, timedelta
import sqlite3
import pytz

import re
import events
import posts
import database

import economy

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents)

posts.setup(bot)
events.setup(bot)
database.setup(bot)
economy.setup(bot)


@bot.event
async def on_member_remove(member):
    """Сохраняет данные участника при выходе с сервера."""
    try:
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()

            role_ids = [role.id for role in member.roles]
            roles_str = ",".join(map(str, role_ids))

            # Получаем актуальные данные участника (например, количество сообщений, реакций, монет и т.д.)
            c.execute("SELECT * FROM users WHERE user_id = ?", (member.id,))
            user_data = c.fetchone()

            if user_data:
                user_id, username, avatar, messages_sent, reactions_sent, time_spent_in_voice_channels, coins, birthday, exp, level, roles = user_data

                # Сохраняем данные при выходе
                c.execute(
                    "INSERT OR REPLACE INTO users (user_id, username, avatar, messages_sent, reactions_sent, "
                    "time_spent_in_voice_channels, coins, birthday, exp, level, roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, username, avatar, messages_sent, reactions_sent, time_spent_in_voice_channels, coins,
                     birthday, exp, level, roles_str)
                )
                conn.commit()

                print(f"Данные участника {member.name} успешно сохранены.")
            else:
                print(f"Не удалось найти данные для участника {member.name}.")

    except Exception as e:
        print(f"Ошибка при сохранении данных участника: {e}")

    try:
        # Создаем Embed сообщение
        embed = disnake.Embed(title=f"Участник {member.name} покинул сервер",
                              color=disnake.Color.red())

        # Получаем список ролей и создаем упоминания
        roles_list = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(name="Роли", value=", ".join(roles_list) if roles_list else "Без ролей", inline=False)

        # Время пребывания на сервере
        time_spent = "неизвестно"  # Здесь можно добавить логику для вычисления времени
        embed.add_field(name="Пробыл на сервере", value=time_spent, inline=True)

        # Добавляем айди участника
        embed.set_footer(text=f"ID участника: {member.id}")

        # Отправляем Embed сообщение
        channel = bot.get_channel(1130597461304561724)  # Замените на ваш канал
        if channel:
            await channel.send(embed=embed)
    except Exception as e:
        print(f"Ошибка при отправке сообщения о выходе участника: {e}")


# Идентификаторы ролей
role_boy_id = 760998034845728780  # Роль мальчика
role_girl_id = 760998034792251411  # Роль девочки
remove_role_id = 1288865862232703096  # Роль, которую нужно снимать при добавлении
emoji = "<:fam_coin:1295370513383948339>"

@bot.command()
@commands.has_role(760998034850709535)
async def give_boy(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=role_boy_id)
    remove_role = disnake.utils.get(ctx.guild.roles, id=remove_role_id)
    notification_channel_id = 1123513070870863932  # ID канала для уведомлений

    if role is None or remove_role is None:
        await ctx.send("Одна из ролей не найдена.")
        return

    try:
        # Проверяем, были ли уже выданы монеты для этого участника
        conn = sqlite3.connect('discord.db')
        cursor = conn.cursor()
        query = "SELECT coins_given FROM users WHERE user_id = ?"
        cursor.execute(query, (member.id,))
        result = cursor.fetchone()

        if result and result[0] == 1:  # Если монеты уже были выданы (1 — это флаг, указывающий на выдачу)
            await ctx.send(f"{member.display_name} уже получил монеты за этого участника.")
            conn.close()
            return

        # Удаляем старую роль и добавляем новую
        await member.remove_roles(remove_role)
        await member.add_roles(role)
        message = await ctx.send(f"Роль {role.name} успешно добавлена участнику {member.display_name}.")
        await ctx.message.delete(delay=5)
        await message.delete(delay=5)

        # Начисляем монеты
        coins_to_add = 1000
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins_to_add, ctx.author.id))
        cursor.execute("UPDATE users SET coins_given = 1 WHERE user_id = ?", (member.id,))  # Устанавливаем флаг
        conn.commit()
        conn.close()

        # Уведомление в указанный канал
        notification_channel = bot.get_channel(notification_channel_id)
        if notification_channel:
            await notification_channel.send(
                f"{ctx.author.display_name}, вам начислено {coins_to_add} {emoji} за верификацию участника!"
            )
        else:
            await ctx.send("Не удалось найти канал для уведомлений.")

    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")


@bot.command()
@commands.has_role(760998034850709535)
async def give_girl(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=role_girl_id)
    remove_role = disnake.utils.get(ctx.guild.roles, id=remove_role_id)
    notification_channel_id = 1123513070870863932  # ID канала для уведомлений

    if role is None or remove_role is None:
        await ctx.send("Одна из ролей не найдена.")
        return

    try:
        # Проверяем, были ли уже выданы монеты для этого участника
        conn = sqlite3.connect('discord.db')
        cursor = conn.cursor()
        query = "SELECT coins_given FROM users WHERE user_id = ?"
        cursor.execute(query, (member.id,))
        result = cursor.fetchone()

        if result and result[0] == 1:  # Если монеты уже были выданы
            await ctx.send(f"{member.display_name} уже получил монеты за этого участника.")
            conn.close()
            return

        # Удаляем старую роль и добавляем новую
        await member.remove_roles(remove_role)
        await member.add_roles(role)
        message = await ctx.send(f"Роль {role.name} успешно добавлена участнику {member.display_name}.")
        await ctx.message.delete(delay=5)
        await message.delete(delay=5)

        # Начисляем монеты
        coins_to_add = 1000
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins_to_add, ctx.author.id))
        cursor.execute("UPDATE users SET coins_given = 1 WHERE user_id = ?", (member.id,))  # Устанавливаем флаг
        conn.commit()
        conn.close()

        # Уведомление в указанный канал
        notification_channel = bot.get_channel(notification_channel_id)
        if notification_channel:
            await notification_channel.send(
                f"{ctx.author.display_name}, вам начислено {coins_to_add} {emoji} за верификацию участника!"
            )
        else:
            await ctx.send("Не удалось найти канал для уведомлений.")

    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")



@bot.command()
@commands.has_role(1291461515467296808)  # Доступ для удаления только у роли 1291461515467296808
async def remove_boy(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=role_boy_id)
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.remove_roles(role)  # Удаляем роль мальчика
        message = await ctx.send(f"Роль {role.name} успешно удалена у участника {member.display_name}.")
        await ctx.message.delete(delay=5)
        await message.delete(delay=5)
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")


@bot.command()
@commands.has_role(1291461515467296808)  # Доступ для удаления только у роли 1291461515467296808
async def remove_girl(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=role_girl_id)
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.remove_roles(role)  # Удаляем роль девочки
        message = await ctx.send(f"Роль {role.name} успешно удалена у участника {member.display_name}.")
        await ctx.message.delete(delay=5)
        await message.delete(delay=5)
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")


@bot.command()
@commands.has_any_role(760998034850709535, 1291461515467296808)
async def vreject(ctx, member: disnake.Member):
    # Идентификаторы ролей
    role_remove_1 = disnake.utils.get(ctx.guild.roles, id=760998034792251406)
    role_remove_2 = disnake.utils.get(ctx.guild.roles, id=1288865862232703096)
    role_add = disnake.utils.get(ctx.guild.roles, id=1304908919403053146)

    if role_remove_1 is None or role_remove_2 is None or role_add is None:
        await ctx.send("Одна из ролей не найдена.")
        return

    try:
        # Убираем роли и добавляем новую роль
        await member.remove_roles(role_remove_1, role_remove_2)
        await member.add_roles(role_add)

        # Отправляем сообщение об успешном выполнении и удаляем через 5 секунд
        message = await ctx.send(f"Роли успешно изменены для участника {member.display_name}.")
        await ctx.message.delete(delay=5)
        await message.delete(delay=5)
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")


@bot.command()
@commands.check_any(commands.has_role(1123262857614721104))
async def mute_event(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=760998034792251402)  # Замените ID роли на фактический ID
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"Роль {role.name} успешно добавлена участнику {member.display_name}.")
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выдачи этой роли.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при выдаче роли: {str(e)}")


@bot.command()
@commands.check_any(commands.has_role(1123262857614721104))
async def unmute_event(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=760998034792251402)  # Замените ROLE_ID на фактический ID роли
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"Роль {role.name} успешно удалена у участника {member.display_name}.")
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для удаления этой роли.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при удалении роли: {str(e)}")


@bot.command()
@commands.check_any(commands.has_role(1123262857614721104))
async def mute_voice(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=760998034792251403)  # Замените ID роли на фактический ID
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"Роль {role.name} успешно добавлена участнику {member.display_name}.")
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выдачи этой роли.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при выдаче роли: {str(e)}")


@bot.command()
@commands.check_any(commands.has_role(1123262857614721104))
async def unmute_voice(ctx, member: disnake.Member):
    role = disnake.utils.get(ctx.guild.roles, id=760998034792251403)  # Замените ROLE_ID на фактический ID роли
    if role is None:
        await ctx.send("Роль не найдена.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"Роль {role.name} успешно удалена у участника {member.display_name}.")
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для удаления этой роли.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при удалении роли: {str(e)}")


@bot.command()
async def report(ctx, member: disnake.Member, *, reason):
    # Получение объекта канала по ID
    channel_id = 760998035018088492  # Замените на фактический ID текстового канала
    target_channel = bot.get_channel(channel_id)

    if target_channel is not None:
        # Создание embed сообщения
        embed = disnake.Embed(
            title="Репорт",
            description=(
                f"Автор: {ctx.author.mention}\n"
                f"Нарушитель: {member.mention}\n"
                f"Причина: {reason}"
            ),
            color=0xFF0000,
        )

        # Отправка embed сообщения в определенный канал
        await target_channel.send(embed=embed)
    else:
        print("Канал не найден.")


@bot.command()
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount)
    message = await ctx.send(f"Было удалено {amount} сообщений...")
    await asyncio.sleep(15)
    await message.delete()


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: disnake
               .Member, *, reason=None):
    await ctx.message.delete(delay=1)  # Если желаете удалять сообщение после отправки с задержкой

    await member.send(f"Вы были кикнуты с сервера!")  # Отправить личное сообщение пользователю
    await ctx.send(f"Участник {member.mention} был кикнут с сервера!")
    await member.kick(reason=reason)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: disnake
              .Member, *, reason=None):
    await member.send(f"You was banned on server")  # Отправить личное сообщение пользователю
    await ctx.send(f"Member **{member.mention}** was banned on this server")
    await member.ban(reason=reason)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)


@bot.command()
async def mute_user(ctx, member: disnake.Member):
    mute_role = disnake.utils.get(ctx.guild.roles, name="role name")

    if mute_role is not None:
        await member.add_roles(mute_role)
        await ctx.send(f"**{ctx.author}** выдал мут для **{member}**")
    else:
        await ctx.send("Мут-роль не найдена")


@bot.event
async def on_command_error(ctx, error):
    print(error)

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author}, у вас недостаточно прав для выполнения данной команды!")

    elif isinstance(error, commands.UserInputError):
        await ctx.send(embed=disnake.Embed(
            description=(
                f"Правильное использование команды: `{ctx.prefix}{ctx.command.name}` "
                f"({ctx.command.brief})\nExample: {ctx.prefix}{ctx.command.usage}"
            )
        ))


@bot.command()
async def bot_help(ctx):
    embed = disnake.Embed(
        title="Меню",
        description="Здесь вы можете просмотреть доступные команды:"
    )
    commands_list = ["clear", "kick", "ban", "unban"]
    descriptions_for_commands = ["Чистит чат", "Кикает участника", "Банит участника", "Разбанивает участника"]

    for command_name, description_command in zip(commands_list, descriptions_for_commands):
        embed.add_field(
            name=command_name,
            value=description_command,
            inline=False  # Будет выводиться в столбик, если True - в строчку
        )

    await ctx.send(embed=embed)


@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)


@bot.command(aliases=['профиль', 'profile'])
async def card_user(ctx, member: disnake.Member = None):
    if member is None:
        member = ctx.author

    # Создаём базовое изображение
    img_width, img_height = 500, 260
    img = Image.new('RGBA', (img_width, img_height), (20, 20, 30))
    img_draw = ImageDraw.Draw(img)

    # Размеры рамок и вычисление равных промежутков
    box_width, box_height = 180, 200
    margin = 30

    # Координаты рамок
    avatar_box_x = margin
    avatar_box_y = (img_height - box_height) // 2
    avatar_box = (avatar_box_x, avatar_box_y, avatar_box_x + box_width, avatar_box_y + box_height)

    text_box_x = avatar_box[2] + (img_width - 2 * margin - box_width - 100) // 2 - 50
    text_box_y = avatar_box_y
    text_box = (text_box_x, text_box_y, text_box_x + box_width + 50, text_box_y + box_height)

    def draw_rounded_rectangle(draw_obj, box, radius, fill, outline=None, width=3):
        draw_obj.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    # Цвет для левой рамки
    left_container_color = (40, 40, 55)  # Цвет для левой рамки
    right_container_color = (40, 40, 55)  # Цвет для правой рамки

    # Рисуем рамки
    draw_rounded_rectangle(img_draw, avatar_box, radius=30, fill=left_container_color, outline=(80, 80, 120), width=2)
    draw_rounded_rectangle(img_draw, text_box, radius=30, fill=right_container_color, outline=(80, 80, 120), width=2)

    # Получение аватара пользователя и добавление свечения
    avatar_url = str(member.avatar.url) if member.avatar else None
    if avatar_url:
        response = requests.get(avatar_url, stream=True)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)

        glow_radius = 60
        glow_circle = Image.new("RGBA", (glow_radius * 2, glow_radius * 2), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_circle)
        glow_draw.ellipse((0, 0, glow_radius * 2, glow_radius * 2), fill=(150, 200, 255, 220))
        glow_circle = glow_circle.filter(ImageFilter.GaussianBlur(4))

        avatar_center = ((avatar_box[0] + avatar_box[2]) // 2, (avatar_box[1] + avatar_box[3]) // 2 - 15)
        img.paste(glow_circle, (avatar_center[0] - glow_radius, avatar_center[1] - glow_radius), glow_circle)

        mask = Image.new("L", avatar.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        img.paste(avatar, (avatar_center[0] - 70, avatar_center[1] - 70 + 5), mask)

    # Загрузка шрифтов
    username_font = ImageFont.truetype('BubblegumSans-Regular.ttf', 20)  # Уменьшен до 20
    info_font = ImageFont.truetype('PTSans-Regular.ttf', 14)

    # Отображение имени пользователя под аватаркой
    text_x = avatar_box_x + (box_width - int(img_draw.textbbox((0, 0), member.name, font=username_font)[2])) // 2
    text_y = avatar_box[3] - 36
    img_draw.text((text_x, text_y), member.name, font=username_font, fill=(255, 255, 255))

    # Подключение к базе данных для получения данных
    with sqlite3.connect('discord.db') as conn:
        c = conn.cursor()

        # Время в голосе
        c.execute("SELECT time_spent_in_voice_channels FROM users WHERE user_id = ?", (member.id,))
        result = c.fetchone()
        time_spent = result[0] if result is not None and len(result) > 0 else 0
        hours, minutes = divmod(time_spent // 60, 60)

        # Баланс монет
        c.execute("SELECT coins FROM users WHERE user_id = ?", (member.id,))
        coins_result = c.fetchone()
        coins = coins_result[0] if coins_result is not None and len(coins_result) > 0 else 0

        # Количество сообщений
        c.execute("SELECT messages_sent FROM users WHERE user_id = ?", (member.id,))
        user_data = c.fetchone()
        messages_sent = user_data[0] if user_data is not None and len(user_data) > 0 else 0

        # Уровень и опыт
        c.execute("SELECT exp FROM users WHERE user_id = ?", (member.id,))
        user_data = c.fetchone()
        experience = user_data[0] if user_data is not None and len(user_data) > 0 else 0

        # Логика для определения топа по накопленному опыту
        c.execute("SELECT COUNT(*) FROM users WHERE exp > ?", (experience,))
        top_position = c.fetchone()[0] + 1  # Добавляем 1, чтобы учесть текущего пользователя

    # Получаем URL кастомного эмодзи
    emoji_id = '1295370513383948339'
    emoji_url = f'https://cdn.discordapp.com/emojis/{emoji_id}.png'
    emoji_response = requests.get(emoji_url, stream=True)
    emoji_img = Image.open(io.BytesIO(emoji_response.content)).convert('RGBA').resize((20, 20),
                                                                                      Image.Resampling.LANCZOS)

    # Загрузка иконок
    icon_online = Image.open("icon_micro2.png").resize((30, 30)).convert("RGBA")
    icon_messages = Image.open("icon_message.png").resize((30, 30)).convert("RGBA")
    icon_balance = Image.open("icon_pocket2.png").resize((30, 30)).convert("RGBA")
    icon_top = Image.open("icon_top4.png").resize((30, 30)).convert("RGBA")

    # Задаем координаты для иконок
    icons_x = text_box[0] + 10  # Располагаем иконки с небольшим отступом от левой границы текстового контейнера

    # Расчёт вертикальных позиций для равномерного размещения строк с учетом рамки
    text_box_height = text_box[3] - text_box[1]
    num_lines = 4  # Общее количество строк
    line_spacing = (text_box_height - 20) / (num_lines + 1)  # Учитываем отступы сверху и снизу

    # Позиции для текста и иконок
    text_y_positions = [int(text_box[1] + (i + 1) * line_spacing) for i in range(num_lines)]

    # Строка "Онлайн" с временем в голосе
    img.paste(icon_online, (icons_x, text_y_positions[0]), icon_online)
    img_draw.text((icons_x + 40, text_y_positions[0] + 5), f"Онлайн - {hours} ч, {minutes} мин", font=info_font,
                  fill=(255, 255, 255))

    # Строка "Сообщений"
    img.paste(icon_messages, (icons_x, text_y_positions[1]), icon_messages)
    img_draw.text((icons_x + 40, text_y_positions[1] + 5), f"Сообщений - {messages_sent}", font=info_font,
                  fill=(255, 255, 255))

    # Строка "Баланс" с эмодзи монетки
    img.paste(icon_balance, (icons_x, text_y_positions[2]), icon_balance)
    balance_text = f"Баланс - {coins} "
    img_draw.text((icons_x + 40, text_y_positions[2] + 5), balance_text, font=info_font, fill=(255, 255, 255))

    # Отображаем эмодзи рядом с текстом
    emoji_x = int(icons_x + 40 + info_font.getlength(balance_text))
    emoji_y = int(text_y_positions[2] + 5)
    img.paste(emoji_img, (emoji_x, emoji_y), emoji_img)

    # Строка "Топ" с позицией
    img.paste(icon_top, (icons_x, text_y_positions[3]), icon_top)
    img_draw.text((icons_x + 40, text_y_positions[3] + 5), f"Топ - #{top_position}", font=info_font,
                  fill=(255, 255, 255))

    # Сохранение изображения в буфер
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    await ctx.send(file=disnake.File(buf, 'profile_card.png'))


@bot.command()
async def minecraft_server(ctx):
    server = 'vanyarozovych.aternos.me:56613'
    response = requests.get(f'https://api.mcsrvstat.us/2/{server}')
    data = response.json()

    if data['online']:
        message = (
            f"✅ - Сервер `{server}` - онлайн. "
            f"На сервере `{data['players']['online']}`/`{data['players']['max']}` игроков онлайн."
        )
    else:
        message = f"❌ - Сервер `{server}` - оффлайн."

    await ctx.send(message)


@bot.command()
async def massrole(ctx, role: disnake
                   .Role):
    for member in ctx.guild.members:
        if role not in member.roles:
            await member.add_roles(role)


def console_input_loop():
    channel_id = int(
        input("Введите ID канала для отправки сообщений: "))  # ID канала, куда бот будет отправлять сообщения
    channel = bot.get_channel(channel_id)
    if channel is None:
        print("Канал не найден!")
        return
    while True:
        message = input("Введите сообщение для отправки (или 'exit' для выхода): ")
        if message.lower() == 'exit':
            break
        asyncio.run_coroutine_threadsafe(channel.send(message), bot.loop)


# Запуск потока для консоли
thread = threading.Thread(target=console_input_loop)
thread.start()


@bot.command()
async def timestamp(ctx, ts: int):
    """Конвертирует Unix timestamp в читаемый формат даты и времени."""
    dt_object = datetime.datetime.fromtimestamp(ts)
    readable_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    await ctx.send(f"Unix timestamp {ts} соответствует: {readable_time} (UTC)")


@bot.command()
async def download_emojis(ctx):
    guild = ctx.guild
    for emoji in guild.emojis:
        with open(f"{emoji.name}.png", "wb") as f:
            await emoji.url.save(f)
        await ctx.send(f"Скачан эмодзи: {emoji.name}")


temporary_roles = {}


@bot.command()
@commands.has_permissions(manage_roles=True)
async def temp_role(ctx, member: disnake.Member, role: disnake.Role, duration: str):
    """
    Выдаёт роль пользователю на определённое количество времени.

    :param ctx: Контекст команды
    :param member: Участник, которому выдать роль
    :param role: Роль, которую нужно выдать
    :param duration: Время в формате числа и единицы измерения (например, 10m, 2h, 5d).
    """

    # Определяем множители для времени
    time_multipliers = {
        "s": timedelta(seconds=1),
        "m": timedelta(minutes=1),
        "h": timedelta(hours=1),
        "d": timedelta(days=1),
        "w": timedelta(weeks=1),
        "mo": timedelta(days=30),  # Приблизительное значение месяца
        "y": timedelta(days=365)  # Приблизительное значение года
    }

    # Проверка корректного формата duration
    match = re.match(r"(\d+)(s|m|h|d|w|mo|y)", duration)
    if not match:
        await ctx.send("Укажите время в формате `<число><единица>`: s, m, h, d, w, mo, y")
        return

    # Извлекаем количество и единицу времени
    amount = int(match.group(1))
    unit = match.group(2)

    if unit not in time_multipliers:
        await ctx.send("Укажите правильную единицу измерения времени: s, m, h, d, w, mo, y.")
        return

    # Вычисляем время окончания
    end_time = datetime.now() + amount * time_multipliers[unit]

    # Проверка прав на управление ролью
    if ctx.guild.me.top_role <= role:
        await ctx.send("У меня недостаточно прав для управления этой ролью.")
        return

    # Выдаём роль и сохраняем в словаре с временными ролями
    await member.add_roles(role)
    await ctx.send(f"Роль {role.mention} выдана {member.mention} на {amount}{unit}.")

    temporary_roles[(member.id, role.id)] = end_time

    # Ожидание окончания срока действия роли
    await asyncio.sleep((end_time - datetime.now()).total_seconds())

    # Проверка и удаление роли
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Роль {role.mention} удалена у {member.mention} после истечения срока.")

        # Удаляем запись о временной роли
        temporary_roles.pop((member.id, role.id), None)


# Обновленные цены для различных периодов
price_data = {
    "month": [10000, 25000, 40000, 75000, 150000],
    "3months": [20000, 50000, 80000, 150000, 300000],
    "6months": [30000, 75000, 120000, 225000, 450000],
    "year": [50000, 125000, 200000, 375000, 750000],
    "lifetime": [100000, 250000, 400000, 750000, 1500000],
}

# Роли для левой и правой стороны
roles_left = [
    (760998034821349443, "<:6645skeluhhton:1303637995920031798>"),
    (760998034821349444, "<:boar:1303630217084145684>"),
    (760998034821349445, "<:31379melodycupcake:1303636889190010943>"),
    (760998034829344808, "<:23926bubbleheart:1303634815777636393>"),
    None,
    (1295719041423511575, "<:43894saneandnormal:1307435606418395147>"),
    (1295719101603381269, "<:32666sleepy:1303689485904515132>"),
    (1295719187775488050, "<:63638crazyinlove:1303689488593195059>"),
    (1295719141696868392, "<:6013donewlife:1303656110275690518>"),
    None,
    (760998034829344812, ""),
    (760998034829344810, ""),
    (760998034829344816, "<:8465banhammer:1307437208051122226>"),
    (760998034829344815, "<:78017blondiepepe:1307437521063514142>"),
]

roles_right = [
    (1295716063845023775, "<:56387sootstar:1307438004721422386>"),
    (1295715951685144626, "<:79705butterflywings:1303634836652822578>"),
    (1295715743240814653, "<:38896fire:1303634825986572349>"),
    (1295715690568880159, "<:8466_googleeagle:1303634809842696242>"),
    None,
    (1294677582939422793, ""),
]

coin_emoji = "<:fam_coin:1295370513383948339>"


class PageNavigation(View):
    def __init__(self, ctx, page=0):
        super().__init__()
        self.ctx = ctx
        self.page = page

    @disnake.ui.button(label="Перейти назад", style=disnake.ButtonStyle.primary)
    async def previous_page(self, button: Button, interaction: disnake.MessageInteraction):
        self.page = (self.page - 1) % 5  # Переход на предыдущую страницу
        embed = generate_embed(self.page)
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Перейти вперед", style=disnake.ButtonStyle.primary)
    async def next_page(self, button: Button, interaction: disnake.MessageInteraction):
        self.page = (self.page + 1) % 5  # Переход на следующую страницу
        embed = generate_embed(self.page)
        await interaction.response.edit_message(embed=embed, view=self)


def generate_embed(page):
    # Название категории цен
    price_category_name = \
        ["Цена за месяц", "Цена за 3 месяца", "Цена за 6 месяцев", "Цена за год", "Цена за всю жизнь"][page]

    # Центровка текста
    centered_title = f"⠀⠀⠀⠀⠀⠀⠀⠀⠀**Магазин ролей: {price_category_name}**⠀⠀⠀⠀⠀⠀⠀⠀⠀"

    # Создаем embed с центровкой заголовка
    embed = disnake.Embed(title=centered_title, color=0x2F3136)

    # Категория цен в зависимости от страницы
    price_category = ["month", "3months", "6months", "year", "lifetime"][page]

    # Цены для левых и правых ролей
    prices = price_data[price_category]

    # Фильтруем None-значения из ролей
    filtered_left_roles = [item for item in roles_left if item is not None]
    filtered_right_roles = [item for item in roles_right if item is not None]

    # Рассчёт начального номера для текущей страницы
    roles_per_page = len([r for r in roles_left if r is not None]) + len([r for r in roles_right if r is not None])
    start_number = page * roles_per_page + 1

    # Текст для левых ролей с номерами
    left_roles_text = ""
    left_price_index = 0
    role_number = start_number  # Нумерация ролей
    for i in range(0, len(filtered_left_roles), 4):  # Группировка по 4 роли
        group_roles = filtered_left_roles[i:i + 4]
        price = prices[left_price_index]
        left_roles_text += f"Цена: {price:,} {coin_emoji}\n".replace(",", " ")  # Форматирование цены
        for item in group_roles:
            role_id, emoji = item
            left_roles_text += f"{role_number}. {emoji} <@&{role_id}>\n"
            role_number += 1
        left_roles_text += "\n"
        left_price_index += 1

    # Текст для правых ролей с номерами
    right_roles_text = ""
    right_price_index = 0
    for i in range(0, len(filtered_right_roles), 4):
        group_roles = filtered_right_roles[i:i + 4]
        price = prices[left_price_index + right_price_index]
        right_roles_text += f"Цена: {price:,} {coin_emoji}\n".replace(",", " ")  # Форматирование цены
        for item in group_roles:
            role_id, emoji = item
            right_roles_text += f"{role_number}. {emoji} <@&{role_id}>\n"
            role_number += 1
        right_roles_text += "\n"
        right_price_index += 1

    # Добавляем поля в embed с выравниванием заголовков
    left_field_name = "⠀⠀⠀**Средние роли**⠀⠀⠀"  # Центрирование пробелами
    right_field_name = "⠀⠀⠀**Дорогие роли**⠀⠀⠀"
    embed.add_field(name=left_field_name, value=left_roles_text, inline=True)
    embed.add_field(name=right_field_name, value=right_roles_text, inline=True)

    return embed


# Команда для отображения магазина ролей с навигацией по страницам
@bot.command()
async def shop_2(ctx):
    view = PageNavigation(ctx)
    embed = generate_embed(view.page)
    await ctx.send(embed=embed, view=view)


ALLOWED_ROLE_ID = 1132210249911246848
last_used = {}

@bot.command()
@commands.has_role(1135313711695921222)
async def mute_others(ctx):
    # Получаем голосовой канал, в котором находится пользователь, вызвавший команду
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None

    if not voice_channel:
        await ctx.send("Вы не находитесь в голосовом канале.")
        return

    try:
        # Мутим всех участников канала, кроме того, кто вызвал команду
        for member in voice_channel.members:
            if member != ctx.author:
                await member.edit(mute=True)  # Мутим участника

        await ctx.send(f"Все участники канала, кроме вас, были замучены.")
    except disnake.Forbidden:
        await ctx.send("У меня недостаточно прав для выполнения этой операции.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {str(e)}")


@bot.command()
async def incognito(ctx, channel_id: int, *, message: str):
    # Проверяем, имеет ли пользователь нужную роль
    role = get(ctx.author.roles, id=ALLOWED_ROLE_ID)
    if not role:
        await ctx.send("Эта команда доступна только для определённой роли!")
        return

    # Проверяем длину сообщения
    if len(message) > 500:
        await ctx.send("Сообщение слишком длинное! Максимальная длина текста — 500 символов.")
        return

    # Проверяем, прошло ли 6 часов с последнего использования команды
    user_id = ctx.author.id
    now = datetime.now()
    if user_id in last_used:
        time_difference = now - last_used[user_id]
        if time_difference < timedelta(hours=6):
            remaining_time = timedelta(hours=6) - time_difference
            await ctx.send(f"Вы сможете использовать эту команду через {remaining_time}.")
            return

    # Проверяем, существует ли указанный канал
    target_channel = bot.get_channel(channel_id)
    if not target_channel:
        await ctx.send("Указанный канал не найден. Проверьте ID канала.")
        return

    # Отправляем сообщение в указанный канал
    try:
        await ctx.message.delete()  # Удалить исходное сообщение, чтобы скрыть использование команды
        await target_channel.send(message)
        last_used[user_id] = now  # Обновляем время последнего использования команды
    except Exception as e:
        await ctx.send(f"Произошла ошибка при выполнении команды: {e}")


bot.run("")
