"""Happy Camper"""

from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
from model import connect_to_db, db, User, Region, Product, Tent, SleepingBag
from model import SleepingPad, BestUse, Brand, History, Category, Rating, Gender
from model import FillType, PadType
from make_update_helpers import make_user, check_brand, make_parent_product
from make_update_helpers import make_tent, make_sleeping_bag, make_sleeping_pad
from make_update_helpers import update_parent_product, update_tent
from make_update_helpers import update_sleeping_bag, update_sleeping_pad
from make_update_helpers import calc_avg_star_rating, reverse_merge_sort_histories
from make_update_helpers import format_phone_number
from search_helpers import search_radius, get_users_in_area, filter_products
from search_helpers import get_products_within_dates, categorize_products
from search_helpers import calc_default_dates, convert_string_to_datetime
import os

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ABC")
app.jinja_env.undefined = StrictUndefined


######################## User stuff ###################################
@app.route('/')
def index():
    """ Page shown when user not logged in. Gives user option to log in for
        create an account.
    """

    return render_template("signedout.html")


@app.route('/logout')
def handle_logout():
    """Processes user logout."""

    session.clear()
    return redirect('/')


@app.route('/handle-login', methods=['POST'])
def handle_login():
    """Processes user login."""

    username = request.form.get('email')
    password = request.form.get('password')

    # Try/except resource: http://docs.sqlalchemy.org/en/latest/orm/exceptions.html
    try:
        user = User.query.filter(User.email == username).one()
    except NoResultFound:
        flash("The email %s does not exist in our records. Please try again." % username)
        return redirect("/")

    if (user.active) and (user.password == password):
        session['user'] = username
        flash("Welcome! Logged in as %s" % username)
        return redirect('/success')
    else:
        flash("Login failed. Please try again.")
        return redirect('/')


@app.route('/create-account')
def create_account():
    """Create account form."""

    return render_template("create-account.html")


@app.route('/handle-create-account', methods=['POST'])
def handle_createaccount():
    """ Process create account form.

        Creates a User object using a function in make_update_helpers.
    """

    password = request.form.get('pword')
    confirm_pword = request.form.get('confirm_pword')

    if password != confirm_pword:
        flash("Passwords don't match. Try again.")
        return redirect('/create-account')
    else:
        user = make_user(password)

        db.session.add(user)
        db.session.commit()

        print "\n\n\n\n*********MADE A NEW USER: %r**********\n\n\n" % user.email

        session['user'] = user.email
        flash("Successfully created account! Logged in as %s" % user.email)

        return redirect('/success')


@app.route('/success')
def enter_site():
    """Page shown when user successfully logs in or creates an account."""

    customer = User.query.filter(User.email == session['user']).one()
    dates = calc_default_dates(7)

    categories = Category.query.all()
    brands = Brand.query.all()

    return render_template("success.html", user=customer,
                           today=dates['today_string'],
                           future=dates['future_string'],
                           product_categories=categories,
                           product_brands=brands)


