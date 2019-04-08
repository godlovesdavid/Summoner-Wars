
from tkinter import Canvas, Toplevel, LEFT, Message, Button, Frame, Scrollbar, VERTICAL, RIGHT, Y, ALL, ARC, Spinbox, HIDDEN, DISABLED, Radiobutton, Label, IntVar
from time import time
from summonerwars.functions import *

defaultdeckclasses = {} #TODO: testing mode

# setup pictures.
gamelogo = PhotoImage(Image.open(r"pics\gamelogo.png"))
lifeicon = PhotoImage(Image.open(r"pics\lifeicon.gif"))
swordicon = PhotoImage(Image.open(r"pics\swordicon.gif"))
abilityicon = PhotoImage(Image.open(r"pics\abilityicon.gif"))
factionicon = PhotoImage(Image.open(r"pics\factionicon.gif"))
rangeicon = PhotoImage(Image.open(r"pics\rangeicon.gif"))
lifeiconwhite = PhotoImage(Image.open(r"pics\lifeiconwhite.gif"))
swordiconwhite = PhotoImage(Image.open(r"pics\swordiconwhite.gif"))
factioniconwhite = PhotoImage(Image.open(r"pics\factioniconwhite.gif"))
rangeiconwhite = PhotoImage(Image.open(r"pics\rangeiconwhite.gif"))
boardimg = PhotoImage(Image.open(r"pics\board.bmp"))
drawicon = PhotoImage(Image.open(r"pics\drawicon.png"))
magicicon = PhotoImage(Image.open(r"pics\magicicon.png"))
discardicon = PhotoImage(Image.open(r"pics\discardicon.png"))
handicon = PhotoImage(Image.open(r"pics\handicon.png"))
drawphasepic = PhotoImage(Image.open(r"pics\drawphase.png"))
summonphasepic = PhotoImage(Image.open(r"pics\summonphase.png"))
eventphasepic = PhotoImage(Image.open(r"pics\eventphase.png"))
movephasepic = PhotoImage(Image.open(r"pics\movephase.png"))
attackphasepic = PhotoImage(Image.open(r"pics\attackphase.png"))
magicphasepic = PhotoImage(Image.open(r"pics\magicphase.png"))
turnpic = PhotoImage(Image.open(r"pics\turn.png"))
preview2playerpic = PhotoImage(Image.open(r"pics\2playerpreview.bmp"))
preview3playerpic = PhotoImage(Image.open(r"pics\3playerpreview.bmp"))
preview4playerpic = PhotoImage(Image.open(r"pics\4playerpreview.bmp"))

selectablelist = []
phasecolor = ''
listpopup = None
tooltip = None

# fonts.
regfont = ("Moire Bold", 8)
lightfont = ("Moire Light", 18)
boldfont = ("Moire Bold", 12)
extraboldfont = ("Moire ExtraBold", 18)

# called to launch the game.
def launchmenus():
	setrepaintable(View())
	window.mainloop()

#for making decks menu.
class DeckPlan(object):
	def __init__(self):
		self.summonerclass = None
		self.commonclasses = {} #dict with class : amount
		self.champclasses = []

	def formdeck(self):
		summoner = self.summonerclass()
		commons = [commonclass(summoner) for commonclass in self.commonclasses for count in range(self.commonclasses[commonclass])]
		champions = [champclass(summoner) for champclass in self.champclasses for count in range(self.champclasses[champclass])]
		walls = [Wall(summoner, faction=summoner.faction) for count in range(3)]
		return Deck(summoner=summoner, commons=commons, champions=champions, walls=walls)


