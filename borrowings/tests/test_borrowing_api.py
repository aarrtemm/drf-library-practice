import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingDetailSerializer
from library.models import Book

BORROWING_URL = reverse("borrowing:borrowing-list")


def sample_book(**params):
    defaults = {
        "title": "Testtitle",
        "author": "TestAuthor",
        "cover": Book.CoverForBook.SOFT,
        "inventory": 4,
        "daily_fee": "22.00",
    }
    defaults.update(**params)
    return Book.objects.create(**defaults)


def detail_url(borrowing_id):
    return reverse("borrowing:borrowing-detail", args=[borrowing_id])


class AnonymousUserApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_show_borrowing_list(self):
        response = self.client.get(BORROWING_URL)

        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_borrowing(self):
        book = sample_book()

        data = {"book": book.id}

        response = self.client.post(BORROWING_URL, data)

        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testUser@test.com", "testpass"
        )

        self.client.force_authenticate(self.user)

    def test_show_borrowing_list(self):
        book = sample_book()
        book2 = sample_book(title="TestTiltle22", author="TestAuthor22")

        Borrowing.objects.create(user=self.user, book=book)
        Borrowing.objects.create(user=self.user, book=book2)

        borrowings = Borrowing.objects.all()

        serializer = BorrowingListSerializer(borrowings, many=True)

        response = self.client.get(BORROWING_URL)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, serializer.data)

    def test_show_borrowing_detail(self):
        book = sample_book()
        borrowing = Borrowing.objects.create(user=self.user, book=book)

        serializer = BorrowingDetailSerializer(borrowing)

        url = detail_url(borrowing.id)
        response = self.client.get(url)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, serializer.data)

    def test_create_borrowing(self):
        book = sample_book()

        data = {"book": book.id}

        response = self.client.post(BORROWING_URL, data=data)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_create_borrowing_with_expected_return_date(self):
        book = sample_book()
        payload = {"book": book.id, "expected_return_date": datetime.date.today()}
        response = self.client.post(BORROWING_URL, data=payload)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_return_borrowing(self):
        book = sample_book()

        borrowing = Borrowing.objects.create(user=self.user, book=book)

        response = self.client.get(
            reverse("borrowing:borrowing-return-borrowing", args=[borrowing.id])
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("is_active"))

    def test_return_already_returned_borrowing(self):
        book = sample_book()
        borrowing = Borrowing.objects.create(
            user=self.user, book=book, actual_return_date=datetime.date.today()
        )

        response = self.client.get(
            reverse("borrowing:borrowing-return-borrowing", args=[borrowing.id])
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_borrowing_out_of_stock(self):
        book = sample_book()

        book.inventory = 0
        book.save()

        data = {"book": book.id}

        response = self.client.post(BORROWING_URL, data)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_borrowing_with_past_expected_return_date(self):
        past_data = datetime.date.today() - datetime.timedelta(days=1)

        book = sample_book()

        data = {"book": book.id, "expected_return_date": past_data}

        response = self.client.post(BORROWING_URL, data)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin.test@test.com", "testpass", is_staff=True
        )
        self.user = get_user_model().objects.create_user(
            "user.test@test.com", "testpass"
        )
        self.client.force_authenticate(self.admin)

    def test_list_borrowings_as_admin(self):
        book1 = sample_book()
        book2 = sample_book(title="testBook2", author="Author2")

        Borrowing.objects.create(user=self.user, book=book1)
        Borrowing.objects.create(user=self.user, book=book2)

        borrowings = Borrowing.objects.all()

        serializer = BorrowingListSerializer(borrowings, many=True)

        response = self.client.get(BORROWING_URL)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, serializer.data)
