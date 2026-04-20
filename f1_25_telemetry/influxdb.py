"""
Converts F1 25 telemetry packets to InfluxDB line protocol points.

Requires influxdb-client: pip install influxdb-client
"""

import time
from typing import List, Optional

from f1_25_telemetry.packets import (
    PacketCarTelemetryData,
    PacketLapData,
    PacketCarStatusData,
    PacketCarDamageData,
    PacketSessionData,
    PacketMotionData,
    PacketMotionExData,
    PacketParticipantsData,
    PacketFinalClassificationData,
    PacketSessionHistoryData,
)

try:
    from influxdb_client import Point
    from influxdb_client.client.write_api import WriteOptions
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False


WHEEL_POSITIONS = ['rear_left', 'rear_right', 'front_left', 'front_right']


def _tags(session_uid: int, car_index: int) -> dict:
    return {
        'session_uid': str(session_uid),
        'car_index': str(car_index),
    }


def _make_point(measurement: str, tags: dict, fields: dict, timestamp_ns: Optional[int] = None) -> 'Point':
    if not INFLUXDB_AVAILABLE:
        raise ImportError('influxdb-client is required: pip install influxdb-client')

    p = Point(measurement)
    for k, v in tags.items():
        p = p.tag(k, v)
    for k, v in fields.items():
        if v is not None:
            p = p.field(k, v)
    if timestamp_ns is not None:
        p = p.time(timestamp_ns)
    return p


def packet_to_points(packet, timestamp_ns: Optional[int] = None) -> List['Point']:
    """Convert any supported F1 25 packet to a list of InfluxDB Points."""
    if timestamp_ns is None:
        timestamp_ns = time.time_ns()

    if isinstance(packet, PacketCarTelemetryData):
        return _car_telemetry_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketLapData):
        return _lap_data_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketCarStatusData):
        return _car_status_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketCarDamageData):
        return _car_damage_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketSessionData):
        return _session_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketMotionData):
        return _motion_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketMotionExData):
        return _motion_ex_to_points(packet, timestamp_ns)
    elif isinstance(packet, PacketFinalClassificationData):
        return _final_classification_to_points(packet, timestamp_ns)

    return []