class DropMenu(object):
	def __init__(self, parentcanvas, coord, cards, command=None):
		width = 150
		height = 20

		self.canvas = parentcanvas
		self.coord = coord
		self.command = command
		self.cards = cards
		#cache pics.
		for card in cards:
			cardcaches[card] = {}
			cardcaches[card]['cardphoto'] = PhotoImage(Image.open(card.cardpicpath).resize((368, 240), Image.ANTIALIAS))

		#make dropdown menu box.
		self.choice = None
		self.stringvar = StringVar(window) #default string is first value entry
		label = Label(window, textvariable=self.stringvar, bg='white', font=regfont)
		hotspot = parentcanvas.create_rectangle((coord[0], coord[1], coord[0] + width, coord[1] + height), fill='white', outline='white')
		parentcanvas.create_polygon((coord[0] + width - 15, coord[1] + height - 15, coord[0] + width - 15 + 10, coord[1] + height - 15, coord[0] + width - 15 + 5, coord[1] + height - 15 + 10), fill='black') #triangle
		parentcanvas.create_window((coord[0] + 1, coord[1] + 1), window=label, anchor='nw')

		#bind popup.
		listpopup.bindpopup(coords=coord, lst=cards, selectables=cards, hotspot=hotspot, fill='white', activefill='white', autoopen=False, command=lambda : self.choose(listpopup.choice))

	def setchoices(self, cards):
		#cache pics.
		for card in cards:
			cardcaches[card] = {}
			cardcaches[card]['cardphoto'] = PhotoImage(Image.open(card.cardpicpath).resize((368, 240), Image.ANTIALIAS))

		clear(self.cards)
		extend(self.cards, cards)

	def choose(self, choice):
		self.choice = choice
		self.stringvar.set(name(self.choice))
		if self.command is not None:
			self.command()

