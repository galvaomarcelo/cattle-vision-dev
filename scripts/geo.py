from pyproj import Geod


# WGS84 ellipsoid
WGS84 = Geod(ellps="WGS84")


def latlon_distance_m(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate geodesic distance between two latitude/longitude points.

    Coordinates are expected in decimal degrees.

    Returns:
        Distance in meters.
    """
    _, _, distance = WGS84.inv(
        longitude_1,
        latitude_1,
        longitude_2,
        latitude_2,
    )

    return abs(distance)


def bearing_deg(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate the forward bearing from point 1 to point 2.

    Returns:
        Bearing in degrees, normalized to [0, 360).
    """
    azimuth, _, _ = WGS84.inv(
        longitude_1,
        latitude_1,
        longitude_2,
        latitude_2,
    )

    return azimuth % 360.0