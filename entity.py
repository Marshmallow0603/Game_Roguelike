import random
from collections import deque
from board import *


class Entity:
	"""Класс всех сущностей"""
	
	def __init__(self, g):
		self.g = g
		self.x = 0
		self.y = 0
		self.curr_target = None
		self.curr_path = deque()
		self.placed = False
		self.energy = 0 #Сколько энергетических точек есть у этой сущности. Используется для контроля скорости движения.
		self.fov = set()
		
	def calc_fov(self) -> set:
		"""Вычисляет все tiles, которые объект может видеть из текущей позиции

		Returns:
			set: множество всех видимых tiles -> tuple(x, y)
		"""
		board = self.g.board
		fov = set()
		fov.add((self.x, self.y))
		#Этап добавления видимых tiles (Свет)
		for x in range(board.cols):
			for point in board.line_between((self.x, self.y), (x, 0), skipfirst=True):
				fov.add(point)
				if board.blocks_sight(*point): 
					break			
			for point in board.line_between((self.x, self.y), (x, board.rows - 1), skipfirst=True):
				fov.add(point)
				if board.blocks_sight(*point):
					break
		for y in range(1, board.rows - 1):
			for point in board.line_between((self.x, self.y), (0, y), skipfirst=True):
				fov.add(point)
				if board.blocks_sight(*point):
					break
			for point in board.line_between((self.x, self.y), (board.cols - 1, y), skipfirst=True):
				fov.add(point)
				if board.blocks_sight(*point):
					break
					
		#Этап последующей обработки
		seen = set()
		for cell in fov.copy():
			if board.blocks_sight(*cell):
				continue
			x, y = cell
			delta_x = x - self.x
			delta_y = y - self.y
			neighbors = {(x-1, y), (x+1, y), (x, y-1), (x, y+1)}
			neighbors -= seen
			neighbors -= fov
			for x_pos, y_pos in neighbors:
				seen.add((x_pos, y_pos))
				if not (0 <= x_pos < board.cols):
					continue
				if not (0 <= y_pos < board.cols):
					continue
				if board.blocks_sight(x_pos, y_pos):
					visible = False
					delta_x_pos = x_pos - x
					delta_y_pos = y_pos - y
					if delta_x <= 0 and delta_y <= 0:
						visible = delta_x_pos <= 0 or delta_y_pos <= 0
					if delta_x >= 0 and delta_y <= 0:
						visible = delta_x_pos >= 0 or delta_y_pos <= 0
					if delta_x <= 0 and delta_y >= 0:
						visible = delta_x_pos <= 0 or delta_y_pos >= 0	
					if delta_x >= 0 and delta_y >= 0:
						visible = delta_x_pos >= 0 or delta_y_pos >= 0
					if visible:
						fov.add((x_pos, y_pos))
      
		return fov
		
	def can_see(self, x, y) -> bool:
		"""Входят ли x и y в видимые точки (fov)
  		"""
		return (x, y) in self.fov
		
	def distance(self, other, same_coordinate=True) -> int:
		"""Считает растояние от одного обЪекта до другого (упращённо)
  		"""
		delta_x = abs(self.x - other.x)
		delta_y = abs(self.y - other.y)
		if same_coordinate:
			return delta_x + delta_y
		return max(delta_x, delta_y)
		
	def distance_pos(self, pos) -> int:
		"""Считает расстояние от точки обЪекта до передаваемой точки (pos)
  		"""
		return abs(self.x - pos[0]) + abs(self.y - pos[1])
		
	def clear_path(self) -> None:
		"""Очистка текущего пути ввиде точек
  		"""
		self.curr_path.clear()
		
	def path_to(self, x, y, maxlen=None) -> None:
		"""Высчитывает путь от обЪект до точки с передоваемой максимальной длиной
  		"""
		if self.curr_target == (x, y) and self.curr_path and self.move_to(*self.curr_path.popleft()):
			if (self.x, self.y) == (x, y):
				self.clear_path()
			return
		path = pathfind(self.g.board, (self.x, self.y), (x, y), rand=True)
		if len(path) < 2:
			return
		if maxlen and len(path) > maxlen+1:
			return
		currX, currY = self.x, self.y
		self.curr_target = (x, y)
		self.curr_path = deque(path[1:])
		newX, newY = self.curr_path.popleft()
		dx = newX - currX
		dy = newY - currY
		self.move(dx, dy)
		
	def set_path(self, path) -> None:
		"""Добавление пути в текущий путь
  		"""
		self.curr_path = deque(path)
		
	def can_place(self, x, y) -> bool:
		"""Проверка, можно ли разместить обЪект на позицию (x, y)
  		"""
		if (x, y) == (self.g.player.x, self.g.player.y): # Поверх игрока нельзя ничего размещать
			return False
		board = self.g.board
		if not board.is_passable(x, y): # Если точки является не проходимым обЪектом
			return False
		neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
		for xp, yp in neighbors:
			if board.is_passable(xp, yp):
				return True
		return False
		
	def place_randomly(self) -> bool:
		"""Размещение случайным образом
  		"""
		board = self.g.board
		for _ in range(200): # Размещаем случайным образом за 200 попыток
			x = random.randint(1, board.cols - 2)
			y = random.randint(1, board.rows - 2)
			if self.can_place(x, y):
				break
		else: #Мы не смогли разместить игрока случайным образом, поэтому давайте проведем поиск по всем возможным позициям в случайном порядке
			row_index = list(range(1, board.rows - 1))
			random.shuffle(row_index)
			found = False
			for ypos in row_index:
				col_index = list(range(1, board.cols - 1))
				random.shuffle(col_index)
				for xpos in col_index:
					if self.can_place(xpos, ypos):
						x, y = xpos, ypos
						found = True
						break
				if found:
					break
			else:
				return False
		self.place_at(x, y)
		return True
		
	def place_at(self, x, y) -> None:
		"""Размещаем обЪект на заданную точку
  		"""
		old = (self.x, self.y)
		self.x = x
		self.y = y
		if self.placed:
			self.g.board.swap_cache(old, (self.x, self.y))
		else:
			self.placed = True
			self.g.board.set_cache(x, y)
		
	def swap_with(self, other) -> None:
		"""Меняет местами позиции двух обЪектов
  		"""
		tmp = (self.x, self.y)
		self.x, self.y = other.x, other.y
		other.x, other.y = tmp
		
	def can_move(self, x, y):
		"""Проверка, может ли объект двигать в указанную точку
  		"""
		return self.g.board.is_passable(x, y)
		
	def move_to(self, x, y) -> bool:
		"""Осуществляет перемещение объекта в указанную точку

		Returns:
			bool: True - успешно, False - нельзя двигаться в указанную точку 
		"""
		board = self.g.board
		if self.can_move(x, y):
			oldpos = (self.x, self.y)
			self.x = x
			self.y = y
			self.g.board.swap_cache(oldpos, (self.x, self.y))
			return True
		return False
		
	def move(self, dx, dy) -> bool:
		"""Осуществляет перемещение объекта с шагом для x (+1n, -1n) и для y (+1n, -1n)
  		
    	Returns:
			bool: True - успешно, False - что-то мешает двигаться в точку
   		"""
		return self.move_to(self.x + dx, self.y + dy)