#the graphical user interface that simply paints a representation of the game and a list of choices given at each game update for player to pick one.
class View(Canvas):
	def __init__(self):
		global listpopup, tooltip, viewstate
		super().__init__(window, width=1000, height=700, bd=-2, bg='#a79d95')

		self.pack(side=LEFT)

		# tooltip.
		tooltip = ToolTip(self)

		#list popup.
		listpopup = ListPopup(self)

		#message and cancel button.
		self.message = Message(window, font=boldfont, fg='#c1c1c1', bg='#040203', bd=-2, width=275, textvariable=messagevar)
		self.okbutton = Button(text='ok', font=boldfont, command=lambda : select(True))
		self.cancelbutton = Button(text='cancel', font=boldfont, command=self.cancel, default='active')
		self.cancelbutton.focus_force() #force focus so we can use spacebar to cancel

		self.loadbutton = Button(text='Restart turn', font=regfont, command=loadlastturn)

		# make start game menu.
		item = self.create_image((500, 350), image=gamelogo)
		self.tag_bind(item, '<ButtonPress-1>', lambda event : self.repaint(viewstate='menu'))

	# cancel button action.
	def cancel(self):
		selectvar.set(None)

		#hide list popup so we wont have the not showable bug.
		if listpopup.state is not 0:
			listpopup.hide()

	def presskey(self, event):
		#space key cancels.
		if event.char == ' ':
			self.cancel()

	#give offset color of an attribute. e.g. boosted life is greenish
	def givecolor(self, card, attname, column):
		offset = 0
		for mod in modifiers:
			if isinstance(mod, OffsetMod):
				if mod.thing is card and mod.attname == attname:
					offset += mod.offset

		if offset > 0:
			return 'green'
		elif offset < 0:
			return 'red'
		else:
			if column == 0:  # drawing on black bg needs white fg
				return 'white'
			else:
				return 'black'

	# draw stats, their icons, and ability buttons.
	def paintstats(self, card, col, row):
		if 'life' not in card.__dict__ or card.life <= 0:
			return

		# life.
		if col == 0:
			icon = lifeiconwhite
		else:
			icon = lifeicon
		self.create_image((188 + row * 100, 60 + col * 100), image=icon, anchor='w')
		self.create_text((200 + row * 100, 60 + col * 100), text=str(card.life) + "/" + str(card.maxlife), fill=self.givecolor(card, 'life', col), font=regfont, anchor='w')

		# # faction icon.
		# if col == 0:
		# 	icon = factioniconwhite
		# else:
		# 	icon = factionicon
		# self.create_image((188 + row * 100, 86 + col * 100), image=icon, anchor='w')
		# self.create_image((200 + row * 100, 86 + col * 100), image=card.owner.faction.logophoto, anchor='w')

		if isinstance(card, Unit):
			# attack.
			if col == 0:
				if card.range > 1:
					icon = rangeiconwhite
				else:
					icon = swordiconwhite
			else:
				if card.range > 1:
					icon = rangeicon
				else:
					icon = swordicon
			self.create_image((188 + row * 100, 72 + col * 100), image=icon, anchor='w')
			self.create_text((200 + row * 100, 72 + col * 100), text=card.atk, font=regfont, anchor='w', fill=self.givecolor(card, 'atk', col))
			#
			# # abilities.
			# count = 0
			# for ability in card.abilities:
			# 	# icon.
			# 	abilityitem = self.create_image((188 + row * 100, 105 + count * 17 + col * 100), image=abilityicon, anchor='w')
			# 	self.create_text((200 + row * 100, 105 + count * 17 + col * 100), text=name(ability), font=regfont, anchor='w')
			#
			# 	if ability in selectablelist:
			# 		if ability.canbuy:
			# 			text = '$'
			# 		elif ability.canuse:
			# 			text = '!'
			# 		button = Button(text=text, font=regfont, command=lambda a=ability: select(a))
			# 		self.create_window((200 + row * 100, 105 + count * 17 + col * 100), window=button, anchor='w')
			# 	count += 1


	# draw card pic on board.
	def paintcard(self, card, col, row):
		carditem = self.create_image((150 + row * 100, 115 + col * 100), image=cardcaches[card]['photo'])

		#bind tooltip.
		cost = ''
		if isinstance(card, Unit):
			cost = "\ncost: " + str(card.cost)

		type = ""
		if isinstance(card, Common):
			type += "\ntype: Common"
		elif isinstance(card, Champion):
			type += "\ntype: Champion"
		elif isinstance(card, Summoner):
			type += "\ntype: Summoner"
			cost = ''

		desc = name(card) + cost + type + "\nfaction: " + card.faction.__name__

		#make tooltip for ability.
		if 'abilities' in card.__dict__:
			desc += '\nAbilities: '
			for ability in card.abilities:
				if ability.cost > 0:
					cost = "cost " + str(ability.cost) + ', '
				else:
					cost = ''
				desc += name(ability).upper() + " " + cost + ability.desc + "\n"
		tooltip.bindtooltip(carditem, desc)

		return carditem


	# redraw window with selectable areas if needed.
	def repaint(self, selectables=(), viewstate='game', whoseturn=None, phase=None, subphase=None):
		global selectablelist, phasecolor
		selectablelist = selectables

		# clear screen first.
		self.delete(ALL)
		tooltip.hide(None)

		if viewstate == 'menu':
			#create decks.
			self.create_text((500, 150), font=extraboldfont, text='Choose 2 factions to play with.', fill='#555351')

			#make selections.
			x = 100
			y = 350
			for faction in defaultdeckclasses:
				faction.photo = PhotoImage(Image.open(faction.path + r'\symbol-lrg.png'))
				item = self.create_image((x, y), image=faction.photo)
				self.tag_bind(item, '<ButtonPress-1>', lambda event, f = faction : select(f))
				if x < 800:
					x += 150
				else:
					x = 100
					y += 140

			#wait for selection.
			decks = []
			for count in range(2):
				window.wait_variable(selectvar)
				add(defaultdeckclasses[selectvar.selection](), decks)

			startbattle(decks)

		# 	#num of players page.
		# 	global numplayers
		# 	numplayers = 2
		# 	label = Label(window, image=preview2playerpic)
		# 	intvar = IntVar()
		# 	def changeimage(num):
		# 		global numplayers
		# 		numplayers = num
		# 		if num is 2:
		# 			label.config(image=preview2playerpic)
		# 		elif num is 3:
		# 			label.config(image=preview3playerpic)
		# 		elif num is 4:
		# 			label.config(image=preview4playerpic)
		# 	self.create_text((250, 250), text='Number of Summoners', font=extraboldfont, fill='black')
		# 	y = 300
		# 	for count in range(2, 3):
		# 		radio = Radiobutton(window, text=count, value=count, variable=intvar, command=lambda c=count : changeimage(c), font=extraboldfont)
		# 		if count is 2:
		# 			firstradio = radio
		# 		self.create_window((250, y), window=radio)
		# 		y += 50
		# 	firstradio.select() #default first radio is selected TODO: doesn't work
		# 	self.create_window((700, 300), window=label)
		# 	self.create_window((800, 600), window=Button(window, text='next', command=lambda : self.repaint(viewstate='create decks')))
		#
		# elif viewstate == 'create decks':
		# 	#deck plan pages.
		# 	commons = []
		# 	def picksummoner(summoner):
		# 		global commons
		# 		if summoner is None:
		# 			plan.summonerclass = None
		# 			commons = []
		# 		else:
		# 			plan.summonerclass = summoner.__class__
		# 			commons = [commonclass(summoner) for commonclass in summoner.faction.commonclasses]
		#
		# 		for menu in commonmenus:
		# 			menu.choose(None)
		# 			menu.setchoices(commons)
		#
		# 	def pickcommon(common, amount):
		# 		if common is not None:
		# 			plan.commonclasses[common.__class__] = amount
		#
		# 	plan = DeckPlan()
		# 	summonermenu = DropMenu(self, (400, 100), cards=[summonerclass() for faction in factions for summonerclass in faction.summonerclasses], command=lambda: picksummoner(summonermenu.choice))
		#
		# 	#make common menus.
		# 	commonmenus = []
		# 	for row in range(6):
		# 		for col in range(3):
		# 			commonmenu = DropMenu(self, (col * 200 + 200, row * 50 + 200), cards=[])
		# 			commonmenu.spinner = Spinbox(window, from_=0, to=10, width=2, command=lambda: pickcommon(commonmenu.choice, amount=commonmenu.spinner.get())) #add amount adjuster
		# 			commonmenu.command = lambda: pickcommon(commonmenu.choice, amount=commonmenu.spinner.get())
		# 			self.create_window((col * 200 + 160, row * 50 + 200), window=commonmenu.spinner, anchor='nw')
		# 			add(commonmenu, commonmenus)

		else: #view state is game
			# draw board.
			self.create_rectangle((0, 0, 1000, 100), fill='#040203', outline='#040203')
			self.create_image((100, 100), image=boardimg, anchor='nw')

			# write phase.
			self.create_text((100, 45), anchor='sw', font=boldfont, text='Phase:', fill='#c1c1c1')

			# make the phase squares and subphase bars.
			photo = None
			phasetext = ""
			x = -100
			y = 48
			if phase is drawphase:
				phasecolor = '#b4cf7c'
				photo = drawphasepic
				phasetext = 'DRAW'
				x = 180
			elif phase is summonphase:
				phasecolor = '#826aaf'
				photo = summonphasepic
				phasetext = 'SUMMON'
				x = 223
			elif phase is eventphase:
				phasecolor = '#e4cd2b'
				photo = eventphasepic
				phasetext = 'EVENT'
				x = 266
			elif phase is movephase:
				phasecolor = '#00ae4d'
				photo = movephasepic
				phasetext = 'MOVE'
				x = 309
			elif phase is attackphase:
				phasecolor = '#da203d'
				photo = attackphasepic
				phasetext = 'ATTACK'
				x = 352
			elif phase is magicphase:
				phasecolor = '#56c0e8'
				photo = magicphasepic
				phasetext = 'MAGIC'
				x = 395

			if subphase is 2:
				x += 14
			elif subphase is 3:
				x += 28

			self.create_image((180, 45), anchor='sw', image=photo)  # squares
			self.create_rectangle((x, y, x + 12, y + 5), fill=phasecolor) # subphase bars
			self.create_text((100, 90), anchor='sw', text=phasetext, font=extraboldfont, fill=phasecolor)  #the big state banner

			#draw load button.
			self.create_window((1000, 0), window=self.loadbutton, anchor='ne')

			# write message.
			self.create_window((500, 35), window=self.message, anchor='w')

			x = 780
			#draw ok button if needed.
			for selectable in selectables:
				if selectable is True:
					self.create_window((x, 35), window=self.okbutton, anchor='w')
					x += 40
					break

			# draw cancel button.
			self.create_window((x, 35), window=self.cancelbutton, anchor='w')
			x += 100

			#draw buttons for numbers if they're selectable. TODO: memory leak because of creating button every frame
			for number in [choice for choice in selectables if isinstance(choice, int) and not isinstance(choice, bool)]:
				self.create_window((x, 35), window=Button(text=number, font=regfont, command=lambda n=number: select(n)), anchor='w')
				x += 20

			#draw buttons for strings.
			for string in [choice for choice in selectables if isinstance(choice, str)]:
				self.create_window((x, 35), window=Button(text=string, font=regfont, command=lambda s=string: select(s)), anchor='w')
				x += len(string) * 10

			# draw cards.
			for summoner in summoners:
				#write 'TURN' on whose turn's side of the board.
				if phase is drawphase and subphase is 1 and summoner is whoseturn:
					if summoner.playernum is 0 or summoner.playernum is 2:
						x = 300
					if summoner.playernum is 1 or summoner.playernum is 3:
						x = 700
					if summoner.playernum is 0 or summoner.playernum is 1:
						y = 400
					if summoner.playernum is 2 or summoner.playernum is 3:
						y = 1100
					self.create_image((x, y), image=turnpic)

				if summoner.playernum is 0 or summoner.playernum is 2:
					x = 50
				if summoner.playernum is 0 or summoner.playernum is 1:
					y = 160
				if summoner.playernum is 1 or summoner.playernum is 3:
					x = 950
				if summoner.playernum is 2 or summoner.playernum is 3:
					y = 760

				#draw draw icon and popup for drawpile.
				if len(selectables) > 0 and len(['selectable in drawpile' for selectable in selectables if selectable in summoner.drawpile]) > 0:
					#make transparent hotspot area.
					listpopup.bindpopup(hotspot=self.create_rectangle((x - 50, y - 60, x + 50, y + 60), fill='#a79d95', outline='#a79d95'), lst=summoner.drawpile, coords=(x, y), selectables=selectables, fill='#a79d95', activefill='white', command=lambda : select(listpopup.choice))
				tooltip.bindtooltip(self.create_image((x, y), image=drawicon), 'draw pile')
				self.create_text((x, y), text=len(summoner.drawpile), font=lightfont)

				#draw magic icon and popup for magicpile.
				y += 120
				if len(selectables) > 0 and len(['selectable in magicpile' for selectable in selectables if selectable in summoner.magicpile]) > 0:
					listpopup.bindpopup(hotspot=self.create_rectangle((x - 50, y - 60, x + 50, y + 60), fill='#a79d95', outline='#a79d95'), lst=summoner.magicpile, coords=(x, y), selectables=selectables, fill='#a79d95', activefill='white', command=lambda : select(listpopup.choice))
				tooltip.bindtooltip(self.create_image((x, y), image=magicicon), 'magic pile')
				self.create_text((x, y), text=len(summoner.magicpile), font=lightfont)

				#draw discard icon and popup for discardpile.
				y += 120
				listpopup.bindpopup(hotspot=self.create_rectangle((x - 50, y - 60, x + 50, y + 60), fill='#a79d95', outline='#a79d95'), lst=summoner.discardpile, coords=(x, y), selectables=selectables, fill='#a79d95', activefill='white', command=lambda : select(listpopup.choice))
				tooltip.bindtooltip(self.create_image((x, y), image=discardicon), 'discard pile')
				self.create_text((x, y), text=len(summoner.discardpile), font=lightfont)

				#draw hand icon and popup for hand (if it's his turn).
				y += 120
				if whoseturn is summoner:
					listpopup.bindpopup(hotspot=self.create_rectangle((x - 50, y - 60, x + 50, y + 60), fill='#a79d95', outline='#a79d95'), lst=summoner.hand, coords=(x, y), selectables=selectables, fill='#a79d95', activefill='white', command=lambda : select(listpopup.choice))
				tooltip.bindtooltip(self.create_image((x, y), image=handicon), 'hand')
				self.create_text((x, y), text=len(summoner.hand), font=lightfont)

				#draw guild icon.
				y += 120
				portraititem = self.create_image((x, y + 30), image=cardcaches[summoner]['photo'])
				tooltip.bindtooltip(portraititem, name(summoner))
				if whoseturn is summoner:
					self.create_text((x, y), text='TURN', font=lightfont)

			# draw things on board.
			for col in range(boardwidth):
				for row in range(boardheight):
					# draw ea. card in cell.
					for thing in board[col][row]:
						carditem = self.paintcard(thing, col, row)

						# make card selectable if it is.
						if thing in selectables:
							#draw the bounding box.
							self.create_line((100 + row * 100, 50 + col * 100, 110 + row * 100, 50 + col * 100), fill=phasecolor, width=3)
							self.create_line((100 + row * 100, 50 + col * 100, 100 + row * 100, 60 + col * 100), fill=phasecolor, width=3)
							self.create_line((190 + row * 100, 50 + col * 100, 200 + row * 100, 50 + col * 100), fill=phasecolor, width=3)
							self.create_line((200 + row * 100, 50 + col * 100, 200 + row * 100, 60 + col * 100), fill=phasecolor, width=3)
							self.create_line((100 + row * 100, 140 + col * 100, 100 + row * 100, 150 + col * 100), fill=phasecolor, width=3)
							self.create_line((100 + row * 100, 150 + col * 100, 110 + row * 100, 150 + col * 100), fill=phasecolor, width=3)
							self.create_line((190 + row * 100, 150 + col * 100, 200 + row * 100, 150 + col * 100), fill=phasecolor, width=3)
							self.create_line((200 + row * 100, 140 + col * 100, 200 + row * 100, 150 + col * 100), fill=phasecolor, width=3)

							self.tag_bind(carditem, '<ButtonRelease-1>', lambda event, selectable=thing: select(selectable), add='+')

					# for ea. cell, make clickable square if cell is in list of selectables.
					if board[col][row] in selectables:
						selectableitem = self.create_rectangle((100 + row * 100, 100 + col * 100, 200 + row * 100, 200 + col * 100), fill=phasecolor, outline=phasecolor)
						self.tag_bind(selectableitem, '<ButtonRelease-1>', lambda event, selectable=board[col][row]: select(selectable), add='+')

			#draw stats.
			for col in range(boardwidth):
				for row in range(boardheight):
					for card in board[col][row]:
						self.paintstats(card, col, row)


