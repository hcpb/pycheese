#!/usr/bin/python

#************************************************************************
#									*
#	Wrapper for generating composites from outut from cheese.	*
#									*
#	Assumes:							*
#		- 777 access to /var/www/html/photobooth and below	*
#		- cheese std output dir @ ~/Pictures/Webcam		*
#		- burst mode selected, and images end _{1,2,3,4}.jpg	*
#		- graphicsmagick is installed				*
#		- overlay is in script dir, named overlay-hcpb.png	*
#		- web server and samba share > photobooth directory	*
#		- can override default overlay image on commandline	*
#		- can turn on/off gutter text and doubleprint via cl	*
#									*
#************************************************************************

# import stuff...
import sys, os, commands 
from string import split, join
import time 

# save date string for placing on photo later...
datetime = time.strftime("%B %d, %Y")

# make executing a shell command easier, print command to console...
def shellcmd(command):
	print ' =>', command
	os.system(command)

# process commangline arguments, if any...
overlay=doubleprint=False
for i in sys.argv[1:]:
	if 'overlay=' in i: overlay = split(i, '=')[1]
	if ('doubleprint'==i) or ('dp'==i): 
		doubleprint=True
		print '\ndoubleprinting...\n'
	if 'nogutter'==i: gutter=False
	else: gutter=True


#============================================================================
#==================================  MAIN  ==================================
#============================================================================

# since we can't force cheese to do what we want, instruct the user...
# not terribly graceful but until cheese can be modified directcly...
raw_input('''

Select camera, put into burst mode with 4 photos per burst after it launches

hit enter when ready...
''')

# launch cheese... explicitly put display in so it can be done over ssh...
shellcmd('cheese -f -w --display=:0.0 &')
cheeserunning=True 

# pointer to overlay image...
if not overlay: overlay=os.path.abspath('.')+'/overlay-hcpb.png'
for i in sys.argv:
	if 'overlay=' in i:
		overlay=split(i, '=')[1]
		break
print '\noverlay =', overlay
print

# find user's home directory, since cheese puts photos in ~/Pictures/Webcam...
userdir = os.path.expanduser('~')+'/Pictures/Webcam'
os.chdir(userdir)

# clear out any old pic in webcam dir (move to single image share directory)...
shellcmd('mv '+userdir+'/* /var/www/html/photobooth/singles')

# set up some variables...
suffix = ['_1.jpg', '_2.jpg', '_3.jpg', '_4.jpg']
location = {}
fourup='_d2x2.jpg'
strip='_strip.jpg'
prnt='_print.jpg'
# locations to place images on larger composite...
location[fourup]=['+25+25', '+25+568', '+972+25', '+972+568']
location[strip]=['+20+648', '+20+1236', '+20+1824', '+20+2412']
processedlist=[]

# run only as long as the cheese app is running...
while(cheeserunning):
	# check to see if cheese is still running...
	a,b=commands.getstatusoutput('pgrep ^cheese')
	if b=='': cheeserunning=False

	# wait for at least a new sequence of four photos (as long as cheese is still running)
	while len(os.listdir(userdir))<4:
	   time.sleep(0.25)
	   a,b=commands.getstatusoutput('pgrep ^cheese')
           if b=='': sys.exit() 

	# get file list in user pic dir...
	files=os.listdir(userdir)
	cc = []
	# strip out any singles and any previously processed images...
	for i in files:
	  tt = split(i, '_')[0]
	  if ('.jpg' not in tt) and (tt not in cc) and (tt not in processedlist): 
	      cc.append(tt)
	cc.sort()

	# generate the composites...
	for i in cc:
	   starttime = time.time() # save the start time so we see how long it took...
	   # generate blank backgrounds...
	   shellcmd('gm convert -size 1920x1111 "xc:#fff" '+i+fourup)
	   shellcmd('gm convert -size 1000x3000 "xc:#fff" '+i+strip)
	   # iterate over image sequence...
	   for index in range(4):
	      # place image on each composite...
	      shellcmd('gm composite -geometry '+location[fourup][index]+ \
	            ' -resize 922x518  '+i+suffix[index]+ ' '+i+fourup+' '+i+fourup)
	      shellcmd('gm composite -geometry '+location[strip][index]+ \
	            ' -resize 960x540  '+i+suffix[index]+ ' '+i+strip+' '+i+strip)

	   # add text in gutters...
	   if gutter:
	     shellcmd('gm convert -font Courier -pointsize 25 -fill black -draw "text 61,561 file:'+ \
	       i+fourup+'" -draw "text 1190,561 HappyCamperPhotoBooth.com"  -draw "text 1700,561 '+ \
	       time.strftime("%b-%d-%Y")+'" '+i+fourup+' '+i+fourup)
	     shellcmd('gm convert -font Courier -pointsize 30 -fill black -draw "text 200,2398 file:'+ \
	        i+strip+'" -draw "text 240,1219 HappyCamperPhotoBooth.com"  -draw "text 400,1808 ' \
	        +time.strftime("%b-%d-%Y")+'" '+i+strip+' '+i+strip)

	   # add overlay to each composite...
	   shellcmd('gm composite -geometry +200+25 -resize 600x600 '+ \
	        overlay+' '+i+strip+' '+i+strip)
	   shellcmd('gm composite -geometry +810+405 -resize 300x300 '+ \
		overlay+' '+i+fourup+' '+i+fourup)

	   if doubleprint:
		shellcmd('gm convert -size 2000x3000 "xc:#fff" '+i+prnt)
		shellcmd('gm convert -size 2000x3000 xc:white -page +0+0 '+i+prnt+ \
			   ' -geometry 1000x3000 -page +0+0 '+i+strip+ \
		           ' -geometry 1000x3000 -page +1000+0 '+i+strip+ \
		           ' -flatten '+i+prnt)

	   # change permissions and move files to share/web directory...
	   shellcmd('chmod 644 *')
	   if doubleprint: shellcmd('mv '+i+'*'+prnt+' /var/www/html/photobooth/composites')
	   shellcmd('mv '+i+'*'+strip+' /var/www/html/photobooth/composites')
	   shellcmd('mv '+i+'*'+fourup+' /var/www/html/photobooth/composites')
	   shellcmd('mv '+i+'*.jpg /var/www/html/photobooth/singles')

	   print # print cycle time for sequence of four...
           print time.time()-starttime
	   print
	   print
	   # add most recently processsed to list...
	   processedlist.append(i)
