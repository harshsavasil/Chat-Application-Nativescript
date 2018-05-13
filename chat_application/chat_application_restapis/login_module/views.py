from rest_framework.response import Response
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.renderers import JSONRenderer
import json
from bson import json_util
from models_user import create_new_user, get_users, login_user, save_push_token_for_notifications
from models_message import add_new_message, get_chat_messages, read_message
from django.views.decorators.csrf import csrf_exempt


def login(request):
    if request.method == 'GET':
        mobile = request.GET.get('mobile')
        password = request.GET.get('password')
        if not mobile:
            return HttpResponse(json_util.dumps({'message': 'Mobile Number is missing.'}), 400)
        if not password:
            return HttpResponse(json_util.dumps({'message': 'Password is missing.'}), 400)
        result = login_user(mobile, password)
        if result:
            return HttpResponse(json_util.dumps({
                'result': 1,
                'message': 'Login Successful.'
            }), 200)
        return HttpResponse(json_util.dumps({
            'result': 0,
            'message': 'Invalid Username or Password'
        }), 400)
    return HttpResponseForbidden()


def post_new_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        mobile_no = data.get('mobile')
        country_code = data.get('country_code')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        password = data.get('password')
        gender = data.get('gender', None)
        if not mobile_no:
            return HttpResponse(json_util.dumps({
                'message': 'Mobile Number is missing.'
            }), status=400)
        if not country_code:
            return HttpResponse(json_util.dumps({
                'message': 'Country Code is missing.'
            }), status=400)
        if not first_name:
            return HttpResponse(json_util.dumps({
                'message': 'First Name of the user is missing.'
            }), status=400)
        if gender == None: 
            return HttpResponse(json_util.dumps({
                'message': 'Gender of the user is missing.'
            }), status=400)
        if not password:
            return HttpResponse(json_util.dumps({
                'message': 'Password of the user is missing.'
            }), status=400)
        if not last_name:
            last_name = ''
            ### data validation ###
            #######################
        result, status_code = create_new_user(mobile_no, country_code, first_name,
                                              last_name, gender, password)
        return HttpResponse(json_util.dumps(result), status=status_code)
    return HttpResponseForbidden()


def contact_list(request):
    if request.method == 'GET':
        user_id = request.GET.get('mobile')
        if user_id:
            result, status_code = get_users(user_id)
            return HttpResponse(json_util.dumps(result), status=status_code)
    return HttpResponseForbidden()

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print data
        to_id = data.get('to', '')
        from_id = data.get('from_id', '')
        message = data.get('text', '')
        message_id = data.get('message_id', '')
        unique_id = data.get('unique_id', '')
        created_time = float(data.get('created_time'))
        if not to_id:
            return HttpResponse(json_util.dumps({
                'message': 'Receiver is missing.'
            }), status=400)
        if not from_id:
            return HttpResponse(json_util.dumps({
                'message': 'Sender is missing.'
            }), status=400)
        if not message:
            return HttpResponse(json_util.dumps({
                'message': 'Message Body is missing.'
            }), status=400)
        if not created_time:
            return HttpResponse(json_util.dumps({
                'message': 'Created Time is missing.'
            }), status=400)
        if not unique_id:
            return HttpResponse(json_util.dumps({
                'message': 'Unique ID is missing.'
            }), status=400)
        result, status_code = add_new_message(to_id, from_id, created_time, \
            message, unique_id, message_id)
        return HttpResponse(json_util.dumps(result), status=status_code)

def retrieve_chat(request):
    if request.method == 'GET':
        calling_id = request.GET.get('user_id', '')
        last_sync_time = request.GET.get('last_sync_time', None)
        if not calling_id:
            return HttpResponse(json_util.dumps({
                'message': 'Mandatory Param is missing.'
            }), status=400)
        if last_sync_time is None and last_sync_time == 0:
            return HttpResponse(json_util.dumps({
                'message': 'Mandatory Param is missing.'
            }), status=400)
        result, status_code = get_chat_messages(calling_id, last_sync_time)
        print result
        return HttpResponse(json_util.dumps(result), status=status_code)

def read_messages(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_number = data.get('user_id')
        contact_number = data.get('contact_id')
        if not user_number or not contact_number:
            return HttpResponse(json_util.dumps({
                'message': 'Mandatory Param is missing.'
            }), status=400)
        result, status_code = read_message(user_number, contact_number)
        return HttpResponse(json_util.dumps(result), status=status_code)

@csrf_exempt
def save_push_token(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        push_token = data.get('token')
        user_number = data.get('user_id')
        if not push_token:
            return HttpResponse(json_util.dumps({
                'message': 'Push Token is missing.'
            }), status=400)
        if not user_number:
            return HttpResponse(json_util.dumps({
                'message': 'User Number is missing.'
            }), status=400)
        result, status_code = save_push_token_for_notifications(user_number, push_token)
        # import pdb ; pdb.set_trace()
        return HttpResponse(json_util.dumps(result), status=status_code)
    return HttpResponseForbidden()