@app.route('/account-info')
def show_account():
    """ Where users can check out their account details.

        This is where they manage their inventory, check our their rental history,
        and rate other users and products.
    """
    customer = User.query.filter(User.email == session['user']).one()

    # To display the state as a name, we need to get the name associated with
    # the region ID.
    state_id = customer.region_id
    st = Region.query.get(state_id).full

    # Put parens and a dash in the phone number to display.
    prettify_phone = format_phone_number(customer.phone)

    # Get today's date to bold stuff in tables based on how soon in the future
    # they are. We will bold two things: rental submissions for products within
    # this user's inventory within the last thirty days and (2) stuff that this
    # user is renting out within the next thirty days.
    today_date = datetime.today()
    last30 = today_date - timedelta(days=30)
    next30 = today_date + timedelta(days=30)

    # Get product inventory for this user, then split into those that are
    # currently available (and will show up in search results) and not
    # available (user has to actively relist if he or she wants it show up
    # in search results).
    products_all = Product.query.filter(Product.owner_user_id == customer.user_id).all()
    products_avail = []
    products_out = []

    product_history_lists = []
    product_histories = []

    # Separate inventory into those that are available and those that are not.
    for product in products_all:
        if product.histories:
            product_history_lists.append(product.histories)
        if product.available:
            products_avail.append(product)
        else:
            products_out.append(product)

    # Pull out individual histories from the list of histories associated with
    # each product.
    for history_list in product_history_lists:
        for history in history_list:
            product_histories.append(history)

    # Use merge sort helper function from make_update_helpers so can list
    # histories in descending order based on rental submission date. We want to
    # show the most recently requested rental first.
    if len(product_histories) > 1:
        desc_date_histories = reverse_merge_sort_histories(product_histories)
    else:
        desc_date_histories = product_histories

    # Moving on to user's history for renting stuff, get all the histories where
    # this user is the renter.
    rentals = History.query.filter(History.renter_user_id == customer.user_id).all()

    # Use the merge sort helper function to show the latest rental first.
    if len(rentals) > 1:
        desc_date_rentals = reverse_merge_sort_histories(rentals)
    else:
        desc_date_rentals = rentals

    return render_template("account-info.html", user=customer, state=st,
                           products_available=products_avail,
                           products_not_available=products_out,
                           desc_order_hist=desc_date_histories,
                           histories=desc_date_rentals, today=today_date, monthago=last30,
                           monthfromnow=next30, phonenum=prettify_phone)


@app.route('/confirm-deactivate-account')
def confirm_deactivate_account():
    """Confirms the user wants to deactivate account."""

    return render_template("confirm-deactivate-account.html")


@app.route('/handle-deactivate-account', methods=['POST'])
def deactivate_account():
    """ Deactivates user account.

        Sets availablility to each owner's product to false.
        Sets user active to false.
    """
    user = User.query.filter(User.email == session['user']).one()
    products = user.products

    for product in products:
        product.available = False

    user.active = False
    db.session.commit()
    session.clear()

    flash("Your account has been deactivated. Thank you for using Happy Camper!")

    return redirect('/')


######################## Listing stuff ###################################
@app.route('/list-product/<int:category_id>')
def list_product(category_id):
    """Shows listing forms for various categories."""

    # Get all brands in the database to show in the brand drop down.
    all_brands = Brand.query.all()
    # Pre-populate available dates.
    dates = calc_default_dates(30)

    templates = {1: 'list-tent.html',
                 2: 'list-sleeping-bag.html',
                 3: 'list-sleeping-pad.html',
                 }

    # If the user wants to list a tent, gets tent-specific spec requests.
    if category_id == 1:
        all_best_uses = BestUse.query.all()
        season_categories = {2: "2-season",
                             3: "3-season",
                             4: "4-season",
                             5: "5-season"}

        return render_template(templates[category_id],
                               brands=all_brands,
                               submit_route='/handle-listing/%d' % category_id,
                               p_today=dates['today_string'],
                               p_month=dates['future_string'],
                               best_uses=all_best_uses,
                               seasons=season_categories)
    # Similarly, if user wants to list a sleeping bag, get info needed to request
    # sleeping bag-specific specs.
    elif category_id == 2:
        all_fill_types = FillType.query.all()
        all_gender_types = Gender.query.all()

        return render_template(templates[category_id],
                               brands=all_brands,
                               submit_route='/handle-listing/%d' % category_id,
                               p_today=dates['today_string'],
                               p_month=dates['future_string'],
                               fill_types=all_fill_types,
                               genders=all_gender_types)

     # And same thing for sleeping pads. Get specific stuff like pad types to
     # show in the template's drop down.
    elif category_id == 3:
        all_pad_types = PadType.query.all()
        all_best_uses = BestUse.query.all()

        return render_template(templates[category_id],
                               brands=all_brands,
                               submit_route='/handle-listing/%d' % category_id,
                               p_today=dates['today_string'],
                               p_month=dates['future_string'],
                               pad_types=all_pad_types,
                               best_uses=all_best_uses)
    else:
        return "Not yet implemented"


