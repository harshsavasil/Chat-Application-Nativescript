from models import get_mongo_db
from datetime import datetime, timedelta
import pymongo
from random import randint
from models_message import add_country_code
from operator import itemgetter

db = get_mongo_db('chat_application')

epoch = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0

def login_user(mobile, password):
    if db.user_info.find({
        'mobile' : mobile,
        'password' : password
    }).count() > 0:
        return True
    return False

def save_push_token_for_notifications(user_number, token):
    user_account = db.user_info.find_one({
        'mobile': str(user_number)
    })
    if user_account:
        db.user_info.update({
            'mobile': str(user_number)
        }, {
            '$set' : {
                'push_token' : str(token)
            }
        })
        return {'result': 1}, 200
    return {'message': 'User Not Authorized'}, 401

def get_unread_count(contact_number, user_number):
    return db.messages.find({
        'from_id' : contact_number,
        'to' : user_number,
        'read_time' : None
    }).count()

def get_last_text(contact_number, user_number):
    last_messages = db.messages.find({
        '$or': [
            {
                '$and' : [{'to': user_number}, {'from_id': contact_number}]
            },{
                '$and' : [{'to': contact_number}, {'from_id': user_number}]
            }
        ]
    }).sort([('timestamp', -1)]).limit(1)
    last_messages = [x for x in last_messages]
    if last_messages:
        return last_messages[0]['text'], unix_time_millis(last_messages[0]['timestamp'])
    default_date = datetime.now() 
    default_date = default_date.replace(year=1995, second=0, microsecond=0)
    return '', unix_time_millis(default_date)

def get_last_seen(user_number):
    last_messages = db.messages.find({
        'from_id': user_number,
    }).sort([('timestamp', -1)]).limit(1)
    for last_message in last_messages:
        return unix_time_millis(last_message['timestamp'])
    default_date = datetime.now() 
    default_date = default_date.replace(year=1995, second=0, microsecond=0)
    default_date = unix_time_millis(default_date)
    return default_date 


def create_new_user(mobile_number, country_code, first_name, last_name, gender, password):
    user_info = dict()
    user_info['mobile'] = mobile_number
    user_info['password'] = password
    user_info['country_code'] = country_code
    user_info['first_name'] = first_name.title()
    user_info['last_name'] = last_name.title()
    user_info['created_date'] = datetime.now()
    user_info['is_active'] = True
    user_info['last_seen'] = datetime.now()
    user_info['deleted_date'] = None
    user_info['last_updated'] = datetime.now()
    user_info['gender'] = gender
    user_info['dp_url'] = 'https://randomuser.me/api/portraits/med/'
    gender = 'men/' if gender == 1 else 'women/'
    user_info['dp_url'] =  user_info['dp_url'] + gender + str(randint(0, 100)) + '.jpg'
    
    try:
        db.user_info.insert(user_info)
        return {
            'result' : 1,
            'message' : 'User Account Successfully created.'
        }, 200
    except pymongo.errors.DuplicateKeyError, ex:
        return {
            'result' : 0,
            'message': 'An account with same number already exists. Please Login'
            }, 400
    except Exception as e:
        print e
        return {
            'message': 'Please try again later.'
            }, 400

def get_users(user_id): 
    users = db.user_info.find().sort([('first_name', 1)])
    user_id = add_country_code(user_id)
    result_json = []
    for user in users:
        mobile = user['country_code'] + user['mobile']
        if user_id == mobile:
            continue
        user_info = dict()
        user_info['number'] = user['country_code'] + user['mobile']
        user_name = user['first_name'] + ' ' + user['last_name']
        user_info['contact'] = {
            'avatar' : user['dp_url'],
            'name' : user_name
        }
        user_info['type'] = 'DIRECT'
        user_info['muted'] = 2
        user_info['text'], user_info['last_message_timestamp'] = \
            get_last_text(user_info['number'], user_id)
        user_info['when'] = get_last_seen(user_info['number'])
        user_info['unread'] = get_unread_count(user_info['number'], user_id)
        result_json.append(user_info)
    result_json.sort(key=lambda e: (e['last_message_timestamp'], e['contact']['name']))
    print result_json    
    return result_json, 200

