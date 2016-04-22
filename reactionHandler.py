from tornado import gen, concurrent

class ReactionHandler():
	def __init__(self, player):
		self.player = player
		self.game = self.player.game
		#we are using a list as a queue here since hands in dominion are usually 5 hence performance not important
		self.reaction_events = []
		
	@gen.coroutine
	def initiate_reaction_event(self, trigger, react_data=None):
		self.turn_owner = self.game.get_turn_owner()

		if len(self.player.hand.get_reactions_for(trigger)) > 1:
			#more than 1 reaction: lock player as he/she chooses order
			self.player.wait_modeless("", self.player, True)
		if self.player != self.turn_owner:
			self.turn_owner.wait("to react", self.player, True)
		
		self.reaction_events.append(ReactionEvent(trigger, self.player,react_data))
		while self.reaction_events:
			reacting = self.reaction_events.pop(0)
			yield reacting.start_reactions()
		#finished all our reactions, unlock reaction wait on me
		self.player.update_wait(True)


class ReactionEvent():
	def __init__(self, trigger, player, react_data=None):
		self.trigger = trigger
		#extra parameter to pass into react function of card
		self.react_data = react_data
		self.player = player

	@gen.coroutine
	def start_reactions(self):
		self.cbs = yield self.need_order_reactions(self.trigger)
		yield self.trigger_reactions()

	@gen.coroutine
	def need_order_reactions(self, trigger):
		reactions = self.player.hand.get_reactions_for(trigger)
		reaction_titles = list(map(lambda x: x.title, reactions))
		react_functions = []
		if len(set(reaction_titles)) == 1:
			react_functions = list(map(lambda x: x.react, reactions))
		else:
			num_reactions = len(reaction_titles)

			selected_order = yield self.player.select(num_reactions, num_reactions, reaction_titles, 
				"Choose the order for your reactions to resolve, #1 is first.", True)
			for card_title in selected_order:
				cb = self.player.hand.get_card(card_title).react
				react_functions.append(cb)
		return react_functions

	#trigger next reaction
	@gen.coroutine
	def trigger_reactions(self):
		if self.cbs:
			cb = self.cbs.pop()
			if self.react_data is None:
				drew_cards = yield gen.maybe_future(cb())
				yield self.reacted(drew_cards)
			else:
				drew_cards = yield gen.maybe_future(cb(self.react_data))
				yield self.reacted(drew_cards)

	#called after a reaction resolves
	@gen.coroutine
	def reacted(self, drew_cards=False):
		if self.trigger == "Gain":
			if self.react_data not in self.player.all_cards():
				# card is gone from gaining, clear remaining reactions for that
				self.cbs = []
		#if we drew any new cards during a card's reaction reprompt all reactions since player may
		#want to reveal cards again, should only re-prompt with attack reactions
		if drew_cards and self.trigger == "Attack":
			yield self.start_reactions()
		elif len(self.cbs) == 0:
			return
		else:
			#cannot get here without having had a reaction first so the reactions are ordered
			yield self.trigger_reactions()
