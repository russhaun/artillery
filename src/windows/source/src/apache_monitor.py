# 127.0.0.1 - - [10/Mar/2012:15:35:53 -0500] "GET /sdfsdfds.dsfds
# HTTP/1.1" 404 501 "-" "Mozilla/5.0 (X11; Linux i686 on x86_64;
# rv:10.0.2) Gecko/20100101 Firefox/10.0.2"
from src.core import *

def tail(some_file):
    this_file = open(some_file)
    # Go to the end of the file
    this_file.seek(0, 2)

    while True:
        line = this_file.readline()
        if line:
            yield line
        yield None
#
# grab the access logs and tail them
#"/var/log/apache2/access.log"
access = read_config("ACCESS_LOG")
access_log = tail(access)
# grab the error logs and tail them
#"/var/log/apache2/error.log"
errors = read_config("ERROR_LOG")
error_log = tail(errors)
