"""
Author: cg8-5712
Date: 2025-04-20
Version: 1.0.0
License: GPL-3.0
LastEditTime: 2025-04-25 19:30:00
Title: 机场信息查询插件
Description: 该插件允许用户通过机场的 ICAO 代码查询机场信息。
             结果可以以文本或图片的形式显示。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union
from datetime import datetime
import aiohttp
import asyncio

@dataclass
class AirportInfo:
    """机场信息数据模型"""
    station_code: str
    icao_id: str
    iata_id: str
    faa_id: Union[str, None]
    name: str
    state: str
    country: str
    source: str
    type: str
    lat: float
    lon: float
    elev: int
    magdec: str
    owner: str
    runways: List[Dict] = field(default_factory=list)
    rwy_num: str = "N/A"
    rwy_length: str = "N/A"
    rwy_type: str = "N/A"
    services: str = "N/A"
    tower: str = "N/A"
    beacon: str = "N/A"
    operations: Union[str, None] = "N/A"
    passengers: Union[str, None] = "N/A"
    freqs: Union[str, None] = "N/A"
    priority: str = "N/A"

    @staticmethod
    async def get_airport_info(station_code: str) -> Union['AirportInfo', str]:
        """获取机场信息"""
        url = f"https://aviationweather.gov/api/data/airport?ids={station_code}&format=json"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        return "获取数据失败"
                    data = await response.json()
            except asyncio.TimeoutError:
                return "请求超时"
            except aiohttp.ClientError as e:
                return f"请求失败: {e}"

        if not data or not data[0]:
            return "未找到机场信息"

        airport_data = data[0]
        return AirportInfo(
            station_code=station_code,
            icao_id=airport_data.get('icaoId', 'N/A'),
            iata_id=airport_data.get('iataId', 'N/A'),
            faa_id=airport_data.get('faaId', None),
            name=airport_data.get('name', 'N/A'),
            state=airport_data.get('state', 'N/A'),
            country=airport_data.get('country', 'N/A'),
            source=airport_data.get('source', 'N/A'),
            type=airport_data.get('type', 'N/A'),
            lat=airport_data.get('lat', 0.0),
            lon=airport_data.get('lon', 0.0),
            elev=airport_data.get('elev', 0),
            magdec=airport_data.get('magdec', 'N/A'),
            owner=airport_data.get('owner', 'N/A'),
            runways=airport_data.get('runways', []),
            rwy_num=str(len(airport_data.get('runways', []))),
            rwy_length=AirportInfo._determine_runway_length(airport_data.get('runways', [])),
            rwy_type=AirportInfo._determine_runway_type(airport_data.get('runways', [])),
            services=airport_data.get('services', 'N/A'),
            tower=airport_data.get('tower', 'N/A'),
            beacon=airport_data.get('beacon', 'N/A'),
            operations=airport_data.get('operations', None),
            passengers=airport_data.get('passengers', None),
            freqs=airport_data.get('freqs', None),
            priority=airport_data.get('priority', 'N/A')
        )

    @staticmethod
    def _determine_runway_length(runways: List[Dict]) -> str:
        """根据跑道长度判断跑道类型"""
        if not runways:
            return "N/A"
        max_length = max([int(r['dimension'].split('x')[0]) for r in runways])
        if max_length > 12000:
            return "L"
        elif 6000 < max_length <= 12000:
            return "M"
        else:
            return "S"

    @staticmethod
    def _determine_runway_type(runways: List[Dict]) -> str:
        """确定跑道表面类型"""
        if not runways:
            return "N/A"
        # 假设所有跑道类型相同
        return runways[0].get('surface', 'N/A')

    @staticmethod
    def format_text_output(airport_data: 'AirportInfo') -> str:
        """格式化文本输出"""
        output = f"""== {airport_data.name} 机场信息 ==
ICAO 代码: {airport_data.icao_id}
IATA 代码: {airport_data.iata_id or 'N/A'}
FAA 代码: {airport_data.faa_id or 'N/A'}
位置: {airport_data.lat}, {airport_data.lon}
海拔: {airport_data.elev} 米
磁偏角: {airport_data.magdec}
所属: {airport_data.owner}
跑道数量: {airport_data.rwy_num}
跑道长度: {airport_data.rwy_length}
跑道类型: {airport_data.rwy_type}
服务: {airport_data.services}
塔台: {airport_data.tower}
信标: {airport_data.beacon}
运营状态: {airport_data.operations or 'N/A'}
年旅客吞吐量: {airport_data.passengers or 'N/A'}
频率: {airport_data.freqs or 'N/A'}
优先级: {airport_data.priority}

== 跑道信息 =="""

        for runway in airport_data.runways:
            output += f"""
跑道编号: {runway['id']}
尺寸: {runway['dimension']}
表面类型: {runway['surface']}
方位角: {runway['alignment']}"""

        return output

    @staticmethod
    def prepare_template_data(airport_data: 'AirportInfo') -> Dict:
        """准备模板数据"""
        runway_rows = []
        for runway in airport_data.runways:
            runway_rows.append({
                "id": runway['id'],
                "dimension": runway['dimension'],
                "surface": runway['surface'],
                "alignment": runway['alignment']
            })

        return {
            "station_code": airport_data.station_code,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": airport_data.name,
            "icao_id": airport_data.icao_id,
            "iata_id": airport_data.iata_id or 'N/A',
            "faa_id": airport_data.faa_id or 'N/A',
            "lat": airport_data.lat,
            "lon": airport_data.lon,
            "elev": airport_data.elev,
            "magdec": airport_data.magdec,
            "owner": airport_data.owner,
            "rwy_num": airport_data.rwy_num,
            "rwy_length": airport_data.rwy_length,
            "rwy_type": airport_data.rwy_type,
            "services": airport_data.services,
            "tower": airport_data.tower,
            "beacon": airport_data.beacon,
            "operations": airport_data.operations or 'N/A',
            "passengers": airport_data.passengers or 'N/A',
            "freqs": airport_data.freqs or 'N/A',
            "priority": airport_data.priority,
            "runways": runway_rows
        }