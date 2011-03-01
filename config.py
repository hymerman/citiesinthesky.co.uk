import os
import logging

# Default URL: if no Redirect URL can be generated, traffic will be diverted here
DEFAULT_URL = 'http://blog.benhymers.com/'

# todo:
# Handle /category/x/page/n properly
# Handle archives like /2010/06 properly

# Send email message when redirect error occurs
ERROR_EMAIL_ACTIVE = True;
ERROR_EMAIL_SENDER = '"Redirector for www.citiesinthesky.co.uk" <b.hymers@gmail.com>';
ERROR_EMAIL_SUBJECT = 'Redirect Script Error';
ERROR_EMAIL_BODY = 'Unable to redirect this url: ';

# Check if the destination URL exists BEFORE redirecting
CHECK_URL_EXISTANCE = True;

# Memcache redirection results
MEMCACHE_ACTIVE = True;
MEMCACHE_EXPIRES_IN_SECONDS = 86400; # 1 day

# Logging level
LOGGING_LEVEL = logging.WARNING;