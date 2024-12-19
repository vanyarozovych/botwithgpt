@bot.command(aliases=['профиль', 'profile'])
async def card_user(ctx, member: disnake.Member = None):
    if member is None:
        member = ctx.author

    # Создаём базовое изображение
    width, height = 600, 300
    img = Image.new('RGBA', (width, height), (20, 20, 30))  # Тёмный фон
    draw = ImageDraw.Draw(img)

    # Получение аватара пользователя и добавление свечения
    avatar_url = str(member.avatar.url) if member.avatar else None
    if avatar_url:
        response = requests.get(avatar_url, stream=True)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)

        # Светящийся круг вокруг аватара
        glow_radius = 55
        glow_circle = Image.new("RGBA", (glow_radius * 2, glow_radius * 2), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_circle)
        glow_draw.ellipse((0, 0, glow_radius * 2, glow_radius * 2), fill=(80, 120, 255, 120))
        glow_circle = glow_circle.filter(ImageFilter.GaussianBlur(15))

        # Координаты центра аватара
        avatar_center = (90, height // 2)
        img.paste(glow_circle, (avatar_center[0] - glow_radius, avatar_center[1] - glow_radius), glow_circle)

        # Закругление аватара
        mask = Image.new("L", avatar.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
        img.paste(avatar, (avatar_center[0] - 50, avatar_center[1] - 50), mask)

    # Загрузка шрифтов
    username_font = ImageFont.truetype('arial.ttf', 28)
    info_font = ImageFont.truetype('arial.ttf', 20)

    # Отображение имени пользователя
    draw.text((180, 30), member.name, font=username_font, fill=(255, 255, 255))

    # Подключение к базе данных для получения данных
    with sqlite3.connect('discord.db') as conn:
        c = conn.cursor()

        # Время в голосе
        c.execute("SELECT time_spent_in_voice_channels FROM users WHERE user_id = ?", (member.id,))
        result = c.fetchone()
        time_spent = result[0] if result is not None else 0
        hours, minutes = divmod(time_spent // 60, 60)
        draw.text((180, 80), f"Время в голосе: {hours} ч, {minutes} мин", font=info_font, fill=(255, 255, 255))

        # Баланс монет
        c.execute("SELECT coins FROM users WHERE user_id = ?", (member.id,))
        coins_result = c.fetchone()
        coins = coins_result[0] if coins_result is not None else 0

    # Загрузка иконок
    icon_online = Image.open("icon_micro2.png").resize((30, 30)).convert("RGBA")
    icon_messages = Image.open("icon_micro2.png").resize((30, 30)).convert("RGBA")
    icon_balance = Image.open("icon_micro2.png").resize((30, 30)).convert("RGBA")
    icon_top = Image.open("icon_micro2.png").resize((30, 30)).convert("RGBA")

    # Отображение иконок и текста
    icons_x, icons_y = 180, 120
    spacing = 40

    img.paste(icon_online, (icons_x, icons_y), icon_online)
    draw.text((icons_x + 40, icons_y + 5), "Онлайн -", font=info_font, fill=(255, 255, 255))

    img.paste(icon_messages, (icons_x, icons_y + spacing), icon_messages)
    draw.text((icons_x + 40, icons_y + spacing + 5), "Сообщений -", font=info_font, fill=(255, 255, 255))

    img.paste(icon_balance, (icons_x, icons_y + 2 * spacing), icon_balance)
    draw.text((icons_x + 40, icons_y + 2 * spacing + 5), f"Баланс - {coins}", font=info_font, fill=(255, 255, 255))

    img.paste(icon_top, (icons_x, icons_y + 3 * spacing), icon_top)
    draw.text((icons_x + 40, icons_y + 3 * spacing + 5), "Топ - 198", font=info_font, fill=(255, 255, 255))

    # Сохранение и отправка изображения
    img.save("user_card.png")
    await ctx.send(file=disnake.File(fp="user_card.png"))


















@bot.command(aliases=['профиль', 'profile'])
async def card_user(ctx, member: disnake.Member = None):
    # Если участник не указан, используем автора команды
    if member is None:
        member = ctx.author

    # Создание изображения для карточки пользователя с цветом #420480
    img = Image.new('RGBA', (400, 200), '#420480')

    # Получение URL аватара
    avatar_url = str(member.avatar)

    # Проверяем, существует ли аватар
    if avatar_url is not None:
        response = requests.get(avatar_url, stream=True)
        response = Image.open(io.BytesIO(response.content))
        response = response.convert('RGBA')
        response = response.resize((100, 100), Image.Resampling.LANCZOS)

        # Создание рамки для аватара
        border_size = 2  # Размер рамки, теперь тоньше
        border_img = Image.new('RGBA', (100 + border_size * 2, 100 + border_size * 2), (0, 0, 0, 255))  # Черная рамка
        border_img.paste(response, (border_size, border_size))

        img.paste(border_img, (15, 15))  # Позиция для рамки аватара
    else:
        print("Пользователь не имеет аватара. Используем стандартное изображение.")

    idraw = ImageDraw.Draw(img)
    name = member.name

    headline = ImageFont.truetype('arial.ttf', size=20)
    undertext = ImageFont.truetype('arial.ttf', size=12)

    idraw.text((145, 15), f'{name}', font=headline, fill=(255, 255, 255))  # Убрали дискриминатор
    idraw.text((145, 50), f'ID: {member.id}', font=undertext, fill=(255, 255, 255))  # Белый текст

    # Получение данных о времени, проведенном в голосовом канале
    with sqlite3.connect('discord.db') as conn:
        c = conn.cursor()
        # Получаем время, проведенное в голосовых каналах
        c.execute("SELECT time_spent_in_voice_channels FROM users WHERE user_id = ?", (member.id,))
        result = c.fetchone()
        time_spent = result[0] if result else 0
        hours, remainder = divmod(time_spent, 3600)
        minutes, _ = divmod(remainder, 60)
        # Перемещаем текст "Время в голосе" под аватар
        idraw.text((15, 130), f'Время в голосе: {hours} ч, {minutes} мин', font=undertext,
                   fill=(255, 255, 255))  # Белый текст

        # Получаем количество монет
        c.execute("SELECT coins FROM users WHERE user_id = ?", (member.id,))
        coins_result = c.fetchone()
        coins = coins_result[0] if coins_result else 0

    # Получаем URL кастомного эмодзи
    emoji_id = '1295370513383948339'  # Замените на ID вашего кастомного эмодзи
    emoji_url = f'https://cdn.discordapp.com/emojis/{emoji_id}.png'

    # Загружаем изображение эмодзи
    emoji_response = requests.get(emoji_url, stream=True)
    emoji_img = Image.open(io.BytesIO(emoji_response.content))
    emoji_img = emoji_img.convert('RGBA')
    emoji_img = emoji_img.resize((20, 20), Image.Resampling.LANCZOS)  # Измените размер по необходимости

    # Перемещаем текст с количеством монет под аватар
    text_position = (15, 150)
    idraw.text(text_position, f'Монеты: {coins}', font=undertext, fill=(255, 255, 255))  # Белый текст

    # Получаем размеры текста с помощью textbbox
    text_bbox = idraw.textbbox(text_position, f'Монеты: {coins}', font=undertext)

    # Вставляем эмодзи рядом с текстом о количестве монет
    emoji_position = (text_bbox[2] + 5, text_position[1] - 5)  # Поднимаем эмодзи немного выше
    img.paste(emoji_img, emoji_position, emoji_img)  # Позиция для эмодзи, измените по необходимости

    # Добавляем текст "fam" в правом нижнем углу
    fam_text_position = (350, 180)  # Позиция для слова "fam", немного правее
    idraw.text(fam_text_position, "fam", font=undertext, fill=(255, 255, 255))  # Белый текст

    img.save('user_card.png')

    await ctx.send(file=disnake.File(fp='user_card.png'))


















    inviter_data = {}

    @bot.event
    async def on_member_join(member):
        try:
            inviter = await find_inviter(member)
            if inviter:
                invites[member.guild.id] = await member.guild.invites()
                inviter_data[member.id] = inviter
                print(f"{inviter} пригласил {member}")

            # Добавление нового пользователя в базу данных
            with sqlite3.connect('discord.db') as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, avatar) VALUES (?, ?, ?)",
                    (member.id, member.name, str(member.avatar))
                )
                conn.commit()

            # Автоматическая выдача ролей
            roles_to_give = [1288865862232703096, 760998034792251406]  # ID ролей для выдачи
            roles = [member.guild.get_role(role_id) for role_id in roles_to_give]

            # Выдача ролей участнику
            await member.add_roles(*roles)

            # Отправка приветственного сообщения (если нужно)
            welcome_channel_id = 1117872265556676728  # Замените на ID канала для приветствий
            welcome_channel = member.guild.get_channel(welcome_channel_id)
            if welcome_channel:
                await welcome_channel.send(
                    f"{member.mention}, **залетел на сервер!**\n<@&760998034850709535>, "
                    f"<@&1291461515467296808>")

        except Exception as e:
            print(f"Ошибка при обработке нового участника: {e}")

    async def find_inviter(member):
        try:
            guild_invites = await member.guild.invites()
            old_invites = invites[member.guild.id]

            for invite in guild_invites:
                for old_invite in old_invites:
                    if invite.code == old_invite.code and invite.uses > old_invite.uses:
                        return invite.inviter
        except Exception as e:
            print(f"Ошибка при получении пригласителя для {member}: {e}")
            return None



    @bot.event
    async def on_member_update(before, after):
        added_roles = set(after.roles) - set(before.roles)
        for role in added_roles:
            if role.id in verification_role_id:
                inviter_id = inviter_data.get(after.id)  # Получаем ID пригласившего пользователя
                if inviter_id is None:
                    print(f"Не найден пригласивший для пользователя {after.name}")
                    return

                inviter = after.guild.get_member(inviter_id)  # Получаем объект пользователя на сервере
                if inviter is None:
                    print(f"Не удалось получить объект пользователя для ID {inviter_id}")
                    return

                try:
                    with sqlite3.connect('discord.db') as conn:
                        c = conn.cursor()

                        # Проверка, не приглашал ли уже этот человек данного пользователя
                        c.execute("SELECT inviter_id FROM verifications WHERE member_id = ?", (after.id,))
                        result = c.fetchone()

                        if not result:
                            # Фиксируем верификацию в базе данных
                            c.execute("INSERT INTO verifications (member_id, inviter_id) VALUES (?, ?)",
                                      (after.id, inviter.id))
                            conn.commit()

                            # Начисление монет
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
                            else:
                                print("Не удалось найти лог-канал для логирования.")
                        else:
                            print(f"Монеты за {after.name} уже начислены.")
                except Exception as e:
                    print(f"Ошибка при начислении монет {inviter.name}: {e}")

    @tasks.loop(minutes=1)
    async def periodic_verification_check():
        for guild in bot.guilds:
            await check_pending_verifications(guild)

    periodic_verification_check.start()

    async def check_pending_verifications(guild):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            for member in guild.members:
                if any(role.id in verification_role_id for role in member.roles):
                    c.execute("SELECT inviter_id FROM verifications WHERE member_id = ?", (member.id,))
                    result = c.fetchone()
                    if not result:  # Если верификация не зафиксирована
                        inviter_id = inviter_data.get(member.id)
                        if inviter_id:
                            inviter = bot.get_user(inviter_id)
                            if inviter:
                                # Начислить монеты и зафиксировать верификацию
                                await add_coins_to_user(inviter, 2000)
                                c.execute("INSERT INTO verifications (member_id, inviter_id) VALUES (?, ?)",
                                          (member.id, inviter.id))
                                conn.commit()





















roles = {
    "760998034821349443": 20000,
    "760998034821349444": 20000,
    "760998034821349445": 20000,
    "760998034829344808": 20000,
    "1295719041423511575": 50000,
    "1295719101603381269": 50000,
    "1295719187775488050": 50000,
    "1295719141696868392": 50000,
    "760998034829344812": 100000,
    "760998034829344810": 100000,
    "760998034829344816": 100000,
    "760998034829344815": 100000,
    "1295716063845023775": 350000,
    "1295715951685144626": 350000,
    "1295715743240814653": 350000,
    "1295715690568880159": 350000,
    "1294677582939422793": 600000,
}

# Объединяем роли в один список
role_items = list(roles.items())

# Определяем количество ролей на странице
ROLES_PER_PAGE = 4


def add_roles_to_shop():
    with sqlite3.connect('discord.db') as conn:
        c = conn.cursor()
        # Создаем таблицу, если ее нет
        c.execute("CREATE TABLE IF NOT EXISTS shop (role_id TEXT PRIMARY KEY, price INTEGER)")
        for role_id, price in roles.items():
            # Проверяем, существует ли запись для текущей роли
            c.execute("SELECT role_id FROM shop WHERE role_id = ?", (role_id,))
            result = c.fetchone()
            if not result:
                # Если роли нет в базе, добавляем её
                c.execute("INSERT INTO shop (role_id, price) VALUES (?, ?)", (role_id, price))
        conn.commit()


# Вызов функции для добавления ролей в магазин
add_roles_to_shop()

@bot.command()
async def shop(ctx, page: int = 1):
    # Определяем роли и цены для разных периодов
    role_items = [
                     (role_id, 'Month', price) for role_id, price in role_items if
                     price in [10000, 25000, 40000, 75000, 150000]
                 ] + [
                     (role_id, '6 months', price) for role_id, price in role_items if
                     price in [20000, 50000, 80000, 150000, 300000]
                 ] + [
                     (role_id, 'Year', price) for role_id, price in role_items if
                     price in [40000, 100000, 160000, 300000, 600000]
                 ] + [
                     (role_id, 'Lifetime', price) for role_id, price in role_items if
                     price in [80000, 200000, 320000, 600000, 1200000]
                 ]

    # Разделяем роли по категориям
    monthly_roles = [(role_id, price) for role_id, price in role_items if duration == 'Month']
    six_month_roles = [(role_id, price) for role_id, price in role_items if duration == '6 months']
    yearly_roles = [(role_id, price) for role_id, price in role_items if duration == 'Year']
    lifetime_roles = [(role_id, price) for role_id, price in role_items if duration == 'Lifetime']

    # Объединяем все роли для нумерации страниц
    all_roles = monthly_roles + six_month_roles + yearly_roles + lifetime_roles

    # Вычисляем количество страниц для каждой категории
    total_pages = sum((len(roles) + ROLES_PER_PAGE - 1) // ROLES_PER_PAGE for roles in
                      [monthly_roles, six_month_roles, yearly_roles, lifetime_roles])

    # Определяем, какие категории и роли отображать
    if page <= len(monthly_roles) // ROLES_PER_PAGE:
        items = monthly_roles
        category_start_index = 0
    elif page <= len(monthly_roles + six_month_roles) // ROLES_PER_PAGE:
        items = six_month_roles
        category_start_index = len(monthly_roles) * ROLES_PER_PAGE
    elif page <= len(monthly_roles + six_month_roles + yearly_roles) // ROLES_PER_PAGE:
        items = yearly_roles
        category_start_index = (len(monthly_roles) + len(six_month_roles)) * ROLES_PER_PAGE
    else:
        items = lifetime_roles
        category_start_index = (len(monthly_roles) + len(six_month_roles) + len(yearly_roles)) * ROLES_PER_PAGE

    # Убедимся, что на странице есть роли
    start_index = (page - 1) * ROLES_PER_PAGE
    end_index = start_index + ROLES_PER_PAGE
    items = items[start_index:end_index]

    if not items:
        await ctx.send("Нет доступных ролей на этой странице.")
        return

    # Создаем красивое и привлекательное сообщение с вложением
    embed = disnake.Embed(title="Магазин ролей", color=0x2F3136)
    embed.set_image(url="https://example.com/your_image.jpg")  # Используйте собственный URL изображения
    embed.set_footer(text="Чтобы купить, используйте: !buy + номер роли")

    # Добавляем роли с их ценами и периодами
    for index, (role_id, duration, price) in enumerate(items):
        unique_index = category_start_index + start_index + index + 1
        role = ctx.guild.get_role(role_id)
        if role:
            embed.add_field(
                name=f"{role.name}",
                value=f"{unique_index}. {role.mention}\nПродолжительность: {duration}\nЦена: {price} {emoji}",
                inline=False
            )

    # Кнопки для перехода между страницами
    buttons = [
        disnake.ui.Button(label="⬅️ Назад", style=disnake.ButtonStyle.blurple, custom_id="previous_page"),
        disnake.ui.Button(label="➡️ Далее", style=disnake.ButtonStyle.blurple, custom_id="next_page"),
    ]

    view = disnake.ui.View()
    for button in buttons:
        view.add_item(button)

    # Отправляем сообщение с вложением и кнопками
    await ctx.send(embed=embed, view=view)

    # Обрабатываем нажатия кнопок для перехода между страницами
    async def button_callback(interaction: disnake.MessageInteraction):
        if interaction.user != ctx.author:
            return

        button_id = interaction.data['custom_id']

        if button_id == "next_page" and view.current_page < total_pages:
            view.current_page += 1
        elif button_id == "previous_page" and view.current_page > 1:
            view.current_page -= 1

        await interaction.response.edit_message(embed=await get_shop_embed(ctx, view.current_page), view=view)

    for button in buttons:
        button.callback = button_callback


async def get_shop_embed(ctx, page):
    # Логика аналогична команде `shop`, но с учетом конкретной страницы.
    pass




























@tasks.loop(minutes=1)
    async def periodic_verification_check():
        for guild in bot.guilds:
            await check_pending_verifications(guild)

    periodic_verification_check.start()

    async def check_pending_verifications(guild):
        with sqlite3.connect('discord.db') as conn:
            c = conn.cursor()
            for member in guild.members:
                if any(role.id in verification_role_id for role in member.roles):
                    c.execute("SELECT inviter_id FROM verifications WHERE member_id = ?", (member.id,))
                    result = c.fetchone()
                    if not result:  # Если верификация не зафиксирована
                        inviter = inviter_data.get(member.id)
                        if inviter:
                            # Начислить монеты и зафиксировать верификацию
                            await add_coins_to_user(inviter, 2000)
                            c.execute("INSERT INTO verifications (member_id, inviter_id) VALUES (?, ?)",
                                      (member.id, inviter.id))
                            conn.commit()

    async def add_coins_to_user(user, amount):
        try:
            with sqlite3.connect('discord.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user.id))
                conn.commit()
            print(f"{user} получил {amount} монет!")
        except Exception as e:
            print(f"Ошибка при обновлении монет для {user}: {e}")