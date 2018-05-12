from models import get_mongo_db
from datetime import datetime
import pymongo
from random import randint
import requests
import json
from bson import ObjectId
from bson import json_util
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
    if message_id:
        previous_msg = db.messages.find_one({
            '_id' : ObjectId(str(message_id))
        })
        if previous_msg:
            return {'result' : 0}, 200 
    if not check_valid_user(remove_country_code(to_id)) or not check_valid_user(from_id):
        return {'message': 'Invalid User'}, 401
    from_id = add_country_code(from_id)
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
    push_token = db.user_info.find_one({
        'mobile' : remove_country_code(to_id)
    })
    status_of_message = 0
    result_json = {}
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
            result_json['sent_time'] = unix_time_millis(sent_time)
            if push_token:
                push_token = push_token.get('push_token')
                if push_token:
                    payload = { 
                        "data" : message_json,
                        "to" : push_token
                    }
                    payload['data']['timestamp'] = unix_time_millis(message_json['timestamp'])
                    payload['data']['_id'] = str(message_json['_id'])
                    AUTHORIZATION_HEADER = "key=" + AUTHORIZATION_KEY
                    headers = {
                        'Authorization': AUTHORIZATION_HEADER,
                        'Content-Type': "application/json",
                        'Cache-Control': "no-cache",
                    }
                    response = requests.request("POST", FCM_NOTIFICATION_URL, data=json_util.dumps(payload), headers=headers)
                    response_body = json.loads(response.text)
                    if response_body.get('success') == 1:
                        delivered_time = datetime.now()
                        db.messages.update({
                            '_id' : ObjectId(str(inserted_id)) 
                        }, {
                            '$set' : {
                                'delivered_time' : delivered_time
                            }
                        })
                        result_json['delivered_time'] = unix_time_millis(delivered_time)
                        status_of_message = 2
            return {
                'result' : 1, 
                'status' : status_of_message, 
                'unique_id' : unique_id,
                'message_timings' : result_json,
                'message_id' : inserted_id
            }, 200
                    
        return {
            'message': 'Message Could not be sent.', 
            'status': status_of_message, 
            'unique_id': unique_id,
            'message_timings' : result_json,
            'message_id' : inserted_id
        }, 400
    except Exception as e:
        print e
        status_of_message = 0
        return {
            'message': 'Message Could not be sent.', 
            'status': status_of_message, 
            'unique_id': unique_id,
            'message_id' : inserted_id
        }, 400
        # logging

        # if db.messages.find_one({
    #     'text' : message,
    #     'sent_time' : convert_millis_to_timestamp(sent_time),
    #     'to' : str(to_id),
    #     'from': str(from_id)
    # }):
    #     return {'result' : 0}, 200
        

def get_chat_messages(user_id, last_sync_time):
    if not check_valid_user(user_id):
        return {'message': 'Invalid User'}, 401
    user_id = add_country_code(user_id)
    if last_sync_time == '0':
        messages = db.messages.find({
            '$or': [
                {
                    'to': user_id,
                },{
                    'from_id': user_id,
                }
            ]
        })
    else:
        last_sync_time = float(last_sync_time)
        last_sync_time = convert_millis_to_timestamp(last_sync_time)
        messages = db.messages.find({
            '$or': [
                {
                    'to': user_id,
                },{
                    'from_id': user_id,
                }
            ],
            'timestamp' : {
                '$gte' : last_sync_time 
            }
        })
    messages_list = []
    for message in messages:
        text_json = dict()
        text_json['text'] = message['text']
        text_json['sender'] = '1' if message['from_id'] == user_id else '0'
        text_json['created'] = (message['timestamp'] - datetime(1970, 1, 1)).total_seconds()
        text_json['contact'] = message['to'] if message['from_id'] == user_id else message['from_id']
        text_json['sent_time'] = (message['sent_time'] - datetime(1970, 1, 1)).total_seconds()
        if message['read_time']:
            text_json['sent'] = 3
        else:
            text_json['sent'] = 1
        messages_list.append(text_json)
    print messages_list
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