@app.route('/handle-listing/<int:category_id>', methods=['POST'])
def handle_listing(category_id):
    """Handles rental listing. """

    # Check if new brand (value -1). If so, make new brand using a helper
    # fucntion from make_update_helpers and gets the brand_id so we can pass that
    # along to make the Product object.
    brand_num = int(request.form.get("brand_id"))
    brand_num = check_brand(brand_num)

    parent_product = make_parent_product(brand_id=brand_num, category_id=category_id)

    db.session.add(parent_product)
    db.session.commit()

    if category_id == 1:
        child_product = make_tent(parent_product.prod_id)
    elif category_id == 2:
        child_product = make_sleeping_bag(parent_product.prod_id)
    elif category_id == 3:
        child_product = make_sleeping_pad(parent_product.prod_id)
    else:
        pass

    db.session.add(child_product)
    db.session.commit()

    flash("Listing successfully posted!")
    return redirect('/product-detail/%d' % parent_product.prod_id)


###################### Editing stuff ################################
@app.route('/edit-listing/<int:prod_id>')
def edit_listing(prod_id):
    """Shows category-specific edit forms."""

    categories = {1: Tent.query.get(prod_id),
                  2: SleepingBag.query.get(prod_id),
                  3: SleepingPad.query.get(prod_id),
                  }

    templates = {1: 'edit-tent.html',
                 2: 'edit-sleeping-bag.html',
                 3: 'edit-sleeping-pad.html',
                 }

    parent_product = Product.query.get(prod_id)
    category_id = parent_product.cat_id
    child_product = categories[category_id]

    all_brands = Brand.query.all()

    if category_id == 1:
        all_best_uses = BestUse.query.all()
        season_categories = {2: "2-season",
                             3: "3-season",
                             4: "4-season",
                             5: "5-season"}

        return render_template(templates[category_id], parent=parent_product,
                               child=child_product, brands=all_brands,
                               best_uses=all_best_uses, seasons=season_categories)
    elif category_id == 2:
        all_fill_types = FillType.query.all()
        all_genders = Gender.query.all()

        return render_template(templates[category_id], parent=parent_product,
                               child=child_product, brands=all_brands,
                               fill_types=all_fill_types, genders=all_genders)
    elif category_id == 3:
        all_pad_types = PadType.query.all()
        all_best_uses = BestUse.query.all()

        return render_template(templates[category_id], parent=parent_product,
                               child=child_product, brands=all_brands,
                               pad_types=all_pad_types, best_uses=all_best_uses)

    else:
        return "Yet to be implemented."


@app.route('/handle-edit-listing/<int:prod_id>', methods=['POST'])
def handle_edit_listing(prod_id):
    """ Updates both the parent and subset objects based on the edit form
        submitted in the route above.
    """

    parent_product = Product.query.get(prod_id)
    category_id = parent_product.cat_id

    brand_num = int(request.form.get("brand_id"))
    brand_num = check_brand(brand_num)

    update_parent_product(prod_id=prod_id, brand_id=brand_num)

    if category_id == 1:
        update_tent(prod_id)
        flash("Your tent listing has been updated!")
    elif category_id == 2:
        update_sleeping_bag(prod_id)
        flash("Your sleeping bag listing has been updated!")
    elif category_id == 3:
        update_sleeping_pad(prod_id)
        flash("Your sleeping pad listing has been updated!")
    else:
        return "This is unimplemented"

    return redirect("/account-info")


