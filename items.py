import random, time
from utils import *


class Item:
	"""Это универсальный элемент, который не делает ничего особенного.
                 Он невидим в игре"""
	
	def __init__(self, name, symbol) -> None:
		self.name = name # название
		self.orig_name = name # настоящие название
		self.symbol = symbol # символ предмета
		self.enchant = 0 # зачарование 
	
	def can_enchant(self) -> bool:
		"""Можно зачаровать (метод перезаписывается для каждого предмета)
  		"""
		return False
		
	def add_enchant(self) -> None:
		"""Зачарование на +1 к предмету
  		"""
		self.enchant += 1
		self.name = self.orig_name + f" +{self.enchant}"
		
	def use(self, player) -> bool:
		"""Использвание предмета (метод перезаписывается для каждого предмета)
  		"""
		g = player.g
		g.print_msg("Вы используете предмет. Кажется, ничего интересного не происходит")
		return True
		
class Scroll(Item):
	"""Это обычная прокрутка, которая ничего не делает. Если вы видите это,
 							значит, это ошибка"""
	
	def __init__(self, name) -> None:
		super().__init__(name, "@")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Вы смотрите на пустой свиток. Он сразу же рассыпается в пыль, потому что он такой бесполезный.")
		return True

class HealthPotion(Item):
	"""Употребление этого напитка увеличивает HP."""
	
	def __init__(self) -> None:
		super().__init__("зелье здоровья", "P")
		
	def use(self, player) -> bool:
		g = player.g
		MAX_HP = player.get_max_hp()
		if player.HP >= MAX_HP:
			g.print_msg("Ваш HP уже заполнен!")
			return False
		else:	
			recover = 10 + dice(2, 40)
			g.print_msg("Вы восстанавливаете HP.")
			player.HP = min(MAX_HP, player.HP + recover)
			return True
			
class SpeedPotion(Item):
	"""Употребление этого зелья временно ускоряет передвижение. 
 		Однако, как только эффект пройдет, короткое время 
     			чувствуется слабость (вялость)."""
	
	def __init__(self) -> None:
		super().__init__("зелье скорости", "S")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты пьешь зелье скорости.")
		player.lose_effect("Lethargy", silent=True)
		if player.has_effect("Haste"):
			g.print_msg("Ваша продолжительность скорости начинает увеличиваться.")
		player.gain_effect("Haste", random.randint(40, 60))
		return True
		
class ResistPotion(Item):	
	"""Употребление этого зелья временно уменьшает урон."""
	
	def __init__(self) -> None:
		super().__init__("зелье сопротивления", "R")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты пьешь зелье сопротивления.")
		if player.has_effect("Resistance"):
			g.print_msg("Ваше сопротивление начинает длиться еще дольше.")
		player.gain_effect("Resistance", random.randint(30, 45))
		return True
		
class InvisibilityPotion(Item):
	""""Употребление этого зелья делает игрока временно невидимым. 
 			Однако атака на монстра уменьшит продолжительность 
    					этого эффекта"""
	
	def __init__(self) -> None:
		super().__init__("зелье невидимости", "C")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты пьешь зелье невидимости.")
		if player.has_effect("Invisible"):
			g.print_msg("Ваша невидимость начинает длиться еще дольше.")
		player.gain_effect("Invisible", random.randint(45, 70))
		return True
		
class RejuvPotion(Item):
	"""Употребление этого зелья значительно улучшает регенерацию на короткое время"""
	
	def __init__(self) -> None:
		super().__init__("зелье омоложения", "J")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты пьешь зелье омоложения.")
		if player.has_effect("Rejuvenated"):
			player.lose_effect("Rejuvenated", silent=True)
		player.gain_effect("Rejuvenated", random.randint(20, 25))
		return True
		
class ClairPotion(Item):
	"""Употребление этого зелья позволяет вам видеть дальше того, что вы обычно можете видеть"""
	
	def __init__(self) -> None:
		super().__init__("зелье ясновидения", "Y")
		
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты пьешь зелье ясновидения.")
		if player.has_effect("Clairvoyance"):
			g.print_msg("Вы чувствуете себя еще более ясновидящим.")
		player.gain_effect("Clairvoyance", random.randint(45, 80))
		return True

