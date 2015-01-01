import client as c
import card
import json

class Game():
	def __init__(self, players):
		self.players = players
		self.first = 0
		self.turn = self.first
		self.turn_count = 0

	def chat(self, msg, speaker):
		for i in self.players:
			i.write_json(command="chat", msg=msg, speaker=speaker)

	def start_game(self):
		self.announce("Starting game with " + str(self.players[0].name) + " and " + str(self.players[1].name))
		for i in self.players:
			i.setup()
		self.announce("<b>---- " + self.players[self.turn].name + " 's turn ----</b>")
		self.players[self.turn].take_turn()

	def announce(self, msg):
		for i in self.players:
			i.write_json(command="announce",msg=msg)

	def change_turn(self):
		self.turn_count += 1
		self.turn = self.turn_count % len(self.players)
		self.announce("<b>---- " + str(self.players[self.turn].name) + " 's turn ----</b>")
		self.players[self.turn].take_turn()

	def get_turn_owner(self):
		return self.players[self.turn]

class DmGame(Game):
	def __init__(self, players):
		Game.__init__(self, players)
		self.empty_piles = 0
		#kingdom = dictionary {card.title => [card, count]} i.e {"Copper": [card.Copper(self,None),10]}
		self.base_supply = self.init_supply([card.Curse(self, None), card.Estate(self, None), 
			card.Duchy(self, None), card.Province(self, None), card.Copper(self,None),
			card.Silver(self, None), card.Gold(self, None)])

		self.kingdom = self.init_supply([card.Village(self, None),
			card.Woodcutter(self,None), card.Militia(self, None),
			card.Cellar(self,None), card.Laboratory(self, None), card.Festival(self, None), 
			card.Council_Room(self,None), card.Remodel(self, None), card.Moneylender(self, None), card.Spy(self, None),
			card.Witch(self,None)])

		self.supply = self.base_supply.copy()
		self.supply.update(self.kingdom)


	#override
	def start_game(self):
		for i in self.players:
			i.write_json(command="kingdomCards", data=self.supply_json(self.kingdom))
			i.write_json(command="baseCards", data=self.supply_json(self.base_supply))
		Game.start_game(self)

	def supply_json(self, supply):
		supply_list = []
		for title, data in supply.items():
			card = data[0]
			count = data[1]
			formatCard = card.to_json()
			formatCard["count"] = count
			supply_list.append(formatCard)
		return json.dumps(supply_list)

	def remove_from_supply(self, card):
		if (card in self.kingdom):
			self.kingdom[card][1] -=1
		else:
			self.base_supply[card][1] -=1
		for i in self.players:
			i.write_json(command="updatePiles", card=card, count=self.supply[card][1])
		if (self.supply[card][1] == 0):
			self.empty_piles += 1

	def init_supply(self, cards):
		supply = {}
		for x in cards:
			if (x.type == "Victory"):
				if (len(self.players) ==2):
					supply[x.title] = [x,8]
				else:
					supply[x.title] = [x,12]
			elif (x.title == "Copper" or x.title=="Silver" or x.title=="Gold"):
				supply[x.title] = [x,30]
			else:
				supply[x.title] = [x,10]
		return supply

	def get_player_from_name(self, name):
		for i in self.players:
			if (i.name == name):
				return i

	def detect_end(self):
		if (self.supply["Province"][1] == 0 or self.empty_piles >=3):
			self.announce("GAME OVER")
			player_vp_list = (list(map(lambda x: (x, x.total_vp()), self.players)))
			winners = [max(player_vp_list, key=lambda x: x[1])]
			player_vp_list.remove(winners[0])
			win_vp = winners[0][1]
			for p in player_vp_list:
				if (p[1] == win_vp):
					winners.append(p)
			if (len(winners) == 1):
				self.announce(winners[0][0].name_string() + " has claimed victory!")
				return True
			else:
				last_player_went = self.players.index(self.get_turn_owner())
				filtered_winners = [p for p in winners if self.players.index(p[0]) > last_player_went]
				if (len(filtered_winners) == 0):
					self.announce(" ".join(x[0].name_string() for x in winners) + " rejoice in a shared victory.")
				elif (len(filtered_winners) == 1):
					self.announce(filtered_winners[0][0].name_string() + " has claimed victory!")
				else:
					self.announce(" ".join([x[0].name_string() for x in filtered_winners]) + " rejoice in a shared victory")
				return True
		else:
			return False