######################## Searching stuff ###################################
@app.route('/search-results')
def show_results():
    """ Shows search results based on location and optional filters for
        category and brand. Uses geolocation-python libary, which uses the
        GoogleMaps API.

    """

    try:
        search_miles = int(request.args.get("search_miles"))
    except ValueError:
        flash("Search radius must be an integer. Please try again.")
        return redirect('/success')

    try:
        search_start_date = convert_string_to_datetime(request.args.get("search_start_date"))
    except ValueError:
        flash("Search dates must be formatted YYYY-mm-dd. Please try again.")
        return redirect('/success')

    try:
        search_end_date = convert_string_to_datetime(request.args.get("search_end_date"))
    except ValueError:
        flash("Search dates must be formatted YYYY-mm-dd. Please try again.")
        return redirect('/success')

    try:
        temp = int(request.args.get("search_area"))
    except ValueError:
        flash("Search center must be a postal code. Please try again.")
        return redirect('/success')

    search_area = request.args.get("search_area")
    category_id = int(request.args.get("category_id"))
    brand_id = int(request.args.get("brand_id"))

    # This is the number of rental days.
    days = (search_end_date - search_start_date).days + 1

    # Puts this search info into the session so we can refer to it in
    # future pages (the "return to your search results" link).
    session['search_start_date'] = search_start_date
    session['search_end_date'] = search_end_date
    session['num_days'] = days
    session['search_area'] = search_area
    session['search_radius'] = search_miles
    session['search_category_id'] = category_id
    session['search_brand_id'] = brand_id

    # Find distinct postal codes in the database.
    query = db.session.query(User.postalcode).distinct()
    postalcodes = query.all()

    # Get zipcodes in the database that are within the search radius.
    # This uses a helper function in search_helpers, which in turn uses
    # the geolocation-python library.
    # In future version of project, save these distance searches in the
    # database.
    postal_codes = search_radius(search_center=search_area,
                                 postalcodes=postalcodes, radius=search_miles)
    # We use list of zipcodes we get above and to then get users within in those
    # zipcodes. We remove the logged in user so we don't show his or her own
    # products.
    logged_in_user = User.query.filter(User.email == session['user']).one()
    users_in_area = get_users_in_area(postal_codes, logged_in_user.user_id)

    # From the list of users we get above, get products those users have listed
    # for rent and are currently available within the search dates.
    available_products = get_products_within_dates(start_date=search_start_date,
                                                   end_date=search_end_date,
                                                   users=users_in_area)
    # Filter out products based on optional category and brand filters.
    filtered_products = filter_products(available_products, category_id=category_id,
                                        brand_id=brand_id)
    # Get categories of interest. If the vale is -1, the user is interested in
    # all categories (can currently select only one or all.)
    if category_id < 0:
        search_categories = Category.query.all()
    else:
        search_categories = [Category.query.get(category_id)]

    # Make a dictionary of available products with categories as the keys of the
    # dictionary.
    products_by_category = categorize_products(categories=search_categories,
                                               products=filtered_products)

    # Create a list of sorted category names so we can display products by
    # category in some kind of consistent order.
    sorted_category_names = sorted(products_by_category.keys())

    # Get all categories and brands to show in the drop downs in the re-search
    # form on top of the search results page.
    all_categories = Category.query.all()
    all_brands = Brand.query.all()

    return render_template("search-results.html", location=search_area,
                           miles=search_miles,
                           search_categories=sorted_category_names,
                           products=products_by_category,
                           product_categories=all_categories,
                           product_brands=all_brands)


######################## Showing stuff ###################################
@app.route('/product-detail/<int:prod_id>')
def show_product(prod_id):
    """ Shows details for product when the user clicks on the image on the
        search results page.
    """
    # Use a different template based on category.
    categories = {1: Tent.query.get(prod_id),
                  2: SleepingBag.query.get(prod_id),
                  3: SleepingPad.query.get(prod_id),
                  }

    templates = {1: 'show-tent.html',
                 2: 'show-sleeping-bag.html',
                 3: 'show-sleeping-pad.html',
                 }

    parent_product = Product.query.get(prod_id)

    category_id = parent_product.cat_id

    child_product = categories[category_id]

    # We show different things if the user is the owner vs. not the owner.
    try:
        search_start_date = session['search_start_date']
    except KeyError:
        search_start_date = 0

    return render_template(templates[category_id], product=parent_product,
                           item=child_product, have_searched=search_start_date)


