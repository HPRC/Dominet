import sets.card as crd
import tornado.gen as gen


# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

class Crossroads(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Crossroads"
		self.description = "Reveal hand.\n{} per Victory card revealed.\n The first time you play this per turn:{}".format(crd.format_draw(1, True), crd.format_actions(3))
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		crossroads_played = [c for c in self.played_by.played_inclusive if c.title == "Crossroads"]
		# if this was the only one played just noow
		if len(crossroads_played) == 1:
			self.played_by.actions += 3
			self.game.announce("-- gaining 3 actions")
		# Announce announces everything to all players in log, reveal_string adds css to cards in log
		self.game.announce("-- reveals " + self.played_by.hand.reveal_string())
		num_victory_cards = len(self.played_by.hand.get_cards_by_type("Victory"))
		drawn = self.played_by.draw(num_victory_cards)
		# needs to be part of crossroads log
		self.game.announce("-- drawing " + drawn)
		crd.Card.on_finished(self, True)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", self.title, "</span>"])


class Duchess(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Duchess"
		self.description = "{}Every player looks at the top card of their deck and can choose to discard it."\
			"\nStatic: When you gain a Duchy, you may gain a Duchess.".format(crd.format_money(2))
		self.price = 2
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		acting_on = []	
		for i in self.game.players:
			top_card = i.topdeck()
			if top_card:
				self.played_by.wait_modeless("to choose", i)
				acting_on.append(i)
				# put the top card back on top of the player's deck
				i.deck.append(top_card)

		yield crd.parallel_selects(
			map(lambda x: x.select(1, 1, ["Discard", "Put Back"], "Discard " + x.deck[-1].title + " from the top of your deck?"), acting_on),
			acting_on, self.post_select)

	def post_select(self, selection, caller):
		card = caller.topdeck()
		if selection[0] == "Discard":
			caller.discard_pile.append(card)
			self.game.announce("-- " + caller.name_string() + " discards " + card.log_string())
		else:
			caller.deck.append(card)
			self.game.announce("-- " + caller.name_string() + " puts back a card")
		if not self.played_by.is_waiting():
			crd.Card.on_finished(self)

	def on_supply_init(self):
		supply_duchy = self.game.supply.get_card("Duchy")
		default_on_gain_function = supply_duchy.on_gain
		supply_duchy.on_gain = staticmethod(lambda x=supply_duchy : self.gain_duchy(x, default_on_gain_function))

	@gen.coroutine
	def gain_duchy(self, duchy, default_function):
			selection = yield duchy.played_by.select(1, 1, ["Yes", "No"], "Gain a Duchess?")
			if selection[0] == "Yes":
				yield duchy.played_by.gain("Duchess")
			yield default_function.__get__(duchy, crd.Card)()
			duchy.played_by.update_mode()

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", self.title, "</span>"])


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Develop(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = 'Develop'
		self.description = 'Trash a card from your hand and gain a card costing exactly 1 less than the trashed card and exactly 1 more than the trashed card in either order'
		self.price = 3
		self.type = 'Action'

	@gen.coroutine
	def play(self, skip = False):
		crd.Card.play(self, skip) 
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), 
			'select a card to develop')
		if selection:
			self.played_by.update_resources()
			self.played_by.discard(selection, self.game.trash_pile)
			card_trashed = self.game.card_from_title(selection[0])
			self.game.announce(self.played_by.name_string() + ' trashes ' + card_trashed.log_string())
			self.game.announce('-- gaining a card costing one more than ' + card_trashed.log_string())
			gain_plus_one = yield self.played_by.select_from_supply('Select a card costing exactly one more than ' + card_trashed.title, 
				card_trashed.get_price() + 1, 
				equal_only=True)
			if gain_plus_one:
				yield self.played_by.gain(gain_plus_one[0])
			
			self.game.announce('-- gaining a card costing one less than ' + card_trashed.log_string())
			gain_minus_one = yield self.played_by.select_from_supply('Select a card costing exactly one less than ' + card_trashed.title, 
				card_trashed.get_price() - 1, 
				equal_only=True)
			if gain_minus_one:
				yield self.played_by.gain(gain_minus_one[0])
			
			crd.Card.on_finished(self, False, False)			
		else:
			crd.Card.on_finished(self)

class Scheme(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = 'Scheme'
		self.description = '{}{} At the end of this turn, you may choose an Action card discarded from play'\
		' this turn and put it on your deck'.format(crd.format_actions(1), crd.format_draw(1))
		self.price = 3
		self.type = 'Action'

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining an action and drawing {}".format(drawn))
		crd.Card.on_finished(self, False, True)

	@gen.coroutine
	def cleanup(self):
		total_schemes_played = len([x for x in self.played_by.played_inclusive if x.title == self.title])
		plural = "s" if total_schemes_played > 1 else ""
		chosen_cards = yield self.played_by.select(None, total_schemes_played, 
			[x.title for x in self.played_by.played_cards if "Action" in x.type], 
			"Select up to {} action card{} to place on top of deck for Scheme".format(total_schemes_played, plural), True)

		for i in chosen_cards:
			for c in self.played_by.played_cards:
				if c.title == i:
					self.played_by.deck.append(c)
					break
		self.played_by.played_cards = [x for x in self.played_by.played_cards if x not in self.played_by.deck]

# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

class Nomad_Camp(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Nomad Camp"
		self.description = "{}{} When you gain this, put it on top of your deck".format(crd.format_buys(1), crd.format_money(2))
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining +$2 and a buy")
		crd.Card.on_finished(self, False)

	def on_gain(self):
		self.played_by.discard_pile.remove(self)
		self.played_by.deck.append(self)
		self.game.announce("-- adding " + self.log_string() + " to the top of their deck")


class Silk_Road(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Silk Road"
		self.description = "Worth {} for every 4 Victory cards in your deck (rounded down)".format(crd.format_vp(1, True))
		self.price = 4
		self.type = "Victory"

	def get_vp(self):
		cards = self.played_by.all_cards()
		victory_cards = [x for x in cards if "Victory" in x.type]
		return int(len(victory_cards) / 4)

class Spice_Merchant(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = 'Spice Merchant'
		self.description = 'You may trash a treasure from your hand. '\
			 "If you do\n {}, {} or\n {}, {}".format(crd.format_draw(2, True), crd.format_actions(1), crd.format_money(2, True), crd.format_buys(1, True))
		self.price = 4
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		treasure_cards = self.played_by.hand.get_cards_by_type("Treasure", True)
		treasure_titles = list(set(map(lambda x: x.title, treasure_cards)))
		if len(treasure_titles) == 0:
			self.game.announce("-- but there were no treasures in hand")
			crd.Card.on_finished(self, False, False)
		else:	
			card_selection = yield self.played_by.select(None, 1, treasure_titles, "Choose a treasure card to trash")
			if card_selection:
				self.played_by.discard(card_selection, self.game.trash_pile)
				self.game.announce("-- trashing " + self.game.log_string_from_title(card_selection[0]))
				perk_selection = yield self.played_by.select(1, 1, ["+2 cards +1 action", "+$2 +1 buy"], 
					"Choose one: +2 Cards +1 Action, or +$2 +1 Buy")
				if perk_selection[0] == "+2 cards +1 action":
					drawn = self.played_by.draw(2)
					self.played_by.actions += 1
					self.game.announce("-- drawing " + drawn + " and gaining +1 action")
					crd.Card.on_finished(self, True, True)
				elif perk_selection[0] == "+$2 +1 buy":	
					self.played_by.balance += 2
					self.played_by.buys += 1
					self.game.announce("-- gaining +$2 and +1 buy")
					crd.Card.on_finished(self, False, True)
			else:
				crd.Card.on_finished(self, False, False)		

class Trader(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Trader"
		self.description = "Trash a card from your hand, Gain X Silvers where X is the cost of the trash card. Whenever you gain a card, you may"\
			"reveal Trader to gain a Silver instead"
		self.price = 4
		self.type = "Action|Reaction"
		self.trigger = "Gain"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),  
			"Select card to trash")
		trashed = self.played_by.hand.get_card(selection[0])
		self.played_by.discard(selection, self.game.trash_pile)
		self.game.update_trash_pile()
		self.game.announce("-- trashing " + self.game.log_string_from_title(selection[0]))
		for i in range(0, trashed.get_price()):
			yield self.played_by.gain("Silver", custom_announce="")
		self.game.announce("-- gaining " + str(trashed.get_price()) + " " + self.game.log_string_from_title("Silver", trashed.get_price() > 1))
		crd.Card.on_finished(self, True)

	@gen.coroutine
	def react(self, to_gain):
		if to_gain.title == "Silver":
			return
		self.played_by.wait_modeless("", self.played_by, True)
		
		selection = yield self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to return " + to_gain.title + " to the supply and gain a Silver instead?")
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			to_gain = self.played_by.search_and_extract_card(to_gain)
			if to_gain:
				self.game.supply.add(to_gain)
				self.game.update_supply_pile(to_gain.title)
				self.game.announce("-- returning " + to_gain.log_string() + " to supply")
				yield self.played_by.gain("Silver")
			else:
				self.game.announce("-- but doesnt have anything to trade")

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])


# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Cache(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Cache"
		self.value = 3
		self.price = 5
		self.description = "{}When you gain this, gain two Coppers".format(crd.format_money(3))

	@gen.coroutine
	def on_gain(self):
		yield self.played_by.gain("Copper")
		yield self.played_by.gain("Copper")

class Embassy(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Embassy"
		self.price = 5
		self.type = "Action"
		self.description = "{} Discard 3 cards.\nWhen you gain this, opponents gain a silver".format(crd.format_draw(5))

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.draw(5)
		to_discard = yield self.played_by.select(3, 3, crd.card_list_to_titles(self.played_by.hand.card_array()), 
			"Discard 3 cards")
		self.played_by.discard(to_discard, self.played_by.discard_pile)
		crd.Card.on_finished(self, True, False)

	@gen.coroutine
	def on_gain(self):
		for i in self.played_by.get_opponents():
			yield i.gain("Silver", False)

class Highway(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Highway"
		self.description = "{}, {}\n While this is in play, cards cost {} less, but not less than {}" \
		                   "".format(crd.format_draw(1, True), crd.format_actions(1, True), crd.format_money(1, True), crd.format_money(0, True))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining an action, drawing " + drawn + " and reducing the cost of cards by $1")

		for i in self.game.supply.unique_cards():
			self.game.price_modifier[i.title] -= 1
		self.game.update_all_prices()
		crd.Card.on_finished(self, True)


class Ill_Gotten_Gains(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Ill Gotten Gains"
		self.description = "Worth {}When you play this, you may gain a copper, putting it in your hand." \
		                   " When you gain this, each other player gains a Curse".format(crd.format_money(1))
		self.value = 1
		self.price = 5
		self.type = "Treasure"
		self.spend_all = False

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

		choice = yield self.played_by.select(1, 1, ["Yes", "No"], "Gain a Copper to hand?")
		if choice[0] == "Yes":
			yield self.played_by.gain_to_hand("Copper")
		crd.Card.on_finished(self, True)

	@gen.coroutine
	def on_gain(self):
		for i in self.played_by.get_opponents():
			yield i.gain("Curse")

	def log_string(self, plural=False):
		return "".join(["<span class='label label-warning'>", self.title, "</span>"])


class Mandarin(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mandarin"
		self.description = "{} Put a card from your hand on top of your deck."\
		"When you gain this, put all treasures in play on top of your deck in any order.".format(crd.format_money(3))
		self.price = 5
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 3
		self.game.announce("-- gaining +$3")
		top_select = self.played_by.hand.auto_select(1, False)
		if top_select:
			self.post_select(top_select)
		else:
			selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),  
				"Select card to put back on top of your deck")
			self.post_select(selection)
			
	def post_select(self, selection):
		if selection:
			self.played_by.discard(selection, self.played_by.deck)
			self.played_by.announce_opponents("-- placing a card back on top of their deck")
			card_string = self.game.log_string_from_title(selection[0])
			self.played_by.announce_self("-- You place " + card_string + " back on top of your deck")
		crd.Card.on_finished(self, True)

	@gen.coroutine
	def on_gain(self):
		played_treasures = [x for x in self.played_by.played_cards if "Treasure" in x.type]
		# remove treasures from played pile
		self.played_by.played_cards = [x for x in self.played_by.played_cards if "Treasure" not in x.type]
		if len(played_treasures) == 1 or len(set(map(lambda x: x.title, played_treasures))) == 1:
			self.game.announce("-- placing treasures back on top of their deck")
			self.played_by.deck += played_treasures
		else:
			yield crd.reorder_top(self.played_by, played_treasures, lambda :self.done_gaining())

	def done_gaining(self):
		self.game.announce("-- placing treasures back on top of their deck")
		if self.game.get_turn_owner() == self.played_by:
			self.played_by.update_mode()

class Margrave(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Margrave"
		self.description = "{}{} Each other player draws a card, then discards down to 3 cards in hand.".format(
			crd.format_draw(3), crd.format_buys(1))
		self.price = 5
		self.type = "Action|Attack"

	@gen.coroutine
	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		drawn = self.played_by.draw(3)
		self.played_by.buys += 1
		self.game.announce("-- drawing {} and gaining a buy".format(drawn))
		self.played_by.update_resources()
		affected = [x for x in self.played_by.get_opponents() if not crd.AttackCard.is_blocked(self, x)]
		if affected:
			for i in affected:
				i.draw(1)
			yield crd.discard_down(affected, 3)
		crd.AttackCard.on_finished(self, True, False)

# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------


class Border_Village(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Border Village"
		self.description = "{}{}" \
		                   "When you gain this, gain a card costing less than this.".format(crd.format_draw(1), crd.format_actions(2))
		self.price = 6
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining two actions and drawing " + drawn)
		crd.Card.on_finished(self)

	@gen.coroutine
	def on_gain(self):
		border_village_cost = self.get_price()
		reduced_cost = border_village_cost - 1
		selection = yield self.played_by.select_from_supply("Gain a card costing up to ${}".format(reduced_cost), reduced_cost)
		yield self.played_by.gain(selection[0], True)


class Farmland(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Farmland"
		self.description = "{}" \
		                   "When you buy this, trash a card from your hand. Gain a card costing exactly " \
		                   "{} more than the trashed card.".format(crd.format_vp(2), crd.format_money(2))
		self.price = 6
		self.vp = 2

	@gen.coroutine
	def on_buy(self):
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                                        "select card to trash")
		if selection:
			self.played_by.discard(selection, self.game.trash_pile)
			card_trashed = self.game.card_from_title(selection[0])
			self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
			selected = yield self.played_by.select_from_supply("Choose the a card to gain", card_trashed.get_price() + 2, True)
			if selected:
				yield self.played_by.gain(selected[0])
				crd.Card.on_finished(self, False, False)