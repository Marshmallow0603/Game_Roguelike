import random, curses, textwrap
from os import get_terminal_size, path
from itertools import islice
from collections import deque

from utils import *
from board import Board
from player import Player
from effect import Effect
from monster import Monster
from items import *

import pickle


class GameTextMenu:
    """Класс, отвечающий за текстовое меню игры"""
        
    def __init__(self, g) -> None:
        self.screen = g.screen 
        self.g = g # объект класса Game
        size = get_terminal_size() # Получаем размеры экрана консоли
        self.terminal_width = size.columns # Ширина терминала
        self.msg = [] # список сообщений для вывода в меню
        
    def add_text(self, txt) -> None:
        """Добавляет текст в список с обрезанием до terminal_width

        Args:
            txt (str): Текст для вывода на экран
        """
        txt = str(txt)
        self.msg.extend(textwrap.wrap(txt, self.terminal_width))
        
    def add_line(self) -> None:
        """Добавляет пустую строку в список
        """
        self.msg.append("")
        
    def clear_msg(self) -> None:
        """Очищает список msg
        """
        self.msg.clear()
        
    def display(self) -> None:
        """Добавляет список msg на экран терминала
        """
        self.screen.clear()
        self.screen.addstr(0, 0, "\n".join(self.msg))
        self.screen.refresh() # Обновление экрана
        
    def close(self) -> None:
        """Выводит саму игру
        """
        self.g.draw_board()
        
    def getch(self) -> int:
        """Ждет, пока пользователь нажмет клавишу

        Returns:
            int: Возвращает целое число (код клавиши)
        """
        return self.screen.getch()
        
    def getchar(self) -> str:
        """Получает код клавиши в строку из Unicode

        Returns:
            str: Строкa, представляющая символ Unicode
        """
        return chr(self.getch())
        
    def wait_for_enter(self):
        """Ожидание нажатия клавиши
        """
        while self.getch() != 10: pass