#remember a selectable item user has chosen.
def select(selectable=None):
	selectvar.set(selectable)
	if listpopup.state is not 0:
		listpopup.hide()


# tooltip is a top level window but without the title bar.
class ToolTip(Toplevel):
	def __init__(self, parentcanvas, delay=0, follow=True):
		# init.
		self.parentcanvas = parentcanvas
		super().__init__(parentcanvas.master, bg='black', padx=1, pady=1)
		self.withdraw()  # Hide initially
		self.overrideredirect(True)  # take out title bar buttons

		# make message (change msgVar to change the text).
		self.msgVar = StringVar()
		self.delay = delay
		self.follow = follow
		self.visible = 0
		self.lastMotion = 0
		Message(self, textvariable=self.msgVar, width=200).grid()

	def bindtooltip(self, canvasitem, msg):
		self.msgVar.set(msg)

		# add bindings.
		self.parentcanvas.tag_bind(canvasitem, '<Enter>', lambda event, m=msg: self.prime(event, m), add='+')  # + means add onto rather than replace
		self.parentcanvas.tag_bind(canvasitem, '<Leave>', self.hide, add='+')

	def prime(self, event, msg):
		self.msgVar.set(msg)
		self.visible = 1
		self.after(int(self.delay * 1000), lambda e=event: self.show(event))

	def show(self, event):
		if self.visible == 1 and time() - self.lastMotion > self.delay:
			self.visible = 2
		if self.visible == 2:
			self.geometry('+%i+%i' % (event.x_root + 10, event.y_root + 10))  # Offset the ToolTip 10x10 pixes southwest of the pointer
			self.deiconify()

	def move(self, event):
		self.lastMotion = time()
		if self.follow == False:  # If the follow flag is not set, motion within the widget will make the ToolTip dissapear
			self.withdraw()
			self.visible = 1
		self.after(int(self.delay * 1000), lambda e=event: self.show(event))

	def hide(self, event):
		self.visible = 0
		self.withdraw()


