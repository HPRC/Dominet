import client as c
import kingdomGenerator as kg
import card
import json
import net


class Game():
	def __init__(self, players):
		self.players = players
		self.first = 0
		self.turn = self.first
		self.turn_count = 1

	def chat(self, msg, speaker):
		for i in self.players:
			i.write_json(command="chat", msg=msg, speaker=speaker)

	def start_game(self):
		self.announce("Starting game with " + str(self.players[0].name) + " and " + str(self.players[1].name))
		for i in self.players:
			i.setup()
		self.announce("<b>---- " + self.players[self.turn].name + " 's turn " + str(self.turn_count) + " ----</b>")
		self.players[self.turn].take_turn()

	def announce(self, msg):
		for i in self.players:
			i.write_json(command="announce",msg=msg)

	def change_turn(self):
		self.turn = (self.turn + 1) % len(self.players)
		if (self.turn == self.first):
			self.turn_count += 1
		self.announce("<b>---- " + str(self.players[self.turn].name) + " 's turn " + str(self.turn_count) + " ----</b>")
		self.players[self.turn].take_turn()

	def get_turn_owner(self):
		return self.players[self.turn]

class DmGame(Game):
	def __init__(self, players):
		Game.__init__(self, players)
		self.trash_pile = []
		self.empty_piles = 0
		#kingdom = dictionary {card.title => [card, count]} i.e {"Copper": [card.Copper(self,None),10]}
		self.base_supply = self.init_supply([card.Curse(self, None), card.Estate(self, None), 
			card.Duchy(self, None), card.Province(self, None), card.Copper(self,None),
			card.Silver(self, None), card.Gold(self, None)])

		generator = kg.kingdomGenerator(self)
		self.kingdom = self.init_supply(generator.random_kingdom())

		self.supply = self.base_supply.copy()
		self.supply.update(self.kingdom)


	#override
	def start_game(self):
		self.load_supplies()
		Game.start_game(self)

	def load_supplies(self):
		for i in self.players:
			i.write_json(command="kingdomCards", data=self.supply_json(self.kingdom))
			i.write_json(command="baseCards", data=self.supply_json(self.base_supply))

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

	def announce_to(self, listeners, msg):
		for i in listeners:
			i.write_json(command="announce", msg=msg)

	def get_player_from_name(self, name):
		for i in self.players:
			if (i.name == name):
				return i

	def update_trash_pile(self):
		for i in self.players:
			i.write_json(command="updateTrash", trash=self.trash_string())

	def detect_end(self):
		if (self.supply["Province"][1] == 0 or self.empty_piles >=3):
			self.announce("GAME OVER")
			player_vp_list = (list(map(lambda x: (x, x.total_vp()), self.players)))
			win_vp = max(player_vp_list, key=lambda x: x[1])[1]
			winners = [p for p in player_vp_list if p[1] == win_vp]
			if (len(winners) == 1):
				for i in player_vp_list:
					self.announce(self.construct_end_string(i[0], i[1], i in winners))
			else:
				last_player_went = self.players.index(self.get_turn_owner())
				filtered_winners = [p for p in winners if self.players.index(p[0]) > last_player_went]
				if (len(filtered_winners) == 0):
					#everyone wins
					for i,vp in winners:
						self.announce(self.construct_end_string(i, win_vp, True))
				else:
					for i in player_vp_list:
						self.announce(self.construct_end_string(i[0], i[1], i in filtered_winners))
			decklists = []
			for i in self.players:
				decklists.append(i.name_string())
				decklists.append("'s decklist:<br>")
				decklists.append(i.decklist_string())
				decklists.append("<br>")
			for i in self.players:
				i.write_json(command="updateMode", mode="gameover", decklists="".join(decklists))
			return True
		else:
			return False

	def construct_end_string(self, player, final_vp, is_winner):
		msg = "claimed victory" if is_winner else "been defeated"
		return (player.name_string() + " has " + msg + " with " + 
			str(final_vp) + " points: " + self.construct_VP_string(player))

	def construct_VP_string(self, player):
		ls = [] 
		for title, data in player.total_vp(True).items():
			if (data[1] == 1):
				ls.append(str(data[1]) + " " + data[0].log_string(False))
			else:
				ls.append(str(data[1]) + " " + data[0].log_string(True))
		return " ".join(ls)

	def players_ready(self):
		for i in self.players:
			if (not i.ready):
				return False
		return True

	def trash_string(self):
		trash_dict = {}
		for x in self.trash_pile:
			if x.title in trash_dict:
				trash_dict[x.title][1] += 1  
			else:
				trash_dict[x.title] = [x,1]
		to_log = []
		for title, data in trash_dict.items():
			if (len(to_log) != 0):
				to_log.append(",")
			to_log.append(str(data[1]))
			to_log.append(data[0].log_string() if data[1] == 1 else data[0].log_string(True))
		return " ".join(to_log)

