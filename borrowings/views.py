from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active", "user_id"]

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

    @action(methods=["GET"], detail=True, url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response(
                {"message": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = timezone.now()
        borrowing.is_active = False
        borrowing.save()

        book = borrowing.book
        book.inventory += 1
        book.save()

        return Response(
            {"message": "Borrowing returned successfully."}, status=status.HTTP_200_OK
        )
