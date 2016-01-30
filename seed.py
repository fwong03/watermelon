from model import Region, User, BestUse, Category, Brand, Product, Tent
from model import FillType, Gender, SleepingBag, PadType, SleepingPad
from model import History, Rating
from model import connect_to_db, db
from server import app
from datetime import datetime
import os


def load_regions():
    """Load regions, i.e. states, for user addresses"""

    print "Regions"
    Region.query.delete()

    for row in open("data/regionsdata"):
        row = row.strip()
        abbr, full = row.split("|")

        a = Region(abbr=abbr, full=full)

        db.session.add(a)

    db.session.commit()


def load_users():
    """Load user data"""

    print "Users"
    User.query.delete()

    for row in open("data/customerdata"):
        row = row.strip()
        row = row.split("|")

        firstn = row[0]
        lastn = row[1]
        staddress = row[2]
        cty = row[3]
        region = row[4]
        zcode = row[5]
        # Jan 7: phone now stored as string, not integer
        phn = row[6]
        login = row[7]
        pword = row[8]
        pic = row[9]

        a = User(fname=firstn, lname=lastn, street=staddress,
                 city=cty, region_id=region, postalcode=zcode, phone=phn,
                 email=login, password=pword, profile_pic_url=pic)

        db.session.add(a)

    db.session.commit()


def load_bestuses():
    """Load best use categories"""

    print "BestUses"
    BestUse.query.delete()

    for row in open("data/bestusesdata"):
        use = row.strip()

        a = BestUse(use_name=use)

        db.session.add(a)

    db.session.commit()


def load_categories():
    """Load product categories"""

    print "Categories"
    Category.query.delete()

    for row in open("data/categoriesdata"):
        name = row.strip()

        a = Category(cat_name=name)

        db.session.add(a)

    db.session.commit()


def load_brands():
    """Load brand names"""

    print "Brands"
    Brand.query.delete()

    for row in open("data/brandsdata"):
        name = row.strip()

        a = Brand(brand_name=name)

        db.session.add(a)

    db.session.commit()


def load_products():
    """Load products data"""

    print "Products"
    Product.query.delete()

    for row in open("data/productsdata"):
        row = row.strip()
        row = row.split("|")

        print row

        category = row[0]
        brand = int(row[1])
        owner = row[2]
        mname = row[3]
        con = row[4]
        desc = row[5]
        date1 = row[6]
        date2 = row[7]
        dollarz = float(row[8])
        image = row[9]
        avail = row[10]

        date1 = datetime.strptime(date1, "%Y-%m-%d")
        date2 = datetime.strptime(date2, "%Y-%m-%d")

        a = Product(cat_id=category, brand_id=brand, owner_user_id=owner,
                    model=mname, condition=con, description=desc,
                    avail_start_date=date1, avail_end_date=date2,
                    price_per_day=dollarz, image_url=image, available=avail)

        db.session.add(a)

    db.session.commit()


def load_tents():
    """Load tents data"""

    print "Tents"
    Tent.query.delete()

    for row in open("data/tentsdata"):
        row = row.strip()
        row = row.split("|")

        product = int(row[0])
        use = int(row[1])
        capacity = int(row[2])
        num_sea = int(row[3])
        weight = int(row[4])
        width = int(row[5])
        length = int(row[6])
        doors = int(row[7])
        poles = int(row[8])

        a = Tent(prod_id=product, use_id=use, sleep_capacity=capacity,
                 seasons=num_sea, min_trail_weight=weight, floor_width=width,
                 floor_length=length, num_doors=doors, num_poles=poles)

        db.session.add(a)

    db.session.commit()


def load_filltypes():
    """Load sleeping bag fill types"""

    print "Fill Types"
    FillType.query.delete()

    for row in open("data/filltypesdata"):
        row = row.strip()
        code, name = row.split("|")

        a = FillType(fill_code=code, fill_name=name)

        db.session.add(a)

    db.session.commit()


def load_gendertypes():
    """Load gender types"""

    print "Gender Types"
    Gender.query.delete()

    for row in open("data/gendersdata"):
        row = row.strip()
        code, name = row.split("|")

        a = Gender(gender_code=code, gender_name=name)

        db.session.add(a)

    db.session.commit()


def load_sleepingbags():
    """Load sleeping bags data"""

    print "Sleeping Bags"
    SleepingBag.query.delete()

    for row in open("data/sleepingbagsdata"):
        row = row.strip()
        row = row.split("|")

        product = int(row[0])
        fill = row[1]
        temp = int(row[2])
        wt = int(row[3])
        lgth = int(row[4])
        ger = row[5]

        a = SleepingBag(prod_id=product, fill_code=fill, temp_rating=temp,
                        weight=wt, length=lgth, gender_code=ger)

        db.session.add(a)

    db.session.commit()


def load_padtypes():
    """Load pad types"""

    print "Pad Types"
    PadType.query.delete()

    for row in open("data/padtypesdata"):
        row = row.strip()
        code, name = row.split("|")

        a = PadType(pad_type_code=code, pad_type_name=name)

        db.session.add(a)

    db.session.commit()


def load_sleepingpads():
    """Load sleeping pads data"""

    print "Sleeping Pads"
    SleepingPad.query.delete()

    for row in open("data/sleepingpadsdata"):
        row = row.strip()
        row = row.split("|")

        product = int(row[0])
        pad_type = row[1]
        use = int(row[2])
        rval = float(row[3])
        lgth = int(row[4])
        wt = int(row[5])
        wdth = int(row[6])

        a = SleepingPad(prod_id=product, type_code=pad_type, use_id=use,
                        r_value=rval, length=lgth, weight=wt, width=wdth)

        db.session.add(a)

    db.session.commit()


def load_histories():
    """Load history data"""

    print "Histories"
    History.query.delete()

    for row in open("data/historiesdata"):
        row = row.strip()
        row = row.split("|")

        product = int(row[0])
        renter = int(row[1])
        rental_submit_date = row[2]
        rental_start_date = row[3]
        rental_end_date = row[4]
        cost = float(row[5])

        try:
            owner_rate = int(row[6])
        except ValueError:
            owner_rate = None
        try:
            renter_rate = int(row[7])
        except ValueError:
            renter_rate = None
        try:
            prod_rate = int(row[8])
        except ValueError:
            prod_rate = None

        rental_submit_date = datetime.strptime(rental_submit_date, "%Y-%m-%d")
        rental_start_date = datetime.strptime(rental_start_date, "%Y-%m-%d")
        rental_end_date = datetime.strptime(rental_end_date, "%Y-%m-%d")

        a = History(prod_id=product, renter_user_id=renter,
                    rental_submission_date=rental_submit_date,
                    start_date=rental_start_date,
                    end_date=rental_end_date, total_cost=cost,
                    owner_rating_id=owner_rate,
                    renter_rating_id=renter_rate, prod_rating_id=prod_rate)

        db.session.add(a)

    db.session.commit()


def load_ratings():
    """Load ratings"""

    print "Ratings"
    Rating.query.delete()

    for row in open("data/ratingsdata"):
        row = row.strip()
        row = row.split("|")

        num_stars = int(row[0])
        text_comments = row[1]

        a = Rating(stars=num_stars, comments=text_comments)

        db.session.add(a)

    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Seed data
    load_regions()
    load_users()
    load_bestuses()
    load_categories()
    load_brands()
    load_products()
    load_tents()
    load_filltypes()
    load_gendertypes()
    load_sleepingbags()
    load_padtypes()
    load_sleepingpads()
    load_ratings()
    load_histories()
