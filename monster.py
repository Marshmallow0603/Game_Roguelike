import random
from utils import *
from entity import Entity
from items import *


class Attack:
	"""Класс атаки"""
	
	def __init__(self, dmg, to_hit, msg="{0} атакует {1}") -> None:
		self.dmg = dmg
		self.to_hit = to_hit # бонус к удару
		self.msg = msg # текст
		
	def can_use(self, mon, player):
		return True	
		
	def on_hit(self, player, mon, dmg):
		pass
	
symbols = {}
dup_warnings = []
								
class Monster(Entity):
	"""Класс монстра"""
	min_level = 1
	speed = 30
	diff = 1
	AC = 10
	to_hit = 0
	passive_perc = 11
	DEX = 10
	WIS = 10
	grapple_dc = 10
	armor = 0
	attacks = [Attack((1, 3), 0)]
	beast = True
	symbol = "?"
	weapon = None
	eff_immunities = set()
	rubbery = False
	
	def __init__(self, g, name="монстр", HP=10, ranged=None, ranged_dam=(2, 3)) -> None:
		super().__init__(g)
		if ranged is None:
			ranged = one_in(5)
		if not isinstance(HP, int):
			raise ValueError(f"HP должно быть целым числом, вместо этого получил {repr(HP)}")
		self.HP = HP
		self.MAX_HP = HP
		self.name = name
		self.ranged = ranged
		self.last_seen = None
		self.dir = None
		self.ranged_dam = ranged_dam
		self.track_timer = 0
		self.is_aware = False
		self.check_timer = 1
		self.effects = {}
		self.summon_timer = None
		self.energy = -random.randrange(self.speed)
		self.target = None
		
	def is_friendly(self) -> bool:
		"""Является ли он дружелюбным?"""
		if self.has_effect("Charmed"):
			return True
		return self.summon_timer is not None
		
	def despawn(self) -> None:
		self.HP = 0
		self.energy = -self.get_speed()
		self.g.remove_monster(self)
		
	def __init_subclass__(cls) -> None:
		if cls.symbol in symbols:
			other = symbols[cls.symbol] 
			dup_warnings.append(f"{cls.__name__} имеет тот же символ, что и {other.__name__}")
		else:
			symbols[cls.symbol] = cls
				
	def get_speed(self) -> int:
		"""Получение скорости
  		"""
		speed = self.speed
		return speed
		
	def reset_check_timer(self) -> None:
		"""Сброс проверки таймера
  		"""
		self.check_timer = random.randint(1, 3)
	
	def move(self, dx, dy) -> bool:
		"""Перемещение с шагом dx и dy"""
		board = self.g.board
		if super().move(dx, dy):
			self.energy -= 30
			return True
		return False
		
	def is_eff_immune(self, eff) -> bool:
		"""Является ли эффект невосприимчивым
  		"""
		return eff in self.eff_immunities
		
	def get_ac(self, avg=False) -> int:
		return 10 + calc_mod(self.DEX, avg)
		
	def choose_polymorph_type(self):
		#Примечание: Небольшой взлом с использованием полиморфизации объектов
		types = Monster.__subclasses__()
		candidates = list(filter(lambda typ: typ.diff <= self.diff and typ.beast and typ != self.__class__, types))
		assert len(candidates) > 0
		tries = 100
		while tries > 0:
			tries -= 1
			maxdiff = max(1, self.diff - one_in(2))
			newdiff = 1
			for _ in range(random.randint(2, 3)):
				newdiff = random.randint(newdiff, maxdiff)
			choices = list(filter(lambda typ: newdiff == typ.diff, candidates))
			if not choices:
				continue 
			chosen = random.choice(choices)
			if one_in(6):
				return chosen
			inst = chosen(self.g)
			if inst.MAX_HP < self.MAX_HP:
				if chosen.armor <= self.armor or one_in(2):
					return chosen
		return random.choice(candidates)		
		
	def polymorph(self):
		oldname = self.name
		typ = self.choose_polymorph_type()
		self.__class__ = typ
		inst = typ(self.g)
		self.ranged = False
		self._symbol = inst.symbol
		self.HP = inst.HP
		self.MAX_HP = inst.MAX_HP
		self.name = inst.name
		self.g.print_msg_if_sees((self.x, self.y), f"{oldname} проевращается в {self.name}!")
					
	def has_effect(self, name) -> bool:
		"""Проверка на существование еффекта в списке
  		"""
		return name in self.effects
		
	def lose_effect(self, name) -> None:
		"""Удаление эффекта 
  		"""
		if name in self.effects:
			del self.effects[name]
			
	def incapacitated(self) -> bool:
		"""Проверка на отрицательный эффект (выведенный из строя)
  		"""
		incap_effs = ["Asleep", "Stunned", "Paralyzed"]
		for e in incap_effs:
			if self.has_effect(e):
				return True
		return False
		
	def gain_effect(self, name, duration) -> None:
		"""Усиление эффкта на duration
  		"""
		if name not in self.effects:
			self.effects[name] = 0
		self.effects[name] += duration
		if self.incapacitated():
			player = self.g.player
			player.remove_grapple(self)
			
	def despawn_summon(self) -> bool:
		if self.summon_timer is None:
			return False
		self.despawn()
		self.g.print_msg_if_sees((self.x, self.y), "Ваш призванный союзник исчезает!")
		return True
		
	def take_damage(self, dam, source=None) -> None:
		"""Функция наносения урона
  		"""
		self.HP -= dam
		if source is self.g.player and self.despawn_summon():
			return
		if self.HP <= 0:
			self.despawn()
			if source is not None:
				if source is self.g.player or source.is_friendly():
					self.g.player.defeated_monster(self)
				else:
					self.despawn_summon()
					
	def do_turn(self) -> None:
		self.energy += self.get_speed()
		while self.energy > 0:
			old = self.energy
			self.actions()
			if self.energy == old:
				self.energy = min(self.energy, 0) 
		self.tick_effects()
			
	def tick_effects(self) -> None:
		if self.summon_timer is not None and self.summon_timer > 0:
			self.summon_timer -= 1
			if self.summon_timer == 0:
				self.despawn()
				self.g.print_msg_if_sees((self.x, self.y), "Ваш призванный союзник исчезает!")
				return
		if self.track_timer > 0:
			self.track_timer -= 1
		for e in list(self.effects.keys()):
			self.effects[e] -= 1
			if self.effects[e] <= 0:
				del self.effects[e]
				if e == "Confused":
					self.g.print_msg_if_sees((self.x, self.y), f"{self.name} больше не сбит с толку.")
				elif e == "Stunned":
					self.g.print_msg_if_sees((self.x, self.y), f"{self.name} больше не ошеломлен.")
				elif e == "Frightened":
					self.g.print_msg_if_sees((self.x, self.y), f"{self.name} обретает мужество.")
				elif e == "Charmed":
					self.g.print_msg_if_sees((self.x, self.y), f"{self.name} снова становится враждебным!", "yellow")
					self.energy -= self.get_speed()
					self.target = self.g.player
				
	def should_use_ranged(self) -> True:
		board = self.g.board
		player = self.g.player
		if not self.has_line_of_fire():
			return False
		return x_in_y(2, 5)
		
	def modify_damage(self, target, damage):
		"""Изменение урона для цели
  		"""
		player = self.g.player
		if target is player:
			protect = target.armor.protect if target.armor else 0
			protect += target.passives["protect"]
		else:
			protect = target.armor	
		if protect > 0:
			if target is player:
				damage -= random.randint(1, protect*4) #Броня может уменьшить урон
			else:
				damage -= random.randint(0, mult_rand_frac(protect, 3, 2))
			if damage <= 0:
				return 0
		if target is player and player.has_effect("Resistance"):
			damage = binomial(damage, 50)
		return max(damage, 0)
		
	def melee_attack(self, target=None, attack=None, force=False) -> None:
		if attack is None:
			attacks = list(filter(lambda a: isinstance(a, list) or a.can_use(self, self.g.player), self.attacks))
			if not attacks:
				return
			attack = random.choice(attacks)
			if isinstance(attack, list):
				c = list(filter(lambda a: a.can_use(self, self.g.player), attack))
				attack = random.choice(c)
		player = self.g.player
		if target is None:
			target = player
		roll = dice(1, 20)
		disadv = 0
		disadv += target.has_effect("Invisible")
		disadv += self.has_effect("Frightened") and self.sees_player()
		for _ in range(disadv):
			roll = min(roll, dice(1, 20))
		if target is player:
			ac_mod = player.get_ac_bonus()
			AC = 10 + ac_mod
		else:
			AC = target.get_ac()
			mon = target
			mon.target = self
		bonus = attack.to_hit
		total = roll + bonus
		if roll == 1:
			hits = False
		elif roll == 20:
			hits = True
		else:
			hits = total >= AC
		
		if not hits:
			if target is not player or roll == 1 or total < AC - ac_mod:
				the_target = "тебя" if target is player else f"{target.name}"
				self.g.print_msg_if_sees((target.x, target.y), f"Атака {self.name} не попадает в {the_target}.")
			else:
				self.g.print_msg(f"Вы уклоняетесь от атаки {self.name}.")
		else:
			damage = self.modify_damage(target, dice(*attack.dmg))
			the_target = "тебя" if target is player else f"{target.name}"
			if damage:		
				self.g.print_msg_if_sees((target.x, target.y), attack.msg.format(self.name, the_target) + f" на {damage} едениц урона!", "red" if target is player else "white")
				if target is player:
					target.take_damage(damage)
					attack.on_hit(player, self, damage)
				else:
					target.take_damage(damage, source=self)
			else:
				self.g.print_msg_if_sees((target.x, target.y), attack.msg.format(self.name, the_target) + " но не причиняет никакого вреда.")
			
	def do_melee_attack(self, target=None) -> None:
		"""Аттака в ближнем бою
  		"""
		player = self.g.player
		if target is not None:
			target = player
		for att in self.attacks:
			if isinstance(att, list):
				attacks = list(filter(lambda a: a.can_use(self, self.g.player), att))
				if not attacks:
					continue
				att = random.choice(attacks)
			if att.can_use(self, player):
				self.melee_attack(player, att)
				
	def saving_throw(self, stat, DC) -> int:
		return dice(1, 20) + calc_mod(stat) >= DC
		
	def do_ranged_attack(self, target=None) -> None:
		if not self.ranged:
			return
		player = self.g.player
		board = self.g.board
		if target is None:
			target = player
		the_target = "тебя" if target is player else f"{target.name}"
		self.g.print_msg(f"{self.name} совершает дальнюю атаку по {the_target}.")
		for point in board.line_between((self.x, self.y), (target.x, target.y), skipfirst=True, skiplast=True):
			self.g.set_projectile_pos(*point)
			self.g.draw_board()
			time.sleep(0.06)
		self.g.clear_projectile()
		roll = dice(1, 20)
		if (target is player and player.has_effect("Invisible")) or self.has_effect("Frightened"): #Игрока труднее поразить, когда он невидим
			roll = min(roll, dice(1, 20))
		bonus = self.to_hit
		if target is player:
			dodge_mod = player.get_ac_bonus()
			AC = 10 + dodge_mod
		else:
			AC = target.AC
		total = roll + self.to_hit
		if roll == 1:
			hits = False
		elif roll == 20:
			hits = True
		else:
			hits = total >= AC
		if not hits:
			if target is player and roll > 1 and total >= AC - dodge_mod:
				self.g.print_msg("Вы уклоняетесь от снаряда.")
			else:
				self.g.print_msg(f"Снаряд не попадает в {the_target}.")
		else:
			damage = self.modify_damage(target, dice(*self.ranged_dam))
			if damage:
				if target is player:
					self.g.print_msg(f"Вы получаете {damage} единиц урона!", "red" if target is player else "white")
				the_target_is = "Вы" if target is player else "{target.name}"
				self.g.print_msg(f"{self.name} получает {damage} единиц урона!", "red" if target is player else "white")
				player.take_damage(damage)
			else:
				self.g.print_msg(f"Снаряд попадает в {the_target}, но не наносит никакого урона.")
		self.energy -= self.get_speed()
			
	def sees_player(self) -> bool:
		"""Проверка на видимость игрока
  		"""
		player = self.g.player
		if player.has_effect("Invisible"):
			return False
		return (self.x, self.y) in player.fov
	
	def can_guess_invis(self) -> bool:
		"""Монстр пытается угадать невидимость
  		"""
		player = self.g.player
		xdist = player.x - self.x
		ydist = player.y - self.y
		dist = abs(xdist) + abs(ydist)
		if dist <= 1 and one_in(4): #Если мы находимся прямо рядом с игроком, у нас больше шансов заметить
			return True
		if not one_in(6): 
			return False
		pen = max(dist - 2, 0) #Штраф за дистанцию; труднее угадать позицию невидимого игрока, который находится далеко
		if not player.last_moved:
			pen += 5 #Если игрок не двигается, труднее понять, где он находится
		return dice(1, 20) + div_rand(self.WIS - 10, 2) - pen >= dice(1, 20) + div_rand(player.DEX - 10, 2)
		
	def guess_rand_invis(self) -> None:
		board = self.g.board
		tries = 100
		while tries > 0:
			dx = random.randint(-2, 2)
			dy = random.randint(-2, 2)
			if (dx, dy) == (0, 0):
				continue
			xp = self.x + dx
			yp = self.y + dy
			if (xp < 0 or xp >= board.cols) or (yp < 0 or yp >= board.cols):
				continue
			if board.blocks_sight(xp, yp) or not board.line_of_sight((self.x, self.y), (xp, yp)):
				tries -= 1
			else:
				self.last_seen = (xp, yp)
				break
				
	def reset_track_timer(self) -> None:
		self.track_timer = random.randint(25, 65)
	
	def check_split(self, chance) -> bool:
		if self.HP < random.randint(10, 20):
			return False #Никакого разделения, если у нас недостаточно HP
		if "jelly" not in self.name.lower():
			return False
		denom = random.randint(self.HP, self.MAX_HP)
		return x_in_y(chance, denom)
		
	def maybe_split(self, dam, mult) -> None:
		if dam <= 0:
			return False
		if not self.check_split(dam*mult):
			return
		self.HP += binomial(dam, 50)
		if self.HP > self.MAX_HP:
			self.HP = self.MAX_HP
		x, y = self.x, self.y
		neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1), (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)]
		random.shuffle(neighbors)
		nx, ny = 0, 0
		g = self.g
		board = self.g.board
		for p in neighbors:
			nx, ny = p
			if board.is_passable(nx, ny):
				break
		else:
			return 
		cx, cy = self.x, self.y
		HP = random.randint(self.HP, self.MAX_HP)
		hp1 = div_rand(HP, 2)
		hp2 = HP - hp1
		m1 = self.__class__(g)
		m2 = self.__class__(g)
		m1.HP = m1.MAX_HP = hp1
		m2.HP = m2.MAX_HP = hp2
		self.g.print_msg(f"{self.name} разделяется на две части!", "yellow")
		self.despawn()
		m1.place_at(x, y)
		m2.place_at(nx, ny)
		g.monsters.append(m1)
		g.monsters.append(m2)
			
	def on_alerted(self, target=None) -> None:
		player = self.g.player
		self.is_aware = True
		if target is not None and target is not player:
			self.target = None
		self.last_seen = (player.x, player.y)
		self.reset_track_timer()
				
	def stop_tracking(self) -> None:
		self.last_seen = None
		self.track_timer = 0
		self.is_aware = False
		self.dir = None
		self.target = None
		
	def apply_armor(self, dam, armor_div=1) -> int:
		prot = random.randint(0, 2*self.armor)
		prot = div_rand(prot, armor_div)
		return max(0, dam - prot)
		
	def has_line_of_fire(self) -> bool:
		player = self.g.player
		return self.g.board.is_clear_path((self.x, self.y), (player.x, player.y))
		
	def sees_target(self) -> bool:
		if self.target is self.g.player:
			return self.sees_player()
		if not self.target:
			return False
		target = self.target
		if self.g.board.line_of_sight((self.x, self.y), (target.x, target.y)):
			return True
		return self.g.board.line_of_sight((target.x, target.y), (self.x, self.y))
		
	def actions(self) -> None:
		if self.has_effect("Asleep") or self.has_effect("Stunned") or self.has_effect("Paralyzed"):
			self.energy = 0
			return
		player = self.g.player	
		if self.target is None:
			self.target = player
		if self.is_friendly():
			self.is_aware = True
		mon_typ = self.__class__.__name__
		if mon_typ == "Troll" and self.HP < self.MAX_HP:
			regen = 2 + one_in(3)
			self.HP = min(self.MAX_HP, self.HP + regen)
			if x_in_y(3, 5) and one_in(self.distance(player)):
				self.g.print_msg_if_sees((self.x, self.y), f"{self.name} медленно восстанавливается.")
		board = self.g.board
		
		target = self.target
		confused = self.has_effect("Confused") and not one_in(4)
		guessplayer = False
		if self.is_aware and player.has_effect("Invisible"):
			guessplayer = self.can_guess_invis() #Даже если игрок невидим, монстр все равно может угадать их местоположение
		if confused:
			dirs = [(-1, 0), (1, 0), (0, 1), (0, -1)]
			if not self.move(*random.choice(dirs)):
				if not self.move(*(d := random.choice(dirs))):
					x, y = self.x + d[0], self.y + d[1]
					obstacle = ""
					if board.blocks_sight(x, y):
						obstacle = "стену"
					elif (m := self.g.get_monster(x, y)):
						obstacle = m.name
					if obstacle:
						self.g.print_msg_if_sees((self.x, self.y), f"{self.name} натыкается на {obstacle}.")
					self.energy -= div_rand(self.get_speed(), 2) #Мы наткнулись на что-то, находясь в замешательстве
			self.energy = min(self.energy, 0)
		elif not self.is_friendly() and self.has_effect("Frightened"):
			if self.sees_player():
				dirs = [(-1, 0), (1, 0), (0, 1), (0, -1)]
				random.shuffle(dirs)
				dist = self.distance(player)
				if dist <= 1 and one_in(4): #Если мы уже находимся рядом с игроком, когда напуганы, есть небольшой шанс, что мы попытаемся атаковать, прежде чем убежать
					self.energy -= self.get_speed()
					self.do_melee_attack()
				else:
					for dx, dy in dirs:
						newx, newy = self.x + dx, self.y + dy	
						newdist = abs(newx - player.x) + abs(newy - player.y)
						if newdist >= dist:
							self.move(dx, dy)
							break
					else:
						if x_in_y(2, 5): #Если монстр напуган и ему некуда бежать, то атакует
							if dist <= 1:
								self.energy -= self.get_speed()
								self.do_melee_attack()
							elif self.ranged and target is player and self.should_use_ranged():
								self.do_ranged_attack()
			elif one_in(2) and dice(1, 20) + calc_mod(self.WIS) >= 15:
				self.lose_effect("Frightened")
		elif self.is_friendly():
			can_see = (self.x, self.y) in player.fov
			if can_see and (mons := list(player.monsters_in_fov())):
				dist = 999
				closest = None
				for m in mons:
					if not board.is_clear_path((self.x, self.y), (m.x, m.y)):
						if not board.is_clear_path((m.x, m.y), (self.x, self.y)):
							continue
					if (d := self.distance(m)) < dist:
						dist = d
						closest = m
				if dist <= 1:
					self.melee_attack(m)
				else:
					self.path_to(m.x, m.y)	
			if self.distance(player) > 4 or not can_see:
				self.path_to(player.x, player.y)
			elif one_in(6):
				dirs = [(-1, 0), (1, 0), (0, 1), (0, -1)]
				random.shuffle(dirs)
				for d in dirs:
					if self.move(*d):
						self.dir = d
						break
		elif (self.is_aware or (target is not player and self.sees_target())) and (self.sees_player() or guessplayer):
			xdist = target.x - self.x
			ydist = target.y - self.y
			self.last_seen = (target.x, target.y)
			self.reset_track_timer()
			if self.distance(target) <= 1:
				self.energy -= self.get_speed()
				self.do_melee_attack(target)
			elif self.ranged and target is player and self.should_use_ranged():
				self.do_ranged_attack()
			else:
				dx = 1 if xdist > 0 else (-1 if xdist < 0 else 0)
				dy = 1 if ydist > 0 else (-1 if ydist < 0 else 0)
				axdist = abs(xdist)
				aydist = abs(ydist)
				old = self.energy
				self.path_to(target.x, target.y)
				moved = self.energy < old
				if not moved and self.distance(target) <= 4 and one_in(5):
					could_route_around = self.g.monster_at(self.x+dx, self.y) or self.g.monster_at(self.x, self.y+dy)
					if could_route_around:
						self.path_to(*self.last_seen, maxlen=self.distance(target)+3)
		else:
			if self.target is not player: #Потерял цель из виду
				self.target = player
			target = self.target
			if target.has_effect("Invisible") and (self.x, self.y) == self.last_seen:
				self.guess_rand_invis() 
			if self.target is player and self.last_seen:
				if self.track_timer > 0:
					if player.has_effect("Invisible"):
						check = dice(1, 20) + calc_mod(player.DEX) < 10 + calc_mod(self.WIS)
					else:
						check = True
					self.path_to(*self.last_seen)
					if (self.x, self.y) == self.last_seen and check:
						sees_you = self.sees_player()
						#Если достигает целевой позиции и по-прежнему не увидит игрока, то выполняет  проверку скрытности, чтобы продолжить отслеживание игрока
						if sees_you or dice(1, 20) + calc_mod(player.DEX) + player.passives["stealth"] < 14 + calc_mod(self.WIS):
							self.last_seen = (player.x, player.y)
						else:
							self.stop_tracking()
				else:
					self.stop_tracking()
			elif not one_in(5):
				choose_new = self.dir is None or (one_in(3) or not self.move(*self.dir))
				if choose_new:
					if self.dir is None:
						dirs = [(-1, 0), (1, 0), (0, 1), (0, -1)]
						random.shuffle(dirs)
						for d in dirs:
							if self.move(*d):
								self.dir = d
								break
					else:
						if self.dir in [(-1, 0), (1, 0)]:
							dirs = [(0, 1), (0, -1)]
						else:
							dirs = [(-1, 0), (1, 0)]
						random.shuffle(dirs)
						for d in dirs:
							if self.move(*d):
								self.dir = d
								break
						else:
							if not self.move(*self.dir):
								d = (-self.dir[0], -self.dir[1])
								self.move(*d)
								self.dir = d
			
