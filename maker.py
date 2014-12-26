#!/usr/bin/python

from xml.dom.minidom import parse, parseString
from optparse import OptionParser
import collections
from PIL import Image, ImageDraw, ImageFont, ImageOps
import random
import os
import struct
import twitter
import urllib2 as urllib
import io
import secrets
from StringIO import StringIO

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="read card templates from", metavar="FILE")
parser.add_option("-o", "--output", dest="output",
                  help="output filename", metavar="FILE")
(options, args) = parser.parse_args()

proxyXml = parse(open(options.filename))

Block = collections.namedtuple('Block', 'location text type id wordwrap')
Location = collections.namedtuple('Location', 'x y rotate')
Text = collections.namedtuple('Text', 'color size')
WordWrap = collections.namedtuple('WordWrap', 'shrinktofit height width')

def makeLocation(nodes):
	rotate = nodes[0].attributes.get('rotate', None)
	if rotate:
		rotate = rotate.value

	return Location(
		x = int(nodes[0].attributes['x'].value),
		y = int(nodes[0].attributes['y'].value),
		rotate = rotate
	)

def makeText(nodes):
	rgbstr = nodes[0].attributes['color'].value[1:]
	color = struct.unpack('BBB', rgbstr.decode('hex'))

	return Text(
		color = color,
		size = int(nodes[0].attributes['size'].value)
	)

def makeWordWrap(nodes):
	if nodes:
		shrinktofit = nodes[0].attributes.get('shrinktofit', None)
		if shrinktofit:
			shrinktofit = shrinktofit.value

		return WordWrap(
			shrinktofit = shrinktofit,
			height = nodes[0].attributes['height'].value,
			width = nodes[0].attributes['width'].value
		)
	else:
		return None

def makeBlock(node):
	id = node.attributes['id'].value
	return Block(
    location = makeLocation(node.getElementsByTagName('location')),
    text = makeText(node.getElementsByTagName('text')),
    wordwrap = makeWordWrap(node.getElementsByTagName('wordwrap')),
    id = id,
    type = node.attributes['type'].value
   )

Template = collections.namedtuple('Template', 'src matches textblocks image')
ImageMask = collections.namedtuple('ImageMask', 'mask x y')
TextBlock = collections.namedtuple('TextBlock', 'block name')
Match = collections.namedtuple('Match', 'name value')

def makeMatch(node):
	return Match(
		name = node.attributes['name'].value,
		value = node.attributes['value'].value
	)

def makeMatches(nodes):
	return [makeMatch(n) for n in nodes]

def makeTextBlock(node):
	return TextBlock(
		block = node.attributes['block'].value,
		name = node.getElementsByTagName('property')[0].attributes['name'].value
	)

def makeTextBlocks(nodes):
	return [makeTextBlock(n) for n in nodes]

def makeImage(nodes):
	if not nodes:
		return None

	return ImageMask(
		x = int(nodes[0].attributes['x'].value),
		y = int(nodes[0].attributes['y'].value),
		mask = nodes[0].attributes['mask'].value
	)

def makeTemplate(node):
	return Template(
		src = node.attributes['src'].value,
		textblocks = makeTextBlocks(node.getElementsByTagName('link')),
		matches = makeMatches(node.getElementsByTagName('match')),
		image = makeImage(node.getElementsByTagName('image'))
	)

blocks = {}
for node in proxyXml.getElementsByTagName('block'):
	block = makeBlock(node)
	blocks[block.id] = block

templates = []
for node in proxyXml.getElementsByTagName('template'):
	template = makeTemplate(node)
	templates.append(template)

def templateMatches(template, matches):
	for m in matches:
		if m not in template.matches:
			return False
	return True

def getCardTemplates(matches):
	return [t for t in templates if templateMatches(t, matches)]

def getRandomCardTemplate(matches):
	print len(getCardTemplates(matches))
	return random.choice(getCardTemplates(matches))

def getFilePath(f):
	return os.path.join(os.path.dirname(options.filename).replace('/Proxy', ''), f)

#### FILL CARD
def fillCard(matches, fillDict, profileImage):
	#template = getRandomCardTemplate(matches)
	template = [t for t in getCardTemplates(matches) if 'Anarch' in t.src][0]

	imagepath = getFilePath(template.src)
	print imagepath
	image = Image.open(imagepath)
	if image.mode != "RGB":
	  image.convert("RGB")
	draw = ImageDraw.Draw(image)

	### fill image
	if template.image:
		fd = urllib.urlopen(profileImage)
		im = Image.open(StringIO(fd.read()))
		mask = Image.open(getFilePath(template.image.mask)).convert('L')
		output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
		output.putalpha(mask)
		output.save('round.png')
		image.paste(output, (template.image.x, template.image.y), output)

	### fill text
	for k, v in fillDict.items():
		textBlock = [b.block for b in template.textblocks if b.name == k]
		if not textBlock:
			print 'did not have entry for ' + k
			continue
		block = blocks[textBlock[0]]
		
		color = block.text.color
		size = block.text.size

		# TODO: ROTATE
		# TODO: shrink to fit
		# TOOD: wrap

		print block
		font = ImageFont.truetype("resources/HelveticaNeue-Bold.ttf", size)
		draw.text((block.location.x, block.location.y), v, color, font=font)
	return image

def fillIdentityFromTwitter():
	api = secrets.getTwitterApi()

	matches = [Match(name = u'Type', value = u'Identity')]
	fillDict = {
		'Name': 'blackmad',
		'Subtitle': 'David Blackman',
		'Cost': '12',
		'Rules': 'these are his rules',
		'Keywords': 'bio'
	}
	image = 'https://pbs.twimg.com/profile_images/501513865822089217/cd_x6dNy_400x400.png'
	image = fillCard(matches, fillDict, image)
	image.save(options.output)

fillIdentityFromTwitter()