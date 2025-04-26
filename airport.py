from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional
from datetime import datetime
import aiohttp
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Runway:
    """Runway data model"""
    id: str
    dimension: str
    surface: str
    alignment: str
    length: int = 0
    width: int = 0

    def __post_init__(self):
        try:
            dims = self.dimension.split('x')
            self.length = int(dims[0])
            self.width = int(dims[1])
        except (IndexError, ValueError) as e:
            logger.warning(f"Runway dimension parsing error: {e}")

    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "dimension": self.dimension,
            "surface": self.surface_type_map.get(self.surface, "Unknown"),
            "alignment": self.alignment,
            "length": self.length,
            "width": self.width
        }

    surface_type_map = {
        "H": "Hard Surface",
        "S": "Soft Surface",
        "G": "Grass",
        "W": "Water",
        "A": "Asphalt",
        "C": "Concrete",
        "T": "Tar",
        "U": "Unpaved"
    }

@dataclass
class AirportInfo:
    """Airport information data model"""
    station_code: str
    icao_id: str
    iata_id: Optional[str] = None
    faa_id: Optional[str] = None
    name: str = "N/A"
    state: str = "N/A"
    country: str = "N/A"
    source: str = "N/A"
    type: str = "N/A"
    lat: float = 0.0
    lon: float = 0.0
    elev: int = 0
    magdec: str = "N/A"
    owner: str = "N/A"
    runways: List[Runway] = field(default_factory=list)
    rwy_num: str = "N/A"
    rwy_length: str = "N/A"
    rwy_type: str = "N/A"
    services: str = "N/A"
    tower: str = "N/A"
    beacon: str = "N/A"
    operations: Optional[str] = None
    passengers: Optional[str] = None
    freqs: Dict[str, str] = field(default_factory=dict)
    priority: str = "N/A"

    @staticmethod
    async def get_airport_info(station_code: str) -> Union['AirportInfo', str]:
        """Get airport information"""
        url = f"https://aviationweather.gov/api/data/airport?ids={station_code}&format=json"
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return f"Failed to get data: HTTP {response.status}"
                    data = await response.json()
            except asyncio.TimeoutError:
                return "Request timeout"
            except aiohttp.ClientError as e:
                return f"Request failed: {str(e)}"

        if not data or len(data) == 0:
            return " Airport information not found"

        airport_data = data[0]
        runways = [
            Runway(
                id=r['id'],
                dimension=r['dimension'],
                surface=r['surface'],
                alignment=r['alignment']
            ) for r in airport_data.get('runways', [])
        ]

        freqs = AirportInfo._parse_frequencies(airport_data.get('freqs'))

        return AirportInfo(
            station_code=station_code,
            icao_id=airport_data.get('icaoId', 'N/A'),
            iata_id=airport_data.get('iataId'),
            faa_id=airport_data.get('faaId'),
            name=airport_data.get('name', 'N/A'),
            state=airport_data.get('state', 'N/A'),
            country=airport_data.get('country', 'N/A'),
            source=airport_data.get('source', 'N/A'),
            type=airport_data.get('type', 'N/A'),
            lat=float(airport_data.get('lat', 0.0)),
            lon=float(airport_data.get('lon', 0.0)),
            elev=int(airport_data.get('elev', 0)),
            magdec=airport_data.get('magdec', 'N/A'),
            owner=AirportInfo._parse_owner_type(airport_data.get('owner', '')),
            runways=runways,
            rwy_num=str(len(runways)),
            rwy_length=AirportInfo._determine_runway_length(runways),
            rwy_type=AirportInfo._determine_runway_type(runways),
            services=AirportInfo._parse_services(airport_data.get('services', '')),
            tower=AirportInfo._parse_tower_status(airport_data.get('tower', '')),
            beacon=AirportInfo._parse_beacon_status(airport_data.get('beacon', '')),
            operations=airport_data.get('operations'),
            passengers=airport_data.get('passengers'),
            freqs=freqs,
            priority=airport_data.get('priority', 'N/A')
        )

    @staticmethod
    def _parse_frequencies(freq_str: Optional[str]) -> Dict[str, str]:
        """Parse frequency string"""
        if not freq_str:
            return {}

        freqs = {}
        try:
            for freq in freq_str.split(';'):
                if ',' not in freq:
                    continue
                service, frequency = freq.split(',')
                freqs[service.strip()] = frequency.strip()
        except Exception as e:
            logger.error(f"Frequency parsing error: {e}")
        return freqs

    @staticmethod
    def _parse_owner_type(owner: str) -> str:
        """Parse ownership type"""
        owner_map = {
            'P': 'Public Airport',
            'R': 'Private Airport',
            'M': 'Military Airport',
            'J': 'Joint Use Airport'
        }
        return owner_map.get(owner, 'Unknown Ownership')

    @staticmethod
    def _parse_services(services: str) -> str:
        """Parse service identifier"""
        service_map = {
            'S': 'Full Service',
            'P': 'Partial Service',
            'L': 'Limited Service',
            'N': 'No Service'
        }
        return service_map.get(services, 'Unknown Service Type')

    @staticmethod
    def _parse_tower_status(tower: str) -> str:
        """Parse tower status"""
        tower_map = {
            'T': 'Tower Available',
            'N': 'No Tower'
        }
        return tower_map.get(tower, 'Unknown Tower Status')

    @staticmethod
    def _parse_beacon_status(beacon: str) -> str:
        """Parse beacon status"""
        beacon_map = {
            'B': 'Beacon Available',
            'N': 'No Beacon'
        }
        return beacon_map.get(beacon, 'Unknown Beacon Status')

    @staticmethod
    def _determine_runway_length(runways: List[Runway]) -> str:
        """Determine runway class based on length"""
        if not runways:
            return "N/A"
        max_length = max(runway.length for runway in runways)
        if max_length > 12000:
            return "Large Airport"
        elif 6000 < max_length <= 12000:
            return "Medium Airport"
        else:
            return "Small Airport"

    @staticmethod
    def _determine_runway_type(runways: List[Runway]) -> str:
        """Determine runway surface type"""
        if not runways:
            return "N/A"
        return Runway.surface_type_map.get(runways[0].surface, "Unknown Type")

    def format_text_output(self) -> str:
        """Format text output"""
        output = f"""== {self.name} Airport Information ==
ICAO Code: {self.icao_id}
IATA Code: {self.iata_id or 'N/A'}
FAA Code: {self.faa_id or 'N/A'}
Location: {self.lat}, {self.lon}
Elevation: {self.elev} meters
Magnetic Declination: {self.magdec}
Ownership: {self.owner}
Number of Runways: {self.rwy_num}
Airport Class: {self.rwy_length}
Runway Type: {self.rwy_type}
Services: {self.services}
Tower: {self.tower}
Beacon: {self.beacon}
Operations Status: {self.operations or 'N/A'}
Annual Passengers: {self.passengers or 'N/A'} million
Frequencies:"""

        for service, freq in self.freqs.items():
            output += f"\n  {service}: {freq}"

        output += "\n\n== Runway Information =="
        for runway in self.runways:
            rwy_dict = runway.to_dict()
            output += f"""
Runway Number: {rwy_dict['id']}
Dimensions: {rwy_dict['length']}x{rwy_dict['width']} meters
Surface Type: {rwy_dict['surface']}
Alignment: {rwy_dict['alignment']}°"""

        return output

    def prepare_template_data(self) -> Dict:
        """Prepare template data"""
        return {
            "station_code": self.station_code,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.name,
            "icao_id": self.icao_id,
            "iata_id": self.iata_id or 'N/A',
            "faa_id": self.faa_id or 'N/A',
            "state": self.state,
            "country": self.country,
            "source": self.source,
            "type": self.type,
            "lat": self.lat,
            "lon": self.lon,
            "elev": self.elev,
            "magdec": self.magdec,
            "owner": self.owner,
            "rwy_num": self.rwy_num,
            "rwy_length": self.rwy_length,
            "rwy_type": self.rwy_type,
            "services": self.services,
            "tower": self.tower,
            "beacon": self.beacon,
            "operations": self.operations or 'N/A',
            "passengers": f"{self.passengers or 'N/A'} million",
            "freqs": self.freqs,
            "priority": self.priority,
            "runways": [runway.to_dict() for runway in self.runways]
        }