class SpelllAttack:
	"""Атака заклинанием"""
	
	def __init__(self, to_hit, efftype, range) -> None:
		self.to_hit = to_hit
		self.eff_type = efftype #Может быть "конус", "взрыв", "луч" или None
		self.range = range
	
	def on_hit_effect(self, target) -> None:
		pass
									
class Bat(Monster):
	"""Летучая мышь"""
	min_level = 1
	diff = 1
	DEX = 15
	WIS = 12
	symbol = "🦇"
	attacks = [
		Attack((1, 3), 0, "{0} кусает {1}")
	]	
	
	def __init__(self, g) -> None:
		super().__init__(g, "летучая мышь", 3, False)

class Wolf(Monster):
	"""Волк"""
	min_level = 1
	diff = 1
	speed = 20
	passive_perc = 9
	DEX = 12
	WIS = 8
	symbol = "🐺"
	attacks = [
		Attack((1, 3), 0, "{0} кусает {1}")
	]
	
	def __init__(self, g) -> None:
		super().__init__(g, "волк", 4, False)
				
class Kobold(Monster):
	"""Кобольд"""
	diff = 2
	min_level = 3
	DEX = 15
	WIS = 7
	to_hit = 4
	passive_perc = 8
	beast = False
	symbol = "🧟"
	weapon = Dagger
	attacks = [
		Attack((2, 4), 4, "{0} ударяет {1} своим кинжалом")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "кобольд", 10, None, (2, 4))

