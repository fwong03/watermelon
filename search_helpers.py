from model import User
from datetime import datetime, timedelta
from geolocation.google_maps import GoogleMaps
from geolocation.distance_matrix import const
import os

""" Helper functions for server.py search-related routes.
     Seven function total.
"""

def search_radius(search_center, postalcodes, radius):
    """ Finds zipcodes in the database that are within a search radius of a
        location.

        This uses the python library geolocation-python, which uses the
        GoogleMaps API.

        Takes in search center as a string, postalcodes as a list of tuples
        (because that is the format returned from the database), and search
        radius in miles as an integer. The function returns the list of
        postal codes in the given list that are within the given radius.

    """
    # Future versions: make a table in the database to store distance search
    # results.
    # For now store frequest searches in a dictionary to prevent eof error,
    # likely from hitting Google Maps API too frequently within a given
    # amount of time.
    distances = {'94612': {'94109': 11.2468,
                           '94612': 0.0,
                           '94040': 45.4221,
                           '94115': 13.2973,
                           '95376': 53.1893,
                           '94043': 39.0842,
                           '10013': 2899.3124,
                           },
                 '94109': {'94109': 0.0,
                           '94612': 10.9361,
                           '94040': 38.9599,
                           '94115': 1.2427,
                           '95376': 62.137,
                           '10013': 2904.9047,
                           '94043': 37.2201,
                           },
                 }

    # SQLite returns the distinct postal codes as a list of tuples. Convert this
    # to a list of postal code strings.
    postalcodes_in_db = []

    for postalcode in postalcodes:
        postalcodes_in_db.append(postalcode[0])

    distinct_postalcodes = postalcodes_in_db
    postalcodes_within_radius = []

    if search_center in distances:
        distinct_postalcodes = []
        postalcodes_to_remove = []

        for postalcode in postalcodes_in_db:
            if postalcode in distances[search_center]:
                if distances[search_center][postalcode] <= radius:
                    postalcodes_within_radius.append(postalcode)
                # Always add postalcode to the list of postal codes to remove.
                postalcodes_to_remove.append(postalcode)

        # Check if there are still postal codes to check.
        if len(postalcodes_in_db) > len(postalcodes_to_remove):
            distinct_postalcodes = [postalcode for postalcode in postalcodes_in_db if postalcode not in postalcodes_to_remove]

    # Use GoogleMaps API there are still things left in distinct_postalcodes
    if distinct_postalcodes:
        google_maps = GoogleMaps(api_key=os.environ['GOOGLE_API_KEY'])

        # Put search center in a list because that is how the the geolocation
        # distance module takes it in as a parameter
        search_center = [search_center]

        # Now we can calculate distances.
        items = google_maps.distance(search_center, distinct_postalcodes).all()

        # Items is list of distance matrix object thingies. Each has an origin,
        # destination, and distance between the origin and destination.
        # First we'll take out the matrix thingies within the search
        # radius of the given search center.
        matrixthingies = []
        for item in items:
            if (item.distance.miles <= radius):
                matrixthingies.append(item)

        # Now we pull out the user location info from the matrixthingies. This info
        # has the city, state, zipcode and country.
        destinations = []
        for thingy in matrixthingies:
            destinations.append(thingy.destination)

        # Now we pull out the zipcode from the list of destinations.
        for destination in destinations:
            line = destination.split()
            postalcode = line[-2].replace(",", "")
            postalcodes_within_radius.append(postalcode)

    return postalcodes_within_radius


def get_users_in_area(postal_codes, user_id):
    """ Finds users in the database that live in one of the given zipcodes.

        (Here I passed in the use_id to make it easier to test. This was before
        I learned how to set cookies in tests.)

    """

    users_in_area = User.query.filter(User.postalcode.in_(postal_codes)).all()
    logged_in_user = User.query.get(user_id)

    if logged_in_user in users_in_area:
        users_in_area.remove(logged_in_user)

    return users_in_area


def filter_products(products, category_id, brand_id):
    """ Filters a given list of products for a given category and brand.

        Takes in list of products, category_id as int and brand_id as integers
        and returns a list of products.
    """

    if category_id < 0 and brand_id < 0:
        return products
    else:
        filtered_products = []

        if category_id > 0 and brand_id < 0:
            for product in products:
                if product.cat_id == category_id:
                    filtered_products.append(product)
        elif (category_id < 0) and (brand_id > 0):
            for product in products:
                if product.brand_id == brand_id:
                    filtered_products.append(product)
        else:
            for product in products:
                if (product.cat_id == category_id) and (product.brand_id == brand_id):
                    filtered_products.append(product)

    return filtered_products


def get_products_within_dates(start_date, end_date, users):
    """ Finds products that are available within a given date range.

        Takes in list of users and returns a list of products
        those users have available for rent within the specified start and
        end dates (inclusive).

    """

    available_products = []

    for user in users:
        if user.active:
            for product in user.products:
                if product.available and (product.avail_start_date <= start_date) and (product.avail_end_date >= end_date):
                    available_products.append(product)

    return available_products


def categorize_products(categories, products):
    """ Organizes products by categories.

        Takes in lists of Category and Product objects and returns dictionary of
        Products objects with category names as keys.

    """
    inventory = {}

    for category in categories:
        inventory[category.cat_name] = []

    for product in products:
        inventory[product.category.cat_name].append(product)

    return inventory


def calc_default_dates(deltadays):
    """ Calculates default dates to pre-populate the search area.

        Takes an integer and returns two datetimes and two strings:
            today: datetime of today
            future: datetime of today plus the number of days
            today_string': string version of 'today' in isoformat and of date
                       only ('yyyy-mm-dd')
            future_string: datetime object of future, isoformat and date only

    """
    dates = {}
    today = datetime.today()
    future = today + timedelta(days=deltadays)

    dates['today'] = today
    dates['future'] = future
    dates['today_string'] = today.date().isoformat()
    dates['future_string'] = future.date().isoformat()

    return dates


def convert_string_to_datetime(date_string):
    """ Converts the date supplied as a string on an HTML form into a datetime.

        Takes in date as string in format "yyyy-mm-dd" (e.g. "2015-11-04"
        for November 4, 2015) and returns datetime object.

    """

    date = datetime.strptime(date_string, "%Y-%m-%d")

    return date