class ConfusionScroll(Scroll):
	"""Чтение этого свитка может привести к замешательству ближайших монстров"""
	
	def __init__(self) -> None:
		super().__init__("свиток замешательства")
	
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Вы читаете свиток замешательства. Свиток рассыпается в пыль.")
		for m in player.monsters_in_fov():
			if m.is_eff_immune("Confused"):
				g.print_msg(f"Монстр {m.name} не подвержен влиянию.")
			elif dice(1, 20) + calc_mod(m.WIS) >= 15:
				g.print_msg(f"Монстр {m.name} сопротивляется.")
			else:
				g.print_msg(f"Монстр {m.name} находится в замешательстве!")
				m.gain_effect("Confused", random.randint(30, 45))
		return True
		
class SleepScroll(Scroll):
	"""Чтение этого свитка может привести к тому, что некоторые из ближайших монстров заснут"""
	
	def __init__(self) -> None:
		super().__init__("свиток сна")
	
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты читаешь свиток сна. Свиток рассыпается в пыль.")
		mons = list(player.monsters_in_fov())
		random.shuffle(mons)
		mons.sort(key=lambda m: m.HP)
		power = dice(10, 8)
		to_affect = []
		for m in mons:
			if m.has_effect("Asleep"):
				continue
			power -= m.HP
			if power < 0:
				break
			to_affect.append(m)
		if to_affect:
			random.shuffle(to_affect)
			for m in to_affect:
				g.print_msg(f"Монстр {m.name} засыпает!")
				m.gain_effect("Asleep", random.randint(30, 45))
				m.reset_check_timer()
				m.is_aware = False
		else:
			g.print_msg("Кажется, ничего не происходит.")
		return True
		
class StunScroll(Scroll):
	"""Чтение этого свитка оглушает случайное количество ближайших монстров."""
	
	def __init__(self) -> None:
		super().__init__("свиток оглушения")
	
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Ты читаешь свиток оглушения. Свиток рассыпается в пыль.")
		seen = list(player.monsters_in_fov())
		random.shuffle(seen)
		affects = seen[:random.randint(1, len(seen))]
		for m in affects:
			if m.HP <= random.randint(125, 175) and not m.is_eff_immune("Stunned"):
				g.print_msg(f"Монстер {m.name} был оглушен!")
				m.gain_effect("Stunned", random.randint(6, 22))
			else:
				g.print_msg(f"Монстр {m.name} не подвержен влиянию.")
		return True
		
class TeleportScroll(Scroll):
	"""Прочтение этого свитка случайным образом телепортирует того, кто его прочитает"""
	
	def __init__(self) -> None:
		super().__init__("свиток телепортации")
	
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Вы читаете свиток телепортации. Свиток рассыпается в пыль.")
		player.teleport()
		player.energy -= player.get_speed()
		return True
		
class SummonScroll(Scroll):
	"""Прочтение этого свитка вызовет дружественных существ"""
	
	def __init__(self) -> None:
		super().__init__("свиток призыва")
	
	def use(self, player) -> bool:
		g = player.g
		g.print_msg("Вы читаете свиток призыва. Свиток рассыпается в пыль.")

		points = list(player.fov)
		points.remove((player.x, player.y))
		types = list(filter(lambda t: t.diff <= 7 and g.level > t.min_level, g.monster_types))
		num = random.randint(2, 3)
		random.shuffle(points)
		points.sort(key=lambda p: abs(p[0] - player.x) + abs(p[1] - player.y))
		ind = 0
		while ind < len(points) and num > 0:
			typ = random.choice(types)
			duration = random.randint(50, 80)
			pos = points[ind]
			if g.monster_at(*pos):
				ind += 1
				continue
			m = typ(g)
			m.ranged = False
			m.place_at(*pos)
			m.summon_timer = duration
			g.monsters.append(m)
			ind += random.randint(1, 2)
			num -= 1
		return True