class ClawGrapple(Attack):
	"""Удар в виде царапания (клешня) """
	
	def __init__(self, dmg, to_hit) -> None:
		super().__init__(dmg, to_hit, "{0} царапает {1}")
		
	def on_hit(self, player, mon, dmg) -> None:
		if not one_in(3) and player.add_grapple(mon):
			player.g.print_msg(f"{mon.name} хватает тебя своей клешней!", "red")

class CrabClaw(ClawGrapple):
	"""Крабья клешня"""
	
	def __init__(self) -> None:
		super().__init__((2, 6), 3)
			
class GiantCrab(Monster):
	"""Гигантский краб"""
	diff = 3
	min_level = 4
	DEX = 15
	WIS = 9
	to_hit = 3
	armor = 2	
	passive_perc = 9
	symbol = "🦀"
	attacks = [
		CrabClaw()
	]
	
	def __init__(self, g) -> None:
		super().__init__(g, "гигантский краб", 20, False)	
						
class RedRabbit(Monster):
	"""Красный кролик"""
	diff = 2
	min_level = 5
	DEX = 15
	to_hit = 4
	passive_perc = 10
	symbol = "🐰"
	attacks = [
		Attack((2, 4), 4, "{0} кусает {1}")
	]
	
	def __init__(self, g) -> None:
		super().__init__(g, "красный кролик", 14, False)


