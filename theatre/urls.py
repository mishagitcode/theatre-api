from django.urls import include, path
from rest_framework.routers import DefaultRouter

from theatre.views import (
    GenreViewSet,
    ActorViewSet,
    PlayViewSet,
    TheatreHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
)

router = DefaultRouter()
router.register("genres", GenreViewSet, basename="genre")
router.register("actors", ActorViewSet, basename="actor")
router.register("plays", PlayViewSet, basename="play")
router.register("theatre-halls", TheatreHallViewSet, basename="theatrehall")
router.register("performances", PerformanceViewSet, basename="performance")
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = [
    path("", include(router.urls)),
]
