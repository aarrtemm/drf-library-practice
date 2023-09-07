from django.db import transaction
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)
from library.models import Book


class BorrowingView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Borrowing.objects.all()
        return Borrowing.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        book_id = request.data.get("book")
        user = request.user
        expected_return_date = request.data.get("expected_return_date")
        actual_return_date = request.data.get("actual_return_date")

        with transaction.atomic():
            try:
                book = Book.objects.get(pk=book_id)
            except Book.DoesNotExist:
                return Response(
                    {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if book.inventory == 0:
                return Response(
                    {"error": "Book is out of stock"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book.inventory -= 1
            book.save()

            borrowing = Borrowing.objects.create(
                book=book,
                user=user,
                expected_return_date=expected_return_date,
                actual_return_date=actual_return_date,
            )

            serializer = self.get_serializer(borrowing)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