class EnchantScroll(Scroll):
	"""Прочтение этого свитка зачаровывает оружие или доспехи по выбору игрока."""
	
	def __init__(self) -> None:
		super().__init__("свиток зачарования")
	
	def use(self, player) -> bool:
		g = player.g
		items = [t for t in player.inventory if t.can_enchant()]
		if not items:
			g.print_msg("У вас нет никаких предметов, которые можно было бы зачаровать.")
		else:
			items.sort(key=lambda t: t.name)
			strings = ", ".join(f"{i+1}. {t.name}" for i, t in enumerate(items))
			g.print_msg("Какой предмет зачаровать? (Введите число)")
			g.print_msg(strings)
			try:
				num = int(g.input())
				if num < 1 or num > len(items):
					g.print_msg(f"Число должно быть в диапазоне от 1 до {len(items)}.")
					return False 
			except ValueError:
				g.print_msg("Вы не ввели номер.")
				return False
			g.print_msg("Ты читаешь свиток заклинаний. Свиток рассыпается в пыль.")
			item = items[num-1]
			g.print_msg(f"Ты очаровываешь свой {item.name}. Он получает бонус +1.")
			item.add_enchant()
		return True
		
class Activity:
	"""Действия с вещами"""
	
	def __init__(self, name, time) -> None:
		self.name = name # название предмета
		self.time = time # время нужное на действие
		
	def on_finished(self, player) -> None:
		pass
		
class WearArmor(Activity):
	"""Надевание брони"""
	
	def __init__(self, armor) -> None:
		super().__init__(f"надеваешь свои {armor.name}", 30)
		self.armor = armor
		
	def on_finished(self, player) -> None:
		player.armor = self.armor
		g = player.g
		g.print_msg(f"Ты заканчиваешь надевать свои {self.armor.name}.")
		
class RemArmor(Activity):
	
	def __init__(self, armor) -> None:
		super().__init__(f"снимаешь свои {armor.name}", 20)
		self.armor = armor
		
	def on_finished(self, player) -> None:
		player.armor = None
		g = player.g
		g.print_msg(f"Вы заканчиваете снимать свои {self.armor.name}.")
				
class Armor(Item):
	"""Класс брони"""
	stealth_pen = 0
	dex_mod_softcap = None #Это означает бонус за ловкость к AC
	
	def __init__(self, name, symbol, protect) -> None:
		super().__init__(name, symbol)
		self._protect = protect
	
	@property 
	def protect(self) -> int:
		return self._protect + self.enchant
		
	def can_enchant(self) -> bool:
		return self.enchant < 3
		
	def use(self, player) -> bool:
		g = player.g
		if player.armor and player.armor.name == self.name:
			if g.yes_no(f"Ты снимишь {self.name}?"):
				player.activity = RemArmor(self)
		else:
			g.print_msg(f"Вы начинаете надевать свои {self.name}.")
			player.activity = WearArmor(self)
		return False 

class LeatherArmor(Armor):
	"""Кожаная броня"""
				
	def __init__(self) -> None:
		super().__init__("кожаные доспехи", "L", 1)

class HideArmor(Armor):
	"""Скрытый доспех"""
				
	def __init__(self) -> None:
		super().__init__("скрытый доспех", "H", 2)
		
class ChainShirt(Armor):
	"""Кольчужная рубашка"""
	dex_mod_softcap = 4
				
	def __init__(self) -> None:
		super().__init__("кольчужная рубашка", "C", 3)
  
####################################################################################
class ScaleMail(Armor):
	stealth_pen = 2
	dex_mod_softcap = 3
				
	def __init__(self) -> None:
		super().__init__("scale mail", "M", 4)

class HalfPlate(Armor):
	stealth_pen = 4
	dex_mod_softcap = 2
				
	def __init__(self) -> None:
		super().__init__("half-plate", "A", 5)

class ChainMail(Armor):
	"""Кольчуга"""
	stealth_pen = 6
	dex_mod_softcap = 1
				
	def __init__(self) -> None:
		super().__init__("кольчуга", "I", 6)

class SplintArmor(Armor):
	stealth_pen = 8
	dex_mod_softcap = 0
				
	def __init__(self) -> None:
		super().__init__("splint armor", "S", 7)

