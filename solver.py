# -*- coding: utf-8 -*-
"""
solver.py

A solution to the Sortable coding challenge. Attempts to match listings
to the product they're talking about.

This meme pretty much summarises the design philosophy behind this code:
http://imgur.com/a/WRkmo

Challenges:
- Hyphens can be used in many ways. They may be:
    1. part of the model #
    2. Replacing a space within a field
    3. As a delimiter between manufacturer and family or family and model
    4. Added in the middle of a compound word

Known sources of misses:
- products with revisions may not be recognized - i.e. X100 and X100a will
not be seen as the same
- no attempt is made to correct for typos
- Abbreviated company names, such as HP and GE fail

Known sources of false positives:
- accessories that fit only one model from the product list can easily cause
a false positive. For example, an iPhone 7 case would be seen as an iPhone 7.
This could be mitigated by rejecting or flagging listings with prices (easy)
or keywords (hard) very different from others in the group.
- results do include bundles of main product + accessories. It's not clear
from the problem definition whether that is okay.

Some interesting failed cases:
- {"product_name":"Ricoh_GXR_(A12)","manufacturer":"Ricoh","model":"GXR (A12)"}
It's unclear whether this product refers to GXR (the body) or A12 (the module),
which are found separately in the listings.

"""


import io
import re
import json
from collections import defaultdict, OrderedDict

import argparse

def get_manufacturer(man):
    """ obtain and simplify the manufacturer ID from dictionary

    Args:
        data (dict): dictionary of information about a product or listing

    Returns:
        man (string): the first four letters of the manufacturer name in lower
            case, or 'unknown' if 'manufacturer' tag is missing or blank
    """

    if len(man) == 0:
        man = 'unknown'
    else:
        man = man.upper()

        # hyphens may replace spaces, like Hewlett-Packard
        man = man.replace('-', ' ')
        man = man.replace('.', '')

        # if there are multiple words, replace by their acronym
        # i.e. Hewlett Packard -> HP
      #  words = man.split()
     #   if len(words) > 1:
     #       man = ''.join([word[0] for word in words])


    return man[:min(4, len(man))]



# remove unnecessary hyphens and spaces
def cleanup_family(family):
    """ converts the string to upper space, removes hyphens and spaces"""
    
    family = family.upper()
    family = family.replace('-', '')
    family = family.replace(' ', '')
    return family

def generate_regex(target):
    """ Generate a regular expression that matches the target string, ignoring
    any spaces or hyphens within either the original or target string. Also,
    if the target starts or ends with a digit, make sure the number before or
    after isn't also a digit.

    Args:
        target (string): the string that we later want to search for

    returns:
        a compiled regular expression that can be used for pattern matching

    Examples:
        A100 matches A-100
        B52 matches B 52
        C100 does NOT match C1000
        150D does NOT match 2150D
    """

    target = target.upper().replace('-', '').replace(' ', '')

    match_string = '(' + r"-?\s?".join([c for c in target]) + ')'

    if target[-1].isdigit():
        match_string = match_string + r'([^\d].*)?$'

    if target[0].isdigit():
        match_string = r'^(.*[^\d])?' + match_string

    return re.compile(match_string)

def match_listing(listing, products_by_man):
    """ attempt to find a product that matches a single listing

    Args:
        listing  (dict): the substring to look for
        products_by_man (collections.defaultdict): a dictionary whose keys
            are shortened manufacturer names and entries are dictionaries
            loaded from the products data file.

    Returns:
        (string) product name if a match is found, otherwise "None"
    """

    title = listing['title']
    man = get_manufacturer(listing['manufacturer'])

    # first, we check if the manufacturer matches. If not, try using
    # the first word of the title as manufacturer ID
    if not man in products_by_man:
        man = get_manufacturer(title.split()[0])

    matches = []

    # second, we makes list of products whose model number is
    # somewhere in the title. This may result in multiple matches
    for product in products_by_man[man]:
        if len(re.findall(product['regex'], title.upper())) > 0:
            matches.append(product)

    # get the longest match - this deals with the problem of one
    # model name being a substring of another i.e.
    # products like ABC and ABC-1
    if len(matches) > 1:
        # "pythonic" is often a synonym for "obfuscated one-liner"
        max_match = max(matches, key=lambda x: len(x['model']))
        max_len = len(max_match['model'])

        new_matches = []
        for match in matches:
            if len(match['model']) == max_len:
                new_matches.append(match)

        matches = new_matches

    # if there are still multiple matches, it is likely
    # that this listing is for an accessory that fits multiple
    # models of camera (or other product). Only return product name
    # if there is only a single match
    if len(matches) == 1:
        return matches[0]['product_name']
    else:
        return 'None'

