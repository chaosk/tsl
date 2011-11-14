import PIL.Image
import logging
import os
from alpha_composite import alpha_composite
from color_manipulation import PNG

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

logging.basicConfig()
logger = logging.getLogger('tsl')
logger.setLevel(logging.DEBUG)

# Taken from spl0k's TeeViewer. Kudos!
"""
(
	'name', (sourceX, sourceY, width, height), (
		(resultX, resultY),
		...
	), (scaleX, scaleY)
),
"""
ITEM_POSITIONS = (
	(
		'body_outline', (96, 0, 96, 96), (
			(0, 0),
		), (1.0, 1.0)
	),
	(
		'foot_outline', (192, 64, 64, 32), (
			(-10, 45),
			(10, 45),
		), (1.0, 0.5)
	),
		(
		'foot', (192, 32, 64, 32), (
			(-10, 45),
		), (1.0, 0.5)
	),
 	(
		'body', (0, 0, 96, 96), (
			(0, 0),
		), (1.0, 1.0)
	),
	(
		'foot', (192, 32, 64, 32), (
			(10, 45),
		), (1.0, 0.5)
	),
	(
		'eye', (64, 96, 32, 32), (
			(35, 23),
			(46, 23),
		), (0.4, 0.4)
	)
)

class Skin(object):
	base_size = 96
	scaled_size = 96
	tile_size = 1
	margin = 1

	def __init__(self, skin_name, custom_colors=False):
		self._elements = {}
		self._elements_priority = []
		self.tee = None
		self.original_tee = None
		self.is_rendered = False
		self.skin_name = skin_name
		self.custom_colors = custom_colors
		self.loaded_colors = False
		self.load(skin_name)

	def load(self, skin_name):
		self.is_rendered = False
		if skin_name[-4:] == ".png":
			logger.info("Loading custom skin.")
			skin_path = skin_name
			
			if self.custom_colors:
				p = PNG(skin_path)
				p.gray()
				# actually, that's a StringIO object
				skin_path = p.to_stringio()
		else:
			logger.info("Loading standard skin.")
			skin_path = os.path.join(os.path.dirname(__file__), os.path.join(
				os.path.join("skins", "grayscale" if self.custom_colors else "default"),
				skin_name + ".png")
			)
		self.loaded_colors = self.custom_colors
		
		try:
			self.spritesheet = PIL.Image.open(skin_path)
		except IOError, e:
			raise e
		self._validate_skin()
		logger.info("Skin \"{0}\" loaded correctly.".format(skin_name))

	def reload(self):
		self.load(self.skin_name)

	def set_rgb(self, body_color, feet_color):
		# 0-255 RGB
		self.set_colors(
			[c/255.0 for c in body_color],
			[c/255.0 for c in feet_color]
		)

	def set_long_rgb(self, body_color, feet_color):
		# long RGB
		rgblong_to_rgb = lambda rgb: rgb / pow (256, 2), (rgb & 65535 ^ 255) / 256, rgb & 255
		self.set_colors(
			[rgblong_to_rgb(c) for c in body_color],
			[rgblong_to_rgb(c) for c in feet_color]
		)

	def set_colors(self, body_color, feet_color):
		if not self.loaded_colors:
			raise SkinException("You cannot set colors when custom_colors" \
				" is set to False. Set it it True and call reload() manually.")
		self.is_rendered = False
		self.custom_colors = {
			'body': body_color,
			'foot': feet_color,
		}

	def scale_tee(self, scale_to):
		if self.base_size != scale_to:
			self.original_tee = self.tee
			self.scaled_size = scale_to
			self.tee = self.original_tee.resize(
				(scale_to, scale_to), PIL.Image.BICUBIC
			)
			logger.info("Scaled tee to {0}x{0}.".format(scale_to))

	def render(self):
		if self.is_rendered:
			raise SkinColorOnDefaultException("Skin is already rendered." \
				" You can set colors again or call reload() to be able to" \
				" render it again.")
		self._get_elements()
		self._render_tee()
		self.is_rendered = True

	def save(self, path):
		self.tee.save(path)
		logger.info("Saved new tee to \"{0}\".".format(path))

	def _validate_skin(self):
		width, height = self.spritesheet.size
		if width != 256 or height != 128:
			raise NotTeeworldsSkin("Image is not a valid Teeworlds skin file.")

	def _get_element(self, name, posX, posY, width, height):
		box = (posX, posY, posX + self.tile_size*width,
			posY + self.tile_size*height)
		logger.debug("Got \"{0}\": ({1}, {2}), {3}x{4}.".format(
			name, posX, posY, width, height)
		)
		return self.spritesheet.crop(box)

	def _get_elements(self):
		for item in ITEM_POSITIONS:
			for coords in item[2]:
				n = 1
				name = item[0]
				while True:
					if not name in self._elements_priority:
						break
					name = "{0}-{1}".format(item[0], n)
					n += 1
				self._elements[name] = \
					(self._get_element(item[0], *item[1]), coords, item[3])
				self._elements_priority.append(name)
		logger.info("Retrieved all skin elements.")

	def _draw_element(self, name):
		element, coords, scale = self._elements[name]
		im = PIL.Image.new('RGBA', self.tee.size, (0,0,0,0))
		element = element.resize([int(self.base_size*scale[n]) for n in range(2)], PIL.Image.BILINEAR)
		im.paste(element, coords)
		name_ = name.split('-')[0]
		if self.custom_colors and name_ in self.custom_colors.keys():
				logger.debug("Colored \"{0}\" element.".format(name))
				im_splitted = im.split()
				for j in range(3):
					out = im_splitted[j].point(lambda i: i * self.custom_colors[name_][j])
					im_splitted[j].paste(out, None)
				im = PIL.Image.merge(im.mode, im_splitted)
		self.tee = alpha_composite(im, self.tee)

	def _render_tee(self):
		self.tee = PIL.Image.new("RGBA", (96, 96), (0,0,0,0))
		for item in self._elements_priority:
			self._draw_element(item)
			logger.debug("Rendered \"{0}\" element.".format(item))
		logger.info("Rendered all elements.")
		logger.info("Your tee is ready to be served.")


class SkinException(Exception):
	pass


class SkinColorOnDefaultException(SkinException):
	pass


class SkinAlreadyRenderedException(SkinException):
	pass


class NotTeeworldsSkin(Exception):
	pass
