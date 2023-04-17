import random, math
    
    
def dice(num:int, sides:int) -> int:
	"""Бросает заданное количество кубиков с заданным количеством граней и получает сумму

	Args:
		num (int): Количество кубиков
		sides (int): Количество граней

	Returns:
		int: Сумма всех бросков
	"""
	return sum(random.randint(1, sides) for _ in range(num))

def div_rand(x:int, y:int) -> None:
	"""Вычисляет x / y, затем случайным образом округляет результат в большую или меньшую сторону в зависимости от остатка
 	"""
	sign = 1
	if (x > 0) ^ (y > 0):  # Определяем знак + или -
		sign = -1
	x = abs(x)
	y = abs(y)
	mod = x % y
	return sign * (x//y + (random.randint(1, y) <= mod))

def mult_rand_frac(num, x, y):
	"""Вычисляет рандомное число при делении u и y, где u= num*x
	"""
	return div_rand(num*x, y)
	
def rand_weighted(*pairs) -> list:
	"""Возвращает рандомное название в зависимости от весов
 	"""
	names, weights = list(zip(*pairs))
	return random.choices(names, weights=weights)[0]

def d20_prob(DC, mod, nat1=False, nat20=False):
	num_over = 21 - DC + mod
	if nat1:
		num_over = min(num_over, 19)
	if nat20:
		num_over = max(num_over, 1)
	return max(0, min(1, num_over/20))

def to_hit_prob(AC, hit_mod=0, adv=False, disadv=False) -> float:
	"""
	Вычисляет процентную вероятность успешного попадания
		1) adv - Если true, вычисляет вероятность с преимуществом
		2) disadv - Если true, вычисляет вероятность с недостатком
	"""
	if adv and disadv:
		adv = False
		disadv = False
	res = d20_prob(AC, hit_mod, True, True)
	if adv:
		res = 1-((1 - res)**2)
	elif disadv:
		res = res**2
	return round(res, 3)
	
def calc_mod(stat, avg=False):
	m = stat - 10
	if avg:
		return m / 2
	else:
		return div_rand(m, 2)
	
def one_in(x) -> bool:
	"""Высчитывает c вероятностью 1/x
    """
	return x <= 1 or random.randint(1, x) == 1

def x_in_y(x, y) -> bool:
	"""Высчитывает вероятность в зависимости от значений x и y
 """
	return random.randint(1, y) <= x	
	
def binomial(num, x, y=100):
	"""Биномиальное распределение
    """
	return sum(1 for _ in range(num) if x_in_y(x, y))
			
def display_prob(perc) -> str:
	"""Правильное отображение на экран процентов
    """
	if perc <= 0:
		return "0%"
	if perc >= 100:
		return "100%"
	if perc <= 0.5:
		return "<1%"
	if perc >= 99.5:
		return ">99%"
	if perc < 50:
		perc = math.ceil(perc - 0.5)
	else:
		perc = math.floor(perc + 0.5)
	return f"{perc}%"
	
class Dice:
	"""Класс игральной кости для вероятностей"""
 
	def __init__(self, num, sides):
		self.num = num
		self.sides = sides
		
	def avg(self):
		return self.num * (self.sides + 1) // 2
		
	def roll(self):
		return dice(self.num, self.sides)
		
	def max(self):
		return self.num*self.sides