# -*- coding: utf-8 -*-
"""
generate_test_data.py

An interactive command line script to generate test data for test.py.

This script chooeses a random listing from listings.txt, and tries to use
solver.py to find the matching product. The user decides if the answer is
correct, or else provides the correct answer.

"""

import io
from collections import defaultdict, OrderedDict
import random
import json

import solver

if __name__ == '__main__':
    listings = []

    products_by_man = solver.load_products('products.txt')
    # load all of the listings, so that we can later pick randomly from them
    with open('listings.txt') as f:
        for line in f:
            listings.append(json.loads(line))

    with io.open('test_data.txt', 'a', encoding='utf-8') as test_file:
        while (True):
            listing = listings.pop(random.randint(0, len(listings)-1))
            print('Listing:\n' + listing['title'])
            print('Manufacturer: '+listing['manufacturer'])

            product_name = solver.match_listing(listing, products_by_man)
            print product_name

            answer = ''
            while answer not in ['y', 'n', 'q']:
                answer = raw_input('Is this correct?').lower()

            if answer == 'y':
                pass
            elif answer == 'n':
                product_name = raw_input('Please enter correct number:')
                product_name.strip()
            elif answer == 'q':
                print('Finished')
                break

            d = OrderedDict([['listing', listing],
                             ['product_name', product_name]])
            test_file.write(json.dumps(d, ensure_ascii=False) + u'\n')
