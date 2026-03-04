from typing import List

from sqlalchemy.orm import Session

from ..models import Location, WeatherData
from ..schemas import LocationCreateSchema, LocationSchema, WeatherDataSchema


class WeatherCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_weather_data(self, weather_data: WeatherDataSchema) -> WeatherDataSchema:
        db_weather_data = WeatherData(**weather_data.model_dump())
        self.db.add(db_weather_data)
        self.db.commit()
        self.db.refresh(db_weather_data)
        return db_weather_data

    def get_weather_data(self, location_id: int) -> WeatherData:
        return (
            self.db.query(WeatherData)
            .filter(WeatherData.location_id == location_id)
            .all()
        )

    def delete_weather_data(self, weather_data_id: int) -> bool:
        db_weather_data = self.get_weather_data(weather_data_id)
        if db_weather_data:
            self.db.delete(db_weather_data)
            self.db.commit()
            return True
        return False


class LocationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_location(self, location: LocationCreateSchema) -> LocationSchema:
        db_location = Location(**location.model_dump())
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location

    def get_location(self, location_id: int) -> Location:
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_locations(self) -> List[Location]:
        return self.db.query(Location).all()

    def delete_location(self, location_id: int) -> Location:
        location = self.get_location(location_id)
        if location:
            self.db.delete(location)
            self.db.commit()
        return location
