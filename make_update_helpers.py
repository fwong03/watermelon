from flask import request, session
from model import User, Region, Brand, Product, Tent
from model import SleepingBag, SleepingPad
from model import db
from datetime import datetime

""" Helper functions used in server.py to make and update products and users.
    Fifteen functions total.

    Also threw in two non-making or updating functions at the end:
    (1) a merge sort helper function to display rental histories in descending
        order based on rental submission date, and
    (2) a formatting function for phone numbers so phone numbers display as
        (xxx) xxx-xxxx on the user's account-info page.

"""


######################## User stuff ###################################
def make_user(password):
    """ Creates User object when a user creates a new account.

        Takes in a password as a string, grabs info from the create account
        form, and returns a User object.

    """

    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    staddress = request.form.get('staddress')
    cty = request.form.get('cty')
    state = request.form.get('state')
    zipcode = request.form.get('zipcode')
    # Change from v1: phone number is a string (used to be integer)
    phonenumber = request.form.get('phonenumber')
    username = request.form.get('username')
    profile_url = request.form.get('profile_url')

    # Get region id from the Regions table
    region = Region.query.filter(Region.abbr == state).one()
    state_id = region.region_id

    if not profile_url:
        profile_url = "static/img/defaultimg.jpg"

    user = User(fname=firstname, lname=lastname, street=staddress,
                city=cty, region_id=state_id, postalcode=zipcode,
                phone=phonenumber, email=username, password=password,
                profile_pic_url=profile_url)

    return user


######################## Listing stuff ###################################
def check_brand(brand_id):
    """ When a user lists an item, we first check if the brand of the item already
        exists in the database. If not, we create it and add it to the
        database's Brands table.

        Takes integer brand_id (which will be -1 if it is a new brand),
        and returns integer brand_id (which, for a new brand, will be the
        brand_id for the newly created Brand object).

    """

    if brand_id < 0:
        new_brand_name = request.form.get("new_brand_name")
        brand = Brand(brand_name=new_brand_name)
        db.session.add(brand)
        db.session.commit()
        brand_id = brand.brand_id

    return brand_id


def make_brand(brandname):
    """ Adds a new brand to the database. This is called by the check_brand
        function above if a new brand needs to be added to the database.
    """

    brand = Brand(brand_name=brandname)

    db.session.add(brand)
    db.session.commit()


def get_brand_id(brandname):
    """Takes brand name as a string and returns brand_id as an integer."""

    brand = Brand.query.filter(Brand.brand_name == brandname).one()
    return brand.brand_id


def make_parent_product(brand_id, category_id):
    """ When a user lists an item, we first make a parent Product object.

        Takes two integers, brand_id and category_id, grabs info from the
        listing form, and returns a Product object.

    """

    modelname = request.form.get("modelname")
    desc = request.form.get("desc")
    cond = request.form.get("cond")
    avail_start = request.form.get("avail_start")
    avail_end = request.form.get("avail_end")
    pricing = float(request.form.get("pricing"))
    image = request.form.get("image")

    if not image:
        image = "static/img/defaultimg.jpg"

    avail_start = datetime.strptime(avail_start, "%Y-%m-%d")
    avail_end = datetime.strptime(avail_end, "%Y-%m-%d")

    user = User.query.filter(User.email == session['user']).one()

    product = Product(cat_id=category_id, brand_id=brand_id,
                      owner_user_id=user.user_id, model=modelname,
                      description=desc, condition=cond,
                      avail_start_date=avail_start, avail_end_date=avail_end,
                      price_per_day=pricing, image_url=image)

    return product


def make_tent(product_id):
    """ Makes a subset Tent object given the corresponding parent Product
        prod_id primary key.

        Takes in prod_id as an integer, grabs info from the list-tent form,
        and returns a Tent object.
    """

    best_use_id = int(request.form.get("bestuse"))
    sleep = int(request.form.get("sleep"))
    seasoncat = int(request.form.get("seasoncat"))
    weight = int(request.form.get("weight"))

    # Deal with optional values.
    try:
        width = int(request.form.get("width"))
    except ValueError:
        width = None
    try:
        length = int(request.form.get("length"))
    except ValueError:
        length = None
    try:
        doors = int(request.form.get("doors"))
    except ValueError:
        doors = None
    try:
        poles = int(request.form.get("poles"))
    except ValueError:
        poles = None

    tent = Tent(prod_id=product_id, use_id=best_use_id,
                sleep_capacity=sleep, seasons=seasoncat, min_trail_weight=weight,
                floor_width=width, floor_length=length, num_doors=doors,
                num_poles=poles)

    return tent


