from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json

class Pharmacy:
    """
    A class representing a pharmacy with essential details such as name, address,
    contact information, and OpenStreetMap (OSM) data such as coordinates and address details.
    """
    
    def __init__(self, name:str, street:str, town:str, state:str=None, phone:str=None, fax:str=None, web:str=None, mail:str=None, gmaps:str=None):
        """Initializes a Pharmacy object with basic details.

        Args:
            name (str): The name of the pharmacy (e.g., "Engel-Apotheke")
            street (str): The street address of the pharmacy
            town (str): The town where the pharmacy is located
            state (str, optional): The state where the pharmacy is located. Defaults to None.
            phone (str, optional): The phone number. Defaults to None.
            fax (str, optional): The fax number. Defaults to None.
            web (str, optional): The website URL. Defaults to None.
            mail (str, optional): The email address. Defaults to None.
            gmaps (str, optional): Google Maps URL. Defaults to None.
        """
        self.name = name

        self.street = street
        self.town = town
        self.state = state

        self.phone = phone
        self.fax = fax

        self.web = web
        self.mail = mail
        self.gmaps = gmaps

        # OSM fields (optional)
        self._latitude: Optional[str] = None
        self._longitude: Optional[str] = None
        self._osm_address: Optional[str] = None

        self.__osm_data = None

    def update_with_osm(self, overwrite_cache:bool=False, fix_data:bool=True) -> None:
        """
        Updates the pharmacy instance with OpenStreetMap data, including the latitude, 
        longitude, and street address information. Optionally updates the name, state, 
        town, and other details based on OSM data.

        Args:
            overwrite_cache (bool, optional): If set to True, forces a re-fetch of the OSM data. Defaults to False.
            fix_data (bool, optional): If set to True, will update the pharmacy's street, town, and state from the OSM data if available. Defaults to True.
        """
        from notdienst_finder.crawlers import osm

        if self.__osm_data is None or overwrite_cache:
            self.__osm_data = osm.request_osm_data(self)

        if self.__osm_data:
            self._latitude = self.__osm_data.get("lat")
            self._longitude = self.__osm_data.get("lon")
            self._osm_address = self.__osm_data.get("display_name")

        if self.__osm_data and fix_data:
            self.street = self.__osm_data["address"]["road"]
            if "house_number" in self.__osm_data["address"].keys():
                self.street += " " + self.__osm_data["address"].get("house_number")
            
            if "town" in self.__osm_data["address"].keys():
                self.town = self.__osm_data["address"]["town"]

            if "state" in self.__osm_data["address"].keys():
                self.state = self.__osm_data["address"]["state"]

    @property
    def latitude(self) -> str:
        """
        Returns the latitude of the pharmacy. If not available, it fetches the OSM data.

        Returns:
            str: The latitude of the pharmacy as a string or None if not available.
        """
        if self._latitude is None:
            self.update_with_osm(overwrite_cache=False, fix_data=False)  # Fetch OSM data if latitude is not set
        return self._latitude

    @property
    def longitude(self) -> str:
        """
        Returns the longitude of the pharmacy. If not available, it fetches the OSM data.

        Returns:
            str: The longitude of the pharmacy as a string or None if not available.
        """
        if self._longitude is None:
            self.update_with_osm(overwrite_cache=False, fix_data=False)  # Fetch OSM data if longitude is not set
        return self._longitude

    def __repr__(self) -> str:
        """
        Provides a string representation of the pharmacy object.

        Returns:
            str: A string that represents the pharmacy object in the form: <Pharmacy {name} ({street}, {town}, {state})>
        """
        return f"<Pharmacy {self.name} ({self.street}, {self.town},  {self.state})>"
    
    def to_dict(self) -> Dict:
        """Converts the Pharmacy object to a dictionary."""
        return {
            "name": self.name,
            "street": self.street,
            "town": self.town,
            "state": self.state,
            "phone": self.phone,
            "fax": self.fax,
            "web": self.web,
            "mail": self.mail,
            "gmaps": self.gmaps,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "osm_address": self._osm_address,
            "osm_data" : self.__osm_data,
        }
    
    def to_json(self) -> str:
        """Converts the Pharmacy object to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Creates a Pharmacy object from a dictionary."""
        pharm = cls(
            name=data["name"],
            street=data["street"],
            town=data["town"],
            state=data.get("state"),
            phone=data.get("phone"),
            fax=data.get("fax"),
            web=data.get("web"),
            mail=data.get("mail"),
            gmaps=data.get("gmaps"),
        )
        pharm._latitude = data.get("latitude")
        pharm._longitude = data.get("longitude")

        pharm._osm_address = data.get("osm_address")
        pharm.__osm_data = data.get("osm_data")
        return pharm
    
    @classmethod
    def from_json(cls, json_str: str):
        """Creates a Pharmacy object from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    

    
def get_emergency_pharmacies(plz:str = "14467", state:str="Brandenburg", date: Optional[datetime] = None, limit: int = 4, morning_change: bool = True) -> List[Pharmacy]:
    """
    Fetches emergency pharmacies based on postal code, state, date, and other filters.

    Args:
        plz (str, optional): The postal code to filter pharmacies. Defaults to "14467".
        state (str, optional): The state to filter pharmacies. Defaults to "Brandenburg".
        date (Optional[int], optional): The specific date to filter pharmacies. Wil return today's information if None. Defaults to None.
        limit (int, optional): The maximum number of pharmacies to fetch. Defaults to 4.
        morning_change (bool, optional): If set to True, fetch pharmacies that are available in the morning before the switch on that day. Defaults to True.

    Raises:
        NotImplementedError: Raises an error if the information for currently unsupported states is requested.

    Returns:
        List[Pharmacy]: A list of Pharmacy objects that match the search criteria.
    """
    if date is None:
        date = datetime.now()

    if state.lower() in ["berlin", "brandenburg"]:
        from notdienst_finder.crawlers import lakbb
        pharmacies = lakbb.get_emergency_pharmacies(plz=plz, date=date, limit=limit, morning_change=morning_change)
    else:
        raise NotImplementedError(f"Your given state '{state}' is currently not yet supported!")
    
    return pharmacies
