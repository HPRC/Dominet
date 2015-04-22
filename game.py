import client as c
import kingdomGenerator as kg
import card
import json
import net
import cardpile as cp
import random
import time
import os


class Game():
	def __init__(self, players, supply_set="default"):
		self.players = players
		self.first = 0
		self.turn = self.first
		self.turn_count = 0
		self.supply_set = supply_set
		self.START_TIME = time.time()
		self.flagged = False

	def chat(self, msg, speaker):
		for i in self.players:
			i.write_json(command="chat", msg=msg, speaker=speaker)

	def start_game(self):
		self.announce("Starting game with " + " and ".join(map(lambda x: str(x.name), self.players)))
		self.setup_log_file()

		for i in self.players:
			i.setup()
		self.announce("<b>---- " + self.players[self.turn].name_string() + " 's turn " + str(self.turn_count) + " ----</b>")
		self.players[self.turn].take_turn()

	def announce(self, msg):
		for i in self.players:
			i.write_json(command="announce", msg=msg)

	def change_turn(self):
		self.turn = (self.turn + 1) % len(self.players)
		if self.turn == self.first:
			self.turn_count += 1
		self.announce("<b>---- " + str(self.players[self.turn].name_string()) + " 's turn " + str(self.turn_count) + " ----</b>")
		self.players[self.turn].take_turn()

	def get_turn_owner(self):
		return self.players[self.turn]

	def setup_log_file(self):
		log_str = "Game created on " + str(self.START_TIME) + "\n Players: " + ", ".join(map(lambda x: str(x.name), self.players))
		file = open('logs/' + str(self.START_TIME) + '.txt', 'w')
		file.write(log_str)
		file.close()

	def get_log_file_path(self):
		flagged = "flagged_" if self.flagged else ""
		return 'logs/' + flagged + str(self.START_TIME) + '.txt'

	def log_json_data(self, data):
		path = self.get_log_file_path()
		if os.path.exists(path):
			file = open(path, 'a')
			file.write(data)
			file.close()

	def rename_log_file(self, new_name):
		# Purpose for this check is because when game ends file path is prefixed with 'finished_'
		# get_log_file_path is naive of this. probably should be adjusted
		if os.path.exists(self.get_log_file_path()):
			os.rename(self.get_log_file_path(), new_name)


class DmGame(Game):
	def __init__(self, players, required_cards, excluded_cards, supply_set="default"):
		Game.__init__(self, players, supply_set)
		# randomize turn order
		random.shuffle(self.players)
		self.trash_pile = []
		self.empty_piles = 0
		self.supply_set = supply_set
		if supply_set == "default":
			rand = random.randint(1, 10)
			if rand <= 3:
				self.supply_set = "prosperity"

		# kingdom = dictionary {card.title => [card, count]} i.e {"Copper": [card.Copper(self,None),10]}
		base_supply = [card.Curse(self, None), card.Estate(self, None),
		               card.Duchy(self, None), card.Province(self, None), card.Copper(self, None),
		               card.Silver(self, None), card.Gold(self, None)]

		if self.supply_set == "prosperity":
			base_supply.append(card.Colony(self, None))
			base_supply.append(card.Platinum(self, None))

		self.base_supply = self.init_supply(base_supply)

		generator = kg.kingdomGenerator(self, required_cards, excluded_cards)
		self.kingdom = self.init_supply(generator.gen_kingdom())

		self.supply = cp.CardPile()
		self.supply.combine(self.base_supply)
		self.supply.combine(self.kingdom)
		self.price_modifier = 0

	# override
	def start_game(self):
		self.load_supplies()
		Game.start_game(self)

	def load_supplies(self):
		for i in self.players:
			i.write_json(command="kingdomCards", data=json.dumps(self.kingdom.to_json()))
			i.write_json(command="baseCards", data=json.dumps(self.base_supply.to_json()))

	def remove_from_supply(self, card_title):
		if card_title in self.kingdom:
			self.kingdom.extract(card_title)
		else:
			self.base_supply.extract(card_title)
		for i in self.players:
			i.write_json(command="updatePiles", card=card_title, count=self.supply.get_count(card_title))
		if self.supply.get_count(card_title) == 0:
			self.empty_piles += 1

	def update_all_prices(self):
		for i in self.players:
			i.write_json(command="updateAllPrices", modifier=self.price_modifier)

	def init_supply(self, cards):
		supply = cp.CardPile()
		num_players = len(self.players)
		for x in cards:
			if "Victory" in x.type:
				if num_players == 2:
					supply.add(x, 8)
				else:
					supply.add(x, 12)
			elif x.type == "Curse":
				supply.add(x, (num_players - 1) * 10)
			elif x.title == "Copper" or x.title == "Silver" or x.title == "Gold":
				supply.add(x, 30)
			elif x.title == "Platinum":
				supply.add(x, 12)
			else:
				supply.add(x, 10)
		return supply

	def announce_to(self, listeners, msg):
		for i in listeners:
			i.write_json(command="announce", msg=msg)

	def get_player_from_name(self, name):
		for i in self.players:
			if i.name == name:
				return i

	def update_trash_pile(self):
		for i in self.players:
			i.write_json(command="updateTrash", trash=self.trash_string())

	def detect_end(self):
		if self.supply.get_count("Province") == 0 or self.empty_piles >= 3 or (self.supply_set == "prosperity" and self.supply.get_count("Colony") == 0):
			self.announce("GAME OVER")
			player_vp_list = (list(map(lambda x: (x, x.total_vp()), self.players)))
			win_vp = max(player_vp_list, key=lambda x: x[1])[1]
			winners = [p for p in player_vp_list if p[1] == win_vp]
			if len(winners) == 1:
				for i in player_vp_list:
					self.announce(self.construct_end_string(i[0], i[1], i in winners))
			else:
				last_player_went = self.players.index(self.get_turn_owner())
				filtered_winners = [p for p in winners if self.players.index(p[0]) > last_player_went]
				if len(filtered_winners) == 0:
					# everyone wins
					for i, vp in winners:
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

			if not self.flagged:
				os.remove(self.get_log_file_path())
			else:
				os.rename(self.get_log_file_path(), "logs/finished_" + str(self.START_TIME) + ".txt")

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
			if title == "VP tokens":
				if data > 0:
					ls.append(str(data) + " <span class='label label-success'>VP tokens</span>")
				continue
			if data[1] == 1:
				ls.append(str(data[1]) + " " + data[0].log_string(False))
			else:
				ls.append(str(data[1]) + " " + data[0].log_string(True))
		return " ".join(ls)

	def players_ready(self):
		for i in self.players:
			if not i.ready:
				return False
		return True

	def trash_string(self):
		trash_dict = {}
		for x in self.trash_pile:
			if x.title in trash_dict:
				trash_dict[x.title][1] += 1  
			else:
				trash_dict[x.title] = [x, 1]
		to_log = []
		for title, data in trash_dict.items():
			if len(to_log) != 0:
				to_log.append(",")
			to_log.append(str(data[1]))
			to_log.append(data[0].log_string() if data[1] == 1 else data[0].log_string(True))
		return " ".join(to_log)

	def card_from_title(self, title):
		return self.supply.get_card(title)

	def log_string_from_title(self, title, plural=False):
		return self.card_from_title(title).log_string(plural)


