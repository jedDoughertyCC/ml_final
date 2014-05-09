'''
Interview assignment for Spotify
Devin Jones - Product Development Analyst

The function "buildPlaylist" takes a string as an input 
	and returns Spotify song urls / playlist
	whose songs names make up the input text
	
If the input string does not match a song name, 
	I first split the string based on punctuation
	then by parts of speech using pyStatParser
I tried to parse by capital letters first but it was significantly slower for a large corpus 
	(+30 seconds for the shakespear poem below)
	
I found the library Parser (pyStatParser) on github which references a few parts of speech treebanks. 
	it builds a parts of speech tree from the input text. the tree hierarchy can be leveraged to reduce
	the total number of recursive function calls to match the input string by traversing the tree from the top down
	rather than random splits in the input string. 
	https://github.com/emilmont/pyStatParser
	
I read that its possible to train a chunker based on examples using nltk.chunk .
	perhaps further work could be done to train a learning machine based on 
	the metadata API to classify potential song names/chunks from text input.
	this would replace the parser library and use nltk.chunk, 
	hopefully increasing the number of large phrase matches and decreasing the number of unmatched words & size of resulting playlist
	http://streamhacker.wordpress.com/2008/12/29/how-to-train-a-nltk-chunker/

Speed:
	Could maintain a hash table of common words that do not have song name matches	to increase speed
	Could look into the multiprocessing library instead of Queue
		but would have to tend to the order of the playlist
'''

import requests
import simplejson as json
import operator
from stat_parser import Parser, display_tree
import Queue
import re
import time

t0 = time.clock()
print 'great poem! let me find a playlist that suits it'

#enter poem here
#poem = 'Shall I compare thee to a summer\'s day? Thou art more lovely and more temperate: Rough winds do shake the darling buds of May, And summer\'s lease hath all too short a date: Sometime too hot the eye of heaven shines, And often is his gold complexion dimmed, And every fair from fair sometime declines, By chance, or nature\'s changing course untrimmed: But thy eternal summer shall not fade, Nor lose possession of that fair thou ow\'st, Nor shall death brag thou wander\'st in his shade, When in eternal lines to time thou grow\'st, So long as men can breathe, or eyes can see, So long lives this, and this gives life to thee.'
poem = 'if i can\'t get you out of my head'
input = poem


curatedplaylist = [] #This will be the final curated playlist
queueforinput =  Queue.Queue() #keeps track of API queries that are subsets of input string
didntmatch = [] #keeps track of api calls that didn't match
	
def nextQueue():
	if queueforinput.qsize() == 0:
		return curatedplaylist
	else:	
		checknext = queueforinput.get()
		buildPlaylist(checknext)

def cache(matchquery): #don't make the same api call twice
	if curatedplaylist: #if input is a duplicate & has already been matched to a song name, add dup to playlist
		for song in curatedplaylist:
			#print 'matchquery: ' + str((matchquery)).strip()
			#print 'song from playlist: ' + str(song[:][0].lower().replace(".","")).strip()
			if str((matchquery)).strip() == str(song[:][0].lower().replace(".","")).strip():
				#print str(song) + ' dup added'
				curatedplaylist.append(song)
				if queueforinput.qsize() == 0:
					return curatedplaylist
				else:	
					checknext = queueforinput.get()
					buildPlaylist(checknext)
	if didntmatch: #don't check words/phrases that we've already checked an found doesn't match							
		for song in didntmatch:
			if str((matchquery)).strip() == str(song.lower().replace(".","")).strip():
				#print 'phrase already found to not match a track: ' + str(matchquery)
				if queueforinput.qsize() == 0:
					return curatedplaylist
				else:	
					checknext = queueforinput.get()
					buildPlaylist(checknext)

def sendCall(matchquery): #sends api call and returns json as python dict
	formatquery = matchquery.replace(" ", "+")
	#build api query
	urlbase = 'https://ws.spotify.com/search/1/track.json?q=' 
	call = urlbase + formatquery
	
	call = requests.get(call) #send call
	returnjson = call.json() #turn api response into a python dict
	return returnjson

