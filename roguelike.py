try:
    import curses
except:    
    print("Встроенный модуль curses не поддерживается в Windows.")
    print("Однако вы можете установить модуль windows-curses, чтобы играть в Windows.")
    while True:
        print("Хотели бы вы установить windows-curses? (Y/N)")
        choice = input(">> ")
        if choice:
            c = choice[0].lower()
            if c == "y":
                print("Начало установки...")
                import subprocess
                code = subprocess.call(["pip", "install", "windows-curses"])
                if code:
                    print("Не удалось установить windows-curses.")
                    exit(code)
                break
            elif c == "n":
                exit()
            else:
                print("Пожалуйста, введите Y или N")
    import curses
    os.system("cls" if os.name == "nt" else "clear")
    
import random, time

from utils import *
from board import *    
from gameobj import *                    
from entity import *        
from items import *
from monster import *
    

if __name__ == "__main__":        
    g = Game()
    try:
        g.game_screensaver()
        g.print_msg("")
        g.print_msg("Добро пожаловать в Roguelike")
        g.print_msg("Нажмите \"?\", если вы хотите просмотреть элементы управления.")
        if g.has_saved_game():
            g.maybe_load_game()    
        if not g.has_saved_game(): #Либо ему не удалось загрузиться, либо игрок решил начать новую игру
            g.generate_level()
        for w in dup_warnings:
            g.print_msg(f"Предупреждение: {w}", "yellow")    
        g.draw_board()
        g.refresh_cache()
        player = g.player
        g.player.recalc_passives()
        while not player.dead:
            refresh = False
            lastenergy = player.energy
            if player.resting:
                g.screen.nodelay(True)
                char = g.screen.getch()
                done = False
                if char != -1 and chr(char) == "r":
                    g.screen.nodelay(False)
                    if g.yes_no("Вы действительно хотите прекратить свой отдых?"):
                        done = True
                        g.print_msg("Вы прекратили свой отдых.")
                    else:
                        g.print_msg("Вы продолжаете отдыхать.")
                        g.screen.nodelay(True)
                time.sleep(0.005)
                player.energy = 0
                if not done and player.HP >= player.get_max_hp():
                    g.print_msg("HP восстановлены.", "green")
                    done = True
                if done:
                    g.screen.nodelay(False)
                    g.player.resting = False
                    player.energy = random.randint(1, player.get_speed())
                    refresh = True
            elif g.player.activity:
                time.sleep(0.01)
                player.energy = 0
                player.activity.time -= 1
                if player.activity.time <= 0:
                    player.activity.on_finished(player)
                    player.activity = None
                    refresh = True
                    player.energy = random.randint(1, player.get_speed())
            else:
                g.screen.nodelay(False)
                curses.flushinp()
                char = chr(g.screen.getch())
                if char == "w":
                    player.move(0, -1)
                elif char == "s":
                    player.move(0, 1)
                elif char == "a":
                    player.move(-1, 0)
                elif char == "d":
                    player.move(1, 0)
                elif char == "q": #Прокрутите вверх
                    g.msg_cursor -= 1
                    if g.msg_cursor < 0:
                        g.msg_cursor = 0
                    refresh = True
                elif char == "z": #Прокрутите вниз
                    g.msg_cursor += 1
                    if g.msg_cursor > (limit := max(0, len(g.msg_list) - g.get_max_lines())):
                        g.msg_cursor = limit
                    refresh = True
                elif char == "f": #Просмотр информации о типах монстров в поле зрения
                    fov_mons = list(player.monsters_in_fov(clairvoyance=True))
                    refresh = True
                    if not fov_mons:
                        g.print_msg("Прямо сейчас ты не видишь никаких монстров")
                    else:
                        fov_mons.sort(key=lambda m: m.name)
                        fov_mons.sort(key=lambda m: m.diff)
                        dup = set()
                        rem_dup = []
                        for m in fov_mons:
                            if m.name not in dup:
                                rem_dup.append(m)
                                dup.add(m.name)
                        fov_mons = rem_dup[:]
                        del rem_dup
                        ac_bonus = player.get_ac_bonus(avg=True)
                        mod = player.attack_mod(avg=True)
                        str_mod = calc_mod(g.player.STR, avg=True)
                        AC = 10 + ac_bonus
                        mon_AC = m.get_ac(avg=True)
                        for m in fov_mons:
                            hit_prob = to_hit_prob(mon_AC, mod)
                            hit_adv = to_hit_prob(mon_AC, mod, adv=True) #Вероятность с преимуществом
                            be_hit = to_hit_prob(AC, m.to_hit)
                            be_hit_disadv = to_hit_prob(AC, m.to_hit, disadv=True)
                            string = f"{m.symbol} - {m.name} "
                            string += f"| Вероятность попадания: {display_prob(hit_prob*100)} ({display_prob(hit_adv*100)} с преимуществом.)"
                            string += f" | {display_prob(be_hit*100)} для попадания в вас ({display_prob(be_hit_disadv*100)} с недостатком.)"
                            string += " | Урон: "
                            for i in range(len(m.attacks)):
                                att = m.attacks[i]
                                if isinstance(att, list):
                                    d = []
                                    for a in att:
                                        x, y = a.dmg
                                        d.append(f"с {x} до {y}")
                                        if i < len(att) - 1:
                                            d.append(", ") 
                                    d = "".join(d)
                                    string += f"({d})"
                                else:
                                    x, y = att.dmg
                                    string += f"с {x} до {y}"
                                if i < len(m.attacks) - 1:
                                    string += ", "
                            if m.armor > 0:
                                string += f" | Защита: {m.armor}"
                            g.print_msg(string)
                elif char == "i": #Меню инвентаря
                    if player.inventory:
                        player.inventory_menu()
                    else:
                        g.print_msg("У вас ничего нет в инвентаре.")
                        refresh = True
                elif char == "r" and player.HP < player.MAX_HP: #Отдохните и дождитесь восстановления HP 
                    aware_count = 0
                    for m in player.monsters_in_fov():
                        if m.is_aware:
                            aware_count += 1
                    if aware_count == 0:
                        g.print_msg("Вы начинаете отдыхать.")
                        player.resting = True
                    else:
                        num_msg = "есть монстры" if aware_count > 1 else "прячится монстр "
                        g.print_msg(f"Ты не можешь успокоиться, когда рядом {num_msg}!", "yellow")
                    refresh = True
                elif char == " ":
                    tile = g.board.get(player.x, player.y)
                    if tile.items:
                        item = tile.items.pop()
                        g.player.add_item(item)
                        g.print_msg(f"Вы подняли {item.name}.")
                        g.player.energy -= g.player.get_speed()
                    elif g.board.get(player.x, player.y).stair:
                        was_any_allies = any(m.summon_timer is not None for m in g.monsters)
                        time.sleep(0.3)
                        g.generate_level()
                        g.level += 1
                        if was_any_allies:
                            g.print_msg("Вы спускаетесь все глубже в подземелье, оставляя своих призванных союзников позади.")
                        else:
                            g.print_msg("Вы спускаетесь все глубже в подземелье.")    
                        for m in player.monsters_in_fov():
                            if x_in_y(3, g.level):
                                continue
                            if dice(1, 20) + calc_mod(player.DEX) - 5 < m.passive_perc:
                                m.is_aware = True
                    else:
                        g.print_msg("Здесь нечего подбирать.")
                    refresh = True
                elif char == "?": #Инструкция по клавишам
                    g.help_menu()
                elif char == ".": #Пропустить ход
                    player.energy = 0
                elif char == "Q": #Выход из игры
                    if g.yes_no("Вы уверены, что хотите выйти из игры?"):
                        curses.nocbreak()
                        curses.echo()
                        exit()
                elif char == "t":
                    player.throw_item()
                    refresh = True
                elif char == "+": #Показывать изношенные кольца
                    if player.worn_rings:
                        num = len(player.worn_rings)
                        g.print_msg(f"На тебе {num} {'колец' if num not in [1, 2, 3, 4] else 'кольц'}{'о' if num == 1 else 'а'}:")
                        g.print_msg(", ".join(r.name for r in player.worn_rings))
                        passives = player.calc_ring_passives()
                        if passives:
                            g.print_msg("Ваши кольца предоставляют следующие пассивные бонусы:")
                            keys = sorted(passives.keys(), key=lambda k: k.lower())
                            g.print_msg(", ".join(f"+{passives[k]} {'к удару' if k == 'to_hit' else k}" for k in keys))
                    else:
                        g.print_msg("Ты не носишь никаких колец.")
                    refresh = True
            moved = player.energy < lastenergy
            if moved:
                g.do_turn()
                busy = player.resting or player.activity
                if not busy or player.ticks % 10 == 0:
                    g.draw_board()
                if not busy or player.ticks % 40 == 0:
                    g.save_game()
            elif refresh:
                g.draw_board()
        g.delete_saved_game()
        g.input("Нажмите enter, чтобы продолжить...")
        g.game_over()
    except Exception as e:
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        import os, traceback
        os.system("clear")
        print("Произошла ошибка:")
        print()
        msg = traceback.format_exception(type(e), e, e.__traceback__)
        msg = "".join(msg)
        print(msg)
        print()
        filename = "roguelike_error.log"
        f = open(filename, "w")
        try:
            f.write(msg)
            print(f"Сообщение об ошибке было записано в {filename}")
        except:
            pass
    except KeyboardInterrupt:
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        import os
        os.system("cls")
        raise
    else:
        curses.nocbreak()
        curses.echo()   