class PlateArmor(Armor):
	stealth_pen = 10
	dex_mod_softcap = -1
				
	def __init__(self) -> None:
		super().__init__("plate armor", "T", 8)
####################################################################################	
  
class Weapon(Item):
	"""Класс Оружие"""
	crit_mult = 2
	crit_thresh = 20
	dmg_type = "default"
	
	def __init__(self, name, symbol, dmg, finesse=False, heavy=False, thrown=None) -> None:
		super().__init__(name, symbol)
		self.dmg = Dice(*dmg)
		self.finesse = finesse
		self.heavy = heavy #Тяжелое оружие получает штраф -2 за броски в атаку
		self.thrown = thrown #Либо нет, либо 2 кортежа, представляющих короткий и длинный диапазоны
	
	def can_enchant(self) -> bool:
		return self.enchant < 3
	
	def use(self, player) -> bool:
		g = player.g
		if self is player.weapon:
			if g.yes_no(f"Убрать своё оружие \"{self.name}\"?"):
				player.weapon = UNARMED
				player.energy -= player.get_speed()
			else:
				return False
		else:
			if player.weapon is not UNARMED:
				player.energy -= player.get_speed()
				g.print_msg(f"Ты переключаешься на свое оружие \"{self.name}\".")
			else:
				g.print_msg(f"Ты владеешь оружием \"{self.name}\".")
			player.weapon = self
			
	def roll_dmg(self) -> int:
		return self.dmg.roll()
		
	def on_hit(self, player, mon) -> None:
		pass
		
class NullWeapon(Weapon):
	"""Кулаки"""
	dmg_type = "дубинка"
	
	def __init__(self) -> None:
		super().__init__("безоружный", "f", (1, 2))
		
	def can_enchant(self) -> bool:
		return False
		
UNARMED = NullWeapon()

class Club(Weapon):
	"""Дубинка"""
	dmg_type = "bludgeon"
	
	def __init__(self) -> None:
		super().__init__("дубинка", "!", (1, 4))
		
class Dagger(Weapon):
	"""Кинжальное оружие"""
	crit_thresh = 19
	dmg_type = "pierce"
	
	def __init__(self) -> None:
		super().__init__("кинжал", "/", (1, 4), finesse=True, thrown=(4, 12))

class Handaxe(Weapon):
	"""Ручной топор"""
	crit_mult = 3
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("ручной топор", "h", (1, 6), thrown=(4, 12))

class Javelin(Weapon):
	"""Копье"""
	dmg_type = "bludgeon"
	
	def __init__(self) -> None:
		super().__init__("копье", "j", (1, 6), thrown=(6, 24))

class Mace(Weapon):
	"""Булава"""
	dmg_type = "bludgeon"
	
	def __init__(self) -> None:
		super().__init__("булава", "T", (1, 6))

class Shortsword(Weapon):
	"""Короткий меч"""
	crit_thresh = 19
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("короткий меч", "i", (1, 6), finesse=True)

class Longsword(Weapon):
	"""Длинный меч"""
	crit_thresh = 19
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("длинный меч", "I", (1, 9))

class Greatclub(Weapon):
	"""Улучшенная дубинка"""
	dmg_type = "bludgeon"
	
	def __init__(self) -> None:
		super().__init__("улучшенная дубинка", "P", (1, 8))

class Battleaxe(Weapon):
	"""Боевой топор"""
	crit_mult = 3
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("боевой топор", "F", (1, 9))

class Morningstar(Weapon): 
	""""##################################################################################################################################################"""
	dmg_type = "pierce"
	
	def __init__(self) -> None:
		super().__init__("morningstar", "k", (1, 8))

class Glaive(Weapon):
	"""Глефа"""
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("глефа", "L", (1, 10), heavy=True)
		
class Greataxe(Weapon):
	"""Двуручный топор"""
	crit_mult = 3
	dmg_type = "slash"
	
	def __init__(self) -> None:
		super().__init__("двуручный топор", "G", (1, 12), heavy=True)

