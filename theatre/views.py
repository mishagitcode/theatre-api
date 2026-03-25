from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from theatre.models import Genre, Actor, Play, TheatreHall, Performance, Reservation
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    GenreSerializer,
    ActorSerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    PlayCreateUpdateSerializer,
    TheatreHallSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    PerformanceCreateUpdateSerializer,
    ReservationSerializer,
    ReservationListSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List genres"),
    retrieve=extend_schema(summary="Retrieve genre"),
)
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    search_fields = ("name",)
    ordering_fields = ("name",)


@extend_schema_view(
    list=extend_schema(summary="List actors"),
    retrieve=extend_schema(summary="Retrieve actor"),
)
class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (IsAdminOrReadOnly,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    search_fields = ("first_name", "last_name")
    ordering_fields = ("first_name", "last_name")


@extend_schema_view(
    list=extend_schema(summary="List plays"),
    retrieve=extend_schema(summary="Retrieve play"),
)
class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("actors", "genres")

    permission_classes = (IsAdminOrReadOnly,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    search_fields = ("title", "description", "actors__first_name", "actors__last_name", "genres__name")
    ordering_fields = ("title",)

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayDetailSerializer
        return PlayCreateUpdateSerializer


@extend_schema_view(
    list=extend_schema(summary="List theatre halls"),
    retrieve=extend_schema(summary="Retrieve theatre hall"),
)
class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = (IsAdminOrReadOnly,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    search_fields = ("name",)
    ordering_fields = ("name", "rows", "seats_in_row")


@extend_schema_view(
    list=extend_schema(summary="List performances"),
    retrieve=extend_schema(summary="Retrieve performance"),
)
class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related("play", "theatre_hall").prefetch_related(
        "tickets",
        "play__actors",
        "play__genres",
    )
    permission_classes = (IsAdminOrReadOnly,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    filterset_fields = ("play", "theatre_hall")
    search_fields = ("play__title", "theatre_hall__name")
    ordering_fields = ("show_time",)

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceCreateUpdateSerializer


@extend_schema_view(
    list=extend_schema(summary="List my reservations"),
    create=extend_schema(summary="Create reservation with tickets"),
    retrieve=extend_schema(summary="Retrieve my reservation"),
)
class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets",
            "tickets__performance",
            "tickets__performance__play",
            "tickets__performance__theatre_hall",
        )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ReservationListSerializer
        return ReservationSerializer