######################## Renting stuff ###################################
@app.route('/rent-confirm/<int:prod_id>', methods=['POST'])
def confirm_rental(prod_id):
    """Confirms the user really wants to rent the item."""

    prod = Product.query.get(prod_id)
    search_start_date_string = session['search_start_date'].date().isoformat()
    search_end_date_string = session['search_end_date'].date().isoformat()

    return render_template("rent-confirm.html", product=prod,
                           start_date_string=search_start_date_string,
                           end_date_string=search_end_date_string)


@app.route('/handle-rental/<int:prod_id>', methods=['POST'])
def handle_rental(prod_id):
    """ Processes a rental. Create associated History object and marks the
        product as unavailable so it doesn't show up in future search results
        until the owner actively relists it.

    """
    user = User.query.filter(User.email == session['user']).one()
    product = Product.query.get(prod_id)
    cost = product.price_per_day * session['num_days']

    history = History(prod_id=prod_id, renter_user_id=user.user_id,
                      start_date=session['search_start_date'],
                      end_date=session['search_end_date'],
                      total_cost=cost)

    product.available = False
    db.session.add(history)
    db.session.commit()

    flash("Rental finalized! Check your account page under \"Items Rented\" for info.")

    return redirect('/account-info')


######################## Rating stuff ###################################
@app.route('/show-owner-ratings/<int:user_id>')
def show_owner_ratings(user_id):
    """Shows owner star ratings and any comments."""

    owner = User.query.get(user_id)
    products = owner.products

    owner_ratings = []

    # Ratings are optional, so we have to check if there are any.
    for product in products:
        for history in product.histories:
            if history.owner_rating:
                owner_ratings.append(history.owner_rating)

    avg_star_rating = calc_avg_star_rating(owner_ratings)

    return render_template("show-owner-ratings.html", ratings=owner_ratings,
                           average=avg_star_rating, prod=product)


@app.route('/show-renter-ratings/<int:renter_id>')
def show_renter_ratings(renter_id):
    """Shows renter star ratings and any comments."""

    histories = History.query.filter(History.renter_user_id == renter_id).all()
    renter = User.query.get(renter_id)

    renter_ratings = []

    for history in histories:
        if history.renter_rating:
            renter_ratings.append(history.renter_rating)

    avg_star_rating = calc_avg_star_rating(renter_ratings)

    return render_template("show-renter-ratings.html", ratings=renter_ratings,
                           average=avg_star_rating, user=renter)


@app.route('/show-product-ratings/<int:prod_id>')
def show_product_ratings(prod_id):
    """Shows product star ratings and any comments."""

    item = Product.query.get(prod_id)
    histories = History.query.filter(History.prod_id == prod_id).all()

    product_ratings = []

    for history in histories:
        if history.product_rating:
            product_ratings.append(history.product_rating)

    avg_star_rating = calc_avg_star_rating(product_ratings)

    return render_template("show-product-ratings.html", ratings=product_ratings,
                           average=avg_star_rating, product=item)


