from models import get_mongo_db
from datetime import datetime, timedelta
import pymongo
from random import randint
import requests
import json
from bson import ObjectId
from bson import json_util
from celery.task.schedules import crontab
from celery.decorators import periodic_task
import time
epoch = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0

db = get_mongo_db('chat_application')
FCM_NOTIFICATION_URL = "https://fcm.googleapis.com/fcm/send"
AUTHORIZATION_KEY = 'AAAAKo6DFHw:APA91bG7m8muu7X_8Y8GuH7EL3ebrClTvVdowTY_5yLOcgPTr2sD8r3o9hpSkFqzrm3qGjEF47zOer9_7yzMvBhhBmbRjrujCR5IZFJ2Q-leUJaPnC_AAuKzCqQYep4euURnMf0nY1za'

def add_country_code(mobile):
    country_code = db.user_info.find_one({ 
        'mobile' : mobile 
    })['country_code']
    return country_code + mobile

def remove_country_code(mobile):
    return mobile[3:]

def check_valid_user(mobile):
    if db.user_info.find_one({ 'mobile' : mobile }):
        return True
    return False

def convert_millis_to_timestamp(millis):
    seconds = millis/1000.0
    return datetime.fromtimestamp(seconds)

def add_new_message(to_id, from_id, created_time, message, unique_id, message_id):
    if not check_valid_user(remove_country_code(to_id)) or not check_valid_user(from_id):
        return {'message': 'Invalid User'}, 401
    from_id = add_country_code(from_id)
    # if message_id:
    #     previous_msg = db.messages.find_one({
    #         '_id' : ObjectId(str(message_id)),
    #     })
    #     if previous_msg:
    #         return {'result' : 0}, 200
    previous_msg = db.messages.find_one({
        'client_id' : (str(unique_id)),
        'from_id' : from_id
    })
    if previous_msg:
        status_of_message = 1
        return {
            'result' : 0,
            'status' : status_of_message, 
            'unique_id' : unique_id,
            'sent_time' : unix_time_millis(previous_msg['sent_time']),
            'message_id' : str(previous_msg['_id'])
        }, 200 
    message_json = dict()
    message_json['to'] = str(to_id)
    message_json['from_id'] = str(from_id)
    ###### created_time #############
    message_json['timestamp'] = convert_millis_to_timestamp(created_time)
    message_json['sent_time'] = None
    message_json['read_time'] = None
    message_json['delivered_time'] = None    
    message_json['text'] = message
    message_json['attachment_url'] = None
    message_json['client_id'] = str(unique_id)
    status_of_message = 0
    try:
        inserted_id = db.messages.insert(message_json)
        if inserted_id:
            sent_time = datetime.now()
            status_of_message = 1
            ### Setting Sent Time of Message ####
            db.messages.update({
                '_id' : ObjectId(str(inserted_id)) 
            }, {
                '$set' : {
                    'sent_time' : sent_time 
                }
            })
            # deliver_message(inserted_id)
            return {
                'result' : 1, 
                'status' : status_of_message, 
                'unique_id' : unique_id,
                'sent_time' : unix_time_millis(sent_time),
                'message_id' : str(inserted_id)
            }, 200
    except Exception as e:
        print e
        status_of_message = 0
        ########## delete if inserted #########

        return {
            'message': 'Message Could not be sent.', 
            'status': status_of_message, 
            'unique_id': unique_id,
            'result' : 0
        }, 400

def send_push_notification(payload):
    AUTHORIZATION_HEADER = "key=" + AUTHORIZATION_KEY
    headers = {
        'Authorization': AUTHORIZATION_HEADER,
        'Content-Type': "application/json",
        'Cache-Control': "no-cache",
    }
    try:
        response = requests.request("POST", FCM_NOTIFICATION_URL, \
            data=json_util.dumps(payload), headers=headers)
        response_body = json.loads(response.text)
        if response_body.get('success') == 1:
            return True
        return False
    except Exception as e:
        print e
        time.sleep(5)
        return False
    
# @periodic_task(run_every=(crontab(minute='*/1')), name="send_undelivered_messages", ignore_result=True)
def send_undelivered_messages():
    print 'Task in running', datetime.now()
    undelivered_messages = db.messages.find({
        "delivered_time" : None,
    })
    for message in undelivered_messages:
        deliver_message(str(message['_id']))
        
def deliver_message(message_id):
    message_doc = db.messages.find_one({
        '_id' : ObjectId(str(message_id))
    })
    if message_doc:
        receiver_user_account = db.user_info.find_one({
            'mobile' : remove_country_code(message_doc['to'])
        })
        receiver_push_token = receiver_user_account.get('push_token')
        if receiver_push_token:
            payload = { 
                "data" : {
                    'text' : message_doc['text'],
                    'from' : message_doc['from_id'],
                    'created_time' : unix_time_millis(message_doc['timestamp']),
                    'message_id' : str(message_doc['_id'])
                },
                "to" : receiver_push_token
            }
            if send_push_notification(payload):            
                delivered_time = datetime.now()
                db.messages.update({
                    '_id' : ObjectId(str(message_id)) 
                }, {
                    '$set' : {
                        'delivered_time' : delivered_time
                    }
                })
                sender_user_account = db.user_info.find_one({
                    'mobile' : remove_country_code(message_doc['from_id'])
                })
                sender_push_token = receiver_user_account.get('push_token')
                payload = { 
                    "data" : {
                        'delivered_time' : unix_time_millis(message_doc['delivered_time']),
                        'unique_id' : str(message_doc['client_id'])
                    },
                    "to" : sender_push_token
                }
                send_push_notification(payload)
            

def get_chat_messages(user_id, last_sync_time):
    if not check_valid_user(user_id):
        return {'message': 'Invalid User'}, 401
    user_id = add_country_code(user_id)
    if last_sync_time == '0' or not last_sync_time:
        messages = db.messages.find({
            'to': user_id,
        })
    else:
        print last_sync_time
        last_sync_time = float(last_sync_time)
        last_sync_time = convert_millis_to_timestamp(last_sync_time)
        messages = db.messages.find({
            'to': user_id,
            'timestamp' : {
                '$gte' : last_sync_time 
            }
        })
    messages_list = []
    for message in messages:
        messages = db.messages.update({
            '_id' : message['_id'],
        }, {
            '$set' : {
                'delivered_time' : datetime.now()
            }
        })
        text_json = dict()
        text_json['text'] = message['text']
        text_json['sender'] = '0'
        text_json['created'] = unix_time_millis(message['timestamp'] - timedelta(hours=5, minutes=30))
        text_json['contact'] = message['from_id']
        text_json['sent_time'] = unix_time_millis(message['sent_time'])
        text_json['message_id'] = str(message['_id'])
        if message['read_time']:
            text_json['sent'] = 3
        else:
            text_json['sent'] = 1
        messages_list.append(text_json)
    return {'messages': messages_list}, 200

def read_message(user_number, contact_number):
    user_number = add_country_code(user_number)
    db.messages.update({
        'from_id' : contact_number,
        'to' : user_number,
        'read_time' : None
    }, {
        '$set': {
            'read_time' : datetime.now()
        }
    }, multi=True)
    return {'result': 1}, 200