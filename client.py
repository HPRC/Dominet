import json
import sets.card as crd
import cardpile as cp
import random
import sets.base as b
import sets.intrigue as intr
import html
import game as g
import waitHandler as w

class Client():
	hand_size = 5

	def __init__(self, name, c_id, handler):
		self.name = name
		self.id = c_id
		self.handler = handler
		self.game = None
		self.ready = False
		self.vp = 0

	# called before players take their turns
	def setup(self):
		pass

	def write_json(self, **kwargs):
		self.handler.write_json(**kwargs)
		if self.game is not None and kwargs["command"] != "announce":
			self.game.logger.log_json_data(str(self.name + ": " + json.dumps(kwargs)), True)

	def take_turn(self):
		self.write_json(command="startTurn")

	def exec_commands(self, data):
		cmd = data["command"]

		if self.game is None:
			if cmd == "chat":
				self.handler.chat(data["msg"], self.name)
			return
		# else do game commands
		if cmd == "chat":
			self.game.chat(data["msg"], self.name)

		self.game.logger.log_json_data(str(self.name + ": " + json.dumps(data)), False)


class DmClient(Client):

	def write_json(self, **kwargs):
		if kwargs["command"] == "updateMode":
			# ignore the last_mode if it was a wait for disconnecting
			if not ("msg" in kwargs and "disconnected" in kwargs["msg"]):
				# callback used to resume mode if reconnect
				self.last_mode = kwargs
		Client.write_json(self, **kwargs)

	def base_deck(self):
		deck = []
		for i in range(0, 7):
			deck.append(crd.Copper(game=self.game, played_by=self))
		for i in range(0, 3):
			deck.append(crd.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, num_cards, return_string=True):
		drawn = []
		if len(self.deck) < num_cards:
			self.shuffle_discard_to_deck()
		for i in range(0, num_cards):
			if len(self.deck) >= 1:
				card = self.deck.pop()
				drawn.append(card)
				self.hand.add(card)
		if not return_string:
			self.update_deck_size()
			return drawn
		if len(drawn) == 0:
			return "nothing"
		elif len(drawn) == 1:
			self.update_deck_size()
			return "a card"
		else:
			self.update_deck_size()
			return str(len(drawn)) + " cards"

	# get top card of deck
	def topdeck(self):
		if len(self.deck) == 0:
			self.shuffle_discard_to_deck()
			if len(self.deck) == 0:
				return None
		return self.deck.pop()

	def shuffle_discard_to_deck(self):
		self.game.announce("<i>" + self.name_string() + " reshuffles</i>")
		random.shuffle(self.discard_pile)
		self.deck = self.discard_pile + self.deck
		self.discard_pile = []
		self.update_deck_size()
		self.update_discard_size()

	def setup(self):
		self.last_mode = {"command":"updateMode", "mode": "action"}
		self.discard_pile = []
		# deck = [bottom, middle, top]
		self.vp = 0
		self.deck = self.base_deck()
		self.hand = cp.HandPile(self)
		self.played = []
		self.played_actions = 0
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		self.update_hand()
		self.waiter = w.WaitHandler(self)
		self.cb = None
		self.protection = 0
		#boolean to keep track of if we bought a card to disable spending treasure afterwards
		self.bought_cards = False
		#cards banned from buying
		self.banned = []

	def update_hand(self):
		self.write_json(command="updateHand", hand=[x.to_json() for x in self.hand.card_array()])

	# override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		self.write_json(command="updateMode", mode="action")
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)

	# override
	def exec_commands(self, data):
		Client.exec_commands(self, data)
		#if we reconnected and an old connection is sending input, ignore
		if self.game is None:
			return
		cmd = data["command"]
		print(self.name + " \033[94m" + json.dumps(data) + "\033[0m")
		if cmd == "ready":
			self.ready = True
			if self.game.players_ready():
				if self.game.turn_count == 0:
					self.game.turn_count = 1
					self.game.start_game()
				else:
					self.resume()
					self.reconnect()
			elif self.game.turn_count != 0:
				#not all players are ready wait for disconnected ones
				self.reconnect()
				self.update_wait()
				#update wait msgs
				for i in self.game.players:
					if i.ready:
						i.waiter.wait(self.waiter.msg)
		elif cmd == "play":
			if not data["card"] in self.hand:
				print("Error " + data["card"] + " not in " + ",".join(self.hand.card_array()))
			else:
				self.hand.play(data["card"])
		elif cmd == "discard":
			self.discard(data["cards"], self.discard_pile)
		elif cmd == "endTurn":
			self.end_turn()
		elif cmd == "buyCard":
			self.buy_card(data["card"])
		elif cmd == "post_selection": 
			self.exec_selected_choice(data["selection"])
		elif cmd == "selectSupply":
			self.exec_selected_choice(data["card"])
		elif cmd == "spendAllMoney":
			self.spend_all_money()
		elif cmd == "returnToLobby":
			self.handler.return_to_lobby()
			self.ready = False
			self.game = None
		elif cmd == "submitBugReport":
			self.game.rename_log_file(g.LOGS_DIR + "/flagged_" + str(self.game.file_title) + ".html")
			self.game.flagged = True


	def exec_selected_choice(self, choice):
		self.update_wait()
		# choice(the parameter) to waiting callback is always a list
		if self.cb is not None:
			temp = self.cb
			self.cb = None
			temp(choice)

	def reconnect(self):
		self.game.announce(self.name_string() + " has reconnected!")
		self.game.load_supplies()
		self.update_hand()
		self.update_resources()
		self.game.update_trash_pile()

	#resumes game after all players ready
	def resume(self):
		for i in self.game.players:
			i.write_json(**i.last_mode)
		
		turn_owner = self.game.get_turn_owner()
		turn_owner.write_json(command="startTurn", actions=turn_owner.actions, 
				buys=turn_owner.buys, balance=turn_owner.balance)

	def end_turn(self):
		# cleanup before game ends
		for x in self.played:
			x.cleanup() 
		self.discard_pile = self.discard_pile + self.played
		self.played = []


		if self.game.detect_end():
			return
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.played_actions = 0
		self.bought_cards = False
		self.banned = []
		self.draw(self.hand_size)
		self.game.reset_prices()
		self.update_hand()
		self.update_discard_size()
		self.update_deck_size()
		self.game.change_turn()

	#used to properly generate a copy of a card from supply to add to my deck
	def gen_new_card(self, card_title):
		supply_card = self.game.card_from_title(card_title)
		# we instantiate a new card by getting the class from the kingdom instance 
		# and instantiating it
		new_card = type(supply_card)(self.game, self)
		#patch the on buy and on gain functions in case they were overriden at supply initialization
		#used for example with trade route
		supply_card.played_by = self
		new_card.on_gain = supply_card.on_gain
		new_card.on_buy = supply_card.on_buy
		return new_card


	def buy_card(self, card_title):
		if self.buys > 0 and self.game.supply.get_count(card_title) > 0 and card_title not in self.banned:
			new_card = self.gen_new_card(card_title)
			self.game.announce("<b>" + self.name + "</b> buys " + new_card.log_string())
			new_card.on_buy()
			new_card.on_gain()
			self.discard_pile.append(new_card)
			self.game.remove_from_supply(card_title)
			self.resolve_on_buy_effects(new_card)
			self.buys -= 1
			self.balance -= new_card.get_price()
			self.hand.do_reactions("Gain", lambda : self.update_resources(), new_card)
			self.bought_cards = True

	def select(self, min_cards, max_cards, select_from, msg, ordered=False):
		if len(select_from) > 0:
			self.write_json(command="updateMode", mode="select", min_cards=min_cards, max_cards=max_cards,
				select_from=select_from, msg=msg, ordered=ordered)
			return True
		else:
			return False

	def set_cb(self, cb, selflock= False):
		if cb != None:
			self.waiter.append_wait(self)
			#only change lock if we are locking, update_wait must be called to unlock
			if selflock:
				self.waiter.set_lock(self, selflock)
		self.cb = cb

	def wait_many(self, msg, on, locked=False):
		for i in on:
			self.waiter.append_wait(i)
			#only change lock if we are locking, update_wait must be called to unlock
			if locked:
				self.waiter.set_lock(i ,True)
		self.waiter.wait(msg)


	def wait(self, msg, on, locked=False):
		self.waiter.append_wait(on)
		self.waiter.wait(msg)
		#only change lock if we are locking, update_wait must be called to unlock
		if locked:
			self.waiter.set_lock(on, True)

	def is_waiting(self):
		return self.waiter.is_waiting()

	def opponents_wait(self, msg, locked=False):
		for i in self.game.players:
			if i.name != self.name:
				#only change lock if we are locking, update_wait must be called to unlock
				if locked:
					i.waiter.set_lock(self, locked)
				i.waiter.append_wait(self)
				i.waiter.wait(msg)

	def update_wait(self, manually_called=False):
		for i in self.game.players:
			if manually_called:
				i.waiter.set_lock(self, False)
			i.waiter.notify(self)

	def discard(self, cards, pile):
		for x in cards:
			card = self.hand.extract(x)
			if card is not None:
				pile.append(card)
		if pile == self.discard_pile:
			self.update_discard_size()
		elif pile == self.game.trash_pile:
			self.game.update_trash_pile()

	def update_mode(self):
		played_money = [x for x in self.played if "Treasure" in x.type]
		# if we have no actions or no action cards and no money cards, buy mode
		if (len(self.hand.get_cards_by_type("Action")) == 0 or self.actions == 0) and len(self.hand.get_cards_by_type("Treasure")) == 0:
			self.update_mode_buy_phase()
		else:
			if not played_money and self.actions > 0 and len(self.hand.get_cards_by_type("Action")) != 0:
				self.write_json(command="updateMode", mode="action")
			else:
				self.update_mode_buy_phase()

	def update_mode_buy_phase(self):
		self.write_json(command="updateMode", mode="buy", bought_cards=self.bought_cards, banned=self.banned)
		if "Peddler" in self.game.supply and self.game.get_turn_owner() == self:
			self.game.card_from_title("Peddler").on_buy_phase()
			self.game.update_all_prices()

	def update_deck_size(self):
		self.write_json(command="updateDeckSize", size=len(self.deck))

	def update_discard_size(self):
		self.write_json(command="updateDiscardSize", size=len(self.discard_pile))

	def get_card_from_supply(self, card, from_supply=True):
		if self.game.supply.get_count(card) <= 0 and from_supply:
			return
		if from_supply:
			self.game.remove_from_supply(card)
		return self.gen_new_card(card)

	def gain(self, card, from_supply=True, suppress_announcement=False, done_gaining=lambda : None):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			if not suppress_announcement:
				self.game.announce(self.name_string() + " gains " + new_card.log_string())
			self.discard_pile.append(new_card)
			self.update_discard_size()
			new_card.on_gain()
			self.hand.do_reactions("Gain", done_gaining, new_card)
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")
			done_gaining()

	def gain_to_hand(self, card, from_supply=True, done_gaining=lambda : None):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			self.game.announce(self.name_string() + " gains " + new_card.log_string() + " to their hand.")
			#add to discard first for reactions so that they can access and manipulate the new card from discard
			self.discard_pile.append(new_card)
			def done_react():
				#if the gained card is still in discard pile, then we can remove and add to hand
				if self.discard_pile and new_card == self.discard_pile[-1]:
					self.hand.add(self.discard_pile.pop())
					self.update_hand()
				done_gaining()
			new_card.on_gain()
			self.hand.do_reactions("Gain", done_react, new_card)
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")
			done_gaining()

	def select_from_supply(self, price_limit=None, equal_only=False, type_constraint=None, allow_empty=False, optional=False):
		if allow_empty or self.game.supply.has_selectable(price_limit, equal_only, type_constraint):
			self.write_json(command="updateMode", mode="selectSupply", price=price_limit, equal_only=equal_only,
				type_constraint=type_constraint, allow_empty=allow_empty, optional=optional)
			return True
		else:
			self.game.announce("-- but there is nothing available")
			return False

	def update_resources(self, playedMoney=False):
		if playedMoney:
			self.update_mode_buy_phase()
		self.write_json(command="updateResources", actions=self.actions, buys=self.buys, balance=self.balance)

	def total_deck_size(self):
		return len(self.deck) + len(self.discard_pile) + len(self.played) + len(self.hand)

	#by default returns list in order starting with players after you
	def get_opponents(self):
		my_index = self.game.players.index(self)
		opponents = []
		for i in range(1, len(self.game.players)):
			opponents.append(self.game.players[(my_index + i) % len(self.game.players)])
		return opponents

	def get_left_opponent(self):
		counter = 0
		for x in self.game.players:
			if x == self:
				break
			counter += 1

		return self.game.players[(counter + 1) % len(self.game.players)]

	def announce_opponents(self, msg):
		self.game.announce_to(self.get_opponents(), msg)

	def spend_all_money(self):
		to_log = []
		to_discard = []
		treasure_cards = [x for x in self.hand.get_cards_by_type("Treasure", True) if x.get_spend_all()]
		if len(treasure_cards) != 0:
			unique_treasure_titles = set(map(lambda x: x.title, treasure_cards))
			for card_title in unique_treasure_titles:
				card = self.hand.get_card(card_title)
				count = self.hand.get_count(card_title)
				for i in range(0, count):
					card.play(True)
				if len(to_log) != 0:
					to_log.append(",")
				to_discard += self.hand.get_all(card_title)
				to_log.append(str(count))
				to_log.append(card.log_string() if count == 1 else card.log_string(True))
			self.discard(list(map(lambda x: x.title, to_discard)), self.played)
			if len(to_log) > 0:
				self.game.announce(self.name_string() + " played " + " ".join(to_log))
				self.update_resources(True)
			self.update_hand()
		else:
			self.update_mode_buy_phase()

	def total_vp(self, returnCards=False):
		total = 0

		# dictionary of vp {"Province" : [<card Province>, 2]}
		vp_dict = {}
		vp_dict["VP tokens"] = self.vp
		total += self.vp
		for card in self.all_cards():
			if "Victory" in card.type or "Curse" in card.type:
				total += card.get_vp()
				if card.title in vp_dict:
					vp_dict[card.title][1] += 1
				else:
					vp_dict[card.title] = [card, 1]
		return total if not returnCards else vp_dict

	def decklist_string(self):
		decklist = cp.CardPile()
		for card in self.all_cards():
			decklist.add(card)
		decklist_str = []
		for card_title in decklist.data.keys():
			decklist_str.append(str(decklist.get_count(card_title)))
			decklist_str.append("-")
			if decklist.get_count(card_title) == 1:
				decklist_str.append(decklist.get_card(card_title).log_string())
			else:
				decklist_str.append(decklist.get_card(card_title).log_string(True))
			decklist_str.append(" ")
		return "".join(decklist_str) + "<br>" + str(len(self.all_cards())) + " cards"

	def name_string(self):
		return "<b>" + html.escape(self.name) + "</b>"

	def get_card_count_in_list(self, card_title, card_list):
		count = 0
		for x in card_list:
			if x.title == card_title:
				count += 1
		return count

	def all_cards(self):
		return self.deck + self.discard_pile + self.played + self.hand.card_array()

	def resolve_on_buy_effects(self, purchased_card):
		for card in self.played:
			card.on_buy_effect(purchased_card)

