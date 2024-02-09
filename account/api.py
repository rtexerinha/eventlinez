from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AccountSerializer
from .serializers import UserSerializer
from promoter.models import Event
from promoter.serializers import EventSerializers

class UserDetailAPI(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = AccountSerializer

    def get(self,  request):
        data = UserSerializer(request.user).data

        roles = []

        if hasattr(request.user, "promoter"):
            roles.append("PROMOTER")
        if hasattr(request.user, "customer"):
            roles.append("CUSTOMER")
        if request.user.partner_set.count():
            partner_roles = request.user.partner_set.values_list('role', flat=True).distinct()
            roles = roles + list(partner_roles)

            events = Event.objects.filter(partner__user=request.user)
            data["events"] = EventSerializers(events, many=True).data

        data['roles'] = roles
        return Response(data)
