from unittest import TestCase
import os
from mock import patch
from datetime import datetime

from server import app
from model import connect_to_db, db
from seed import load_regions, load_users, load_bestuses, load_categories
from seed import load_brands, load_products, load_tents, load_filltypes
from seed import load_gendertypes, load_sleepingbags, load_padtypes
from seed import load_sleepingpads, load_ratings, load_histories
from model import User, Brand, Product, Tent, SleepingBag, Category, Rating, SleepingPad

from make_update_helpers import check_brand, make_brand, get_brand_id
from search_helpers import get_users_in_area, filter_products, convert_string_to_datetime
from search_helpers import get_products_within_dates, categorize_products

from make_update_helpers import calc_avg_star_rating
from search_helpers import search_radius, calc_default_dates


class IntegrationTestCase(TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True
        connect_to_db(app, "sqlite:////tmp/temp.db")

        db.create_all()

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

    def tearDown(self):
        # can put in here the python (os) to remove a file r
        db.session.remove()
        os.remove("////tmp/temp.db")

    def test_homepage(self):
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('Create one here', result.data)

    def test_handle_successful_login(self):
        result = self.client.post('/handle-login', data={'email': 'phar@fignewton.com',
                                  'password': 'abc'}, follow_redirects=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn('Find Stuff', result.data)

    def test_handle_failed_login(self):
        result = self.client.post('/handle-login', data={'email': 'the@godpigeon.com',
                                  'password': 'abc'}, follow_redirects=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn('Create one here', result.data)

    # def test_logout(self):
    #     result = self.client.post('/logout', follow_redirects=True)

    #     self.assertEqual(result.status_code, 200)
    #     self.assertIn('<p><b>Login Here</b></p>', result.data)

    def test_handle_successful_create_account(self):
        result = self.client.post('handle-create-account', data={'pword': '123',
                                  'confirm_pword': '123', 'firstname': 'The',
                                  'lastname': 'Brain', 'staddress': '8 6th St',
                                  'cty': 'San Francisco', 'state': 'CA',
                                  'zipcode': '94103', 'phonenumber': '4155552222',
                                  'username': 'the@brain.com'}, follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('Find Stuff', result.data)

    def test_handle_failed_create_account(self):
        result = self.client.post('handle-create-account', data={'pword': '123',
                                  'confirm_pword': 'abc'}, follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Contact Info</h3>', result.data)

    def test_show_account_info(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'franken@berry.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')

            result = self.client.get('/account-info')
            self.assertEqual(result.status_code, 200)

    def test_handle_tent_listing(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'phar@fignewton.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')

            result = c.post('/handle-listing/1', data={'category_id': 1,
                            'brand_id': 3, 'modelname': 'Kaiju 6',
                            'desc': 'Guaranteeing campground fun for the family, blah blah',
                            'cond': 'Excellente', 'avail_start': '2015-11-20',
                            'avail_end': '2015-12-31', 'pricing': 4.5, 'image': None,
                            'user': User.query.get(1), 'bestuse': 2, 'sleep': 6,
                            'seasoncat': 3, 'weight': 200, 'length': 80, 'width': 25,
                            'doors': 3, 'poles': 3}, follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('Listing successfully posted!', result.data)

        product = Product.query.filter(Product.model == 'Kaiju 6').one()
        self.assertEqual(product.model, 'Kaiju 6')

        tent = Tent.query.get(product.prod_id)
        self.assertEqual(tent.sleep_capacity, 6)

    def test_handle_sleepingbag_listing(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'count@chocula.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')

            result = c.post('/handle-listing/2', data={'category_id': 2,
                            'brand_id': 2, 'modelname': 'Arrow Rock 15',
                            'desc': 'By the time you clean up dinner and organize, blah blah',
                            'cond': 'Lost some feathers', 'avail_start': '2016-03-01',
                            'avail_end': '2016-03-31', 'pricing': 3.0, 'image': None,
                            'user': User.query.get(2), 'filltype': 'D', 'temp': 15,
                            'bag_weight': 45, 'length': 43, 'gender': 'U'},
                            follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('Listing successfully posted!', result.data)

        product = Product.query.filter(Product.model == 'Arrow Rock 15').one()
        self.assertEqual(product.brand_id, 2)

        sleepingbag = SleepingBag.query.get(product.prod_id)
        self.assertEqual(sleepingbag.fill_code, 'D')

    def test_handle_sleepingpad_listing(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'trix@rabbit.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')

            result = c.post('/handle-listing/3', data={'category_id': 3,
                            'brand_id': -1, 'new_brand_name': 'Exped', 'modelname': 'Mega Mat 10',
                            'desc': 'mega big and mega warm',
                            'cond': 'mega good', 'avail_start': '2017-03-01',
                            'avail_end': '2017-06-15', 'pricing': 2.50, 'image': None,
                            'user': User.query.get(3), 'padtype': 'F', 'bestuse': 2,
                            'r_val': 9.5, 'pad_weight': 38, 'pad_length': '78'},
                            follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('Listing successfully posted!', result.data)

        product = Product.query.filter(Product.model == 'Mega Mat 10').one()
        self.assertEqual(product.brand.brand_name, 'Exped')

        sleepingpad = SleepingPad.query.get(product.prod_id)
        self.assertEqual(sleepingpad.type_code, 'F')

    def test_submit_renter_rating(self):
        result = self.client.post('handle-user-rating', data={'hist_id': 7,
                                  'num_stars': 3, 'is_owner': 0, 'comments': 'abcdefg'},
                                  follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('History id=7', result.data)

    def test_submit_owner_rating(self):
        result = self.client.post('handle-user-rating', data={'hist_id': 7,
                                  'num_stars': 3, 'is_owner': 1, 'comments': 'abcdefg'},
                                  follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('History id=7', result.data)

    def test_submit_product_rating(self):
        result = self.client.post('handle-product-rating', data={'hist_id': 7,
                                  'num_stars': 3, 'comments': 'abcdefg'},
                                  follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('history_id=7', result.data)

    def test_delist_product(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'franken@berry.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')
            result = self.client.post('handle-delist-product', data={'prod_id': 1},
                                      follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('<li>This product has been delisted.</li>', result.data)
        self.assertEqual(Product.query.get(1).available, 0)

    def test_deactivate_account(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'spuds@mackenzie.com'

            c.set_cookie('localhost', 'MYCOOKIE', 'cookie_value')

            result = self.client.post('handle-deactivate-account',
                                      follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('Your account has been deactivated. Thank you for using Happy Camper!',
                      result.data)
        self.assertEqual(User.query.get(5).active, 0)

    def test_find_users(self):
        franken = User.query.filter(User.fname == 'Franken').one()
        self.assertEqual(franken.fname, 'Franken')
        self.assertEqual(franken.email, 'franken@berry.com')

    def test_find_product(self):
        product = Product.query.filter(Product.model == 'Sugar Shack 2').one()
        self.assertEqual(product.condition, 'Good. Used twice.')

        tent = Tent.query.get(product.prod_id)
        self.assertEqual(tent.sleep_capacity, 2)

    def test_get_users_in_area(self):
        users_in_area = get_users_in_area(['94612'], 1)
        users_names = []

        for user in users_in_area:
            users_names.append(user.fname)

        self.assertEqual(sorted(users_names), ['Count', 'Trix'])

    def test_filter_products(self):
        filtered_products = filter_products(Product.query.all(), 1, 1)
        self.assertEqual(filtered_products[0].model, 'Passage 2')

    def test_check_brand(self):
        self.assertEqual(check_brand(3), 3)

    def test_make_brand(self):
        make_brand("ABC")
        self.assertEqual(Brand.query.filter(Brand.brand_name == "ABC").one().brand_name, "ABC")

        brand = Brand.query.filter(Brand.brand_name == "ABC").one()

    def test_get_brand_id(self):
        self.assertEqual(get_brand_id("REI"), 1)

    def test_get_products_within_dates(self):
        start_date = convert_string_to_datetime('2015-10-31')
        end_date = convert_string_to_datetime('2015-11-01')

        products = get_products_within_dates(start_date, end_date, User.query.all())

        self.assertEqual(products[0].prod_id, 1)

    def test_categorize_products(self):
        categories = [Category.query.get(1), Category.query.get(2)]
        products = [Product.query.get(1), Product.query.get(2), Product.query.get(5)]

        inventory = categorize_products(categories, products)

        self.assertEqual(inventory['Tents'][0].prod_id, 1)
        self.assertEqual(inventory['Sleeping Bags'][0].prod_id, 5)


class SearchHelpersTestCase(TestCase):

    def test_googlemaps_api(self):
        searchcenter = '94612'
        postalcodes = [('94608',), ('94102',), ('94040',), ('95376',), ('95451',),
                       ('92277',), ('10013',), ('02139',)]

        within20 = search_radius(searchcenter, postalcodes, 20)
        within60 = search_radius(searchcenter, postalcodes, 60)
        within200 = search_radius(searchcenter, postalcodes, 200)

        self.assertEqual(sorted(within20), sorted(['94608', '94102']))
        self.assertEqual(sorted(within60), sorted(['94608', '94102', '94040',
                                                   '95376']))
        self.assertEqual(sorted(within200), sorted(['94608', '94102', '94040',
                                                    '95376', '95451']))

    def test_search_radius(self):
        searchcenter1 = '94612'
        searchcenter2 = '94109'
        searchcenter3 = '94040'
        searchcenter4 = '10013'
        postalcodes = [('94612',), ('94109',), ('94040',), ('95376',), ('10013',)]

        self.assertEqual(sorted(search_radius(searchcenter1, postalcodes, 20)), sorted(['94109', '94612']))
        self.assertEqual(sorted(search_radius(searchcenter1, postalcodes, 60)), sorted(['94109', '94612', '94040', '95376']))
        self.assertEqual(sorted(search_radius(searchcenter2, postalcodes, 20)), sorted(['94109', '94612']))
        self.assertEqual(sorted(search_radius(searchcenter2, postalcodes, 60)), sorted(['94109', '94612', '94040']))
        self.assertEqual(sorted(search_radius(searchcenter3, postalcodes, 20)), ['94040'])
        self.assertEqual(sorted(search_radius(searchcenter4, postalcodes, 20)), ['10013'])

    # http://www.robotswillkillusall.org/posts/how-to-mock-datetime-in-python/
    # https://pypi.python.org/pypi/mock
    @patch('search_helpers.datetime')
    def test_calc_default_dates(self, mock_dt):
        expected = {'future': datetime(2015, 12, 18),
                    'today_string': '2015-11-18',
                    'today': datetime(2015, 11, 18),
                    'future_string': '2015-12-18'}

        mock_dt.today.return_value = datetime(2015, 11, 18)
        self.assertEqual(calc_default_dates(30), expected)

    def test_convert_string_to_datetime(self):
        test_date = convert_string_to_datetime("2015-11-18")
        self.assertEqual(test_date, datetime(2015, 11, 18))

    def test_calc_avg_star_rating(self):
        rating1 = Rating(rating_id=1, stars=4, comments="abc")
        rating2 = Rating(rating_id=3, stars=2, comments="def")
        rating3 = Rating(rating_id=3, stars=3, comments="ghi")
        ratings = [rating1, rating2, rating3]

        self.assertEqual(calc_avg_star_rating(ratings), 3)


class MakeUpdateTestCase(TestCase):
    def test_create_user_object(self):
        user1 = User(fname='Michelle', lname='Tanner', street='1709 Broderick Street',
                     city='San Francisco', region_id=1, postalcode='94115',
                     phone=4155556666, email='michelle@tanner.com', password='123')

        user2 = User(fname='Grumpy', lname='Grandpa', street='54 Elizabeth Street #31',
                     city='New York', region_id=2, postalcode='10013',
                     phone=2125556666, email='grumpy@grandpa.com', password='123')

        self.assertEqual(user1.email, 'michelle@tanner.com')
        self.assertEqual(user2.email, 'grumpy@grandpa.com')
        self.assertEqual(user1.region_id, 1)
        self.assertEqual(user2.region_id, 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
