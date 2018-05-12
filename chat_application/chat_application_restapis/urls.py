"""chat_application_restapis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url
from chat_application_restapis.login_module import views

urlpatterns = [
    url(r'^login/$', views.login),
    url(r'^signup/$', views.post_new_user),
    url(r'^contact_list/$', views.contact_list),
    # url(r'^edit_user_info/$', views.update_user_info),
    url(r'^send_message/$', views.send_message),
    url(r'^retrieve_chats/$', views.retrieve_chat),
    url(r'^read_message/$', views.read_messages),
    url(r'^save_push_token/$', views.save_push_token),
    
]