def buildTrackList(returnjson): #builds list of track names, their popularity index, and href codes based on api output
	tracklist = returnjson["tracks"] #return detail on all tracks from query as list
	tracknamelist = []
	for track in tracklist:
		trackname = [track.get('name'),float(track.get('popularity')),track.get('href')]
		tracknamelist.append(trackname)
	return tracknamelist

def appendSong(match): #appends most popular exact track name match & href code to playlist
	bestmatch = sorted(match, key = operator.itemgetter(1),reverse=True)[0]
	#build track url
	trackcode = str(bestmatch[2]).split(":")[2]
	trackurl = 'http://open.spotify.com/track/' + trackcode
	curatedplaylist.append([bestmatch[0],trackurl])	
	

def buildPlaylist(string):
	#print 'search query: ' + string
	#print 'queue size: ' + str(queueforinput.qsize())		#used for debugging

	originalinput = string #keeps information from capital letters
		
	matchquery = string.lower() #format input string for matching
	
	cache(matchquery) #don't make the same api call twice
	
	returnjson = sendCall(matchquery) #raw json from api
	tracknamelist = buildTrackList(returnjson) #pull out songs, popularity and href code
	
	#add query/search result matches to new list
	match = []
	for track in tracknamelist:
		if matchquery == track[:][0].lower().replace(".",""):
			match.append(track)
	
	
	'''	handles cases where there is no match.
		breaks input string first by punctuation, 
		then into chunks with pyStatParser, 
		and finally throws out one word no-matches
	'''
	hascaps = re.findall('[A-Z][^A-Z]*', originalinput) #for boolean logic
	haspunkt = (',' in matchquery) or ('.' in matchquery) or ('?' in matchquery) or (':' in matchquery) #for boolean logic
	
	if not match:
		didntmatch.append(matchquery) #don't send the same api call twice
		#print 'no exact matches for \'' + matchquery + '\''
		
		if (' ' in matchquery): #for search queries with more than one word:
			if haspunkt: #if input has punctuation 
				#splits corpus by punctuation, adds to queue
				matchquery = matchquery.replace('?',',').replace('.',',').replace(':',',') 
				phrases = matchquery.split(',')
				#print 'phrases: ' + str(phrases)
				for phrase in phrases:
					phrase = phrase.strip()
					#print 'phrase appended to queue: ' + str(phrase)
					queueforinput.put(phrase) #add to queue
				nextQueue()
			else: #for small inputs or inputs that have already been parsed by above
				parser = Parser() #pyStatParser
				
				try:
					phrase = matchquery.strip()
					sentencestructure =  parser.parse(phrase.replace(".","")) #append POS tags and makes a tree
					print sentencestructure.draw() #uncomment this to see tree map of input string
					treesize = len(sentencestructure)  #identifies 2nd level splits in tree of input string
					
					for i in range(0,treesize): #breaks the input string into main groupings, stores in a queue for api calls
					
						partofinput = " ".join(sentencestructure[i].leaves()) #rebuild string from treenode
						partofinput = partofinput.replace(' n\'t','n\'t').replace(' \'s','\'s').strip() #handle apostrophes
						#print partofinput 									#used for debugging
						#print 'partofinput appended to queue: ' + str(partofinput)
						queueforinput.put(partofinput) #add to queue			
				except: #was getting an error if pyStatParser couldn't determine POS based on english language syntax
					words = phrase.replace(".","").split() #this splits the phrase into words as a fail-safe
					for word in words:
						queueforinput.put(word)
				nextQueue()
		nextQueue()
	else: #appends most popular song from search results to the playlist	
		appendSong(match)
	
	nextQueue()	
	
buildPlaylist(input)

print 'For the poem: ' + poem
print 'We\'ve curated the playlist:'
for song,href in curatedplaylist:
	print song + ':',href
print time.clock() - t0, "seconds process time"
