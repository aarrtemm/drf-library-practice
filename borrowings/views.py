from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)


class BorrowingView(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Borrowing.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
