# App Name: Gredirector
# Author: Ivan De Marino - ivan.de.marino@gmail.com
# Forked from: http://blog.dantup.com/2010/01/generic-redirection-script-for-google-app-engine

import webob
import urlparse
import logging
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import memcache

import config


# Check if a URL exists, trying a URL Fetch
def check_url_exists(url):
	# Search the Memcache
	memcachekey = "check_url_exists-" + url;
	result = memcache.get(memcachekey) if config.MEMCACHE_ACTIVE else None;

	# Nothing in Memcache
	if ( result == None ):
		logging.debug("Existence of URL '%s' not in Memcache" % (url) );
		try:
			response = urlfetch.fetch(url, allow_truncated=True, deadline=10); # Wait as much as possible: 10 sec
			if ( response.status_code == 200 ):
				logging.debug("Verified URL '%s' existence" % (url));
				result = True;
			else:
				logging.error("Unable to Verify URL '%s' existence" % (url));
				result = False;
		except:
			# In case of InvalidURLError or DownloadError
			logging.error("Exception while Verifying URL '%s' existence" % (url));
			result = False;

		# Store the result in Memcache for config.MEMCACHE_EXPIRES_IN_SECONDS
		memcache.set(memcachekey, result, time=config.MEMCACHE_EXPIRES_IN_SECONDS);

	return result;

def looks_like_archive(path):
	if re.match("^/[\d]+/[\d]+[/]?$", path) is None:
		return False
	return True

def looks_like_feed(path):
	return path.endswith("/feed") or path.endswith("/feed/")

def remove_trailing_forward_slash(string):
	if string[-1:] == "/":
		return string[:-1]

	return string

# Wordpress liked to surround a typographic hyphen with two other hyphens.
# Replace this weird construct with one normal hyphen.
def fix_stupid_hyphen_character(string):
	return string.replace("-%E2%80%93-", "-")

# Generates the URL to redirect to
def get_redirect_url(url):
	# Search the Memcache
	memcachekey = "get_redirect_url-" + url;
	result = memcache.get(memcachekey) if config.MEMCACHE_ACTIVE else None;

	# Nothing in Memcache
	if ( result == None ):
		logging.debug("Redirect for URL '%s' not in Memcache" % (url) )
		scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
	
		
		# Fix empty paths to be just '/' for consistency
		if path == '':
			path = '/'

		# Check for /page/n
		if path.startswith('/page'):
			result = 'http://blog.benhymers.com' + remove_trailing_forward_slash(path)

		# There are no per-tag feeds yet so just redirect all feeds to the main one
		# Do this before checking for categories since categories can have feeds
		elif looks_like_feed(path):
			logging.debug("Found feed URL")
			result = 'http://blog.benhymers.com/feeds/atom.xml'

		# Check for /category/x
		# Take everything from the 10th character (after /category/)
		# Ignore /category/x/page/n since it's hard and nobody really visits it anyway...
		elif path.startswith('/category'):
			result = 'http://blog.benhymers.com/tag/' + remove_trailing_forward_slash(path[10:])

		elif path.startswith('/about-ben') or path.startswith('/employers-look-here'):
			result = 'http://www.benhymers.com'

		# Even redirect to the main page; we don't want it to look like this page still exists
		elif path.startswith('/cities-in-the-sky'):
			result = 'http://www.citiesinthesky.co.uk'

		# Unfortunately there are no archive pages in bloggart just yet, so redirect to the main page
		elif looks_like_archive(path):
			logging.debug("Looks like an archive page")
			result = 'http://blog.benhymers.com/archive/'

		elif path.endswith('/comment-page-1/'):
			logging.debug("Trimmed comment page")
			result = 'http://blog.benhymers.com' + path[:16] + '/'

		elif path.endswith('/trackback/'):
			logging.debug("Trackback URL")
			result = 'http://blog.benhymers.com' + path[:11] + '/'

		# Assume that any other path is an actual page, in which case the mapping is direct
		else:
			result = 'http://blog.benhymers.com' + fix_stupid_hyphen_character(remove_trailing_forward_slash(path)) + '/'

		# Store the result in Memcache for config.MEMCACHE_EXPIRES_IN_SECONDS
		memcache.set(memcachekey, result, time=config.MEMCACHE_EXPIRES_IN_SECONDS)

	return result;


# Main Request Handler
class MainHandler(webapp.RequestHandler):
	def get(self):
		# Perform redirect
		url = get_redirect_url(self.request.url);

		# Check that we were able to build a URL and that this URL actually exists
		if url and (check_url_exists(url) if config.CHECK_URL_EXISTANCE else True):
			logging.info("Redirecting URL '%s' to URL '%s'" % (self.request.url, url) );
			self.redirect(url, permanent=True);
		else:
			# Log that we didn't know what this was, and redirect to a good default
			logging.error("Unable to Redirect URL '%s'" % (self.request.url) );
			if config.ERROR_EMAIL_ACTIVE:
				mail.send_mail_to_admins(
					sender=config.ERROR_EMAIL_SENDER,
					subject=config.ERROR_EMAIL_SUBJECT,
					body=config.ERROR_EMAIL_BODY + self.request.url
				);
			self.redirect(config.DEFAULT_URL, permanent=True);


application = webapp.WSGIApplication([("/.*", MainHandler)], debug=True);


def main():
	logging.getLogger().setLevel(config.LOGGING_LEVEL);
	run_wsgi_app(application);


if __name__ == "__main__":
	main();