class Wand(Item):
	"""Волшебная палочка"""
	
	def __init__(self, name, charges, efftype="blast") -> None:
		super().__init__(name, "Î")
		self.charges = charges
		self.efftype = efftype
	
	def wand_effect(self, player, mon) -> None:
		self.g.print_msg("Кажется, ничего особенного не происходит.")
		
	def use(self, player) -> bool:
		g = player.g
		monsters = list(player.monsters_in_fov())
		g.print_msg(f"У этой палочки остались {self.charges} заряды.")
		target = g.select_monster_target()
		if not target:
			return
		if g.board.line_of_sight((player.x, player.y), (target.x, target.y)):
			line = list(g.board.line_between((player.x, player.y), (target.x, target.y)))
		else:
			line = list(g.board.line_between((target.x, target.y), (player.x, player.y)))
			line.reverse()
		if self.efftype == "ray":
			t = player.distance(target)
			def raycast(line, rnd):
				line.clear()
				dx = target.x - player.x
				dy = target.y - player.y
				i = 1
				x, y = player.x, player.y
				hittarget = False
				while True:
					nx = rnd(player.x + dx * (i/t))
					ny = rnd(player.y + dy * (i/t))
					i += 1
					if (nx, ny) == (x, y):
						continue
					if (x, y) == (target.x, target.y):
						hittarget = True
					if g.board.blocks_sight(nx, ny):
						return hittarget #Луч должен, по крайней мере, попасть в цель, если он не достигнет никого другого
					x, y = nx, ny
					line.append((x, y))
			rounds = (int, round, math.ceil)
			line = []
			for f in rounds:
				if raycast(line, f):
					break
			g.blast.clear()
			for x, y in line:
				t = g.get_monster(x, y)
				if t is not None:
					if not target.despawn_summon():
						self.wand_effect(player, t)
						t.on_alerted()
				g.blast.add((x, y))
				g.draw_board()
				time.sleep(0.001)
			time.sleep(0.05)
			g.blast.clear()
			g.draw_board()
		else:
			for x, y in line:
				g.set_projectile_pos(x, y)
				g.draw_board()
				time.sleep(0.03)
				if (t := g.get_monster(x, y)) is not None:
					if t is not target and x_in_y(3, 5): #Если на пути окажется существо, мы можем поразить его вместо намеченной цели.
						g.print_msg(f"Монстер {t.name} стоит на пути.")
						target = t
						break
			g.clear_projectile()
			if not target.despawn_summon():
				self.wand_effect(player, target)
		self.charges -= 1
		player.did_attack = True
		alert = 2 + (self.efftype == "ray") #Эффекты лучей, воздействующие на всех монстров в линии, с гораздо большей вероятностью насторожат монстров
		for m in player.monsters_in_fov():
			if x_in_y(alert, 4) or m is target: #Взмах волшебной палочки, скорее всего, предупредит ближайших монстров о вашем местонахождении
				m.on_alerted()
		return (True if self.charges <= 0 else None)
		
class MagicMissile(Wand):
	"""Эту палочку можно использовать для стрельбы магическими снарядами по существам, которые всегда будут попадать"""
	
	def __init__(self) -> None:
		super().__init__("жезл волшебных снарядов", random.randint(3, 7))
	
	def wand_effect(self, player, target) -> None:
		g = player.g
		dam = 0
		for _ in range(3):
			dam += target.apply_armor(random.randint(2, 5))
		msg = f"Волшебные снаряды попали в {target.name} "
		if dam <= 0:
			msg += "но не причиняйте никакого вреда."
		else:
			target.HP -= dam
			msg += f"на {dam} единиц урона."
			if target.HP > 0:
				msg += f" Его HP: {target.HP}/{target.MAX_HP}"
		g.print_msg(msg)
		if target.HP <= 0:
			player.defeated_monster(target)

class PolymorphWand(Wand):
	"""Эту палочку можно использовать для превращения ближайших врагов во что-то более слабое."""
	
	def __init__(self) -> None:
		super().__init__("палочка превращения", random.randint(random.randint(2, 7), 7))
	
	def wand_effect(self, player, target) -> None:
		g = player.g
		if target.saving_throw(target.WIS, 15):
			g.print_msg(f"Монстр {target.name} сопротивляется.")
		else:
			target.polymorph()
			