class PoisonBite(Attack):
	"""Ядовитый укус"""
	def __init__(self) -> None:
		super().__init__((2, 4), 6, "{0} кусает {1}")
	
	def on_hit(self, player, mon, dmg) -> None:
		g = player.g
		poison = dice(4, 6) + dice(1, 3)
		if dmg < poison:
			poison = random.randint(dmg, poison)
		player.do_poison(poison)			
  
class SpecterDrain(Attack):
	"""Призрачное истощение"""
	
	def __init__(self) -> None:
		super().__init__((3, 8), 4)
		
	def on_hit(self, player, mon, dmg) -> None:
		player.drain(random.randint(1, dmg))

class GiantPoisonousSnake(Monster):
	"""Гигантская ядовитая змея"""
	diff = 3
	min_level = 8
	DEX = 18
	WIS = 10
	to_hit = 6
	passive_perc = 10
	symbol = "🐍"
	attacks = [
		PoisonBite()
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "гигантская ядовитая змея", 22, False)

class Skeleton(Monster):
	"""Скелет"""
	diff = 3
	min_level = 7
	DEX = 14
	WIS = 8
	to_hit = 4
	armor = 1
	passive_perc = 9
	beast = False
	symbol = "💀"
	weapon = Shortsword
	attacks = [
		Attack((2, 6), 4, "{0} поражает тебя своим коротким мечом")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "скелет", 26, None, (2, 6))

