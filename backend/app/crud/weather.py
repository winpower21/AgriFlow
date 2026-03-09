"""
Weather and Location CRUD module.

Provides two service classes:

  - **WeatherCRUD** — manages weather data records linked to locations.
    Weather observations are stored per-location and can be retrieved as
    a historical series for climate tracking and agricultural planning.

  - **LocationCRUD** — manages standalone Location records (GPS
    coordinates, addresses).  Locations may be associated with
    plantations or used independently for weather data collection.

Note: These classes are *not* exported via ``crud/__init__.py`` and
must be imported directly::

    from app.crud.weather import WeatherCRUD, LocationCRUD

Potential issues to be aware of:
  - ``WeatherCRUD.get_weather_data()`` returns a *list* of WeatherData
    (via ``.all()``) but the return type annotation says single
    ``WeatherData``.  ``delete_weather_data()`` passes an ID to
    ``get_weather_data()`` which actually filters by ``location_id``,
    so the delete may not work as intended.
  - ``LocationCRUD.delete_location()`` returns the deleted Location
    object (or None if not found) rather than a boolean, unlike the
    convention used by other services.
"""

from typing import List

from sqlalchemy.orm import Session

from ..models import Location, WeatherData
from ..schemas import LocationCreateSchema, LocationSchema, WeatherDataSchema


class WeatherCRUD:
    """Service class for weather data database operations.

    Follows the service-object pattern: instantiate with a SQLAlchemy
    ``Session``, then call methods to create, query, or delete weather
    observation records.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_weather_data(self, weather_data: WeatherDataSchema) -> WeatherDataSchema:
        """Persist a new weather observation record.

        The incoming Pydantic schema is dumped to a dict and unpacked
        into the WeatherData ORM constructor.  The ``location_id`` FK
        in the schema ties the observation to a specific Location.
        """
        db_weather_data = WeatherData(**weather_data.model_dump())
        self.db.add(db_weather_data)
        self.db.commit()
        self.db.refresh(db_weather_data)
        return db_weather_data

    def get_weather_data(self, location_id: int) -> WeatherData:
        """Retrieve all weather observations for a given location.

        Returns a list of WeatherData rows filtered by ``location_id``,
        ordered by the database's default (insertion order / primary key).

        Note: The return type annotation says single ``WeatherData`` but
        the implementation returns a list via ``.all()``.
        """
        return (
            self.db.query(WeatherData)
            .filter(WeatherData.location_id == location_id)
            .all()
        )

    def delete_weather_data(self, weather_data_id: int) -> bool:
        """Delete a weather observation by ID.

        Caveat: This currently delegates to ``get_weather_data()`` which
        filters by ``location_id``, not by primary key.  As a result the
        ``weather_data_id`` argument is treated as a ``location_id``, and
        the returned list (not a single object) is passed to
        ``session.delete()``, which may raise an error.
        """
        db_weather_data = self.get_weather_data(weather_data_id)
        if db_weather_data:
            self.db.delete(db_weather_data)
            self.db.commit()
            return True
        return False


class LocationCRUD:
    """Service class for location database operations.

    Manages standalone Location records that can be linked to
    plantations or used as reference points for weather data.

    Attributes:
        db: The active SQLAlchemy session used for all queries.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_location(self, location: LocationCreateSchema) -> LocationSchema:
        """Create a new location record from the validated schema."""
        db_location = Location(**location.model_dump())
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def get_location(self, location_id: int) -> Location:
        """Retrieve a single location by primary key, or None if not found."""
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_locations(self) -> List[Location]:
        """Retrieve all location records."""
        return self.db.query(Location).all()

    def delete_location(self, location_id: int) -> Location:
        """Delete a location by ID and return the deleted object.

        Returns the Location that was removed, or None if no location
        with the given ID was found.  Unlike other services that return
        a boolean, this method returns the ORM object itself so the
        caller can inspect it after deletion if needed.
        """
        location = self.get_location(location_id)
        if location:
            self.db.delete(location)
            self.db.commit()
        return location
