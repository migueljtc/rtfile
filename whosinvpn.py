import time
from datetime import datetime
import argparse
import sys
import logging

FIND_ME_IN = "Log In"
FIND_ME_OUT = "Log Out"
USR_NAME_STRING = "usrName"
HTML_FILE_NAME = "index.html"
CURRENT_LOGGED_USERS = {}
START_UP_TIME = ""
LOG_FILE = "whosinvpn.csv"


def follow(thefile):
    # The actual function that simulates "tail -f"
    # in unix. Returns the last written line

    thefile.seek(0, 2)

    while True:
        in_line = thefile.readline()
        if not in_line:
            time.sleep(0.1)
            continue
        yield in_line


def add_user(raw_line):
    # This function adds a new user to the list of users
    # it parses the line and fetches the user name

    global CURRENT_LOGGED_USERS

    user = process_line_in(raw_line)
    print("add: Processing user: " + user)

    # make sure not to add the same user twice
    if user not in CURRENT_LOGGED_USERS:
        # get the time/date user connected
        _time_now = datetime.now()
        login_time = _time_now.strftime("%d/%m/%Y, %H:%M:%S")

        # add user and connection date to dict
        CURRENT_LOGGED_USERS[user] = login_time
        update_html(CURRENT_LOGGED_USERS)
        print("Added user: " + user)
        logging.info('Added user: %s', user)
        logging.info('Active Users: %s', str(len(CURRENT_LOGGED_USERS)))

    print("Active users: " + str(len(CURRENT_LOGGED_USERS)))


def remove_user(raw_line):
    # This function removes a user from the list of users
    # it parses the line and fetches the user name to
    # be removed

    global CURRENT_LOGGED_USERS
    user = process_line_out(raw_line)
    print("remove: Processing user: " + user)

    # avoid removing non-existant elements
    if user in CURRENT_LOGGED_USERS:
        del CURRENT_LOGGED_USERS[user]
        update_html(CURRENT_LOGGED_USERS)
        print("Removed user: " + user)
        logging.info('Removed user: %s', user)
        logging.info('Active Users: %s', str(len(CURRENT_LOGGED_USERS)))

    print("Active users: " + str(len(CURRENT_LOGGED_USERS)))


def update_html(_current_logged_users):
    # Prints the list of users and their number results to an html
    # which will autorefresh every 3 seconds
    # Set the time of the update as well as the startup of program

    global START_UP_TIME

    now = datetime.now()
    t_now = now.strftime("%d/%m/%Y, %H:%M:%S")

    header = '''<html>
  <head>
  <title>VPN Users Online: </title>
  <meta http-equiv="refresh" content="3">
  <link rel="stylesheet" href="wvpn.css">
  </head>
  <body>
  <h2>VPN Users Online : {}</h2> <h3> Last Refresh: {}
  </h3>
  <h5> {} </h5>
  </body>
  <footer> <h5> Online since: {}</h5> </footer>
  </html>'''.format(len(_current_logged_users), t_now,
            create_html_table(
                _current_logged_users), START_UP_TIME)

    with open(HTML_FILE_NAME, 'w') as out:
        out.write(header + '\n')


def process_line_in(raw_line):
    # Finds the strings in which the user name is between
    # Strips user name from it

    index_start = raw_line.find('usrName')
    index_end = raw_line.find("attackStatus")
    return raw_line[index_start + 8:index_end].strip()


def process_line_out(raw_line):
    # Finds the strings in which the user name is between
    # Strips user name from it

    index_start = raw_line.find('usrName')
    index_end = raw_line.find("ifdir")
    return raw_line[index_start + 8:index_end].strip()


def create_html_table(user_list_dic):
    # This function creates a HTML table
    # with the logged in users and returns a string
    # with the result

    table = "<table>\n"
    # Create the table's column headers
    header = ["Users Connected", "Login Time"]
    table += "  <tr>\n"
    for column in header:
        table += "    <th>{0}</th>\n".format(column.strip())
    table += "  </tr>\n"

    # Create the table's row data
    for _user in user_list_dic:
        row = [_user, user_list_dic[_user]]
        table += "  <tr>\n"
        for column in row:
            table += "    <td>{0}</td>\n".format(column)
        table += "  </tr>\n"
    table += "</table>"

    return table


if __name__ == '__main__':
    # The main, opens file and tails it every time a keyword is found
    # adds/removes an user

    # Parse arguments
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-f', '--file', help='Log File path', required=True)
    parser.add_argument('-out', '--output', help='Html output file path')
    parser.add_argument('-log', '--logfile', help='Log file  path')
    args = vars(parser.parse_args())

    # set arguments to variables
    if args['file']:
        my_log_file_path = args['file']
    if args['output']:
        HTML_FILE_NAME = args['output']
    if args['logfile']:
        LOG_FILE = args['logfile']

    # Initiate logging
    logging.basicConfig(
        filename=LOG_FILE, filemode='a',
        format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)

    logging.info('--- WhosInVpn Started ---')

    # Init variables
    time_now = datetime.now()
    START_UP_TIME = time_now.strftime("%d/%m/%Y, %H:%M:%S")

    # Open the log file
    try:
        logfile = open(my_log_file_path)
    except IOError:
        print("File ", my_log_file_path, " not found exiting...")
        sys.exit()

    # Follow the file
    loglines = follow(logfile)

    # clean up html on start
    update_html(CURRENT_LOGGED_USERS)

    # The actual file parsing
    for line in loglines:
        if FIND_ME_IN in line:
            # print (line)
            add_user(line)
        if FIND_ME_OUT in line:
            # print (line)
            remove_user(line)