def _car_telemetry_to_points(packet: PacketCarTelemetryData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i, car in enumerate(packet.car_telemetry_data):
        tags = _tags(session_uid, i)
        fields = {
            'speed': int(car.speed),
            'throttle': round(car.throttle, 4),
            'brake': round(car.brake, 4),
            'steer': round(car.steer, 4),
            'clutch': int(car.clutch),
            'gear': int(car.gear),
            'engine_rpm': int(car.engine_rpm),
            'drs': int(car.drs),
            'rev_lights_percent': int(car.rev_lights_percent),
            'engine_temperature': int(car.engine_temperature),
        }

        for j, pos in enumerate(WHEEL_POSITIONS):
            fields[f'brakes_temp_{pos}'] = int(car.brakes_temperature[j])
            fields[f'tyre_surface_temp_{pos}'] = int(car.tyres_surface_temperature[j])
            fields[f'tyre_inner_temp_{pos}'] = int(car.tyres_inner_temperature[j])
            fields[f'tyre_pressure_{pos}'] = round(car.tyres_pressure[j], 3)
            fields[f'surface_type_{pos}'] = int(car.surface_type[j])

        points.append(_make_point('car_telemetry', tags, fields, timestamp_ns))

    return points


def _lap_data_to_points(packet: PacketLapData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i, lap in enumerate(packet.lap_data):
        tags = _tags(session_uid, i)
        fields = {
            'last_lap_time_ms': int(lap.last_lap_time_in_ms),
            'current_lap_time_ms': int(lap.current_lap_time_in_ms),
            'sector1_time_ms': int(lap.sector1_time_ms_part) + int(lap.sector1_time_minutes_part) * 60000,
            'sector2_time_ms': int(lap.sector2_time_ms_part) + int(lap.sector2_time_minutes_part) * 60000,
            'delta_to_car_in_front_ms': int(lap.delta_to_car_in_front_ms_part) + int(lap.delta_to_car_in_front_minutes_part) * 60000,
            'delta_to_race_leader_ms': int(lap.delta_to_race_leader_ms_part) + int(lap.delta_to_race_leader_minutes_part) * 60000,
            'lap_distance': round(lap.lap_distance, 3),
            'total_distance': round(lap.total_distance, 3),
            'safety_car_delta': round(lap.safety_car_delta, 3),
            'car_position': int(lap.car_position),
            'current_lap_num': int(lap.current_lap_num),
            'pit_status': int(lap.pit_status),
            'num_pit_stops': int(lap.num_pit_stops),
            'sector': int(lap.sector),
            'current_lap_invalid': int(lap.current_lap_invalid),
            'penalties': int(lap.penalties),
            'total_warnings': int(lap.total_warnings),
            'grid_position': int(lap.grid_position),
            'driver_status': int(lap.driver_status),
            'result_status': int(lap.result_status),
            'pit_lane_time_in_lane_ms': int(lap.pit_lane_time_in_lane_in_ms),
            'pit_stop_timer_ms': int(lap.pit_stop_timer_in_ms),
            'speed_trap_fastest_speed': round(lap.speed_trap_fastest_speed, 3),
        }
        points.append(_make_point('lap_data', tags, fields, timestamp_ns))

    return points


def _car_status_to_points(packet: PacketCarStatusData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i, status in enumerate(packet.car_status_data):
        tags = _tags(session_uid, i)
        fields = {
            'traction_control': int(status.traction_control),
            'anti_lock_brakes': int(status.anti_lock_brakes),
            'fuel_mix': int(status.fuel_mix),
            'front_brake_bias': int(status.front_brake_bias),
            'pit_limiter_status': int(status.pit_limiter_status),
            'fuel_in_tank': round(status.fuel_in_tank, 4),
            'fuel_capacity': round(status.fuel_capacity, 4),
            'fuel_remaining_laps': round(status.fuel_remaining_laps, 4),
            'max_rpm': int(status.max_rpm),
            'idle_rpm': int(status.idle_rpm),
            'max_gears': int(status.max_gears),
            'drs_allowed': int(status.drs_allowed),
            'drs_activation_distance': int(status.drs_activation_distance),
            'actual_tyre_compound': int(status.actual_tyre_compound),
            'visual_tyre_compound': int(status.visual_tyre_compound),
            'tyres_age_laps': int(status.tyres_age_laps),
            'vehicle_fia_flags': int(status.vehicle_fia_flags),
            'engine_power_ice': round(status.engine_power_ice, 2),
            'engine_power_mguk': round(status.engine_power_mguk, 2),
            'ers_store_energy': round(status.ers_store_energy, 2),
            'ers_deploy_mode': int(status.ers_deploy_mode),
            'ers_harvested_this_lap_mguk': round(status.ers_harvested_this_lap_mguk, 2),
            'ers_harvested_this_lap_mguh': round(status.ers_harvested_this_lap_mguh, 2),
            'ers_deployed_this_lap': round(status.ers_deployed_this_lap, 2),
            'network_paused': int(status.network_paused),
        }
        points.append(_make_point('car_status', tags, fields, timestamp_ns))

    return points


def _car_damage_to_points(packet: PacketCarDamageData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i, damage in enumerate(packet.car_damage_data):
        tags = _tags(session_uid, i)
        fields = {
            'front_left_wing_damage': int(damage.front_left_wing_damage),
            'front_right_wing_damage': int(damage.front_right_wing_damage),
            'rear_wing_damage': int(damage.rear_wing_damage),
            'floor_damage': int(damage.floor_damage),
            'diffuser_damage': int(damage.diffuser_damage),
            'sidepod_damage': int(damage.sidepod_damage),
            'drs_fault': int(damage.drs_fault),
            'ers_fault': int(damage.ers_fault),
            'gearbox_damage': int(damage.gearbox_damage),
            'engine_damage': int(damage.engine_damage),
            'engine_mguh_wear': int(damage.engine_mguh_wear),
            'engine_es_wear': int(damage.engine_es_wear),
            'engine_ce_wear': int(damage.engine_ce_wear),
            'engine_ice_wear': int(damage.engine_ice_wear),
            'engine_mguk_wear': int(damage.engine_mguk_wear),
            'engine_tc_wear': int(damage.engine_tc_wear),
            'engine_blown': int(damage.engine_blown),
            'engine_seized': int(damage.engine_seized),
        }
        for j, pos in enumerate(WHEEL_POSITIONS):
            fields[f'tyre_wear_{pos}'] = round(damage.tyres_wear[j], 4)
            fields[f'tyre_damage_{pos}'] = int(damage.tyres_damage[j])
            fields[f'brakes_damage_{pos}'] = int(damage.brakes_damage[j])
            fields[f'tyre_blisters_{pos}'] = int(damage.tyre_blisters[j])

        points.append(_make_point('car_damage', tags, fields, timestamp_ns))

    return points


def _session_to_points(packet: PacketSessionData, timestamp_ns: int) -> List['Point']:
    tags = {'session_uid': str(packet.header.session_uid)}
    fields = {
        'weather': int(packet.weather),
        'track_temperature': int(packet.track_temperature),
        'air_temperature': int(packet.air_temperature),
        'total_laps': int(packet.total_laps),
        'track_length': int(packet.track_length),
        'session_type': int(packet.session_type),
        'track_id': int(packet.track_id),
        'session_time_left': int(packet.session_time_left),
        'session_duration': int(packet.session_duration),
        'pit_speed_limit': int(packet.pit_speed_limit),
        'safety_car_status': int(packet.safety_car_status),
        'ai_difficulty': int(packet.ai_difficulty),
        'num_safety_car_periods': int(packet.num_safety_car_periods),
        'num_virtual_safety_car_periods': int(packet.num_virtual_safety_car_periods),
        'num_red_flag_periods': int(packet.num_red_flag_periods),
        'forecast_accuracy': int(packet.forecast_accuracy),
    }
    return [_make_point('session', tags, fields, timestamp_ns)]


def _motion_to_points(packet: PacketMotionData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i, motion in enumerate(packet.car_motion_data):
        tags = _tags(session_uid, i)
        fields = {
            'world_position_x': round(motion.world_position_x, 3),
            'world_position_y': round(motion.world_position_y, 3),
            'world_position_z': round(motion.world_position_z, 3),
            'world_velocity_x': round(motion.world_velocity_x, 3),
            'world_velocity_y': round(motion.world_velocity_y, 3),
            'world_velocity_z': round(motion.world_velocity_z, 3),
            'g_force_lateral': round(motion.g_force_lateral, 4),
            'g_force_longitudinal': round(motion.g_force_longitudinal, 4),
            'g_force_vertical': round(motion.g_force_vertical, 4),
            'yaw': round(motion.yaw, 4),
            'pitch': round(motion.pitch, 4),
            'roll': round(motion.roll, 4),
        }
        points.append(_make_point('car_motion', tags, fields, timestamp_ns))

    return points


def _motion_ex_to_points(packet: PacketMotionExData, timestamp_ns: int) -> List['Point']:
    session_uid = packet.header.session_uid
    player_idx = packet.header.player_car_index
    tags = _tags(session_uid, player_idx)

    fields = {
        'height_of_cog_above_ground': round(packet.height_of_cog_above_ground, 4),
        'local_velocity_x': round(packet.local_velocity_x, 4),
        'local_velocity_y': round(packet.local_velocity_y, 4),
        'local_velocity_z': round(packet.local_velocity_z, 4),
        'angular_velocity_x': round(packet.angular_velocity_x, 4),
        'angular_velocity_y': round(packet.angular_velocity_y, 4),
        'angular_velocity_z': round(packet.angular_velocity_z, 4),
        'angular_acceleration_x': round(packet.angular_acceleration_x, 4),
        'angular_acceleration_y': round(packet.angular_acceleration_y, 4),
        'angular_acceleration_z': round(packet.angular_acceleration_z, 4),
        'front_wheels_angle': round(packet.front_wheels_angle, 4),
        'front_aero_height': round(packet.front_aero_height, 4),
        'rear_aero_height': round(packet.rear_aero_height, 4),
        'front_roll_angle': round(packet.front_roll_angle, 4),
        'rear_roll_angle': round(packet.rear_roll_angle, 4),
        'chassis_yaw': round(packet.chassis_yaw, 4),
        'chassis_pitch': round(packet.chassis_pitch, 4),
    }
    for j, pos in enumerate(WHEEL_POSITIONS):
        fields[f'suspension_position_{pos}'] = round(packet.suspension_position[j], 4)
        fields[f'suspension_velocity_{pos}'] = round(packet.suspension_velocity[j], 4)
        fields[f'suspension_acceleration_{pos}'] = round(packet.suspension_acceleration[j], 4)
        fields[f'wheel_speed_{pos}'] = round(packet.wheel_speed[j], 4)
        fields[f'wheel_slip_ratio_{pos}'] = round(packet.wheel_slip_ratio[j], 4)
        fields[f'wheel_slip_angle_{pos}'] = round(packet.wheel_slip_angle[j], 4)
        fields[f'wheel_lat_force_{pos}'] = round(packet.wheel_lat_force[j], 4)
        fields[f'wheel_long_force_{pos}'] = round(packet.wheel_long_force[j], 4)
        fields[f'wheel_vert_force_{pos}'] = round(packet.wheel_vert_force[j], 4)
        fields[f'wheel_camber_{pos}'] = round(packet.wheel_camber[j], 4)
        fields[f'wheel_camber_gain_{pos}'] = round(packet.wheel_camber_gain[j], 4)

    return [_make_point('car_motion_ex', tags, fields, timestamp_ns)]


def _final_classification_to_points(packet: PacketFinalClassificationData, timestamp_ns: int) -> List['Point']:
    points = []
    session_uid = packet.header.session_uid

    for i in range(packet.num_cars):
        result = packet.classification_data[i]
        tags = _tags(session_uid, i)
        fields = {
            'position': int(result.position),
            'num_laps': int(result.num_laps),
            'grid_position': int(result.grid_position),
            'points': int(result.points),
            'num_pit_stops': int(result.num_pit_stops),
            'result_status': int(result.result_status),
            'result_reason': int(result.result_reason),
            'best_lap_time_ms': int(result.best_lap_time_in_ms),
            'total_race_time': round(result.total_race_time, 3),
            'penalties_time': int(result.penalties_time),
            'num_penalties': int(result.num_penalties),
            'num_tyre_stints': int(result.num_tyre_stints),
        }
        points.append(_make_point('final_classification', tags, fields, timestamp_ns))

    return points


class InfluxDBWriter:
    """
    Convenience wrapper that writes F1 25 telemetry data to InfluxDB.

    Usage:
        writer = InfluxDBWriter(
            url='http://localhost:8086',
            token='my-token',
            org='my-org',
            bucket='f1-telemetry',
        )
        writer.write(packet)
        writer.close()
    """

    def __init__(self, url: str, token: str, org: str, bucket: str, batch_size: int = 500):
        if not INFLUXDB_AVAILABLE:
            raise ImportError('influxdb-client is required: pip install influxdb-client')

        from influxdb_client import InfluxDBClient

        self.bucket = bucket
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(
            write_options=WriteOptions(batch_size=batch_size)
        )

    def write(self, packet, timestamp_ns: Optional[int] = None) -> int:
        """Write a packet to InfluxDB. Returns the number of points written."""
        points = packet_to_points(packet, timestamp_ns)
        if points:
            self.write_api.write(bucket=self.bucket, record=points)
        return len(points)

    def close(self):
        self.write_api.close()
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