def make_sleeping_bag(product_id):
    """ Makes a subset SleepingBag object given the corresponding parent Product
        prod_id primary key.

        Takes in prod_id as an integer, grabs info from the list-sleepingbag
        form, and returns a SleepingBag object.
    """

    filltype = request.form.get("filltype")
    temp = int(request.form.get("temp"))
    bag_weight = int(request.form.get("bag_weight"))

    # Deal with optional values.
    try:
        length = int(request.form.get("length"))
    except ValueError:
        length = None
    try:
        gender = request.form.get("gender")
    except ValueError:
        gender = None

    sleeping_bag = SleepingBag(prod_id=product_id, fill_code=filltype,
                               temp_rating=temp, weight=bag_weight, length=length,
                               gender_code=gender)

    return sleeping_bag


def make_sleeping_pad(product_id):
    """ Makes a subset SleepingPad object given the corresponding parent Product
        prod_id primary key.

        Takes in prod_id as an integer, grabs info from the list-sleepingpad
        form, and returns a SleepingPad object.
    """

    padtype = request.form.get("padtype")
    best_use_id = int(request.form.get("bestuse"))
    r_val = float(request.form.get("r_val"))
    pad_weight = int(request.form.get("pad_weight"))
    pad_length = int(request.form.get("pad_length"))

    # Deal with optional values.
    try:
        pad_width = int(request.form.get("pad_length"))
    except ValueError:
        pad_width = None

    sleeping_pad = SleepingPad(prod_id=product_id, type_code=padtype,
                               use_id=best_use_id, r_value=r_val,
                               weight=pad_weight,
                               length=pad_length, width=pad_width)

    return sleeping_pad


###################### Editing stuff ################################
def update_parent_product(prod_id, brand_id):
    """ Updates parent Product attributes.

        Takes integers brand_id and category_id, and uses info from the edit form
        to update the parent Product.
    """

    product = Product.query.get(prod_id)

    product.available = True
    product.brand_id = brand_id
    product.model = request.form.get("modelname")
    product.description = request.form.get("desc")
    product.condition = request.form.get("cond")
    product.price_per_day = float(request.form.get("pricing"))
    product.image_url = request.form.get("image")

    avail_start = request.form.get("avail_start")
    avail_end = request.form.get("avail_end")

    avail_start = datetime.strptime(avail_start, "%Y-%m-%d")
    avail_end = datetime.strptime(avail_end, "%Y-%m-%d")

    product.avail_start_date = avail_start
    product.avail_end_end = avail_end

    db.session.commit()

    return


def update_tent(prod_id):
    """ Updates tent object with the given prod_id.

        Grabs info from the category-specific area of the edit item form.
    """

    tent = Tent.query.get(prod_id)

    tent.use_id = int(request.form.get("bestuse"))
    tent.sleep_capacity = int(request.form.get("sleep"))
    tent.seasons = int(request.form.get("seasoncat"))
    tent.min_trail_weight = int(request.form.get("weight"))

    # Deal with optional values.
    try:
        tent.floor_width = int(request.form.get("width"))
    except ValueError:
        tent.floor_width = None

    try:
        tent.floor_length = int(request.form.get("length"))
    except ValueError:
        tent.floor_length = None

    try:
        tent.num_doors = int(request.form.get("doors"))
    except ValueError:
        tent.num_doors = None

    try:
        tent.num_poles = int(request.form.get("poles"))
    except ValueError:
        tent.num_poles = None

    db.session.commit()

    return


