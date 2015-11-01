import sets.card as crd

class Copper(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Copper"
		self.value = 1
		self.price = 0
		self.description = "+$1"

	def play(self, skip=False):
		crd.Money.play(self, skip)
		if "Grand Market" in self.game.supply and "Grand Market" not in self.played_by.banned:
			self.played_by.banned.append("Grand Market")
			self.played_by.update_mode_buy_phase()

	def get_spend_all(self):
		if "Grand Market" in self.game.supply and self.played_by is not None:
			spend_all_treasures = [x for x in self.played_by.hand.get_cards_by_type("Treasure", True) if x.title != "Copper" and x.get_spend_all()]
			potential_balance = 0
			for x in spend_all_treasures:
				potential_balance += x.value
			if self.played_by.balance >=6 or potential_balance + self.played_by.balance >=6:
				return False
			else:
				return True
		else:
			return True

class Silver(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Silver"
		self.value = 2
		self.price = 3
		self.description = "+$2"


class Gold(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Gold"
		self.value = 3
		self.price = 6
		self.description = "+$3"


class Platinum(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Platinum"
		self.value = 5
		self.price = 9
		self.description = "+$5"


class Curse(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Curse"
		self.description = "-1 VP"
		self.price = 0
		self.vp = -1
		self.type = "Curse"

	def get_vp(self):
		return self.vp
		
	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-curse'>", self.title, "s</span>" if plural else "</span>"])

class Estate(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Estate"
		self.description = "1 VP"
		self.price = 2
		self.vp = 1


class Duchy(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Duchy"
		self.description = "3 VP"
		self.price = 5
		self.vp = 3

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Duchies</span>" if plural else self.title, "</span>"])


class Province(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Province"
		self.description = "6 VP"
		self.price = 8
		self.vp = 6


class Colony(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Colony"
		self.description = "10 VP"
		self.price = 11
		self.vp = 10

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Colonies</span>" if plural else self.title, "</span>"])