@app.route('/rate-user-modal/<int:user_id>-<int:history_id>-<int:owner_is_true>')
def rate_user(user_id, history_id, owner_is_true):
    """ External HTML for modal that pops up to rate other users.

        The owner_is_true variable is used to determine if we want to show the
        modal to rate an owner or a renter. Value 0 is renter, 1 is owner.
    """

    # Show different star rating text based  on if the rating is for an owner or
    # a renter.
    star_categories = [{1: "1: Awful. Would not rent to this person again.",
                        2: "2: Worse than expected, but not awful. Might rent to this person again.",
                        3: "3: As expected. Would rent to this person again.",
                        4: "4: Awesome! Would be happy to rent to this person again."
                        },

                       {1: "1: Awful. Would not rent from this person again.",
                        2: "2: Not as good as expected, but might rent from again.",
                        3: "3: As expected. Would rent from again.",
                        4: "4: Awesome! Would rent from again.",
                        }]

    # Sort the star ratings so the most positive rating (value 4) is on top.
    star_keys_reversed = sorted(star_categories[0].keys(), reverse=True)

    user_to_rate = User.query.get(user_id)

    return render_template("rate-user-modal.html",
                           user=user_to_rate,
                           submit_route='/handle-user-rating',
                           star_ratings=star_categories[owner_is_true],
                           star_values=star_keys_reversed,
                           is_owner=owner_is_true,
                           hist_num=history_id)


@app.route('/handle-user-rating', methods=['POST'])
def handle_owner_rating():
    """ Handles owner rating form submission.
        This is submitted to the database via ajax.
    """

    number_stars = int(request.form.get("num_stars"))
    comments_text = request.form.get("comments")
    # 0 means rating is for renter, 1 means rating is for owner.
    is_owner = int(request.form.get("is_owner"))
    history_id = int(request.form.get("hist_id"))

    rating = Rating(stars=number_stars, comments=comments_text)

    db.session.add(rating)
    db.session.commit()

    history = History.query.get(history_id)

    if is_owner:
        history.owner_rating_id = rating.rating_id
    else:
        history.renter_rating_id = rating.rating_id

    db.session.commit()

    # The form stays on the account-info page, so user does not see below.
    return "History id=%d, Rating id=%d" % (history_id, rating.rating_id)


@app.route('/rate-product-modal/<int:prod_id>-<int:history_id>')
def rate_product(prod_id, history_id):
    """External HTML for modal popup to rate product."""

    star_rating_categories = {1: '1: Awful. Would not rent again',
                              2: '2: Not as good as expected, but might rent again if in a pinch.',
                              3: '3: As expected. Would not mind renting again if needed.',
                              4: '4: Great! Even better than expected. Would be happy to rent again if needed.',
                              }

    item = Product.query.get(prod_id)
    star_keys_reversed = sorted(star_rating_categories.keys(), reverse=True)

    return render_template("rate-product-modal.html",
                           product=item,
                           star_ratings=star_rating_categories,
                           submit_route='/handle-product-rating',
                           star_values=star_keys_reversed,
                           hist_num=history_id)


@app.route('/handle-product-rating', methods=['POST'])
def handle_product_rating():
    """ Handles product rating form submission.

        Like the user ratings, database is updated via ajax so the user stays on
        the account-info page.

    """

    history_id = int(request.form.get("hist_id"))
    number_stars = int(request.form.get("num_stars"))
    comments_text = request.form.get("comments")

    product_rating = Rating(stars=number_stars, comments=comments_text)
    db.session.add(product_rating)
    db.session.commit()

    history = History.query.get(history_id)
    history.prod_rating_id = product_rating.rating_id

    db.session.commit()

    return "Product rating id=%d submitted for history_id=%d" % (
                                          product_rating.rating_id, history_id)


######################## Delisting stuff ###################################
@app.route('/confirm-delist-product/<int:prod_id>')
def confirm_delist_product(prod_id):
    """Confirms the user wants to delist product."""

    item = Product.query.get(prod_id)

    return render_template("confirm-delist-product.html", product=item)


@app.route('/handle-delist-product', methods=['POST'])
def delist_product():
    """ Delists product. Marks as unavailable so it doesn't show up in search_start_date
        results.
    """

    prod_id = int(request.form.get("prod_id"))
    product = Product.query.get(prod_id)
    product.available = False
    db.session.commit()

    flash("This product has been delisted.")

    return redirect('/account-info')


######################################################################
if __name__ == "__main__":

    connect_to_db(app, os.environ.get("DATABASE_URL"))

    db.create_all(app=app)

    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