def update_sleeping_bag(prod_id):
    """ Updates sleeping bag object of given prod_id.

        Grabs info from the category-specific area of the edit item form.
    """

    sleeping_bag = SleepingBag.query.get(prod_id)

    sleeping_bag.fill_code = request.form.get("filltype")
    sleeping_bag.temp_rating = int(request.form.get("temp"))

    # Deal with optional values.
    try:
        sleeping_bag.weight = int(request.form.get("bag_weight"))
    except ValueError:
        sleeping_bag.weight = None

    try:
        sleeping_bag.length = int(request.form.get("length"))
    except ValueError:
        sleeping_bag.length = None

    gender = request.form.get("gender")

    if gender == "Z":
        sleeping_bag.gender_code = None
    else:
        sleeping_bag.gender_code = gender

    db.session.commit()

    return


def update_sleeping_pad(prod_id):
    """ Updates sleeping pad object of given prod_id.

        Grabs info from the category-specific area of the edit item form.
    """

    sleeping_pad = SleepingPad.query.get(prod_id)

    sleeping_pad.type_code = request.form.get("padtype")
    sleeping_pad.use_id = int(request.form.get("bestuse"))
    sleeping_pad.r_value = float(request.form.get("r_val"))
    sleeping_pad.weight = int(request.form.get("pad_weight"))
    sleeping_pad.length = int(request.form.get("pad_length"))

    # Deal with optional values.
    try:
        sleeping_pad.width = int(request.form.get("pad_width"))
    except ValueError:
        sleeping_pad.width = None

    db.session.commit()

    return


# These are not related to making or updating objects. Just threw them in here
# so I wouldn't have another helper function file.
def calc_avg_star_rating(ratings):
    """ Calculates average star rating to one decimal point to display one
        show-user and show-product-ratings templates.

        Takes a list of ratings and returns average star rating as a
        float. If no star ratings, returns -1.

    """
    avg_star_rating = -1

    if ratings:
        sum_stars = 0
        count_star_ratings = 0

        for rating in ratings:
            if rating.stars:
                sum_stars += rating.stars
                count_star_ratings += 1

        avg_star_rating = float(sum_stars) / count_star_ratings

    return avg_star_rating


def reverse_merge_sort_histories(lst):
    """ Sorts histories in descending order based on rental_sumbission_date
        for display on a user's acount-info page.

        Takes in list of product histories and returns a list of sorted histories.
    """

    if len(lst) > 1:
        midpt = int(len(lst) / 2)
        lst1 = lst[:midpt]
        lst2 = lst[midpt:]

        # Recursively split the lists in half. Degenerate case is list of
        # single items.
        reverse_merge_sort_histories(lst1)
        reverse_merge_sort_histories(lst2)

        # Function will continue here when the recrusive splits complete.
        lst1_index = 0
        lst2_index = 0
        # Use below to write over the list passed in as a parameter.
        ordered_lst_index = 0

        # Loop through histories in each of the lists and compare which has a later
        # rental sumbission date. The history with the later rental submission
        # date is added first.
        while lst1_index < len(lst1) and lst2_index < len(lst2):

            if lst1[lst1_index].rental_submission_date > lst2[lst2_index].rental_submission_date:
                lst[ordered_lst_index] = lst1[lst1_index]
                lst1_index += 1
            else:
                lst[ordered_lst_index] = lst2[lst2_index]
                lst2_index += 1

            ordered_lst_index += 1

        # If one list is longer than the other, we add all its histories to
        # the end of the list.
        while lst1_index < len(lst1):
            lst[ordered_lst_index] = lst1[lst1_index]
            ordered_lst_index += 1
            lst1_index += 1

        while lst2_index < len(lst2):
            lst[ordered_lst_index] = lst2[lst2_index]
            ordered_lst_index += 1
            lst2_index += 1

        return lst


def format_phone_number(phonenumber):
    """ Formats phone number in (xxx) xxx-xxxx format.

        Takes in string and returns string.

        Note (Jan 7): had this in here in v1 because was storing
        phone number as an integer. Now storing as a string,
        so potentially can add to database in the "prettified"
        format. But leave for now.
    """

    pretty_phone_num = "("

    for idx in range(0, 3):
        pretty_phone_num += phonenumber[idx]

    pretty_phone_num += ") "

    for idx in range(3, 6):
        pretty_phone_num += phonenumber[idx]

    pretty_phone_num += "-"

    for idx in range(6, 10):
        pretty_phone_num += phonenumber[idx]

    return pretty_phone_num
