from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from library.models import Book
from library.serializers import BookSerializer

BOOK_URL = reverse("library:book-list")


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


def detail_url(book_id):
    return reverse("library:book-detail", args=[book_id])


class UnauthenticatedBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_show_book_list_for_unauth_user(self):
        response = self.client.get(BOOK_URL)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_show_book_derail_for_unauth_user(self):
        book = sample_book()
        url = detail_url(book.id)

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


class AuthenticatedBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testUser@test.com", "testpass"
        )

        self.client.force_authenticate(self.user)

    def test_list_book(self):
        sample_book()

        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, serializer.data)

    def test_book_retrieve(self):
        book = sample_book(title="BookTest1")
        url = detail_url(book.id)

        response = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, serializer.data)

    def test_create_book_forbidden(self):
        payload = {
            "title": "Testtitle",
            "author": "TestAuthor",
            "cover": "TestCover",
            "inventory": 4,
            "daily_fee": "22.00",
        }

        response = self.client.post(BOOK_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testAdmin@test.com",
            "testpass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = {
            "title": "Testtitle1",
            "author": "TestAuthor",
            "cover": Book.CoverForBook.HARD,
            "inventory": 5,
            "daily_fee": "22.00",
        }

        response = self.client.post(BOOK_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_partial_update_book(self):
        book = sample_book()

        payload = {
            "title": "testTitle2",
            "cover": Book.CoverForBook.HARD,
            "inventory": 2,
        }

        url = detail_url(book.id)
        response = self.client.patch(url, payload)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get("title"), payload["title"])
        self.assertEquals(response.data.get("cover"), payload["cover"])
        self.assertEquals(
            response.data.get(
                "inventory",
            ),
            payload["inventory"],
        )

    def test_update_book(self):
        book = sample_book()

        payload = {
            "title": "Testtitle",
            "author": "TestAuthor2",
            "cover": Book.CoverForBook.HARD,
            "inventory": 2,
            "daily_fee": "22.00",
        }
        url = detail_url(book.id)
        response = self.client.put(url, payload)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get("title"), payload["title"])
        self.assertEquals(response.data.get("author"), payload["author"])
        self.assertEquals(response.data.get("cover"), payload["cover"])
        self.assertEquals(response.data.get("inventory"), payload["inventory"])
        self.assertEquals(response.data.get("daily_fee"), payload["daily_fee"])

    def test_delete_book(self):
        book = sample_book()
        url = detail_url(book.id)

        response = self.client.delete(url)

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
