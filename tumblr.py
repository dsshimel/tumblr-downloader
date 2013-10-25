import sys

class Tumblr:
	from bs4 import BeautifulSoup
	import requests, re, sys, os, operator
	

	_images_downloaded = set()
	_posts_visited = set()
	_post_pattern = re.compile('/post/(\d+)')
	_dirname_pattern = re.compile('http://(.+?)/')
	_tumblr_name_pattern = re.compile('http://(www.)?(.+?).tumblr.com/')
	_source_post_pattern = re.compile('(http://(www.)?(.+?).tumblr.com/)post/(\d+)')
	_filename_info_pattern = re.compile('(tumblr_\w+_)(\d\d\d)\.(\w+)')
	_img_url_pattern = re.compile('(http://(\d\d)\.media\.tumblr\.com/(\w+)/)(tumblr_\w+_\d\d\d\.\w+)')
	_simple_img_url_pattern = re.compile('(http://(\d?\d?)\.?media\.tumblr\.com/)(tumblr_\w+_?\d?\d?\d?\.\w+)')
	_gif_img_type = set(['gif'])
	_static_img_types = set(['png', 'jpg', 'jpeg', 'bmp'])
	_supported_img_types = _gif_img_type.union(_static_img_types)
	_img_sizes = [250, 400, 500]
		
	_tumblr_url = ''
	_tumblr_name = ''
	_dirname = None
	_process_post_links = True
	_get_gifs = True
	_get_static = True
	
	@staticmethod
	def fix_tumblr_url(base_url):
		return base_url # will do actual fixing later if needed
	
	@staticmethod
	def get_tumblr_name(url):
		return Tumblr._tumblr_name_pattern.search(url).group(2)
	
	@staticmethod
	def get_page(url):
		status_code = 200
		content = ''
		try:
			response = Tumblr.requests.get(url)
			status_code = response.status_code
			content = response.content
		except Tumblr.requests.exceptions.MissingSchema as ms:
			print "couldn't get URL: " + url
			raise
		except:
			print "couldn't get " + url
			print Tumblr.sys.exc_info()[0]
		return status_code, content
	
	def change_tumblr_url(new_url):
		_tumblr_url = new_url
		_images_downloaded.clear()
		_posts_visited.clear()
	
	def __init__(self, tumblr_url, get_gifs=True, get_static=True):
		self._tumblr_url = Tumblr.fix_tumblr_url(tumblr_url)
		self._tumblr_name = Tumblr.get_tumblr_name(self._tumblr_url)
		self._get_gifs = get_gifs
		self._get_static = get_static
	
	# static-ish for now, but probably may want more configuration in the future
	def save_image_from_url(self, image_url, filepath):
		succeeded = False
		directory_and_filepath = self.get_directory_name() + '/' + filepath
		status_code, content = Tumblr.get_page(image_url)
		try:
			if 200 == status_code:
				with open(directory_and_filepath, 'wb') as f:
					# maybe decouple this by passing in file handle
					f.write(content)
					print 'saved ' + image_url
					succeeded = True
				filesize = Tumblr.os.stat(directory_and_filepath)
				if filesize < 1024L:
					print 'may not have gotten ' + image_url
			else:
				print str(status_code) + ' could not get ' + image_url
		except IOError as ioe:
			print 'IOError: Failed to save ' + image_url + ': ', ioe
		except:
			print 'Failed to save ' + image_url + ': ', Tumblr.sys.exc_info()[0]
		return succeeded
	
	@staticmethod
	def remove_avatar_file_urls(urls):
		result = []
		for url in urls:
			if 'avatar_' not in url:
				result.append(url)
		return result
	
	@staticmethod
	def remove_non_file_urls(urls): # rewrite with list comprehension or filter or something
		result = []
		for url in urls:
			if url[url.rfind('.') + 1:] in Tumblr._supported_img_types:
				result.append(url)
		return result
	
	@staticmethod
	def get_url_and_filename_for_big_img(img_url, filename):
		img_url_big, filename_big = img_url, filename
		img_url_match = Tumblr._img_url_pattern.search(img_url)
		filename_match = Tumblr._filename_info_pattern.search(filename)
				
		if filename_match:
			filename_big = filename_match.group(1) + '500.' + filename_match.group(3)
		else:
			filename_big = filename
			
		if img_url_match:
			img_url_big = img_url_match.group(1) + filename_big
		else:
			try:
				img_url_big = Tumblr._simple_img_url_pattern.search(img_url).group(1) + filename_big
			except AttributeError as ae:
				print 'simple img url regex failed on url: ' + img_url
				print ae
		
		return img_url_big, filename_big
	
	@staticmethod
	def get_url_and_filename_for_medium_img(img_url, filename):
		img_url_medium, filename_medium = img_url, filename
		img_url_match = Tumblr._img_url_pattern.search(img_url)
		filename_match = Tumblr._filename_info_pattern.search(filename)
				
		if filename_match:
			filename_medium = filename_match.group(1) + '400.' + filename_match.group(3)
		else:
			filename_medium = filename
			
		if img_url_match:
			img_url_medium = img_url_match.group(1) + filename_medium
		else:
			try:
				img_url_medium = Tumblr._simple_img_url_pattern.search(img_url).group(1) + filename_medium
			except AttributeError as ae:
				print 'simple img url regex failed on url: ' + img_url
				print ae
		
		return img_url_medium, filename_medium
	
	@staticmethod
	def get_file_name_from_url(url):
		return url[url.rfind('/') + 1:]
		
	@staticmethod
	def get_filetype(filename):
		return filename[filename.rfind('.') + 1:]
		
	@staticmethod
	def get_tumblr_img_urls_from_soup(imgs_soup):
		urls = []
		for img in imgs_soup:
			if img.has_key('src'):
				urls.append(img['src'])
		return urls
		
	def get_directory_name(self, first=None, last=None, directory_for_saving=None): # perhaps there's a better way
		if not self._dirname:
			match = self._dirname_pattern.search(self._tumblr_url)
			self._dirname = match.group(1)
			if first and last:
				self._dirname += '_pages_' + str(first) + '_to_' + str(last)
			if directory_for_saving:
				self._dirname = directory_for_saving + self._dirname
		return self._dirname
		
	def make_img_directory(self, first, last, directory_for_saving='./'):
		dirname = self.get_directory_name(first, last, directory_for_saving)
		if not Tumblr.os.path.exists(dirname):
			Tumblr.os.makedirs(dirname)
	
	def filetype_allowed(self, filetype):
		result = True
		if not self._get_gifs and filetype in Tumblr._gif_img_type:
			result = False
		elif not self._get_static and filetype in Tumblr._static_img_types:
			result = False
		return result
	
	def process_posts(self, links_soup, source_tumblrs):
		for link in links_soup:
			if not link.has_key('href'):
				continue
			match = Tumblr._source_post_pattern.search(link['href'])
			if not match:
				continue
			name = match.group(3)
			# don't count occurences of this tumblr
			if not name or name == self._tumblr_name:
				continue
			url = match.group(1)
			if source_tumblrs.has_key(url):
				source_tumblrs[url] += 1
			else:
				source_tumblrs[url] = 1
	
	def process_imgs(self, imgs_soup):
		print 'possible number of images: ' + str(len(imgs_soup))
		img_urls = Tumblr.get_tumblr_img_urls_from_soup(imgs_soup)
		img_urls = Tumblr.remove_non_file_urls(img_urls)
		img_urls = Tumblr.remove_avatar_file_urls(img_urls)
		print 'after filtering, possible number of images: ' + str(len(img_urls))
		for img_url in img_urls:
			if img_url in self._images_downloaded: # skip images we already have
				print 'already have ' + img_url
				continue
			filename = Tumblr.get_file_name_from_url(img_url)
			if filename:
				if not filename.startswith('tumblr_'): # skip non-tumblr images
					print filename + ' is not a tumblr image'
					continue
				if not self.filetype_allowed(Tumblr.get_filetype(filename)):
					continue
				
				img_url_big, filename_big = Tumblr.get_url_and_filename_for_big_img(img_url, filename)
				img_url_medium, filename_medium = Tumblr.get_url_and_filename_for_medium_img(img_url, filename)
				
				# how to attempt to get medium (400) images?
				if self.save_image_from_url(img_url_big, filename_big):
					self._images_downloaded.add(img_url_big)
				elif self.save_image_from_url(img_url_medium, filename_medium):
					self._images_downloaded.add(img_url_medium)
				elif self.save_image_from_url(img_url, filename): # we couldn't get the big image? settle for the small one
					self._images_downloaded.add(img_url)
	
	@staticmethod
	def is_post_link(link):
		result = False
		if link.has_key('href'):
			if Tumblr._post_pattern.search(link['href']):
				result = True
		return result
		
	@staticmethod
	def page_soup_has_posts(soup):
		has_posts = False
		links = soup.find_all('a')
		for link in links:
			if Tumblr.is_post_link(link):
				has_posts = True
				break;
		return has_posts
			
	def get_tumblr_page_url(self, page_number):
		return self._tumblr_url + 'page/' + str(page_number)
		
	def get_soup_for_tumblr_page(self, page_number):
		ATTEMPTS = 10
		attempt_number = 1
		while attempt_number <= ATTEMPTS:
			try:
				status_code, content = Tumblr.get_page(self.get_tumblr_page_url(page_number))
				return self.BeautifulSoup(content)
			except: # seems to solve an issue with data encoding (http://stackoverflow.com/questions/6180521/unicodedecodeerror-utf8-codec-cant-decode-bytes-in-position-3-6-invalid-dat,
				# or http://stackoverflow.com/questions/7873556/utf8-codec-cant-decode-byte-0x96-in-python
				print 'Failed to soupify page content on attempt ' + str(attempt_number) + '.'
				attempt_number += 1
		print 'Could not soupify page ' + str(page_number) + ' after ' + str(ATTEMPTS) + ' attempts. Skipping.'
		return ''
	
	def save_images_from_tumblr(self, first=1, last=None, directory_for_saving='./'): # indexed starting at 1
		if not first:
			first = 1
		self.make_img_directory(first, last, directory_for_saving)
		source_tumblrs = {}
		if last:
			for page_number in xrange(first, last + 1): # increment last by 1 so that (1, 1) gets you page 1
				print 'processing page ' + str(page_number) + ' of ' + str(last)
				page_soup = self.get_soup_for_tumblr_page(page_number)
			
				self.process_imgs(page_soup.find_all('img'))
				self.process_posts(page_soup.find_all('a'), source_tumblrs) # find the blogs that this tumblr reblogged
		else:
			page_number = first
			while(True):
				print 'processing page ' + str(page_number)
				page_soup = self.get_soup_for_tumblr_page(page_number)
				if not Tumblr.page_soup_has_posts(page_soup):
					print 'no posts found on page ' + str(page_number)
					break;
				else:
					self.process_imgs(page_soup.find_all('img'))
					self.process_posts(page_soup.find_all('a'), source_tumblrs) # find the blogs that this tumblr reblogged
					page_number += 1
		
		sorted_sources = sorted(source_tumblrs.iteritems(), key=Tumblr.operator.itemgetter(1), reverse=True) # order these by frequency
		with open(self._dirname + '/Source Tumblrs.txt', 'w+') as f:
			for url, freq in sorted_sources:
				f.write(url + '\t' + str(freq) + '\n')
		

def parse_cmd_line_args(args):
	tumblr_url, start_page, end_page, directory_for_saving = None, None, None, './'
	for arg in args[1:]:
		if arg.isdigit():
			if not start_page:
				start_page = int(arg)
			else:
				end_page = int(arg)
		else:
			if not tumblr_url:
				tumblr_url = arg
			else:
				directory_for_saving = arg
				last_char = directory_for_saving[-1]
				if last_char != '/' or last_char != '\\':
					directory_for_saving += '/'

	return tumblr_url, start_page, end_page, directory_for_saving

if __name__ == '__main__':
	tumblr_url, start_page, end_page, directory_for_saving = parse_cmd_line_args(sys.argv)
	t = Tumblr(tumblr_url, True, True)
	if end_page:
		print t._tumblr_url + ', pages ' + str(start_page) + ' through ' + str(end_page)		
	elif start_page:
		print t._tumblr_url + ', starting at page ' + str(start_page)
	else:
		print t._tumblr_url
	t.save_images_from_tumblr(start_page, end_page, directory_for_saving)
