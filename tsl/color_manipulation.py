import png

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

class PNG(object):
	def __init__(self, filename):
		self.filename = filename
		image = png.Reader(filename).asRGBA()
		self.width = image[0]
		self.height = image[1]
		self.pixel_list = list(image[2])

	def save(self, filename="test.png"):
		w = png.Writer(self.width, self.height, \
			greyscale=False, alpha=True)
		f = open(filename, "wb")
		w.write(f, self.pixel_list)
		f.close()

	def to_stringio(self):
		w = png.Writer(self.width, self.height, \
			greyscale=False, alpha=True)
		f = StringIO()
		w.write(f, self.pixel_list)
		f.seek(0)
		return f

	def gray(self):
		_list = []
		for row in self.pixel_list:
			_list.extend(row)

		for i in range(self.width*self.height):
			v = int((_list[i*4]+_list[i*4+1]+_list[i*4+2])/3)
			_list[i*4] = v
			_list[i*4+1] = v
			_list[i*4+2] = v

		pitch = self.width*4
		org_weight = 0
		freq = 256*[0]
		new_weight = 192

		for y in range(96):
			for x in range(96):
				if _list[y*pitch+x*4+3] > 128:
					freq[_list[y*pitch+x*4]] += 1

		for i in range(256):
			if freq[org_weight] < freq[i]:
				org_weight = i

		inv_org_weight = 255-org_weight
		inv_new_weight = 255-new_weight
		for y in range(96):
			for x in range(96):
				v = _list[y*pitch+x*4]
				if v <= org_weight:
					v = int((v/float(org_weight)) * new_weight)
				else:
					v = int(((v-org_weight)/float(inv_org_weight))*inv_new_weight + new_weight)
				_list[y*pitch+x*4] = v
				_list[y*pitch+x*4+1] = v
				_list[y*pitch+x*4+2] = v

		for y in range(self.height):
			for x in range(self.width):
				self.pixel_list[y][x*4] = _list[y*pitch+x*4]
				self.pixel_list[y][x*4+1] = _list[y*pitch+x*4+1]
				self.pixel_list[y][x*4+2] = _list[y*pitch+x*4+2]
				self.pixel_list[y][x*4+3] = _list[y*pitch+x*4+3]

	def add_color(self, r, g, b):
		for row in self.pixel_list:
			for i in range(self.width):
				if row[i*4+3] == 0:
					continue
				row[i*4] = max(0, min(r-(255-row[i*4]), 255))
				row[i*4+1] = max(0, min(g-(255-row[i*4+1]), 255))
				row[i*4+2] = max(0, min(b-(255-row[i*4+2]), 255))

	def __repr__(self):
		return "<PNG: {0} x {1}>".format(self.width, self.height)
