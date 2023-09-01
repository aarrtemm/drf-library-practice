from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


class BorrowingView(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = BorrowingSerializer
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]