class Dracula(Monster):
	"""Гигантская летучая мышь"""
	diff = 3
	speed = 60
	min_level = 8
	DEX = 16
	WIS = 12
	to_hit = 4
	symbol = "🧛🏿"
	attacks = [
		Attack((2, 6), 4, "{0} кусает {1}")
	]

	def __init__(self, g) -> None:
		super().__init__(g, "гигантская летучая мышь", 26, False)

class DarkWolf(Monster):
	"""Тёмный волк"""
	diff = 3
	min_level = 9
	DEX = 11
	to_hit = 4
	passive_perc = 10
	symbol = "🐶"
	attacks = [
		Attack((2, 8), 4, "{0} кусает {1}")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "тёмный волк", 38, False)

class CrazyBoar(Monster):
	"""Сумасшедший кабан"""
	diff = 4
	speed = 40
	min_level = 12
	DEX = 11
	WIS = 12
	to_hit = 5
	symbol = "🐗"
	attacks = [
		Attack((4, 4), 4, "{0} таранит {1}")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "сумасшедший кабан", 38, False)

class Orc(Monster):
	"""Орк"""
	diff = 4
	speed = 30
	min_level = 12
	DEX = 12	
	WIS = 11
	to_hit = 5
	armor = 2
	passive_perc = 10
	beast = False
	symbol = "🧌"
	weapon = Greataxe
	attacks = [
		Attack((2, 12), 3, "{0} ударяет {1} своим огромным топором")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "орк", 30, None, (2, 6))

