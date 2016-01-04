class ReactionHandler():
	def __init__(self, player, trigger, resume=lambda : None, react_data=None):
		self.player = player
		self.game = self.player.game
		self.trigger = trigger
		self.turn_owner = self.game.get_turn_owner()
		# we are using a list as a queue here since largest hand in dominion is <10 (most reactions < 10) hence performance not important
		self.reactions_queue = []
		# callback to call after finish all reactions
		self.resume = resume
		# extra parameter to pass into react function of card
		self.react_data = react_data

	def initiate_reactions(self):
		if len(self.player.hand.get_reactions_for(self.trigger)) > 1:
			#more than 1 reaction: lock player with dummy callback to be overridden
			self.player.set_cb(lambda : None, True)
		if not self.need_order_reactions():
			self.trigger_reactions()

	def need_order_reactions(self):
		reactions = self.player.hand.get_reactions_for(self.trigger)
		reaction_titles = list(map(lambda x: x.title, reactions))
		if len(set(reaction_titles)) == 1:
			self.reactions_queue = list(map(lambda x: x.react, reactions))
			return False
		else:
			num_reactions = len(reaction_titles)

			self.player.set_cb(self.finish_ordering_reactions)
			self.player.select(num_reactions, num_reactions, reaction_titles, 
				"Choose the order for your reactions to resolve, #1 is first.", True)
			return True

	def finish_ordering_reactions(self, order):
		for card_title in order:
			cb = self.player.hand.get_card(card_title).react
			self.reactions_queue.append(cb)

		self.trigger_reactions()

	# trigger next reaction
	def trigger_reactions(self):
		if self.reactions_queue:
			cb = self.reactions_queue.pop()
			if self.react_data is None:
				cb(self.reacted)
			else:
				cb(self.reacted, self.react_data)

	# called after a reaction resolves
	def reacted(self, drew_cards=False):
		# if we drew any new cards during a card's reaction reprompt all reactions since player may
		# want to reveal cards again, should only re-prompt with attack reactions
		if drew_cards and self.trigger == "Attack":
			new_reactions = self.player.hand.get_reactions_for(self.trigger)
			if len(new_reactions) > 0:
				self.initiate_reactions()
				self.game.get_turn_owner().wait("to react", self.player)
			else:
				# finished all our reactions, unlock reaction wait on me
				self.player.update_wait(True)
				self.player.update_mode()
				self.resume()
		elif len(self.reactions_queue) == 0:
			# finished all our reactions, unlock reaction wait on me
			self.player.update_wait(True)
			self.player.update_mode()
			self.resume()
		else:
			# cannot get here without having had a reaction first so the reactions are ordered
			self.trigger_reactions()