#popup showing card stack.
class ListPopup(Toplevel):
	def __init__(self, parentcanvas):
		# make this popup.
		self.parentcanvas = parentcanvas
		self.commands = {} #for setting clicked hotspot to a command
		self.choice = None
		super().__init__(parentcanvas.master)

		self.withdraw()
		self.overrideredirect(True)  # take out title bar buttons

		self.frame = Frame(self)
		self.frame.pack()
		self.canvas = Canvas(self.frame, bg='#FFFFFF', width=300, height=600)
		self.scroller = Scrollbar(self.frame, orient=VERTICAL, command=self.canvas.yview)
		self.scroller.pack(side=RIGHT, fill=Y)
		self.canvas.bind_all("<MouseWheel>", self.mousewheel) #bind mouse wheel to scroller
		self.canvas.pack()

		self.delay = 0  # set delay here
		self.state = 0
		self.lastmotion = 0

	def mousewheel(self, event):
		self.canvas.yview_scroll(int(-event.delta / 100), "units")

	def bindpopup(self, coords, lst, selectables, hotspot, fill, activefill, autoopen=True, command=None):
		if autoopen:
			event = '<Enter>'
		else:
			event = '<ButtonPress-1>'
		self.parentcanvas.tag_bind(hotspot, event, lambda event, c=coords, l=lst, s=selectables, h=hotspot, f=fill, a=activefill: self.spawn(event, c, l, s, h, f, a), add='+')
		self.parentcanvas.tag_bind(hotspot, '<ButtonPress-3>', self.hide, add='+') #right clicking hides popup in case we alt-tab and it can't hide anymore
		self.frame.bind('<Leave>', self.hide, add='+')

		self.commands[hotspot] = command
		self.choice = None

	def spawn(self, event, coords, lst, selectables, hotspot, fill, activefill):
		if self.state == 1 or self.state == 2:  # already being shown
			return

		self.hotspot = hotspot
		self.coords = coords
		self.lst = lst
		self.selectables = selectables
		self.fill = fill
		self.activefill = activefill

		# ready to show at a certain area.
		x = coords[0] - 100
		if x < 0:  # set lower x limit
			x = 100
		elif x + 368 > self.parentcanvas.winfo_width():  # set upper x limit
			x = self.parentcanvas.winfo_width() - 480
		self.geometry('+%d+%d' % (x + self.master.winfo_rootx(), 100 + self.master.winfo_rooty()))
		self.state = 1

		# make cards in this popup.
		y = 0
		for card in self.lst:
			carditem = self.canvas.create_image((0, y), image=cardcaches[card]['cardphoto'], anchor='nw')
			if self.selectables is not None and card in self.selectables:
				#make box around card if it is selectable.
				self.canvas.create_rectangle(0, y, 368, y + 10, fill=phasecolor, outline=phasecolor)
				self.canvas.create_rectangle(0, y + 10, 10, y + 230, fill=phasecolor, outline=phasecolor)
				self.canvas.create_rectangle(358, y + 10, 368, y + 230, fill=phasecolor, outline=phasecolor)
				self.canvas.create_rectangle(0, y + 230, 368, y + 240, fill=phasecolor, outline=phasecolor)
				self.canvas.tag_bind(carditem, '<ButtonPress-1>', lambda event, c=card: self.choose(c))
			y += 240

		# set popup dimensions.
		self.canvas.config(width=368, height=600, yscrollcommand=self.scroller.set, scrollregion=(0, 0, 300, y))
		self.scroller.update()

		# change hotspot item color.
		self.parentcanvas.itemconfig(self.hotspot, fill=self.activefill)

		#call show after delay.
		self.after(int(self.delay * 1000), self.show)

	# call this when user has chosen a selectable card from list.
	def choose(self, choice):
		self.state = 0
		self.withdraw()
		self.parentcanvas.itemconfig(self.hotspot, fill=self.fill, outline=self.fill)
		self.canvas.delete(ALL)

		#save choie.
		self.choice = choice

		#also do saved command.
		if self.commands[self.hotspot] is not None:
			self.commands[self.hotspot]()

	def show(self, event=None):
		if self.state == 1 and time() - self.lastmotion >= self.delay:
			self.state = 2
		if self.state == 2:
			self.deiconify()

	def hide(self, event=None):
		self.state = 0
		self.withdraw()
		self.parentcanvas.itemconfig(self.hotspot, fill=self.fill, outline=self.fill)
		self.canvas.delete(ALL)