def load_products(filename):
    """ read in the products file, and return them in a dictionary keyed by 
    a shortened version of their manufacturer string
    
    Args:
        filename (string): /path/to/file where the product information is
            stored in JSON format
            
    returns: 
        products_by_manufacturer (defaultdict): dictionary of lists of product
            dictionaries, keyed by a shortened version of their manufacturer 
            string.     
    """
    
    products_by_manufacturer = defaultdict(list)
    
    # use like model_words[man][word] = count
    model_words = defaultdict(lambda: defaultdict(int))

    with io.open(filename, 'r', encoding='utf-8') as products_file:
        for line in products_file:
            data = json.loads(line)
            
            man = get_manufacturer(data['manufacturer'])

            if data['model'].isdigit() and 'family' in data:
                data['model'] = data['family'] + ' ' + data['model']
                
            model = data['model']

            
            # treat hyphens as spaces only if there are no spaces
            if ' ' in model:
                word_list = model.split(' ')
            else:
                word_list = model.split('-')
                
            for word in word_list:
                model_words[man][word] += 1
            # if the model number is literally just a number, put it together
            # with the family name, since it's very likely that it would
            # be written that way, and we avoid false positives if the number
            # is used in some other context (like, say, focal length)

            products_by_manufacturer[man].append(data)

    # now reduce the model tag to a single word if any single word is enough
    # to uniquely identify the model. For example, all Panasonic cameras have
    # the prefix DMC-, so some listings will omit that since it adds little
    # information
    for man in products_by_manufacturer:
        for product in products_by_manufacturer[man]:
            model = product['model']
            
            # treat hyphens as spaces only if there are no spaces
            if ' ' in model:
                word_list = model.split(' ')
            else:
                word_list = model.split('-')
                
            if len(word_list) > 1:            
                has_unique = False
                
                # check if any word is unique, and also not just a number
                for word in word_list:
                    if model_words[man][word] == 1 and not word.isdigit():
                        has_unique = True
                
                if has_unique:
                    new_model = ''
                    for word in word_list:
                        if model_words[man][word]  < 5:
                            new_model = new_model + word
                    product['model'] = new_model
                    
            product['regex'] = generate_regex(product['model'])
                
    return products_by_manufacturer

def match_all(listings_file_name, products_file_name, results_file_name):
    """ attempt to find products that match each listing in the listings file

    Args:
        listings_path (string): name of the file containing listing objects
        products_file_name (string): name of file containing product objects
        results_file_name (string): name of file to write results to

    Returns:
        None; results are written to the specified file
    """

    results = defaultdict(list)

    print("Loading product information...")
    # load the product information
    products_by_man = load_products(products_file_name)

    print("Searching listings...")
    # look up every listing in the listings file
    with io.open(listings_file_name, 'r', encoding='utf-8') as listings_file:
        for line in listings_file:
            listing = json.loads(line)
            product_name = match_listing(listing, products_by_man)
            if product_name != "None":
                results[product_name].append(listing)

    print("Writing results file...")
    
    # now need to output the result
    with io.open(results_file_name, 'w', encoding='utf-8') as result_file:
        for key in results:
            if len(results[key]) > 0:
                entry = OrderedDict([['product_name', key],
                                     ['listings', results[key]]])
                json_line = json.dumps(entry, ensure_ascii=False)
                result_file.write(json_line + u'\n')
    print("Done")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--listings", default = 'listings.txt', 
                        help="input listings file")
    parser.add_argument("-p", "--products", default = 'products.txt', 
                        help="input products file")
    parser.add_argument("-r", "--results", default = 'results.txt', 
                        help="output results file")
    args = parser.parse_args()
    
    match_all(args.listings, args.products, args.results)
