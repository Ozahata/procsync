from contextlib import closing
import MySQLdb
import string
from random import randint, sample
import datetime

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_DATABASE = "procsync_db1"

# How many register wish add
QUANTITY = 10

def rand_string(characters, min_size=None, max_size=None, fixed=None, repeat_characters=False):
    """
    @param characters: List of characters that with to be random (Default: letters and numbers).
    @param min_size: Minimal length allow (Default: 1).
    @param max_size: Maximal length allow (Default: Limit is the length of characters).
        - If put more that the length of characters will use other
        - Type of random (repeat_characters need be True).
    @param fixed: Is the length that need return with the characters. (Default: random)
    @param repeat_characters: if true, the range need be the same that characters. (Default: False)
    @return: A random string defined by a list of characters requested. (by default will not repeat the character). 
    """
    if characters is None or len(characters) == 0:
        characters = string.letters + string.digits
    size = len(characters)
    if min_size is None or not isinstance(min_size, int): min_size = 1
    if max_size is None or not isinstance(max_size, int): max_size = size
    if min_size > max_size: raise ArithmeticError("min_size is greater than max_size!")
    if fixed is None or not isinstance(fixed, int): fixed = randint(min_size, max_size)
    if (max_size > size and repeat_characters) or (fixed is not None and fixed > size and not repeat_characters): raise TypeError("Impossible not repeat the characters if the max_size is greater than characters!")
    if fixed is None:
        return ''.join([ choice(characters) for _ in range(randint(min_size, max_size)) ]) if repeat_characters else ''.join(sample(characters, randint(min_size, max_size)))
    else:
        return ''.join([ choice(characters) for _ in range(fixed) ]) if repeat_characters else ''.join(sample(characters, fixed))

def insert_rows(host, user, password, db, quantity):
    try:
        connection = MySQLdb.connect(host=host, user=user, passwd=password, db=db)
        with closing(connection.cursor()) as cursor:
            for item in range(quantity):
                # ADD IN TABLE
                cursor.execute("""INSERT INTO origin (text) VALUES ('%s');""" % (rand_string(string.ascii_letters, min_size=3)))
                if item % 200 == 0: connection.commit()
        connection.commit()
        connection.close()
    except Exception, e:
        print "Exception: ", e
        
if __name__ == "__main__":
    host = raw_input("Enter the host [%s]: " % DB_HOST)
    host = host if host != "" else DB_HOST
    user = raw_input("Enter the user [%s]: " % DB_USER)
    user = user if user != "" else DB_USER
    password = raw_input("Enter the password [%s]: " % DB_PASSWORD)
    password = password if password != "" else DB_PASSWORD
    db = raw_input("Enter the database [%s]: " % DB_DATABASE)
    db = db if db != "" else DB_DATABASE
    quantity = raw_input("Enter the quantity [%s]: " % QUANTITY)
    quantity = quantity if quantity != "" else QUANTITY    
    insert_rows(host, user, password, db, int(quantity))
