__author__ = 'Qyon'

import settings
from observer import Observer
import logging

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
# create file handler and set level to debug
fileHandler = logging.FileHandler('allegro_observer.log')
fileHandler.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

for lname in ('allegro', 'observer', ):
    logger = logging.getLogger(lname)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)

for lname in ( 'suds.client',  ):
    logger = logging.getLogger(lname)
    logger.setLevel(logging.ERROR)
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)


def main():
    observer = Observer(settings)
    observer.watch()

if __name__ == "__main__":
    main()