from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AccountSerializer
from .serializers import UserSerializer
from promoter.models import Event, Partner
from promoter.serializers import EventListSerializers
from django.db.models import Q


def get_user_role(user, event):
    try:
        partner = user.partner_set.get(event=event)
        if partner is not None:
            return partner.role
    except Partner.DoesNotExist:
        pass
    if event.promoter.user == user:
        return 'PROMOTER'


class UserDetailAPI(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = AccountSerializer

    def get(self,  request):
        data = UserSerializer(request.user).data

        roles = []
        if hasattr(request.user, "promoter"):
            roles.append("PROMOTER")
        if request.user.partner_set.count():
            partner_roles = request.user.partner_set.values_list('role', flat=True).distinct()
            roles = roles + list(partner_roles)
        data['roles'] = roles

        events = Event.objects.filter(Q(partner__user=request.user) | Q(promoter__user=request.user)).distinct()
        serialized_events = []
        for event in events:
            event_data = EventListSerializers(event).data
            event_data["role"] = get_user_role(request.user, event)
            serialized_events.append(event_data)

        if len(serialized_events) <= 0:
            return Response(
                {"Error": "User not Promoter or Partner or Doorman"}, status=403)
        data["events"] = serialized_events

        return Response(data)
