from rest_framework import serializers
from theatre.models import (
    Genre,
    Actor,
    Play,
    TheatreHall,
    Performance,
    Reservation,
    Ticket
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name")


class PlayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "title", "description")


class PlayDetailSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres")


class PlayCreateUpdateSerializer(serializers.ModelSerializer):
    actor_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Actor.objects.all(),
        source="actors"
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        source="genres"
    )

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actor_ids", "genre_ids")


class TheatreHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    theatre_hall_capacity = serializers.IntegerField(source="theatre_hall.capacity", read_only=True)
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "play_title",
            "theatre_hall",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "show_time",
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        return obj.theatre_hall.capacity - obj.tickets.count()


class PerformanceDetailSerializer(serializers.ModelSerializer):
    play = PlayDetailSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time", "taken_places")

    def get_taken_places(self, obj):
        return [{"row": t.row, "seat": t.seat} for t in obj.tickets.all()]


class PerformanceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")

    def validate(self, attrs):
        performance = attrs["performance"]
        row = attrs["row"]
        seat = attrs["seat"]
        hall = performance.theatre_hall

        if row < 1 or row > hall.rows:
            raise serializers.ValidationError(
                {"row": f"Row must be in range 1..{hall.rows}"}
            )
        if seat < 1 or seat > hall.seats_in_row:
            raise serializers.ValidationError(
                {"seat": f"Seat must be in range 1..{hall.seats_in_row}"}
            )

        return attrs


class TicketListSerializer(serializers.ModelSerializer):
    performance = PerformanceListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user
        reservation = Reservation.objects.create(user=user)

        for ticket_data in tickets_data:
            Ticket.objects.create(reservation=reservation, **ticket_data)

        return reservation


class ReservationListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")