class BlackBear(Monster):
	"""Черный медведь"""
	diff = 4
	speed = 40
	min_level = 13
	DEX = 10
	WIS = 12
	to_hit = 3
	armor = 1
	passive_perc = 13
	symbol = "🐻"
	attacks = [
		Attack((2, 6), 3, "{0} кусает {1}"),
		Attack((4, 4), 3, "{0} царапает {1}")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "черный медведь", 38, False)

class GhostBear(Monster):
	"""Призрачный медведь"""
	diff = 5
	speed = 40
	min_level = 15
	DEX = 10	
	WIS = 12
	to_hit = 3
	armor = 1
	passive_perc = 13
	symbol = "🐼"
	attacks = [
		Attack((2, 8), 3, "{0} кусает {1}"),
		Attack((4, 6), 3, "{0} царапает {1}"),
		SpecterDrain()
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "призрачный медведь", 68, False)
  
class Specter(Monster):
	"""Призрак"""
	diff = 5
	speed = 50
	min_level = 18
	DEX = 14
	WIS = 10
	to_hit = 4
	passive_perc = 10
	symbol = "👻"
	attacks = [
		SpecterDrain()
	]
		
	def __init__(self, g):
		super().__init__(g, "призрак", 44, False)


class WalkingFlower(Monster):
	"""Ходячий цветок"""
	diff = 5
	speed = 45
	DEX = 17
	WIS = 12
	min_level = 16
	to_hit = 5
	passive_perc = 14
	symbol = "✿"
	attacks = [
		Attack((2, 6), 5, "{0} атакует {1} своей лазой"),
		Attack((4, 6), 5, "{0} атакует {1} своими корнями")
	]
		
	def __init__(self, g):
		super().__init__(g, "ходячий цветок", 52, False)

