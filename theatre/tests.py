from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)


def create_user(**params):
    defaults = {
        "username": "user",
        "password": "testpass123",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def create_genre(name="Drama"):
    return Genre.objects.create(name=name)


def create_actor(first_name="Tom", last_name="Hardy"):
    return Actor.objects.create(first_name=first_name, last_name=last_name)


def create_play(
    title="Hamlet",
    description="A tragedy about revenge.",
    actors=None,
    genres=None,
):
    play = Play.objects.create(title=title, description=description)
    if actors:
        play.actors.set(actors)
    if genres:
        play.genres.set(genres)
    return play


def create_theatre_hall(name="Main Hall", rows=10, seats_in_row=12):
    return TheatreHall.objects.create(
        name=name,
        rows=rows,
        seats_in_row=seats_in_row,
    )


def create_performance(play=None, theatre_hall=None, **params):
    if play is None:
        play = create_play()
    if theatre_hall is None:
        theatre_hall = create_theatre_hall()

    defaults = {
        "show_time": timezone.now() + timedelta(days=1),
    }
    defaults.update(params)

    return Performance.objects.create(
        play=play,
        theatre_hall=theatre_hall,
        **defaults,
    )


class ModelTests(TestCase):
    def test_theatre_hall_capacity_property(self):
        hall = create_theatre_hall(rows=15, seats_in_row=20)

        self.assertEqual(hall.capacity, 300)

    def test_ticket_clean_raises_error_for_invalid_row_and_seat(self):
        performance = create_performance(
            theatre_hall=create_theatre_hall(rows=5, seats_in_row=6)
        )
        reservation = Reservation.objects.create(user=create_user())
        ticket = Ticket(
            row=7,
            seat=8,
            performance=performance,
            reservation=reservation,
        )

        with self.assertRaises(ValidationError):
            ticket.full_clean()


class PublicTheatreApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_genre_list_is_public_and_ordered(self):
        create_genre(name="Drama")
        create_genre(name="Comedy")

        response = self.client.get(reverse("genre-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [genre["name"] for genre in response.data],
            ["Comedy", "Drama"],
        )

    def test_actor_search_filters_results(self):
        create_actor(first_name="Emma", last_name="Stone")
        create_actor(first_name="Ryan", last_name="Gosling")

        response = self.client.get(reverse("actor-list"), {"search": "Emma"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "Emma")

    def test_play_detail_returns_nested_actors_and_genres(self):
        actor = create_actor(first_name="Ian", last_name="McKellen")
        genre = create_genre(name="Tragedy")
        play = create_play(
            title="King Lear",
            description="A tragedy of family and power.",
            actors=[actor],
            genres=[genre],
        )

        response = self.client.get(reverse("play-detail", args=[play.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], play.title)
        self.assertEqual(
            response.data["actors"],
            [{"id": actor.id, "first_name": "Ian", "last_name": "McKellen"}],
        )
        self.assertEqual(
            response.data["genres"],
            [{"id": genre.id, "name": "Tragedy"}],
        )

    def test_performance_list_can_be_filtered_by_play(self):
        hall = create_theatre_hall(rows=5, seats_in_row=5)
        selected_play = create_play(title="Hamlet")
        other_play = create_play(title="Macbeth")
        performance = create_performance(play=selected_play, theatre_hall=hall)
        create_performance(play=other_play, theatre_hall=hall)

        reservation = Reservation.objects.create(user=create_user(username="buyer"))
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=reservation,
        )

        response = self.client.get(
            reverse("performance-list"),
            {"play": selected_play.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["play"], selected_play.id)
        self.assertEqual(response.data[0]["tickets_available"], 24)
        self.assertEqual(response.data[0]["theatre_hall_capacity"], 25)


class AdminTheatreApiTests(APITestCase):
    def test_non_admin_cannot_create_genre(self):
        client = APIClient()
        client.force_authenticate(create_user())

        response = client.post(
            reverse("genre-list"),
            {"name": "Musical"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_play_with_related_entities(self):
        client = APIClient()
        admin_user = create_user(username="admin", is_staff=True)
        client.force_authenticate(admin_user)
        actor = create_actor()
        genre = create_genre()
        payload = {
            "title": "Othello",
            "description": "A tragedy about jealousy and betrayal.",
            "actor_ids": [actor.id],
            "genre_ids": [genre.id],
        }

        response = client.post(reverse("play-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=response.data["id"])
        self.assertEqual(play.title, payload["title"])
        self.assertEqual(list(play.actors.values_list("id", flat=True)), [actor.id])
        self.assertEqual(list(play.genres.values_list("id", flat=True)), [genre.id])

    def test_admin_can_create_performance(self):
        client = APIClient()
        admin_user = create_user(username="manager", is_staff=True)
        client.force_authenticate(admin_user)
        play = create_play()
        hall = create_theatre_hall()
        show_time = (timezone.now() + timedelta(days=2)).isoformat()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": show_time,
        }

        response = client.post(reverse("performance-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Performance.objects.filter(
                play=play,
                theatre_hall=hall,
            ).exists()
        )


class ReservationApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(username="customer")
        self.other_user = create_user(username="another_customer")
        self.play = create_play()
        self.hall = create_theatre_hall(rows=3, seats_in_row=4)
        self.performance = create_performance(
            play=self.play,
            theatre_hall=self.hall,
        )

    def test_authentication_required_for_reservation_list(self):
        response = self.client.get(reverse("reservation-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_create_reservation_with_tickets(self):
        self.client.force_authenticate(self.user)
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": self.performance.id},
                {"row": 1, "seat": 2, "performance": self.performance.id},
            ]
        }

        response = self.client.post(
            reverse("reservation-list"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation = Reservation.objects.get(id=response.data["id"])
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.tickets.count(), 2)

    def test_reservation_list_contains_only_current_users_items(self):
        own_reservation = Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=self.other_user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=self.performance,
            reservation=own_reservation,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("reservation-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_reservation.id)
        self.assertEqual(len(response.data[0]["tickets"]), 1)

    def test_user_cannot_access_another_users_reservation(self):
        reservation = Reservation.objects.create(user=self.other_user)
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("reservation-detail", args=[reservation.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_ticket_payload_does_not_create_reservation(self):
        self.client.force_authenticate(self.user)
        payload = {
            "tickets": [
                {"row": 10, "seat": 1, "performance": self.performance.id},
            ]
        }

        response = self.client.post(
            reverse("reservation-list"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