class WandOfFear(Wand):
	"""Эту палочку можно использовать для того, чтобы заставить ближайших врагов испугаться игрока."""
	
	def __init__(self) -> None:
		super().__init__("жезл страха", random.randint(3, 7))
	
	def wand_effect(self, player, target) -> None:
		g = player.g
		if target.is_eff_immune("Frightened"):
			g.print_msg(f"Монстр {target.name} не подвержен влиянию.")
		elif target.saving_throw(target.WIS, 15):
			g.print_msg(f"Монстр {target.name} сопротивляется.")
		else:
			g.print_msg(f"Монстр {target.name} напуган!")
			target.gain_effect("Frightened", random.randint(30, 60))
	
class LightningWand(Wand):
	"""Эту палочку можно использовать для метания молний, нанося урон ближайшим врагам"""
	
	def __init__(self) -> None:
		super().__init__("жезл молнии", random.randint(3, 7), efftype="ray")
	
	def wand_effect(self, player, target) -> None:
		g = player.g
		numdice = 8
		if not target.has_effect("Paralyzed") and target.saving_throw(target.DEX, 15):
			numdice = 4
			g.print_msg(f"Монстр {target.name} частично сопротивляется.")
		damage = target.apply_armor(dice(numdice, 6))
		msg = f"Стрела молнии поражает {target.name} "
		if damage <= 0:
			msg += "но не причиняет никакого вреда."
		else:
			msg += f"на {damage} единиц урона."
			target.HP -= damage
		g.print_msg(msg)
		if target.HP <= 0:
			player.defeated_monster(target)
		else:
			target.maybe_split(damage, 6)

class Ring(Item):
	"""Это кольцо, которое может обеспечить пассивный бонус при снаряжении"""
	#Пассивами могут быть: STR, DEX, protect, stealth, dodge, to_hit
	_valid_passives = {"STR", "DEX", "protect", "stealth", "dodge", "to_hit"}
	def __init__(self, name, wear_msg, rem_msg, passives={}) -> None:
		super().__init__(name, "ô")
		for key in passives:
			if key not in self._valid_passives:
				raise ValueError(f"{key!r} не является действительным пассивом")
		self.wear_msg = wear_msg
		self.rem_msg = rem_msg
		self.passives = passives
		
	def use(self, player) -> bool:
		g = player.g
		worn_rings = player.worn_rings
		if self in worn_rings:
			if g.yes_no(f"Снять своё {self.name}?"):
				g.print_msg(f"Ты снимаешь своё {self.name}.")
				g.print_msg(self.rem_msg)
				worn_rings.remove(self)
				player.recalc_passives()
		else:
			if len(worn_rings) >= 7:
				g.print_msg(f"На тебе уже надето максимальное количество колец.")
				return False	
			else:
				g.print_msg(f"Ты надеваешь {self.name}.")
				g.print_msg(self.wear_msg)
				worn_rings.append(self)
				player.recalc_passives()
				
class ProtectionRing(Ring):
	"""Это кольцо может обеспечить небольшой бонус к защите при снаряжении"""
	
	def __init__(self) -> None:
		super().__init__("кольцо защиты", "Вы чувствуете себя более защищенным.", "Вы чувствуете себя более уязвимым.",
			passives={"защита": 1}
		)
		
class StrengthRing(Ring):
	"""Это кольцо может обеспечить дополнительный прирост силы при снаряжении"""
	
	def __init__(self) -> None:
		super().__init__("кольцо силы", "Ты чувствуешь себя сильнее.", "Ты больше не чувствуешь себя таким сильным.",
			passives={"STR": 3}
		)

class DexterityRing(Ring):
	"""Это кольцо может стать бонусом к ловкости при снаряжении"""
	
	def __init__(self) -> None:
		super().__init__("кольцо ловкости", "Вы чувствуете, что ваша ловкость улучшилась.", "Вы чувствуете себя менее подвижным.",
			passives={"DEX": 3}
		)	