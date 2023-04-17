import random


class Effect:
	"""Родительский класс для всех эффектов
    """
	name = "Generic Effect"
	
	def __init__(self, duration, add_msg, rem_msg) -> None:
		self.duration = duration # продолжительность
		self.add_msg = add_msg # текст влияния эффекта
		self.rem_msg = rem_msg # тест после спада эффекта
		
	def on_expire(self, player) -> None: # Метод будет перезаписан для эффекта
		"""Что будет с игроком, когда закончится действие эффекта"""
		pass
		
class Lethargy(Effect):
	"""Класс эффекта Вялость
 	"""
	name = "Lethargy"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Вы начинаете чувствовать вялость.", "Ваша энергия возвращается.")
				
class Haste(Effect):
	"""Класс эффекта Спешка (увеличивает скорость)"""
	name = "Haste"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Вы начинаете двигаться быстрее.", "Ваша дополнительная скорость иссякает.")
	
	def on_expire(self, player) -> None: # После бега игрок устаёт
		g = player.g
		player.gain_effect("Lethargy", random.randint(4, 10))
		
class Resistance(Effect):
	"""Класс эффекта Сопротивление
 	"""
	name = "Resistance"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Вы чувствуете себя более устойчивым к повреждениям.", "Ты снова чувствуешь себя уязвимой.")
	
class Invisible(Effect):
	"""Класс эффекта Невидимость
 	"""
	name = "Invisible"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Ты стал невидимым.", "Ты стал видимым.")

class Rejuvenated(Effect):
	"""Класс эффекта Омоложение
 	"""
	name = "Rejuvenated"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Вы начинаете чувствовать себя чрезвычайно помолодевшим.", "Омоложение проходит.")

class Clairvoyance(Effect):
	"""Класс эффекта Ясновидение
 	"""
	name = "Clairvoyance"
	
	def __init__(self, duration) -> None:
		super().__init__(duration, "Вы чувствуете себя гораздо более проницательным.", "Твое ясновидение угасает.")
