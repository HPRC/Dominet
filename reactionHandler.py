from tornado import gen, concurrent

class ReactionHandler():
	def __init__(self, player):
		self.player = player
		self.game = self.player.game
		self.turn_owner = self.game.get_turn_owner()
		#we are using a list as a queue here since largest hand in dominion is <10 (most reactions < 10) hence performance not important
		self.reactions_queue = []
		

	@gen.coroutine
	def initiate_reactions(self, trigger, react_data=None):
		self.trigger = trigger
		#extra parameter to pass into react function of card
		self.react_data = react_data
		self.done_reacting_future = concurrent.Future()

		if len(self.player.hand.get_reactions_for(self.trigger)) > 1:
			#more than 1 reaction: lock player as he/she chooses order
			self.player.wait_modeless("", self.player, True)
		if self.player != self.turn_owner:
			self.turn_owner.wait("to react", self.player, True)
		yield self.need_order_reactions()
		yield self.trigger_reactions()
		yield self.done_reacting_future
		#finished all our reactions, unlock reaction wait on me
		self.player.update_wait(True)

	@gen.coroutine
	def need_order_reactions(self):
		reactions = self.player.hand.get_reactions_for(self.trigger)
		reaction_titles = list(map(lambda x: x.title, reactions))
		if len(set(reaction_titles)) == 1:
			self.reactions_queue += list(map(lambda x: x.react, reactions))
		else:
			num_reactions = len(reaction_titles)

			selected_order = yield self.player.select(num_reactions, num_reactions, reaction_titles, 
				"Choose the order for your reactions to resolve, #1 is first.", True)
			for card_title in selected_order:
				cb = self.player.hand.get_card(card_title).react
				self.reactions_queue.append(cb)

	#trigger next reaction
	@gen.coroutine
	def trigger_reactions(self):
		if self.reactions_queue:
			cb = self.reactions_queue.pop()
			if self.react_data is None:
				yield gen.maybe_future(cb(self.reacted))
			else:
				yield gen.maybe_future(cb(self.reacted, self.react_data))

	#called after a reaction resolves
	@gen.coroutine
	def reacted(self, drew_cards=False):
		#if we drew any new cards during a card's reaction reprompt all reactions since player may
		#want to reveal cards again, should only re-prompt with attack reactions
		if drew_cards and self.trigger == "Attack":
			new_reactions = self.player.hand.get_reactions_for(self.trigger)
			if len(new_reactions) > 0:
				self.initiate_reactions()
				self.turn_owner.wait("to react", self.player)
			else:
				if self.done_reacting_future.running():
					self.done_reacting_future.set_result("finished reactions")
		elif len(self.reactions_queue) == 0:
			if self.done_reacting_future.running():
				self.done_reacting_future.set_result("finished reactions")
		else:
			#cannot get here without having had a reaction first so the reactions are ordered
			yield self.trigger_reactions()


