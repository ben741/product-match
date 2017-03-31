# product-match

This code attempts to match known products (supplied in the file products.txt) to listings (from the file listings.txt).

To run the full code, use `python solver.py`. You can also specify other files for listings, products and results - use `python solver.py --help` for options.

This code was written in python2, but it seems to run fine on a fresh python 3.6 installation. It uses only the standard libraries, so it should Just Work.

To test the code against a limited subset of listings, use `python test.py`. To add more test cases, use `python generate_test_data.py`.

The script`generate_test_data.py` selects a random listing from listings.txt and offers you the solution found by `solver.py`. You can either agree that it's correct, or figure out the correct solution and provide it. Either way, the new listing-product_name pair is appended to the file test_data.txt.
