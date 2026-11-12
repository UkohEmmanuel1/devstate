from rest_framework.decorators import api_view
from rest_framework.response import Response
from .views import user_topic
from django.conf import settings

@api_view(["GET"])
def notification_config(request):
    return Response({"server": settings.NTFY_SERVER, "topic": user_topic(request.user), "configured": bool(user_topic(request.user))})
