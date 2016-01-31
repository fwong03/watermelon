# Models and database for Happy Camper Hackbright project.
# Version 2:January 7, 2015

from flask_sqlalchemy import SQLAlchemy
import datetime
import os

db = SQLAlchemy()

##############################################################


class Region(db.Model):
    """Regions (i.e., states) for user addresses."""

    __tablename__ = "regions"

    region_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    abbr = db.Column(db.String(2), nullable=False, unique=True)
    full = db.Column(db.String(16), nullable=False, unique=True)

    user = db.relationship('User', backref='region')

    def __repr__(self):
        return "<Region region_id=%d, abbreviation=%s, fullname=%s>" % (
            self.region_id, self.abbr, self.full)


class User(db.Model):
    """Happy Camper user"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # User has option to deactivate account (mentor Bert rec).
    active = db.Column(db.Boolean, default=True)
    fname = db.Column(db.String(32), nullable=False)
    lname = db.Column(db.String(32), nullable=False)
    street = db.Column(db.String(32), nullable=False)
    city = db.Column(db.String(32), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.region_id'),
                          nullable=False)
    # Make postal code a string since it may start with zero (e.g. '02139')
    postalcode = db.Column(db.String(10), nullable=False)
    # Change from v1: make phone a string. Otherwise use BigInteger? When
    # converted to Postgresql, phone numbers were larger than int4
    phone = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(32), nullable=False)
    profile_pic_url = db.Column(db.String(128))

    # Make a backref so we can easily access the renter associated with a
    # rental history.
    renter = db.relationship('History', backref='renter')

    def __repr__(self):

        return "<User user_id=%d, name=%s %s, postalcode=%s, email=%s>" % (
            self.user_id, self.fname, self.lname, self.postalcode, self.email)


class Category(db.Model):
    """Product categories used to specify product subset table"""

    __tablename__ = 'categories'

    cat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cat_name = db.Column(db.String(16), nullable=False, unique=True)

    def __repr__(self):

        return "<Category cat_id=%d, cat_name=%s>" % (self.cat_id, self.cat_name)


class BestUse(db.Model):
    """Best uses for tents and sleeping pads."""

    __tablename__ = "bestuses"

    use_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    use_name = db.Column(db.String(16), nullable=False, unique=True)

    tent = db.relationship('Tent', backref='bestuse')
    sleepingpad = db.relationship('SleepingPad', backref='bestuse')

    def __repr__(self):
        return "<BestUse use_id=%d, use_name=%s>" % (self.use_id, self.use_name)


class Brand(db.Model):
    """ Brands.

        Make a separate brand table (per mentor Bert rec) to give ourselves
        the flexiblity to change how these are displayed later on.
    """

    __tablename__ = "brands"

    brand_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    brand_name = db.Column(db.String(64), nullable=False, unique=True)

    def __repr__(self):
        return "<Brand brand_id=%d, brand_name=%s>" % (self.brand_id, self.brand_name)


class Product(db.Model):
    """Product parent class."""

    __tablename__ = 'products'

    prod_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cat_id = db.Column(db.Integer, db.ForeignKey('categories.cat_id'),
                       nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.brand_id'),
                         nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                              nullable=False)

    # We use the available boolean to change the status to "unavailable" if
    # the item is rented out or the owner delists it (mentor Bert rec).
    available = db.Column(db.Boolean, default=True)
    model = db.Column(db.String(64), nullable=False)
    condition = db.Column(db.String(356))
    description = db.Column(db.String(384))
    avail_start_date = db.Column(db.DateTime, nullable=False)
    avail_end_date = db.Column(db.DateTime, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)

    # Do image url now since image upload sounds like it will take a while to
    # figure out.
    image_url = db.Column(db.String(128))

    # Put subset table backrefs here so we can easily access parent product info
    # while on a subset object.
    tent = db.relationship('Tent', uselist=False, backref='product')
    sleepingbag = db.relationship('SleepingBag', uselist=False, backref='product')
    sleepingpad = db.relationship('SleepingPad', uselist=False, backref='product')

    # Other backrefs. We want to be able to see which products an user has
    # available for rent, which products we have of a certain brand or
    # category, and the product associated with a history.
    owner = db.relationship('User', backref='products')
    brand = db.relationship('Brand', backref='products')
    category = db.relationship('Category', backref='products')
    histories = db.relationship('History', backref='product')

    def __repr__(self):
        return "<Product prod_id=%d, cat_id=%d, owner_id=%d, brand_id: %d, model=%s, description=%s, condition=%s, avail=%r to %r, price=%r>" % (
            self.prod_id, self.cat_id, self.owner_user_id, self.brand_id, self.model,
            self.description, self.condition, self.avail_start_date, self.avail_end_date, self.price_per_day)


class Tent(db.Model):
    """Tent is one of the subset tables of Product."""

    __tablename__ = 'tents'

    prod_id = db.Column(db.Integer, db.ForeignKey('products.prod_id'),
                        primary_key=True)
    use_id = db.Column(db.Integer, db.ForeignKey('bestuses.use_id'),
                       nullable=False)
    sleep_capacity = db.Column(db.Integer, nullable=False)
    seasons = db.Column(db.Integer, nullable=False)
    min_trail_weight = db.Column(db.Integer, nullable=False)
    # These are optional
    floor_width = db.Column(db.Integer)
    floor_length = db.Column(db.Integer)
    num_doors = db.Column(db.Integer)
    num_poles = db.Column(db.Integer)

    def __repr__(self):
        return "<Tent prod_id=%d, use_id=%d, capacity=%d, seasons=%d, weight=%d, length=%r, width=%r, num_doors=%r, num_poles=%r>" % (
            self.prod_id, self.use_id, self.sleep_capacity,
            self.seasons, self.min_trail_weight, self.floor_width,
            self.floor_length, self.num_doors, self.num_poles)


class FillType(db.Model):
    """Fill types for sleeping bags."""

    __tablename__ = 'filltypes'

    fill_code = db.Column(db.String(1), primary_key=True)
    fill_name = db.Column(db.String(16), unique=True)

    sleepingbag = db.relationship('SleepingBag', backref='filltype')


class Gender(db.Model):
    """Pull gender out so future tables can reference and have option to easily
    find all women's stuff.

    """
    __tablename__ = 'genders'

    gender_code = db.Column(db.String(1), primary_key=True)
    gender_name = db.Column(db.String(8), nullable=False, unique=True)

    sleepingbag = db.relationship('SleepingBag', backref='gender')

    def __repr__(self):
        return "<Gender gender_code=%s gender_name=%s>" % (self.gender_code,
                                                           self.gender_name)


class SleepingBag(db.Model):
    """Sleeping bags is one of the subset tables of Product"""

    __tablename__ = 'sleepingbags'

    prod_id = db.Column(db.Integer, db.ForeignKey('products.prod_id'),
                        primary_key=True)
    fill_code = db.Column(db.String(1), db.ForeignKey('filltypes.fill_code'),
                          nullable=False)
    temp_rating = db.Column(db.Integer, nullable=False)

    # These are optional.
    weight = db.Column(db.Integer)
    length = db.Column(db.Integer)
    gender_code = db.Column(db.String(1), db.ForeignKey('genders.gender_code'))

    def __repr__(self):
        return "<Sleeping Bag prod_id=%d, fill_code=%s, temp_rating=%d, weight=%d, length=%d, gender=%s>" % (
            self.prod_id, self.fill_code, self.temp_rating, self.weight,
            self.length, self.gender_code)


class PadType(db.Model):
    """Pad types for sleeping pads."""

    __tablename__ = 'padtypes'

    pad_type_code = db.Column(db.String(1), primary_key=True)
    pad_type_name = db.Column(db.String(16), unique=True)

    sleepingpad = db.relationship('SleepingPad', backref='padtype')


class SleepingPad(db.Model):
    """Sleeping pads is one of the subset tables of Product"""

    __tablename__ = 'sleepingpads'

    prod_id = db.Column(db.Integer, db.ForeignKey('products.prod_id'),
                        primary_key=True)
    type_code = db.Column(db.String(1), db.ForeignKey('padtypes.pad_type_code'),
                          nullable=False)
    use_id = db.Column(db.Integer, db.ForeignKey('bestuses.use_id'),
                       nullable=False)
    r_value = db.Column(db.Float, nullable=False)
    length = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer)
    # Optional.
    width = db.Column(db.Integer)

    def __repr__(self):
        return "<Sleeping Pad prod_id=%d, type_code=%s, bestuse_id=%d, r-value=%r, length=%d, weight=%d, width=%r>" % (
            self.prod_id, self.type_code, self.use_id, self.r_value,
            self.length, self.weight, self.width)


class History(db.Model):
    """Rental histories"""

    __tablename__ = 'histories'

    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prod_id = db.Column(db.Integer, db.ForeignKey('products.prod_id'),
                        nullable=False)
    renter_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                               nullable=False)
    rental_submission_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

    # Ratings are optional
    owner_rating_id = db.Column(db.Integer, db.ForeignKey('ratings.rating_id'))
    renter_rating_id = db.Column(db.Integer, db.ForeignKey('ratings.rating_id'))
    prod_rating_id = db.Column(db.Integer, db.ForeignKey('ratings.rating_id'))

    # Took a while to figure out how to be on a rating and find the associated product
    # without annoyingly long queries.
    # I used this so I can show owner and renter ratings across all products they've
    # rented or rented out.
    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    owner_rating = db.relationship('Rating', foreign_keys='History.owner_rating_id',
                                   backref='ohistory',
                                   order_by=rental_submission_date.desc())
    renter_rating = db.relationship('Rating', foreign_keys='History.renter_rating_id',
                                    backref='rhistory',
                                    order_by=rental_submission_date.desc())
    # Didn't use below but I put it in just in case.
    product_rating = db.relationship('Rating', foreign_keys='History.prod_rating_id',
                                     backref='phistory',
                                     order_by=rental_submission_date.desc())

    def __repr__(self):
        return "<History history_id=%d, prod_id=%d, rental_submit_date= %r, renter_user_id=%r, owner_rating_id=%r, renter_rating_id=%r, prod_rating_id=%r>" % (
            self.history_id, self.prod_id, self.rental_submission_date, self.renter_user_id,
            self.owner_rating_id, self.renter_rating_id, self.prod_rating_id)


class Rating(db.Model):
    """Renters can rate owners and products, owners can rate renters."""

    __tablename__ = 'ratings'

    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stars = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.String(128))

    def __repr__(self):
        return "<Rating rating_id=%d, stars=%d, comments=%s>" % (self.rating_id,
                                                                 self.stars,
                                                                 self.comments)


class PostalCode(db.Model):
    """To store lats and longs of zip codes.
        Source: http://www.opengeocode.org/download.php#cityzip
        Make postalcode an integer to make search faster
    """

    __tablename__ = 'postalcodes'

    postalcode_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    postalcode = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return "<Postalcode postalcode_id=%d, postalcode=%d, latitude=%f, longitude=%f>" % (
                                                                                self.postalcode_id,
                                                                                self.postalcode,
                                                                                self.latitude,
                                                                                self.longitude)
    

##############################################################################

def connect_to_db(app, db_uri=None):
    """Connect the database to our Flask app."""

    postgrespassword = os.environ['POSTGRES_PASSWORD']

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'postgresql://%s/happycamper' % postgrespassword
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # This allows direct database interaction if this module is run interactively.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
