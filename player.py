import random, time, math
from collections import defaultdict
from utils import *

from entity import Entity
from items import *
from os import get_terminal_size


class Player(Entity):
	
	def __init__(self, g) -> None:
		super().__init__(g)
		self.exp = 0 # Очки опыта
		self.level = 1 # Уровень игрока
		self.HP = self.MAX_HP 
		self.dead = False # Смерть
		self.ticks = 0
		self.resting = False # Отдых (регенирация)
		self.weapon = UNARMED # Оружее
		self.inventory = [] # инвентарь
		self.energy = 30 
		self.speed = 30
		
		self.base_str = 10 # Сила по умолчанию
		self.base_dex = 10 # Ловкость по умолчанию
		self.mod_str = 0 # бонус сила
		self.mod_dex = 0 # бонус ловкость
		self.passives = defaultdict(int) # "STR", "DEX", "protect", "stealth", "dodge", "to_hit"
		
		self.hp_drain = 0 # утечка здоровья
		self.poison = 0 # яд
		self.effects = {} # еффекты
		self.armor = None # броня
		self.activity = None # действия
		self.did_attack = False 
		self.last_attacked = False 
		self.moved = False 
		self.last_moved = False 
		
		self.grappled_by = [] # монстры, которые атакуют
		self.worn_rings = [] # изношенные кольца
		
	def calc_ring_passives(self) -> list:
		"""Вычисление пассивов колец
  		"""
		passives = defaultdict(int)
		for ring in self.worn_rings:
			for stat, val in ring.passives.items():
				passives[stat] += val**2
		for p in passives:
			passives[p] = math.ceil(round(math.sqrt(passives[p]), 3))
		return passives
		
	def recalc_passives(self) -> None:
		"""Пересчитывает пассивы
  		"""
		passives = self.calc_ring_passives()
		self.passives = passives

	@property
	def STR(self):
		return self.base_str + self.mod_str
		
	@property
	def DEX(self):
		return self.base_dex + self.mod_dex
			
	def add_grapple(self, mon) -> bool:
		"""Добавление монстров в список, которые будут очень близко
  		"""
		if mon.distance(self) > 1: #Мы не сможем сцепиться, если будем недостаточно близко
			return False
		if mon in self.grappled_by:
			return False
		self.grappled_by.append(mon)
		return True
			
	def remove_grapple(self, mon) -> None:
		"""Удаление монстра из списка"""
		if mon in self.grappled_by:
			self.grappled_by.remove(mon)
		
	def get_ac_bonus(self, avg=False) -> float:
		"""Получение бонуса AC (Бонус AC в основном уравновешивает бонус атаки)
  		"""
		s = calc_mod(self.DEX, avg)
		if self.armor:
			armor = self.armor
			if armor.dex_mod_softcap is not None:
				softcap = armor.dex_mod_softcap
				if s > softcap:
					diff = s - softcap
					if avg:
						s = softcap + diff / 4
					else:
						s = softcap + div_rand(diff, 4)
		if self.has_effect("Haste"):
			s += 2
		s += self.passives["dodge"]
		s -= 2 * len(self.grappled_by)
		return s
		
	def get_max_hp(self) -> int:
		""" Получение макс. HP
  		"""
		return max(self.MAX_HP - self.hp_drain, 0)
		
	def get_speed(self) -> int:
		"""Получение скорости
  		"""
		speed = self.speed
		if self.has_effect("Haste"):
			speed *= 2
		elif self.has_effect("Lethargy"):
			speed = speed * 2 // 3
		return int(speed)
		
	def max_exp(self) -> int:
		"""Максимальный опыт в зависимости от уровня
  		"""
		return 50 + int((self.level - 1)**1.2 * 20) + 1
		
	def gain_exp(self, amount) -> None:
		"""Метод получения опыта
  		"""
		self.exp += amount
		old_level = self.level
		dex_inc = False
		while self.exp >= self.max_exp():
			self.exp -= self.max_exp()
			self.level += 1
			avg = (self.base_str+self.base_dex)//2
			past_softcap = avg >= 20
			if self.level % (4+2*past_softcap) == 0:
				if one_in(2):
					self.base_str += 1
				else:
					self.base_dex += 1
					dex_inc = True
			if self.level % (3+past_softcap) == 0:
				self.g.print_msg(f"Вы поднялись до {(self.level)} уровня!", "green")
				old_level = self.level
				while True:
					user = self.g.input("Хотели бы вы увеличить СИЛУ(S) или ЛОВКОСТЬ(D)?")
					user = user.upper()
					if user == "S":
						self.base_str += 1
						break
					elif user == "D":
						self.base_dex += 1
						dex_inc = True
						break
					else:
						self.g.print_msg("Пожалуйста, войдите \"S\" или \"D\"")
		if dex_inc and self.armor:
			softcap = self.armor.dex_mod_softcap
			if softcap is not None:
				thresh = 10 + softcap * 2
				if self.DEX >= thresh:
					self.g.print_msg("Примечание: Любой бонус к уклонению, превышающий этот уровень DEX, уменьшается из-за вашей тяжелой брони.")	
		if self.level > old_level:
			self.g.print_msg(f"Вы поднялись до {(self.level)} уровня!", "green")
		
	@property
	def MAX_HP(self) -> int:	
		return 100 + (self.level - 1)*20
	
	def interrupt(self, force=False) -> None:
		""" Прерыватель отдыха
  		"""
		if self.resting:
			self.g.print_msg("Ваш отдых был прерван.", "yellow")
			self.resting = False
		elif self.activity:
			if force or not self.g.yes_no(f"Продолжить {self.activity.name}?"):
				self.g.print_msg(f"Ты остановил действие {self.activity.name}.")
				self.activity = None
	
	def drain(self, amount) -> None:
		"""Истощение
  		"""
		if amount <= 0:
			return
		self.hp_drain += amount
		self.HP = min(self.HP, self.get_max_hp())
		self.g.print_msg("Твоя жизненная сила иссякла!", "red")
		self.interrupt()
		if self.get_max_hp() <= 0:
			self.g.print_msg("Ты умер!", "red")
			self.dead = True	
	
	def do_poison(self, amount) -> None:
		"""Действие яда
  		"""
		if amount <= 0:
			return
		amount += random.randint(0, amount)
		self.poison += amount
		if self.has_effect("Rejuvenated"):
			self.g.print_msg("Омоложение блокирует действие яда в вашем организме.")
		elif self.poison >= self.HP:
			self.g.print_msg("Ты смертельно отравлен!", "red")
		else:
			self.g.print_msg("Ты отравлен!", "yellow")
	
	def take_damage(self, dam, poison=False) -> None:
		"""Получение урона от яда
  		"""
		if dam <= 0:
			return
		self.HP -= dam
		if not poison: #Повреждение ядом должно прерывать деятельность только в том случае, если оно может привести к летальному исходу
			self.interrupt()
		else:
			if self.poison >= self.HP:
				if self.resting or self.activity:
					self.g.print_msg("Количество яда в вашем организме смертельно!", "red")
					self.interrupt()
		if self.HP <= 0:
			self.HP = 0
			self.g.print_msg("Ты умер!", "red")
			self.dead = True
		elif self.HP <= self.get_max_hp() // 4:
			self.g.print_msg("*** ВНИМАНИЕ: у вас низкий уровень HP! ***", "red")
	
	def add_item(self, item) -> None:
		"""Добавление предметов в инвентарь
  		"""
		if isinstance(item, Wand):
			w = next((t for t in self.inventory if isinstance(t, Wand) and type(t) == type(item)), None)
			if w is not None:
				w.charges += item.charges
			else:
				self.inventory.append(item)
		else:
			self.inventory.append(item)
			
	def rand_place(self) -> None:
		"""Генерация рандомной стартовой позиции
  		"""
		self.x = 0
		self.y = 0
		if not super().place_randomly():
			raise RuntimeError("Не удалось сгенерировать допустимую стартовую позицию для игрока")
	
	def teleport(self) -> None:
		"""Телепортация с возможностью не срабатывания
  		"""
		board = self.g.board
		oldloc = (self.x, self.y)
		for _ in range(500): # 500 попыток
			x = random.randint(1, board.cols - 2)
			y = random.randint(1, board.rows - 2)
			if board.is_passable(x, y) and (x, y) != oldloc:
				seeslastpos = board.line_of_sight((x, y), oldloc)
				if not seeslastpos: #Мы телепортировались и скрылись из виду
					for m in self.monsters_in_fov():
						m.track_timer = min(m.track_timer, dice(1, 7)) #Пусть монстры немного подумают
				self.g.print_msg("Ты телепортировался!")
				self.x = x
				self.y = y
				self.fov = self.calc_fov()
				self.grappled_by.clear()
				break
		else:
			self.g.print_msg("Вы чувствуете, что начинаете телепортироваться, но ничего не происходит.")
	
	def grapple_check(self) -> bool:
		"""Проверка захвата
  		"""
		if self.grappled_by:
			stat = max(self.DEX, self.STR) #Давайте воспользуемся более высоким из двух вариантов
			for m in self.grappled_by[:]:
				mod = calc_mod(stat)
				if m.has_effect("Confused"):
					mod += 4 #Получите бонус, избежав захвата сбитого с толку монстра
				if dice(1, 20) + mod >= m.grapple_dc:
					if self.STR > self.DEX or (self.STR == self.DEX and one_in(2)):
						self.g.print_msg(f"Ты избавляешься от '{m.name}'.")
					else:
						self.g.print_msg(f"Ты выкручиваешься из захвата {m.name}.")
					self.remove_grapple(m)
					m.energy -= m.get_speed() # Таким образом, они не могут сразу повторно схватить игрока
				else:
					self.g.print_msg(f"Вам не удастся избежать захвата '{m.name}'.", "yellow")	
			self.energy -= self.get_speed()	
			return True
		return False
	
	def move(self, dx, dy) -> bool:
		"""Движение игрока
  		"""
		if self.dead:
			self.energy = 0
			return False
		board = self.g.board
		adj = []
		if (m := self.g.get_monster(self.x-1, self.y)):
			adj.append(m)
		if (m := self.g.get_monster(self.x+1, self.y)):
			adj.append(m)
		if (m := self.g.get_monster(self.x, self.y+1)):
			adj.append(m)
		if (m := self.g.get_monster(self.x, self.y+1)):
			adj.append(m)
		if (m := self.g.get_monster(self.x + dx, self.y + dy)):
			self.moved = True
			if m.is_friendly():
				if self.grapple_check():
					return
				self.energy -= 30
				self.swap_with(m)
				m.energy = min(m.energy - 30, 0)
				self.g.print_msg(f"Вы меняетесь местами с '{m.name}'.")
			else:
				self.attack(dx, dy)
			return True
		board = self.g.board
		if not board.is_passable(self.x + dx, self.y + dy):
			return False
		self.moved = True
		if self.grapple_check():
			return True
		if not super().move(dx, dy):
			return False
		self.fov = self.calc_fov()
		speed = self.get_speed()
		board = self.g.board
		if dx != 0 or dy != 0:
			tile = board.get(self.x, self.y)
			if not tile.walked:
				tile.walked = True
				if tile.items:
					strings = list(map(lambda item: item.name, tile.items))
					if len(strings) == 1:
						self.g.print_msg(f"Вы видите здесь {strings[0]}.")
					else:
						self.g.print_msg(f"В этом локации вы видите следующие элементы: {', '.join(strings)}")
		for m in adj:
			dist = abs(self.x - m.x) + abs(self.y - m.y)
			if m.has_effect("Confused") or m.has_effect("Stunned"): #Сбитые с толку монстры не могут совершать удачные атаки
				continue
			if m.is_friendly():
				continue
			mon_speed = m.get_speed()
			fuzz = speed//3
			is_faster = mon_speed > speed + random.randint(-fuzz, fuzz)
			if m.is_aware and m.sees_player() and dist >= 2 and is_faster and one_in(3):
				self.g.print_msg(f"Когда вы отдаляетесь от '{m.name}', это создает возможность для атаки!", "yellow")
				m.melee_attack(target=self)
		self.energy -= 30
		return True
		
	def gain_effect(self, name, duration) -> None:
		"""Усиление эффекта
     	"""
		types = self.g.effect_types
		if name in types:
			typ = types[name]
			if name in self.effects:
				self.effects[name].duration += div_rand(duration, 2)
			else:
				self.effects[name] = (eff := typ(duration))
				self.g.print_msg(eff.add_msg)
				
	def lose_effect(self, effect, silent=False) -> None:
		"""Потеря эффекта
  		"""
		if effect in self.effects:
			eff = self.effects[effect]
			if silent:
				self.g.print_msg(eff.rem_msg)
			del self.effects[effect]
			eff.on_expire(self)
	
	def has_effect(self, name) -> bool:
		"""Есть ли эффект в списке?
  		"""
		return name in self.effects
		
	def sees(self, pos, clairv=False) -> bool:
		"""Проверка на видимость
  		"""
		clairv = clairv and self.has_effect("Clairvoyance")
		if pos in self.fov:
			return True
		elif clairv:
			x, y = pos
			dx = self.x - x 
			dy = self.y - y
			dist = math.sqrt(dx**2 + dy**2)
			return round(dist) <= 8
		else:
			return False
		
	def monsters_in_fov(self, include_friendly=False, clairvoyance=False) -> tuple:
		"""Выводит генератор всех видимых монстров, ввиде (x, y) монстра
  		"""
		if clairvoyance:
			clairvoyance = self.has_effect("Clairvoyance")
		for m in self.g.monsters:
			if not include_friendly and m.is_friendly():
				continue
			mx, my = m.x, m.y
			dx = self.x - mx 
			dy = self.y - my
			dist = math.sqrt(dx**2 + dy**2)
			if (mx, my) in self.fov or (clairvoyance and round(dist) <= 8):
				yield m
			
	def adjust_duration(self, effect, amount) -> None:
		"""Функция регулировки продолжительности
  		"""
		if effect in self.effects:
			eff = self.effects[effect]
			eff.duration += amount
			if eff.duration <= 0:
				del self.effects[effect]
				self.g.print_msg(eff.rem_msg)
				eff.on_expire(self)
			
	def stealth_mod(self) -> int:
		"""Cкрытый режим
  		"""
		mod = self.passives["stealth"]
		if self.last_attacked:
			mod -= 5
		if self.has_effect("Invisible"):
			mod += 5
		if self.armor:
			if self.armor.stealth_pen > 0:
				mod -= self.armor.stealth_pen
		return mod
		
	def knockback(self, dx, dy) -> None:
		"""Отбрасывание
  		"""
		if dx == 0 and dy == 0:
			return
		board = self.g.board
		newpos = self.x+dx, self.y+dy
		oldpos = (self.x, self.y)
		dist = 0
		for x, y in board.line_between(oldpos, newpos, skipfirst=True):
			if not board.is_passable(x, y):
				if dist > 0:
					dam = dice(2, dist*3)
					self.g.print_msg(f"При ударе вы получаете {dam} единиц урона!", "red")
					self.take_damage(dam)
				return
			if dist == 0:
				self.g.print_msg("Ты отброшен назад!", "red")
				self.interrupt(force=True)
			dist += 1
			self.move_to(x, y)
			self.g.draw_board()
			time.sleep(0.01)
		
		
	def throw_item(self) -> None:
		"""Выбросить предмет
  		"""
		throwable = filter(lambda t: isinstance(t, Weapon), self.inventory)
		mon = self.g.get_monster(self.x, self.y)
		# throwable = filter(lambda t: t.thrown is not None, throwable)
		throwable = list(throwable)
		g = self.g
		if not throwable:
			g.print_msg("У тебя нет никакого оружия, которым можно было бы воспользоваться.")
			return
		if not (mons := list(self.monsters_in_fov())):
			g.print_msg("Вы не видите никаких целей для броска предмета.")
			return
		strings = ", ".join(f"{i+1}. {t.name}" for i, t in enumerate(throwable))
		g.print_msg("Какой предмет выбросить? (Введите число)")
		g.print_msg(strings)
		try:
			num = int(g.input())
			if num < 1 or num > len(throwable):
				g.print_msg(f"Число должно быть в диапазоне от 1 до {len(throwable)}.")
				return
		except ValueError:
			g.print_msg("Вы не ввели номер.")
			return
		item = throwable[num - 1]
		if item.thrown:
			short, long = item.thrown
		else:
			short, long = 4, 12
		def cond(m): #Здесь мы берем количество плиток в строке 
			dx = abs(self.x - m.x)
			dy = abs(self.y - m.y)
			return max(dx, dy) <= long
		target = g.select_monster_target(cond, error=f"Ни одна из ваших целей не находится в пределах досягаемости {item.name}.")
		if not target:
			return
		g.select = target
		dx = abs(self.x - target.x)
		dy = abs(self.y - target.y)
		num_tiles = max(dx, dy)
		pen = 0
		foe_adjacent = False
		if (m := g.get_monster(self.x-1, self.y)) and m.is_aware and not m.incapacitated():
			foe_adjacent = True
		elif (m := g.get_monster(self.x+1, self.y)) and m.is_aware and not m.incapacitated():
			foe_adjacent = True
		elif (m := g.get_monster(self.x, self.y+1)) and m.is_aware and not m.incapacitated():
			foe_adjacent = True
		elif (m := g.get_monster(self.x, self.y+1)) and m.is_aware and not m.incapacitated():
			foe_adjacent = True
		if foe_adjacent: #Если есть монстр, который может видеть нас и находится прямо рядом с нами, целиться будет сложнее
			pen += 4
		avg_pen = pen
		if num_tiles > short:
			scale = 8
			g.print_msg(f"Точность дальнобойности снижается за пределами {short} плиток.", "yellow")
			pen += mult_rand_frac(num_tiles - short, scale, long - short) 
			avg_pen += scale*(num_tiles-short)/(long-short)
		if item.heavy:
			pen += 2
			g.print_msg(f"Это оружие тяжелое, поэтому точность снижается.", "yellow")
		if not item.thrown:
			pen += 2
			g.print_msg(f"Это оружие не предназначено для метания, поэтому точность снижается.", "yellow")
		mod = self.attack_mod(throwing=False, avg=False)
		avg_mod = self.attack_mod(throwing=False, avg=True)
		mod -= pen
		avg_mod -= avg_pen
		AC = target.get_ac()
		avg_AC = target.get_ac(avg=True)
		if target.incapacitated():
			AC = min(AC, 5)
			avg_AC = min(avg_AC, 5)
		prob = to_hit_prob(avg_AC, avg_mod)*100
		prob_str = display_prob(prob)
		self.g.print_msg(f"Бросание {item.name } в {target.name } - {prob_str} к попаданию.")
		c = g.input("Нажмите enter, чтобы запустить, или введите \"C\", чтобы отменить")
		g.select = None
		if c and c[0].lower() == "c":
			return
		if g.board.line_of_sight((self.x, self.y), (target.x, target.y)):
			line = list(g.board.line_between((self.x, self.y), (target.x, target.y)))
		else:
			line = list(g.board.line_between((target.x, target.y), (self.x, self.y)))
			line.reverse()
		for x, y in line:
			g.set_projectile_pos(x, y)
			g.draw_board()
			time.sleep(0.03)
		g.clear_projectile()
		roll = dice(1, 20)
		crit = False
		if roll == 1:
			hits = False
		elif roll == 20:
			hits = True
			crit = dice(1, 20) + mod >= AC
		else:
			hits = roll + mod >= AC
		if hits:
			dmg = item.dmg
			damage = dmg.roll()
			damage += calc_mod(self.attack_stat())
			damage += item.enchant
			if not item.thrown:
				damage = random.randint(1, damage)
			if crit:
				bonus = 0
				for _ in range(item.crit_mult - 1):
					bonus += dmg.roll()
				if not item.thrown:
					bonus = random.randint(1, bonus)
				damage += bonus
			damage = target.apply_armor(damage, 1+crit) #Криты дают 50% бронепробиваемости
			if target.rubbery:
				if self.weapon.dmg_type == "bludgeon":		
					damage = binomial(damage, damage, mon.HP)
				elif self.weapon.dmg_type == "slash":
					damage = binomial(damage, 50)
			if damage <= 0:
				if target.rubbery and self.weapon.dmg_type == "bludgeon":
					g.print_msg(f"{item.name} безвредно отскакивает от {target.name}.")
				else:
					g.print_msg(f"{item.name.title()} попадает в {target.name }, но не наносит никакого ущерба.")
			else:
				msg = f"{item.name.title()} попадает в {target.name} на {damage} единиц урона."
				if target.HP > damage: #Выводите сообщение HP только в том случае, если атака их не убила
					msg += f" Его HP: {target.HP-damage}/{target.MAX_HP}"
				self.g.print_msg(msg)
				if crit:
					self.g.print_msg("Критический урон!", "green")
				target.take_damage(damage, self)
		else:
			g.print_msg(f"{item.name.title()}  не попадает в {target.name}.")
		g.spawn_item(item.__class__(), (target.x, target.y))	
		if item is self.weapon:
			self.weapon = UNARMED
		
		self.inventory.remove(item)
		self.did_attack = True
		for m in self.monsters_in_fov():
			if m is target:
				if not m.despawn_summon():
					m.on_alerted()
			elif one_in(3):
				m.on_alerted()
		cost = 30
		if not item.thrown:
			cost *= 2 if item.heavy else 1.5
		self.energy -= cost
		
	def is_unarmed(self) -> bool:
		return self.weapon is UNARMED
			
	def detectability(self):
		"""Незамеченность"""
		d = []
		mons = list(filter(lambda m: not m.is_aware, self.monsters_in_fov()))
		if not mons:
			return None 
		mod = self.stealth_mod() + calc_mod(self.DEX, avg=True)
		total_stealth = 1
		for m in mons:
			perc = m.passive_perc - 5*m.has_effect("Asleep")
			stealth_prob = d20_prob(perc, mod, nat1=True)	
			if not self.last_attacked:
				stealth_prob += (1 - stealth_prob)/2
			total_stealth *= stealth_prob
   
		return 1 - total_stealth
		
	def do_turn(self) -> None:
		self.last_attacked = self.did_attack
		self.last_moved = self.moved
		self.moved = False
		
		self.mod_str = 0
		self.mod_dex = 0
		
		#Пассивные модификаторы идут сюда
		self.mod_str += self.passives["STR"]
		self.mod_dex += self.passives["DEX"]		

		self.ticks += 1
		for m in self.grappled_by[:]:
			dist = abs(m.x - self.x) + abs(m.y - self.y)
			if dist > 1:
				self.remove_grapple(m)
		if self.poison > 0:
			dmg = 1 + math.isqrt(self.poison//3)
			if dmg > self.poison:
				dmg = self.poison
			self.poison -= dmg
			if not self.has_effect("Rejuvenated"): #Омоложение позволяет яду действовать, не нанося никакого ущерба
				self.take_damage(dmg, True)
				if dmg > 3:
					if one_in(2):
						self.g.print_msg("Ты чувствуешь себя очень больным.", "red")
				elif one_in(3):
					self.g.print_msg("Ты чувствуешь себя больным.", "red")
		elif self.HP < self.get_max_hp():
			if self.ticks % 6 == 0:
				self.HP += 1
		if self.has_effect("Rejuvenated"):
			if self.hp_drain > 0:
				self.hp_drain -= 1
			self.HP += random.randint(4, 8)
			self.HP = min(self.HP, self.get_max_hp())
			if self.ticks % 6 == 0:
				self.g.print_msg("Вы чувствуете себя чрезвычайно помолодевшим.", "green")
		elif self.ticks % 6 == 0:
			if self.hp_drain > 0 and one_in(4):
				self.hp_drain -= 1
				if self.hp_drain == 0:
					self.g.print_msg("Вы полностью оправились от истощения.", "green")
		for e in list(self.effects.keys()):
			self.adjust_duration(e, -1)
		mod = self.stealth_mod()
		for m in self.g.monsters:
			m.check_timer -= 1
			if m.check_timer <= 0 or self.did_attack or one_in(15): 
				m.reset_check_timer()
				if not m.is_aware or self.did_attack: 
					roll = dice(1, 20)
					perc = m.passive_perc
					if m.has_effect("Asleep"):
						perc -= 5
					if (m.x, m.y) in self.fov and (one_in(30) or roll + div_rand(self.DEX - 10, 2) + mod < perc):
						m.on_alerted()
						m.lose_effect("Asleep")
		self.did_attack = False
		
	def attack_stat(self) -> int:
		"""Характеристика атаки
  		"""
		stat = self.STR
		if self.weapon.finesse:
			stat = max(stat, self.DEX)
		return stat
		
	def attack_mod(self, throwing=False, avg=False) -> int:
		stat = self.attack_stat()
		mod = calc_mod(stat, avg=avg)
		if not throwing:
			if self.weapon:
				if self.weapon.heavy:
					mod -= 2
			else:
				mod += 2
		return mod + self.passives["to_hit"]
		
	def base_damage_dice(self) -> int:
		return self.weapon.dmg # урон оружия
		
	def get_protect(self) -> int:
		"""Получение защиты
  		"""
		protect = self.armor.protect if self.armor else 0
		protect += self.passives["protect"]
		return protect
		
	def attack(self, dx, dy):
		"""Режим атаки
  		"""
		x, y = self.x + dx, self.y + dy
		if not self.g.monster_at(x, y):
			self.g.print_msg("Ты наносишь удар в воздух.")
			self.energy -= self.get_speed()
			return
		mon = self.g.get_monster(x, y)
		self.energy -= min(self.get_speed(), 45)
		roll = dice(1, 20)
		adv = False
		if not mon.is_aware or self.has_effect("Invisible"):
			adv = True
		finesse = self.weapon.finesse
		unarmed = self.weapon is UNARMED
		sneak_attack = adv and dice(1, 20) + calc_mod(self.DEX) + self.passives["stealth"] >= mon.passive_perc
		chance = 3
		if unarmed:
			chance -= 1
		elif finesse:
			chance += 1
		sneak_attack = sneak_attack and x_in_y(chance, 8)
		if mon.has_effect("Asleep"):
			sneak_attack = True
		eff_ac = mon.get_ac()
		if mon.has_effect("Paralyzed"):
			eff_ac = min(eff_ac, 5)
			adv = True
			
		if adv:
			roll = max(roll, dice(1, 20))
		crit = False
		
		mod = self.attack_mod()
		thresh = self.weapon.crit_thresh
		crit_threat = roll >= thresh
		if crit_threat and dice(1, 20) + mod >= eff_ac:
			hits = True
			crit = True
		elif roll == 1:
			hits = False
		elif roll == 20:
			hits = True
		else:
			hits = roll + mod >= eff_ac
		if sneak_attack:
			if one_in(3):
				self.g.print_msg(f"{mon.name} был в шоке, как вы его затали врасплох!")
			else:
				self.g.print_msg(f"Вы застаете {mon.name} врасплох!")
			hits = True
			mon.energy -= random.randint(15, 30)
		if mon.has_effect("Asleep"):
			hits = True
			mon.lose_effect("Asleep")
		mon.on_alerted()
		if not sneak_attack: #Если мы совершили внезапную атаку, давайте продолжим действовать скрытно
			self.did_attack = True
		if not hits:
			self.g.print_msg(f"Ваша атака не попадает в {mon.name}.")
		else:
			stat = self.attack_stat()
			dmgdice = self.base_damage_dice()
			dam = dmgdice.roll()
			mult = self.weapon.crit_mult
			if crit:
				for _ in range(mult - 1):
					dam += dmgdice.roll()
			if sneak_attack:
				scale = 6
				lev = self.level
				if finesse:
					lev = mult_rand_frac(lev, 4, 3)
				val = random.randint(1, lev)
				scale_int = 1 + (val - 1) // scale
				scale_mod = (val - 1) % scale
				bonus = dice(scale_int, 6) + mult_rand_frac(dice(1, 6), scale_mod, scale)
				if unarmed:
					bonus = max(1, div_rand(bonus, 3))
				softcap = dmgdice.avg()*mult
				if bonus > softcap:
					diff = bonus - softcap
					bonus = softcap + div_rand(diff, 3)
				dam += bonus
			dam += div_rand(stat - 10, 2)
			dam += self.weapon.enchant
			dam = max(dam, 1)
			dam = mon.apply_armor(dam, 1+crit)
			min_dam = dice(1, 6) if sneak_attack else 0 #Внезапные атаки гарантированно наносят от 1 до 6 единиц урона
			dam = max(dam, min_dam)
			dmgtype = self.weapon.dmg_type
			if mon.rubbery:
				if dmgtype == "bludgeon":
					dam = binomial(dam, dam, mon.HP)
				elif dmgtype == "slash":
					dam = binomial(dam, 50)
			
			if dam > 0:
				msg = f"Ты попал в {mon.name} на {dam} единиц урона."
				if mon.HP > dam:
					msg += f" Его HP: {mon.HP-dam}/{mon.MAX_HP}"
				self.g.print_msg(msg)
				if crit:
					self.g.print_msg("Критический урон!", "green")
			elif mon.rubbery and dmgtype == "bludgeon":
				self.g.print_msg(f"Вы попадаете в {mon.name}, но ваша атака отскакивает от него.")
				do_reveal = one_in(7)
				if not self.is_unarmed() and one_in(5) and dice(1, 20) + calc_mod(self.DEX) <= 12:
					reflectdmg = dmgdice.roll()
					prot = self.get_protect()
					if prot > 0:
						reflectdmg = max(0, reflectdmg - random.randint(0, prot*2))
					if reflectdmg > 0:
						reflectdmg = max(1, binomial(reflectdmg, 60))
						do_reveal = True
						self.g.print_msg(f"Атака отражена в вас на {reflectdmg} единиц урона!", "red")
						self.take_damage(reflectdmg)
						self.energy -= 20
				if do_reveal:
					self.g.print_msg(f"Этот тип урона, по-видимому, крайне неэффективен против {mon.name}. Возможно, вам придется использовать что-нибудь поострее.")
			else:	
				self.g.print_msg(f"Ты попал в {mon.name }, но не причинили никакого вреда.")
			mon.take_damage(dam, self)
			if dmgtype == "slash":
				mon.maybe_split(dam, 2)
			self.adjust_duration("Invisible", -random.randint(0, 6))
			if not sneak_attack:
				for m in self.monsters_in_fov():
					d = m.distance(self, False)
					if one_in(6) or one_in(d):
						m.on_alerted()
			
	def defeated_monster(self, mon) -> None:
		"""Поверженный монстр
  		"""
		self.g.print_msg(f"{mon.name.title()} умирает!", "green")
		self.g.remove_monster(mon)
		num = len(list(filter(lambda m: not m.is_friendly(), self.g.monsters)))
		self.remove_grapple(mon)
		v1 = min(mon.diff, 6*math.log2(1+mon.diff/6))
		val = (v1 - 1)**0.85
		
		gain = math.ceil(min(12 * 2**val, 60 * 1.5**val) - 6)
		self.gain_exp(gain)
		if mon.weapon:
			if isinstance(mon.weapon, list):
				for w in mon.weapon:
					if one_in(3):
						weapon = w()
						self.g.print_msg(f"{mon.name.title()} сбрасывает свой {weapon.name}!", "green")
						self.g.spawn_item(weapon, (mon.x, mon.y))
			elif one_in(3):
				weapon = mon.weapon()
				self.g.print_msg(f"{mon.name.title()} сбрасывает свой {weapon.name}!", "green")
				self.g.spawn_item(weapon, (mon.x, mon.y))
		if num == 0:
			if self.g.level == 1:
				self.g.print_msg("Уровень завершен! Поднимитесь по лестнице, отмеченной знаком '>', затем нажмите SPACE, чтобы подняться на следующий уровень.")
			board = self.g.board
			los_tries = 100
			while True:
				sx = random.randint(1, board.cols - 2)
				sy = random.randint(1, board.rows - 2)
				if not board.is_passable(sx, sy):
					continue
				if los_tries > 0 and board.line_of_sight((self.x, self.y), (sx, sy)):
					los_tries -= 1
					continue
				if abs(self.x - sx) + abs(self.y - sy) <= 4:
					continue
				tile = board.get(sx, sy)
				if tile.items:
					continue
				tile.symbol = ">"
				tile.stair = True
				break
	
	def inventory_menu(self) -> None:
		from gameobj import GameTextMenu
		menu = GameTextMenu(self.g)
		max_lines = get_terminal_size().lines	
		max_cols = get_terminal_size().columns // 4
		scroll = 0
		items = self.inventory[:]
		d = {}
		for item in items:
			name = item.name
			if isinstance(item, Wand):
				name += f" - заряды {item.charges}"
			elif isinstance(item, Ring) and item in self.worn_rings:
				name += " (изношенный)"
			if name not in d:
				d[name] = [0, item]
			d[name][0] += 1
		strings = []
		choices = []
		for i, name in enumerate(sorted(d.keys())):
			n = name
			num, item = d[name]
			if num > 1:
				n += f" ({num})"
			strings.append(n)
			choices.append(item)
		shown_return_msg = False
		chars = "1234567890abcdefghijklmnop"
		while True:
			menu.clear_msg()
			menu.add_text("Какой элемент выберите?")
			menu.add_text("Используйте клавиши W и S для прокрутки, нажмите Q для отмены")
			menu.add_line()
			num_display = min(len(chars), max_lines - 3)
			scroll_limit = max(0, len(strings) + num_display)
			n = min(len(strings), num_display)
			padsize = min(30, get_terminal_size().columns)
			for i in range(n):
				string = strings[i].ljust(padsize)
				if i == scroll:
					string += " (~)"
				menu.add_text(f"{chars[i]} - {string}")
			menu.add_line()
			menu.display()
			while (char := menu.getch()) not in [119, 115, 10, 113]: pass # Ожидание ввода
			if chr(char) == "w":
				if scroll > 0:
					scroll -= 1
			elif chr(char) == "s":
				if scroll < n-1:
					scroll += 1	
			elif chr(char) == "q": 
				break
			else:
				item = choices[scroll]
				menu.clear_msg()
				menu.add_text(item.name.title())
				menu.add_line()
				
				if isinstance(item, Weapon):
					dmg = item.dmg
					X, Y = dmg.num, dmg.sides
					menu.add_text(f"Это оружие наносит базовый урон от {X} до {Y}.")
					if item.heavy:
						menu.add_text("Это оружие тяжелое, поэтому атаки немного менее точны.")
					if item.finesse:
						menu.add_text("Это оружие разработано таким образом, что позволяет ему адаптироваться к стилю вашего персонажа. Броски атаки и урона используйте более высокий из ваших STR или DEX.")
					if item.crit_thresh < 20:
						diff = 21 - item.crit_thresh 
						menu.add_text(f"Базовый критический шанс с этим оружием в {diff} раз выше.")
					if item.crit_mult > 2:
						menu.add_text(f"Это оружие наносит {item.crit_mult}x урона при критическом попадании.")
				elif isinstance(item, Armor):
					if item.stealth_pen > 0:
						menu.add_text(f"Эта броня имеет тенденцию издавать некоторый шум при движении. -{item.stealth_pen} для проверки скрытности.")
				menu.add_line()
				menu.add_text("Enter - использовать элемент")
				menu.add_text("Q - вернуться")
				menu.display()
				while (char := menu.getch()) not in [113, 10]: pass # Ожидание ввода
				if chr(char) == "q":
					pass
				elif char == 10:
					menu.close()
					result = item.use(self)
					if result is not False: #False, чтобы не использовать время до хода или item
						if result is not None: 
							self.inventory.remove(item)
						self.energy -= self.get_speed()
					return

		menu.close()
			
			# elif chr(char) in chars:
			# 	ind = chars.index(char) 
			# 	if ind < num_display:
			# item = choices[scroll]
			# menu.clear_msg()
			# menu.add_text(item.name)
			# menu.add_line()
			# menu.add_text(item.description)

			# if isinstance(item, Weapon):
			# 	dmg = item.dmg
			# 	X, Y = dmg.num, dmg.sides
			# 	menu.add_text(f"Это оружие наносит базовый урон {X}x{Y}.")
			# 	if item.heavy:
			# 		menu.add_text("Это оружие тяжелое, поэтому атаки немного менее точны.")
			# 	if item.finesse:
			# 		menu.add_text("Это оружие разработано таким образом, что позволяет ему адаптироваться к стилю вашего персонажа. Броски атаки и урона используйте более высокий из ваших STR или DEX.")
			# 	if item.crit_thresh < 20:
			# 		diff = 21 - item.crit_thresh 
			# 		menu.add_text(f"Базовый критический шанс с этим оружием в {diff} раз выше.")
			# 	if item.crit_mult > 2:
			# 		menu.add_text(f"Это оружие наносит {item.crit_mult}x урона при критическом попадании.")
			# elif isinstance(item, Armor):
			# 	if item.stealth_pen > 0:
			# 		menu.add_text(f"Эта броня имеет тенденцию издавать некоторый шум при движении. -{item.stealth_pen} для проверки скрытности.")
			# menu.add_line()
			# menu.add_text("u - использовать элемент")
			# menu.add_text("Enter - вернуться")
			# menu.display()
			# 		while True:
			# 			while (char := menu.getch()) not in [117, 10]: pass # Ожидание ввода
			# 			if char == 10:
			# 				break
			# 			elif chr(char) == "u":
			# 				menu.close()
			# 				result = item.use(self)
			# 				if result is not False: #False, чтобы не использовать время до хода или item
			# 					if result is not None: 
			# 						self.inventory.remove(item)
			# 					self.energy -= self.get_speed()
			# 				return
		# menu.close()