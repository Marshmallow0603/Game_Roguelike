# import math

# def line_between(pos1, pos2, skipfirst=False, skiplast=False):
# 		x1, y1 = pos1
# 		x2, y2 = pos2
# 		delta_x = abs(x2 - x1)
# 		sign_x = 1 if x1 < x2 else -1
# 		delta_y = -abs(y2 - y1)
# 		sign_y = 1 if y1 < y2 else -1
# 		error = delta_x + delta_y
  
# 		while True:
# 			do_yield = True
   
# 			if (skipfirst and (x1, y1) == pos1) or (skiplast and (x1, y1) == pos2):
# 				do_yield = False
    
# 			if do_yield:
# 				yield (x1, y1)
    
# 			if (x1, y1) == (x2, y2):
# 				return

# 			e2 = 2 * error
# 			if e2 >= delta_y:
# 				if x1 == x2:
# 					return
# 				error += delta_y
# 				x1 += sign_x
# 			if e2 <= delta_x:
# 				if y1 == y2:
# 					return 
# 				error += delta_x
# 				y1 += sign_y
    
# def in_bounds(x, y) -> bool:
# 	"""Проверяет, что обЪект не вышел за границы
# 	"""
# 	return 0 <= x < 100 and 0 <= y < 100
    
# def get_in_radius(pos, radius) -> tuple:
# 	"""Получаем точки входящие в радиус (генератор кортежей x и y)
# 	"""
# 	x, y = pos
# 	for px in range(x-radius, x+radius+1):
# 		for py in range(y-radius, y+radius+1):
# 			if (px, py) != pos and in_bounds(x, y):
# 				yield (px, py)
    
# def get_in_cone(pos, radius, angle, widthdeg=60):
# 		cone_x, cone_y = pos 
# 		angle %= 360
# 		for x, y in get_in_radius(pos, radius):
# 			delta_x = x - cone_x
# 			delta_y = y - cone_y
# 			dist = math.sqrt(delta_x**2 + delta_y**2)
# 			if round(dist) > radius:
# 				continue
# 			dir = math.degrees(math.atan2(delta_y, delta_x))
# 			half = widthdeg/2
# 			if dir < 0:
# 				dir += 360
			
# 			if abs(angle - dir) <= half:
# 				yield x, y
# 			elif angle + half >= 360 and dir <= (angle + half) % 360:
# 				yield x, y 
# 			elif angle - half < 0 and dir >= angle-half+360:
# 				yield x, y



# a = get_in_cone((20,20), 5, 45)
# for i in a:
#     print(i)



# from os import terminal_size

# terminal_size(columns=100, lines=50)

# import os
# cmd = 'mode 250,26'
# os.system(cmd)


# square_size = 228
# tree_height = 26

# for h in range(tree_height):
#     if h % 2 == 0:
#         num_leaves = h + 1
#         num_spaces = (square_size - num_leaves) // 2
#         print(" " * num_spaces + "X" * num_leaves + " " * num_spaces)
#     else:
#         num_leaves = h + 2
#         num_spaces = (square_size - num_leaves) // 2
#         print(" " * num_spaces + "X" * num_leaves + " " * num_spaces)

# print(" " * 100 + "|")


# s = [
#     ['●▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ஜ۩۞۩ஜ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●'], 
#     ['░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░'],
#     ['░░░░░░░░░░░░░█░█░█░█▀▀▀░█░░░░█▀▀▀░█▀▀█░█▀█▀█░█▀▀▀░░░░░░░░░░░░'],
#     ['░░░░░░░░░░░░░█░█░█░█▀▀▀░█░░░░█░░░░█░░█░█░█░█░█▀▀▀░░░░░░░░░░░░'],
#     ['░░░░░░░░░░░░░▀▀▀▀▀░▀▀▀▀░▀▀▀▀░▀▀▀▀░▀▀▀▀░▀░▀░▀░▀▀▀▀░░░░░░░░░░░░'],
#     ['░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░'],
#     ['●▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ஜ۩۞۩ஜ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬●']
#     ]

# for i in s:
#     print(*i)


# string = 'cat' 
# width = 4
# fillchar = '*' 
# print(string.just(width, fillchar))

# print(ord('q'))

    
import random, time
import math
from collections import deque
from os import get_terminal_size
import curses

from utils import *
from board import *    
from gameobj import *                    
from entity import *        
from items import *
from monster import *


g = Game()