class JellyAcidAttack(Attack):
	"""Кислотная атака желе"""
	
	def __init__(self) -> None:
		super().__init__((4, 6), 6, "{0} атакует {1}")
	
	def on_hit(self, player, mon, dmg) -> None:
		g = player.g
		self.g.print_msg("Кислота обжигает!", "red")
		player.take_damage(dice(1, 12))

class AcidSlime(Monster):
	"""Кислотная желе"""
	diff = 6
	speed = 10	
	DEX = 6
	WIS = 6
	min_level = 18
	to_hit = 6
	passive_perc = 8
	beast = False
	symbol = "🦠"
	eff_immunities = {"Charmed", "Frightened"}
	attacks = [
		JellyAcidAttack()
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "кислотная желе", 90, False)

class Ogre(Monster):
	"""Огр"""
	diff = 6
	DEX = 8
	WIS = 7
	min_level = 20
	to_hit = 6
	armor = 2
	passive_perc = 8
	beast = False
	symbol = "👹"
	weapon = Club
	attacks = [
		Attack((2, 6), 6, "{0} бьет {1} своей дубинкой"),
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "огр", 118, False)

class PolarBear(Monster):
	"""Полярный медведь"""
	diff = 6
	speed = 40
	min_level = 18
	DEX = 10
	WIS = 13
	to_hit = 7
	armor = 2
	passive_perc = 13
	symbol = "🐻‍❄️"
	attacks = [
		Attack((2, 8), 7, "{0} кусает {1}"),
		Attack((4, 6), 7, "{0} царапает {1}")
	]
		
	def __init__(self, g):
		super().__init__(g, "полярный медведь", 84, False)

