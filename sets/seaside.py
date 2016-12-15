import sets.card as crd
import tornado.gen as gen

# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

class Lighthouse(crd.Duration):
	def __init__(self, game, played_by):
		crd.Duration.__init__(self, game, played_by)
		self.title = "Lighthouse"
		self.description = "{} Now and at the start of your next turn {}" \
		"While this is in play, you are unaffected by attack cards".format(crd.format_actions(1), crd.format_money(1))
		self.price = 2

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.balance += 1
		self.played_by.actions += 1
		self.played_by.protection = 9999
		self.game.announce("-- gaining +$1 and +1 action")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		self.played_by.balance += 1
		self.game.announce("-- gaining +$1")
		self.played_by.protection = 0


class Pearl_Diver(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Pearl Diver"
		self.description = "{} {}" \
											 "Look at the bottom card of your deck. You may put it on top.".format(crd.format_draw(1), crd.format_actions(1))
		self.price = 2
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing " + drawn + " and gaining +1 actions")

		if len(self.played_by.deck) == 0:
			self.played_by.shuffle_discard_to_deck()

		if len(self.played_by.deck):
			bottom_card = self.played_by.deck[0].title
			selection = yield self.played_by.select(1, 1, ["Yes", "No"],
			            "The bottom card of your deck is " + bottom_card.title() + ". Move it to the top of your deck?")

			if selection[0] == "Yes":
				bottom_card = self.played_by.deck.pop(0)
				self.played_by.deck.append(bottom_card)
				self.game.announce("-- moving the bottom card to the top")
		else:
			self.game.announce("-- but has no cards in deck")

		crd.Card.on_finished(self)

# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Fishing_Village(crd.Duration):
	def __init__(self, game, played_by):
		crd.Duration.__init__(self, game, played_by)
		self.title = "Fishing Village"
		self.description = "Now and at the start of your next turn, {}{}".format(crd.format_actions(2), crd.format_money(1),
		                                                                       crd.format_actions(1), crd.format_money(1))
		self.price = 3

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.balance += 1
		self.played_by.actions += 2
		self.game.announce("-- gaining +$1 and +2 actions")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		self.played_by.balance += 1
		self.played_by.actions += 1
		self.game.announce('-- gaining +$1 and +1 action')


class Warehouse(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Warehouse"
		self.description = "{} {} Discard 3 cards".format(crd.format_draw(3), crd.format_actions(1))
		self.price = 3
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(3)
		self.played_by.actions += 1
		self.game.announce("-- gaining 1 action and drawing " + drawn)

		to_discard = yield self.played_by.select(3, 3, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                                         "Discard 3 cards")
		yield self.played_by.discard(to_discard, self.played_by.discard_pile)
		self.game.announce("-- discarding {} cards".format(len(to_discard)))
		crd.Card.on_finished(self)

# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------


class Caravan(crd.Duration):
	def __init__(self, game, played_by):
		crd.Duration.__init__(self, game, played_by)
		self.title = "Caravan"
		self.price = 4
		self.description = "{} " \
		"Now and at the start of your next turn, {}".format(crd.format_actions(1), crd.format_draw(1))

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining +1 action and drawing {}".format(drawn))
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing {}".format(drawn))


class Salvager(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Salvager"
		self.price = 4
		self.description = "{} " \
		"Trash a card from your hand, {} equal to its cost.".format(crd.format_buys(1), crd.format_money('X'))
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.buys += 1
		self.game.announce("-- gaining +1 Buy")

		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                                        "Select a card to salvage")
		selected_card = self.game.card_from_title(selection[0])
		selected_card_cost = selected_card.get_price()

		yield self.played_by.discard(selection, self.game.trash_pile)
		self.played_by.balance += selected_card_cost

		self.game.announce('-- trashing {}, gaining +${}'.format(selected_card.log_string(), selected_card_cost))
		crd.Card.on_finished(self)


class Sea_Hag(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Sea Hag"
		self.description = "Each other player discards the top card of their deck, " \
		                   "then gains a Curse putting it on top of their deck"
		self.price = 4
		self.type = "Action|Attack"

	@gen.coroutine
	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		yield self.fire(self.played_by.get_left_opponent())

	@gen.coroutine
	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			topdeck = player.topdeck()
			if topdeck:
				yield player.discard_floating([topdeck])
				self.game.announce('-- ' + player.name_string() + ' discards ' + self.game.log_string_from_title(topdeck.title))
			else:
				self.game.announce('-- {} discards nothing'.format(player.name_string()))
			yield player.gain_to_deck('Curse')
			yield crd.AttackCard.get_next(self, player)

class Treasure_Map(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Treasure Map"
		self.price = 4

		self.description = "Trash this and another copy of Treasure Map from your hand." \
		                   " If you do trash two Treasure Maps, gain 4 Gold cards, putting them on top of your deck."
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		if self.played_by.hand.get_count('Treasure Map') > 0:
			selection = yield self.played_by.select(1, 1, ["Yes", "No"], "Would you like to trash "
			            "this and another copy of treasure map from hand to gain 4 Gold to the top of your deck?")
			if selection[0] == 'Yes':
				self.game.trash_pile.append(self.played_by.played_cards.pop())

				self.played_by.discard(['Treasure Map'], self.game.trash_pile)
				yield self.played_by.discard(['Treasure Map'], self.game.trash_pile)

				self.game.update_trash_pile()
				for i in range(0, 4):
					yield self.played_by.gain_to_deck("Gold", True, "")
				self.game.announce("-- gaining 4 {} to the top of their deck".format(self.game.log_string_from_title("Gold", True)))

		else:
			self.game.announce('-- but there were no other copies of treasure map in hand')

		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Bazaar(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Bazaar"
		self.price = 5
		self.description = "{} {} {}".format(crd.format_draw(1), crd.format_actions(2), crd.format_money(1))
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 1
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing {}, gaining +2 actions and gaining +$1".format(drawn))
		crd.Card.on_finished(self)


class Explorer(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Explorer"
		self.description = "You may reveal a Province card from your hand. If you do, gain a Gold card, putting it into your hand." \
		                   " Otherwise, gain a Silver card, putting it into your hand"
		self.price = 5
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		selected = False
		if self.played_by.hand.get_count('Province') > 0:
			selection = yield self.played_by.select(1, 1, ['Yes', 'No'], "Reveal Province?")
			if selection[0] == 'Yes':
				self.game.announce("-- revealing a {}".format(self.played_by.hand.get_card("Province").log_string()))
				self.played_by.gain_to_hand('Gold')
				selected = True

		if not selected:
			self.played_by.gain_to_hand('Silver')

		crd.Card.on_finished(self)


class Merchant_Ship(crd.Duration):
	def __init__(self, game, played_by):
		crd.Duration.__init__(self, game, played_by)
		self.title = "Merchant Ship"
		self.price = 5
		self.description = "Now and at the start of your next turn {}".format(crd.format_money(2))

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.balance += 2
		self.game.announce("-- gaining +$2")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		self.played_by.balance += 2
		self.game.announce("-- gaining +$2")


class Tactician(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Tactician"
		self.price = 5
		self.description = "Discard your hand. " \
		                   "If you discarded any cards this way, then at the start of your next turn, \n" \
		                   "{} {} {}".format(crd.format_draw(5), crd.format_buys(1), crd.format_actions(1))
		self.type = "Action|Duration"

	@gen.coroutine
	def play(self, skip=False):
		# checks to see if Tactician is the only card in hand, if so call duration super play(), otherwise call card super play()
		if len(self.played_by.hand) > 1:
			crd.Duration.play(self, skip)
			yield self.played_by.discard(crd.card_list_to_titles(self.played_by.hand.card_array()), self.played_by.discard_pile)
			self.game.announce("-- discarding their hand")
			self.duration = self.active_duration
		else:
			crd.Card.play(self, skip)
			self.game.announce("-- but there was nothing to discard")
			self.duration = lambda : None

		crd.Duration.on_finished(self)

	def active_duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(5)
		self.played_by.buys += 1
		self.played_by.actions += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 Buy, +1 Action")

class Treasury(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Treasury"
		self.description = "{} {} {}" \
		                   "When you discard this card from play, if you didn't buy a Victory card this turn, " \
		                   "you may put this on top of your deck".format(crd.format_draw(1), crd.format_money(1),
		                                                                 crd.format_actions(1))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.balance += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing " + drawn + " and gaining +$1, +1 action")
		crd.Card.on_finished(self)

	@gen.coroutine
	def cleanup(self):
		total_victories_bought = len([x for x in self.played_by.bought_cards if 'Victory' in x.type])
		if total_victories_bought == 0:
			total_treasuries_played = len([x for x in self.played_by.played_cards if x.title == self.title])
			if total_treasuries_played > 1:
				selection = yield self.played_by.select(1, 1, [x for x in range(0, total_treasuries_played + 1)],
				                                        'Select the amount of treasuries you would like to return to the top of your deck')
				amount_to_return = selection[0]
			else:
				selection = yield self.played_by.select(1, 1, ['Yes', 'No'],
				                                        'Would you like to return Treasury to the top of your deck?')
				if selection[0] == 'Yes':
					amount_to_return = 1
				else:
					amount_to_return = 0

			count = 0
			for i in range(len(self.played_by.played_cards) - 1, -1, -1):
				if self.played_by.played_cards[i].title == 'Treasury':
					self.played_by.deck.append(self.played_by.played_cards[i])
					self.played_by.played_cards.pop(i)
					count += 1

				if count == amount_to_return:
					break


class Wharf(crd.Duration):
	def __init__(self, game, played_by):
		crd.Duration.__init__(self, game, played_by)
		self.title = "Wharf"
		self.description = "Now and at the start of your next turn:\n" \
		                   "{} {}.".format(crd.format_draw(2), crd.format_buys(1))
		self.price = 5

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.buys += 1
		self.game.announce("-- gaining +1 Buy and drawing {}".format(drawn))
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(2)
		self.played_by.buys += 1
		self.game.announce(" -- gaining +1 Buy and drawing {}".format(drawn))

# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------
