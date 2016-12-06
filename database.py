import os
import pymongo
import datetime
# from bson.objectid import ObjectId
from operator import itemgetter

# from dotenv import Dotenv

# env = Dotenv('./.env')
env = os.environ

class BensKillerDatabase(object):

    def __init__(self):
        user = env['MONGO_USER']
        pwd  = env['MONGO_PWD']
        connection_string = 'mongodb://{0}:{1}@ds115738.mlab.com:15738/guestmeal-users'.format(user, pwd)
        conn = pymongo.MongoClient(connection_string)
        db = conn.get_database('guestmeal-users')
        self.users        = db.get_collection('users')
        self.transactions = db.get_collection('transactions')
        self.emails       = db.get_collection('emails')

    def calculate_current_price(self, record):
        now = datetime.datetime.today()
        price = 10 - float(record['min_price'])
        delta = (now - record['time']).total_seconds() / (60 * 60 * 24) # seconds in a day
        pd = price * delta
        return (10 - pd)

    def insert_record(self, uid, min_price):
        now = datetime.datetime.today()
        self.users.insert_one({
            'uid'   : uid,
            'min_price': min_price,
            'time'  : now,
            'sold'  : 0,
            })
        return True

    def remove_record(self, uid, min_price):
        self.users.remove({
            'uid'   : uid,
            'min_price': min_price,
            })
        return True

    def get_price(self, uid):
        try:
            records = self.users.find({
                'uid' : uid,
                'sold'  : 0,
                }).sort('time', -1)
            most_recent = records[0]
        except IndexError:
            print("user not found!")
            return
        return most_recent['min_price']

    def get_active_lowest_price(self):
        meals = self.get_available_meals()
        if meals:
            return meals[0]
        return None

    def mark_sold(self, mongo_id=False, seller_id=False, min_price=False):

        if not(mongo_id) and not(seller_id):
            raise ValueError("common man gimme something (no parameters)")
        elif mongo_id:
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
            print(mongo_id)
            result = self.users.find_one_and_update({
                '_id'        : mongo_id,
                'sold'       : 0
                }, {"$set" :{
                '_id'        : mongo_id,
                'sold'       : 1
                }})
            print(result)
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
            return not(type(result) == type(None))

        elif seller_id and min_price:
            result = self.users.find_one_and_update({
                'uid'        : seller_id,
                'min_price'  : min_price,
                'sold'       : 0
                }, {"$set" :{
                'uid'        : seller_id,
                'min_price'  : min_price,
                'sold'       : 1
                }})
            return result.acknowledged

    def mark_expired(self, uid, min_price):
        return self.users.find_one_and_update({
            'uid'        : uid,
            'min_price'  : min_price,
            'sold'       : 0
            }, {"$set" :{
            'uid'        : uid,
            'min_price'  : min_price,
            'sold'       : 2
            }})

    def get_available_meals(self):
        records = self.users.find({
            'sold' : 0
        })
        # need to keep track of lowest price and that user id
        prices = []
        for record in records:
            current_price = self.calculate_current_price(record)

            ####check if price has expired !!!
            if record['time'] + datetime.timedelta(hours=24) < datetime.datetime.now():
               self.mark_expired(record['uid'], record['min_price'])
               print('expired')
            else:
               prices.append((current_price, record))

        return sorted(prices, key=itemgetter(0))


    def get_all(self):
        return list(self.users.find({}))

    ####transactions

    def is_available(self, uid):
        results = (list(self.users.find({
            'uid'        : uid,
            'sold'       : 0
            })))
        if results:
            return results[0]
        else:
            return None

    def create_transaction(self, buyer_uid, mongo_id, selling_price):
        '''
        buyer_uid (str)
        mongo_id  (ObjectId or int)
        selling_price (float/int)
        '''
        now = datetime.datetime.today()
        entry =  self.users.find({
            '_id' : mongo_id
            })[0]
        price      = entry['min_price']
        seller_uid = entry['uid']

        res = self.transactions.insert_one({
            'seller'           : seller_uid,
            'buyer'            : buyer_uid,
            'selling_price'    : selling_price,
            'min_price    '    : price,
            'time'             : now,
            })
        if not(res.acknowledged):
            raise ValueError("transaction NOT reccorded in database")
        return self.mark_sold(mongo_id)

    def get_list_transactions(self, uid):
            selling_records = self.transactions.find({
                'seller' : uid,
                }).sort('time', -1)
            buying_records = self.transactions.find({
                'buyer' : uid,
                }).sort('time', -1)
            return list(buying_records) + list(selling_records)


##########################
#example usage code
##########################

bkd = BensKillerDatabase()

# bkd.insert_record('nico', 5.5)
# print(bkd.get_price('nico'))


# print(bkd.get_price('ben'))
# bkd.insert_record('ben', 3.5)
# print(bkd.get_price('ben'))


##########################
#example usage code (transactions)
##########################

'''
In [1]: i = bkd.get_active_lowest_price()[1]['_id']

In [2]: if bkd.is_available(i):
       ...:     bkd.create_transaction('johnson', i, 8)
'''