class Rhinoceros(Monster):
	"""Носорог"""
	diff = 6
	speed = 40
	min_level = 19
	DEX = 8
	WIS = 12
	to_hit = 7
	armor = 2
	passive_perc = 13
	symbol = "🦏"
	attacks = [
		Attack((2, 8), 7, "{0} бодает {1}")
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "носорог", 90, False)

class Sasquatch(Monster):
	"""Снежный человек"""
	diff = 7
	speed = 40
	min_level = 22
	DEX = 10
	WIS = 16
	to_hit = 6
	armor = 2
	passive_perc = 17
	beast = False
	symbol = "🧟‍♂️"
	attacks = [
		Attack((2, 8), 6, "{0} бъёт {1} своим кулаком"),
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "снежный человек", 118, False)

class ScorpionClaw(ClawGrapple):
	"""Коготь скорпиона"""
	
	def __init__(self) -> None:
		super().__init__((2, 8), 4)
		
class ScorpionSting(Attack):
	"""Атака скорпиона"""
	
	def __init__(self) -> None:
		super().__init__((2, 10), 4, "{0} жалит {1}")
	
	def on_hit(self, player, mon, dmg):
		g = player.g
		poison = dice(4, 10)
		if dmg < poison:
			poison = random.randint(dmg, poison)
		player.do_poison(poison)			
		
class InfernalScorpion(Monster):
	"""Адский скорпион"""
	diff = 7
	speed = 40
	min_level = 21
	DEX = 13
	WIS = 9
	to_hit = 4
	armor = 4
	passive_perc = 9
	grapple_dc = 12
	symbol = "🦂"
	attacks = [
		ScorpionClaw(),
		ScorpionClaw(),
		ScorpionSting()
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "адский скорпион", 98, False)

class AdhesiveSlimeAttack(Attack):
	"""Атака клейкой слизью"""
	
	def __init__(self) -> None:
		super().__init__((5, 8), 6, "{0} атакует {1}")
	
	def on_hit(self, player, mon, dmg) -> None:
		g = player.g
		if not one_in(7) and player.add_grapple(mon):
			g.print_msg(f"{mon.name} прилипает к вам, удерживая вас на месте!", "red")

class GiantGreenSlime(Monster):
	"""Гигантская зеленая слизь"""
	diff = 8
	speed = 30
	min_level = 24
	DEX = 14
	WIS = 8
	to_hit = 4
	passive_perc = 9
	grapple_dc = 19 #Он настолько липкий, что выходное DC установлено довольно высоко
	symbol = "🟢"
	attacks = [
		AdhesiveSlimeAttack(),
	]
		
	def __init__(self, g) -> None:
		super().__init__(g, "гигантская зеленая слизь", 168, False)


class Troll(Monster):
	"""Троль"""
	diff = 9
	speed = 40
	min_level = 28
	DEX = 13
	WIS = 9
	to_hit = 7
	passive_perc = 11
	armor = 4
	symbol = "👺"
	attacks = [
		Attack((2, 6), 7, "{0} кусает {1}"),
		Attack((4, 6), 7, "{0} царапает {1}"),
		Attack((4, 6), 7, "{0} царапает {1}"),
	]
	
	def __init__(self, g) -> None:
		super().__init__(g, "троль", 168, False)
