from model import User, PostalCode, db
from datetime import datetime, timedelta
from geolocation.google_maps import GoogleMaps
from geolocation.distance_matrix import const
from make_update_helpers import make_postalcode
from sqlalchemy.orm.exc import NoResultFound
import os
import math

""" Helper functions for server.py search-related routes.
     Seven function total.
"""


def calc_Haversine_distance(lat1, lng1, lat2, lng2):
    """ Uses the Haversine formual to calculate the distance in miles between two
        pairs of lat and longs.

    """

############# TODO: MAKE TEST CHECKING DISTANCES ##############################
    radius_of_earth_miles = 3960
    # radius_of_earth_km = 6373

    convert_to_radians = math.pi / 180

    d_lat = convert_to_radians * (lat2 - lat1)
    d_lon = convert_to_radians * (lng2 - lng1)
    lat1_radians = convert_to_radians * lat1
    lat2_radians = convert_to_radians * lat2

    a = math.sin(d_lat / 2)**2 + (math.cos(lat1_radians) * math.cos(lat2_radians) * math.sin(d_lon / 2)**2)
    c = 2 * math.asin(math.sqrt(a))

    d = radius_of_earth_miles * c

    return d


def search_radius(search_center_string, postalcodes, radius):
    """ Finds zipcodes in the database that are within a search radius of a
        location.

        This uses the python library geolocation-python, which uses the
        GoogleMaps API.

        Takes in search center as a string, postalcodes as a list of tuples
        (because that is the format returned from the database), and search
        radius in miles as an integer. The function returns the list of
        postal codes in the given list that are within the given radius.

    """

    search_center_int = int(search_center_string)

    # Check if zipcode is in database. If not, get lat and long from
    # GoogleMaps and add it to the database.

############# TODO: MAKE TEST WHEN ZIPCODE IN DB AND ZIPCODE NOT IN DB #####
    try:
        search_center_obj = PostalCode.query.get(search_center_int)
    except NoResultFound:
        make_postalcode(search_center_string)
        search_center_obj = PostalCode.query.get(search_center_int)


    # SQLite returns the distinct postal codes as a list of tuples. Convert this
    # to a list of postal code strings.
    postalcodes_in_db = []

    for postalcode in postalcodes:
        postalcodes_in_db.append(postalcode[0])

    postalcodes_within_radius = []
    lat1 = search_center_obj.latitude
    lng1 = search_center_obj.longitude

    for postalcode in postalcodes_in_db:
        location = PostalCode.query.get(int(postalcode))
        lat2 = location.latitude
        lng2 = location.longitude

        distance = calc_Haversine_distance(lat1, lng1, lat2, lng2)

        if distance <= radius:
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