class Game:
    """Класс настройки самой игры"""
        
    def __init__(self):
        self.screen = curses.initscr()
        curses.start_color() # назначение цветов по умолчанию
        curses.init_pair(1, curses.COLOR_RED, 0)
        curses.init_pair(2, curses.COLOR_GREEN, 0)
        curses.init_pair(3, curses.COLOR_YELLOW, 0)
        curses.init_pair(4, curses.COLOR_BLUE, 0)
        curses.init_pair(5, curses.COLOR_MAGENTA, 0)
        curses.init_pair(6, curses.COLOR_CYAN, 0)
        
        self.screen.clear()
        curses.noecho() # инициализация считывания клавиш
        self.board = Board(self, 40, 16) # инициализируем сцену
        self.player = Player(self)
        self.monsters = []
        self.msg_list = deque(maxlen=50)
        self.msg_cursor = 0
        self.blast = set() 
        self.projectile = None # Снаряд
        self.select = None
        self.level = 1
        self.revealed = [] # Найденные
        types = Effect.__subclasses__() # список всех эффектов (наследников)
        self.effect_types = {t.name:t for t in types}
        self.monster_types = Monster.__subclasses__() # список всех монстров (наследников)
        
    def __getstate__(self):
        d = self.__dict__.copy()
        del d["screen"]
        return d
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.screen = curses.initscr()
        
    def load_game(self) -> None:
        """Загрузка сохранённой игры
        """
        try:
            obj = pickle.load(open("save.pickle", "rb"))
            self.__dict__.update(obj.__dict__) # Заменяем на сохранённые обЪекты
        except:
            self.print_msg("Не удается загрузить сохраненную игру.", "yellow")
            self.delete_saved_game() # Удаляем файл сохранения игры
            
    def save_game(self):
        """Сохранение игры
        """
        pickle.dump(self, open("save.pickle", "wb"))
        
    def has_saved_game(self) -> bool:
        """Проверяет на сохранение игры (продолжение игры)

        Returns:
            bool: True, если файл был найден
        """
        return path.exists("save.pickle")
        
    def delete_saved_game(self):
        """Удаляет файл с сохранениями
        """
        if self.has_saved_game():
            import os
            os.remove("save.pickle")
        
    def help_menu(self):
        """Меню для помощи в управлении
        """
        menu = GameTextMenu(self)
        
        menu.add_text("Используйте клавиши WASD для перемещения")
        menu.add_text("Используйте клавиши Q и Z для прокрутки журнала сообщений")
        menu.add_text("F - просмотр информации о монстрах, которые в данный момент находятся в поле зрения")
        menu.add_text("R - отдыхайте, пока HP не восстановится")
        menu.add_text("SPACE - забрать предмет")
        menu.add_text("I - меню инвентаря")
        menu.add_text("SPACE - спуститесь на следующий уровень (когда стоите на символе '>')")
        menu.add_text("? - снова вызывает это меню")
        menu.add_text(". - дождитесь своей очереди")
        menu.add_text("T - бросить бросаемый предмет")
        menu.add_text("+ - просмотр снаряженных колец (и бонусов от них)")
        menu.add_text("SHIFT+Q - выйти из игры")
        menu.add_line()
        menu.add_text("Нажмите enter, чтобы продолжить")
        menu.display() # Вывод текста на экран 
        menu.wait_for_enter() # Ожидание ввода клавиш
        menu.close() # Возвращение в игру
        
    def game_screensaver(self) -> None:
        """Заставка перед игрой
        """
        s = [
        ['●▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ஜ۩۞۩ஜ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●'], 
        ['░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░'],
        ['░░░░░░░░░░░░░█░█░█░█▀▀▀░█░░░░█▀▀▀░█▀▀█░█▀█▀█░█▀▀▀░░░░░░░░░░░░'],
        ['░░░░░░░░░░░░░█░█░█░█▀▀▀░█░░░░█░░░░█░░█░█░█░█░█▀▀▀░░░░░░░░░░░░'],
        ['░░░░░░░░░░░░░▀▀▀▀▀░▀▀▀▀░▀▀▀▀░▀▀▀▀░▀▀▀▀░▀░▀░▀░▀▀▀▀░░░░░░░░░░░░'],
        ['░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░'],
        ['●▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ஜ۩۞۩ஜ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●']
        ]
        menu = GameTextMenu(self)   
        while True:
            menu.clear_msg()
            for i in s:
                    menu.add_text(*i)
            menu.add_text('Нажмите enter, чтобы начать игру...')
            menu.display()
            if menu.getch() == 10:
                break
            
        menu.close() # Закрытие меню
        
    def maybe_load_game(self) -> None:
        """Возможность продолжить игру
        """
        if not self.has_saved_game():
            return
        menu = GameTextMenu(self)   
        
        while True:
            menu.clear_msg()
        
            menu.add_text("Продолжить сохраненную игру")
            menu.add_line()
            menu.add_text("У вас есть сохраненная игра.")
            menu.add_line()
            menu.add_text("Нажмите 1, чтобы загрузить сохраненную игру.")
            menu.add_text("Нажмите 2, чтобы начать новую игру.")
            menu.display()
            while (user := chr(menu.getch())) not in ["1", "2"]: pass # Ожидание ввода
            if user == "1":
                self.load_game() # Загружает сохранённую игру
                break
            else:
                menu.clear_msg()
                menu.add_text("Вы действительно хотите начать новую игру? Весь прогресс будет потерян!")
                menu.add_line()
                menu.add_text("Введите Y или N")
                menu.display()
                while (newgame := chr(menu.getch()).upper()) not in ["Y", "N"]: pass
                if newgame == "Y":
                    self.delete_saved_game() # Удаляет файл предыдущего сохранения
                    break
                
        menu.close() # Закрытие меню
        
    def game_over(self) -> None:
        """Окончание игры (игрок умер)
        """
        menu = GameTextMenu(self)               
        p = self.player
        
        menu.add_text("GAME OVER")
        menu.add_line()
        menu.add_text(f"Вы достигли {self.level} уровень подземелья")
        menu.add_text(f"Вы достигли {p.level} уровень XP")
        menu.add_line()
        menu.add_text(f"Ваша окончательная статистика была:")
        menu.add_text(f"STR {p.STR}, DEX {p.DEX}")
        menu.add_line()
        menu.add_text("Нажмите enter, чтобы выйти")
        menu.display()
        menu.wait_for_enter()
            
    def set_projectile_pos(self, x, y) -> None:
        """Установка положения снаряда
        """
        self.projectile = (x, y)
        
    def clear_projectile(self) -> None:
        """Очистка положения снаряда
        """
        self.projectile = None
        
    def spawn_item(self, item, pos:tuple) -> None:
        """Добавление по позиции предметов на сцену
        """
        self.board.get(*pos).items.append(item)
        
    def input(self, message=None) -> str:
        """Ввод текста в терминал (декодирование потока байтов)

        Args:
            message: Текст. Defaults to None.

        Returns:
            str: Введённый ранее текст в терминал
        """
        if message:
            self.print_msg(message)
            
        self.draw_board()
        curses.echo()
        
        string = self.screen.getstr()
        curses.noecho()
        
        self.draw_board()
        return string.decode()
        
    def yes_no(self, message) -> bool:
        """Ожидание ввода и проверка на Y/N

        Args:
            message: Текст (вопрос)

        Returns:
            bool: True - Yes, False - No.
        """
        while (choice := self.input(message + " (Y/N)").lower()) not in ["y", "n"]:
            self.print_msg("Пожалуйста, введите \"Y\" или \"N\"")
        return choice == "y"
        
    def select_monster_target(self, cond=None, error="Ни один из монстров не является подходящей мишенью."):
        """Выбор монстра в виде цели
        """
        monsters = list(self.player.monsters_in_fov())
        if not monsters:
            self.print_msg("Вы не видите никаких монстров, на которых можно было бы нацелиться.")
            return None
        if cond:
            monsters = list(filter(cond, monsters))
            if not monsters:
                self.print_msg(error)
                return None
            
        self.print_msg("На какого монстра нацелиться?")
        self.print_msg("Используйте клавиши A и D для выбора")
        monsters.sort(key=lambda m: m.y)
        monsters.sort(key=lambda m: m.x)
        
        index = random.randrange(len(monsters))
        last = -1
        while True:
            self.select = monsters[index]
            if last != index:
                self.draw_board()
                last = index
            curses.flushinp()
            num = self.screen.getch()
            char = chr(num)
            if char == "a":
                index -= 1
                if index < 0:
                    index += len(monsters)
            elif char == "d":
                index += 1
                if index >= len(monsters):
                    index -= len(monsters)
            if num == 10:
                break
        self.select = None
        return monsters[index]
        
    def add_monster(self, m) -> None:
        """Добавление монстра в рандомное место на сцене

        Args:
            m: Монстр (объект класса Monster)
        """
        if m.place_randomly(): # класс Monster наследуется от Entity
            self.monsters.append(m)
            
    def place_monster(self, typ):
        m = typ(self)
        if m.place_randomly():
            self.monsters.append(m)
            return m
        return None
    
    def generate_level(self) -> None:
        """Генерация уровня
        """
        self.monsters.clear()
        self.board.generate() # создание карты
        self.player.rand_place() # рандомное размещение игрока
        self.player.fov = self.player.calc_fov() # Вычисляем все видимые tiles -> tuple(x, y)
        
        count_monster = random.randint(3, 4) + random.randint(0, int(1.4*(self.level - 1)**0.65)) # рандомное количество монстров
        monsters = self.monster_types # список монстров
        for _ in range(count_monster):
            pool = []
            for t in monsters:
                minlevel = t.min_level-1
                thresh =  int(minlevel*1.7)
                thresh = min(thresh, minlevel+10)
                lev = self.level
                if lev > random.randint(minlevel, thresh): # Нужно, чтобы монстры были слабее уровня подземелья
                    pool.append(t)
                    
            assert len(pool) > 0 
            typ = random.choice(pool) # рандомно берём тип монстра из отсортированного списка (по уровню)
            m = typ(self) # инициализируем тип монстра
            delta = random.randint(0, max(1, m.MAX_HP//10)) - random.randint(0, max(1, m.MAX_HP//10))
            new_HP = max(1, m.MAX_HP + delta)
            m.HP = m.MAX_HP = new_HP
            if m.place_randomly(): # добавление в рандомное место
                if one_in(2) and x_in_y(8, self.level):
                    los_tries = 100
                    while los_tries > 0:
                        if not self.player.sees((m.x, m.y)):
                            break
                        m.place_randomly()
                        los_tries -= 1
                self.monsters.append(m)
        
        def place_item(type_item):
            """Размещает предмет на сцене

            Args:
                type_item: Класс предмета
            """
            for j in range(600):
                
                x = random.randint(1, self.board.cols - 2)
                y = random.randint(1, self.board.rows - 2)
                
                if self.board.is_passable(x, y):
                    tile = self.board.get(x, y)
                    if not tile.items:
                        tile.items.append(item := type_item())
                        return item
            return None
                        
        if not one_in(8):   
            types_item = [
                (HealthPotion, 55), # Зелье здоровья
                (ResistPotion, 20), # Зелье сопротивления
                (SpeedPotion, 20), # Зелье скорости
                (InvisibilityPotion, 12), # Зелье невидимости
                (RejuvPotion, 3), # Зелье восстановления
                (ClairPotion, 9) # Зелье ясновидения
            ]
            for _ in range(4):
                if x_in_y(45, 100):
                    typ = rand_weighted(*types_item)
                    place_item(typ) 
                elif x_in_y(60, 100):
                    if one_in(2):
                        place_item(HealthPotion)
                    break
                    
            if one_in(5):
                typ = random.choice([StrengthRing, ProtectionRing, DexterityRing]) # Кольцо силы, кольцо защиты, кольцо ловкости
                place_item(typ)
                
            if self.level > dice(1, 6) and x_in_y(3, 8):
                typ = rand_weighted(
                    (MagicMissile, 10), # Волшебный снаряд
                    (PolymorphWand, 5), # Полиморфная рука
                    (WandOfFear, 3), # Жезл cтраха
                    (LightningWand, 2) # Жезл-молния
                )
                place_item(typ)
            
            if x_in_y(2, 5):
                typ = rand_weighted(
                    (StunScroll, 2),
                    (TeleportScroll, 3),
                    (SleepScroll, 2),
                    (ConfusionScroll, 3),
                    (SummonScroll, 2),
                    (EnchantScroll, 5)
                )
                place_item(typ)
                
            types_item = [
                (Club, 65),
                (Dagger, 35),
                (Greatclub, 35),
                (Handaxe, 17),
                (Javelin, 17),
                (Mace, 17),
                (Battleaxe, 11),
                (Shortsword, 11),
                (Longsword, 9),
                (Morningstar, 9),
                (Glaive, 8),
                (Greataxe, 7),
            ]
            types_item = [t for t in types_item if t[1] >= int(65/self.level)]
            num = binomial(random.randint(2, 3), 50)
            for _ in range(num):
                if (weapon := place_item(rand_weighted(*types_item))):
                    if one_in(20):
                        for _ in range(3):
                            weapon.add_enchant()
                            if not one_in(3):
                                break
                
            if self.level > 1 and x_in_y(min(55 + self.level, 80), 100):
                types_item = [LeatherArmor]
                if self.level > 2:
                    types_item.append(HideArmor)
                if self.level > 5:
                    types_item.append(ChainShirt)
                if self.level > 8:
                    types_item.append(ScaleMail)
                if self.level > 10:
                    types_item.append(HalfPlate)
                if self.level > 13:
                    types_item.append(SplintArmor)
                if self.level > 15:
                    types_item.append(PlateArmor)
                num = 1
                if self.level > random.randint(1, 3) and one_in(3):
                    num += 1
                    if self.level > random.randint(1, 6) and one_in(3):
                        num += 1
                for _ in range(num):
                    place_item(random.choice(types_item))
        
        self.revealed.clear()
        self.draw_board()
        self.refresh_cache()
    
    def monster_at(self, x, y, include_player=False):
        """Проверка pos монстра в pos игрока
        """
        if (x, y) == (self.player.x, self.player.y):
            return include_player
        return self.board.get_cache(x, y)
        
    def get_monster(self, x, y):
        """Получем монстра, у которого pos monster == pos obj
        """
        if not self.monster_at(x, y):
            return None
        return next((monster for monster in self.monsters if (monster.x, monster.y) == (x, y)), None)
        
    def remove_monster(self, m) -> None:
        """Удаляет объект монстра
        """
        try:
            ind = self.monsters.index(m)
        except ValueError:
            pass
        else:
            del self.monsters[ind]
            self.board.unset_cache(m.x, m.y)
        
    def print_msg_if_sees(self, pos, msg, color=None) -> None:
        """Выводит сообщение, если игрок видим
        """
        assert len(pos) == 2 and type(pos) == tuple
        if self.player.sees(pos, clairv=True):
            self.print_msg(msg, color=color)
            
    def print_msg(self, msg:str, color:str=None) -> None:
        """Выводит текст на экран

        Args:
            msg (str): Текст
            color (str): Название цвета. Defaults to None.
        """
        m = {
            "red": 1,
            "green": 2,
            "yellow": 3
        }
        color = m.get(color, 0)
        size = get_terminal_size()
        terminal_width = size.columns
        for line in str(msg).splitlines():
            self.msg_list.extend(map(lambda s: (s, color), textwrap.wrap(line, terminal_width)))
        self.msg_cursor = max(0, len(self.msg_list) - self.get_max_lines())
        
    def get_max_lines(self) -> None:
        """Получает максимальную длину текста
        """
        return min(8, get_terminal_size().lines - (self.board.rows + 2))
        
    def draw_board(self) -> None:
        """Выводит игру на экран терминала
        """
        screen = self.screen
        board = self.board
        screen.clear()
        
        p = self.player
        hp_str = f"HP {p.HP}/{p.get_max_hp()}"
        c = 0
        if p.HP <= p.get_max_hp()//8:
            c = curses.color_pair(1) | curses.A_BOLD
        elif p.HP <= p.get_max_hp()//4:
            c = curses.color_pair(3) 
            
        width = get_terminal_size().columns
        screen.addstr(0, 0, hp_str, c)
        
        dr = f" (Истощение -{p.hp_drain})" if p.hp_drain > 0 else ""
        screen.addstr(0, len(hp_str), f"{dr} | DG. LV {self.level} | XP {p.exp}/{p.max_exp()} ({p.level})")
        
        wd = min(width, 60)
        str_string = f"STR {p.STR}"
        screen.addstr(0, wd - len(str_string), str_string, self._stat_mod_color(p.mod_str))
        dex_string = f"DEX {p.DEX}"
        screen.addstr(1, wd - len(dex_string), dex_string, self._stat_mod_color(p.mod_dex))
        
        dmgdice = p.weapon.dmg
        X = dmgdice.num
        Y = dmgdice.sides
        w = f"{p.weapon.name} ({X} до {Y})"
        screen.addstr(2, wd - len(w), w)
        armor = self.player.armor
        if armor:
            ar_str = f"{armor.name} ({armor.protect})" 
            screen.addstr(3, wd - len(ar_str), ar_str)
            
        detect = p.detectability()
        if detect is not None:
            stealth = round(1/max(detect, 0.01) - 1, 1)
            det_str = f"{stealth} скрытность"
            screen.addstr(4, wd - len(det_str), det_str)
        
        fov = self.player.fov.copy()
        if self.player.has_effect("Clairvoyance"):
            for point in self.board.get_in_circle((self.player.x, self.player.y), 8):
                x, y = point
                neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1), (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)]
                surrounded = True
                for xp, yp in neighbors:
                    if not self.board.in_bounds(xp, yp):
                        continue
                    if not board.blocks_sight(xp, yp):
                        surrounded = False
                        break
                    
                if not surrounded:
                    fov.add(point)
                    
        for point in fov:
            tile = board.get(*point)
            if not tile.revealed:
                tile.revealed = True
                self.revealed.append(point)
                
        offset = 1
        marked = set()
        for col, row in self.revealed:
            tile = board.get(col, row)
            s = tile.symbol
            color = 0
            if (col, row) == (self.player.x, self.player.y):
                s = "P"
                if not self.player.has_effect("Invisible"):
                    color = curses.A_REVERSE
                else:
                    color = curses.color_pair(4)
            elif tile.items:
                item = tile.items[-1]
                s = item.symbol
                color = curses.color_pair(2)
                if isinstance(item, (Scroll, Armor)):
                    color = curses.color_pair(4) | curses.A_BOLD
                elif isinstance(item, Wand):
                    color = curses.color_pair(5) | curses.A_BOLD
                elif isinstance(item, Weapon):
                    color = curses.color_pair(5) | curses.A_REVERSE
            elif tile.symbol == " ":
                if (col, row) in fov:
                    s = "."
                    color = curses.color_pair(3)
                if self.projectile:
                    x, y = self.projectile
                    if (col, row) == (x, y):
                        s = "*"
            if (col, row) in self.blast:
                color = curses.color_pair(2)
                color |= curses.A_REVERSE
                marked.add((col, row))
            try:
                screen.addstr(row + offset, col, s, color)
            except curses.error:
                pass
            
        monpos = set()
        for m in self.monsters:
            x, y = m.x, m.y
            if (x, y) in fov:
                monpos.add((x, y))
                color = curses.color_pair(3) if m.ranged else 0
                if m.has_effect("Confused"):
                    color = curses.color_pair(4)
                elif m.has_effect("Stunned"):
                    color = curses.color_pair(5)
                elif not m.is_aware:
                    if m.has_effect("Asleep"):
                        color = curses.color_pair(4)
                    color |= curses.A_REVERSE
                elif m.is_friendly():
                    color = curses.color_pair(6)
                if m is self.select or (m.x, m.y) in self.blast:
                    color = curses.color_pair(2)
                    color |= curses.A_REVERSE
                try:
                    screen.addstr(y+offset, x, m.symbol, color)
                except curses.error:
                    pass
                
        for x, y in (self.blast - monpos - marked):
            if not self.board.in_bounds(x, y):
                continue
            try:
                screen.addstr(y+offset, x, " ", curses.color_pair(2) | curses.A_REVERSE)
            except curses.error:
                pass
        
        max_lines = self.get_max_lines()
        messages = list(islice(self.msg_list, self.msg_cursor, self.msg_cursor+self.get_max_lines()))
        for i, msg in enumerate(messages):
            message, color = msg
            c = curses.color_pair(color)
            if color == 1:
                c |= curses.A_BOLD
            if i == len(messages) - 1 and self.msg_cursor < max(0, len(self.msg_list) - self.get_max_lines()):
                message += " (↓)"
            try:
                screen.addstr(board.rows + i + offset + 1, 0, message, c)
            except:
                pass
        
        try:
            screen.move(board.rows + offset, 0)
        except curses.error:
            pass
        screen.refresh()
        
    def _stat_mod_color(self, mod):
        if mod > 0:
            return curses.color_pair(2)
        if mod < 0:
            return curses.color_pair(1)
        return 0
        
    def refresh_cache(self) -> None:
        """Обновляет кэш столкновений с монстрами
        """
        board = self.board
        board.clear_cache()
        board.set_cache(self.player.x, self.player.y)
        for m in self.monsters[:]:
            board.set_cache(m.x, m.y)  
        
    def do_turn(self):
        while self.player.energy <= 0:
            if one_in(10): #На случай, если что-то пойдет не так, время от времени обновляйем кэш столкновений с монстрами
                self.refresh_cache()
            self.player.do_turn()
            order = self.monsters[:]
            random.shuffle(order)
            order.sort(key=lambda m: m.get_speed(), reverse=True)
            self.player.energy += self.player.get_speed()       
            for m in order:
                if m.HP > 0:
                    m.do_turn()
                else:
                    self.remove_monster(m)
                if self.player.dead:
                    return
                
