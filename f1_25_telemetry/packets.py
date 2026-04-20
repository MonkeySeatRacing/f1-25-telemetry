"""
F1 25 UDP telemetry packet structures.
Based on the EA F1 25 UDP specification.
"""

import ctypes
import json


def to_json(*args, **kwargs):
    kwargs.setdefault("indent", 2)
    kwargs["sort_keys"] = True
    kwargs["ensure_ascii"] = False
    kwargs["separators"] = (",", ": ")
    return json.dumps(*args, **kwargs)


class PacketMixin(object):
    def get_value(self, field):
        return self._format_type(getattr(self, field))

    def pack(self):
        return bytes(self)

    @classmethod
    def size(cls):
        return ctypes.sizeof(cls)

    @classmethod
    def unpack(cls, buffer):
        return cls.from_buffer_copy(buffer)

    def to_dict(self):
        return {k: self.get_value(k) for k, _ in self._fields_}

    def to_json(self):
        return to_json(self.to_dict())

    def _format_type(self, value):
        class_name = type(value).__name__

        if class_name == "float":
            return round(value, 3)

        if class_name == "bytes":
            return value.decode()

        if isinstance(value, ctypes.Array):
            return _format_array_type(value)

        if hasattr(value, "to_dict"):
            return value.to_dict()

        return value


def _format_array_type(value):
    results = []
    for item in value:
        if isinstance(item, Packet):
            results.append(item.to_dict())
        else:
            results.append(item)
    return results


class Packet(ctypes.LittleEndianStructure, PacketMixin):
    _pack_ = 1

    def __repr__(self):
        return self.to_json()


# -----------------------------------------------------------------------------
# Header - 29 bytes
# -----------------------------------------------------------------------------

class PacketHeader(Packet):
    _fields_ = [
        ("packet_format", ctypes.c_uint16),             # 2025
        ("game_year", ctypes.c_uint8),                  # Game year - last two digits e.g. 25
        ("game_major_version", ctypes.c_uint8),         # Game major version - "X.00"
        ("game_minor_version", ctypes.c_uint8),         # Game minor version - "1.XX"
        ("packet_version", ctypes.c_uint8),             # Version of this packet type
        ("packet_id", ctypes.c_uint8),                  # Identifier for the packet type
        ("session_uid", ctypes.c_uint64),               # Unique identifier for the session
        ("session_time", ctypes.c_float),               # Session timestamp
        ("frame_identifier", ctypes.c_uint32),          # Identifier for the frame
        ("overall_frame_identifier", ctypes.c_uint32),  # Overall frame identifier (no flashback reset)
        ("player_car_index", ctypes.c_uint8),           # Index of player's car in the array
        ("secondary_player_car_index", ctypes.c_uint8), # Index of secondary player's car (255 if none)
    ]


# -----------------------------------------------------------------------------
# Motion - 1349 bytes
# -----------------------------------------------------------------------------

class CarMotionData(Packet):
    _fields_ = [
        ("world_position_x", ctypes.c_float),      # World space X position - metres
        ("world_position_y", ctypes.c_float),      # World space Y position
        ("world_position_z", ctypes.c_float),      # World space Z position
        ("world_velocity_x", ctypes.c_float),      # Velocity in world space X - metres/s
        ("world_velocity_y", ctypes.c_float),      # Velocity in world space Y
        ("world_velocity_z", ctypes.c_float),      # Velocity in world space Z
        ("world_forward_dir_x", ctypes.c_int16),   # World space forward X direction (normalised)
        ("world_forward_dir_y", ctypes.c_int16),   # World space forward Y direction (normalised)
        ("world_forward_dir_z", ctypes.c_int16),   # World space forward Z direction (normalised)
        ("world_right_dir_x", ctypes.c_int16),     # World space right X direction (normalised)
        ("world_right_dir_y", ctypes.c_int16),     # World space right Y direction (normalised)
        ("world_right_dir_z", ctypes.c_int16),     # World space right Z direction (normalised)
        ("g_force_lateral", ctypes.c_float),       # Lateral G-Force component
        ("g_force_longitudinal", ctypes.c_float),  # Longitudinal G-Force component
        ("g_force_vertical", ctypes.c_float),      # Vertical G-Force component
        ("yaw", ctypes.c_float),                   # Yaw angle in radians
        ("pitch", ctypes.c_float),                 # Pitch angle in radians
        ("roll", ctypes.c_float),                  # Roll angle in radians
    ]


class PacketMotionData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_motion_data", CarMotionData * 22),
    ]


# -----------------------------------------------------------------------------
# Session - 753 bytes
# -----------------------------------------------------------------------------

class MarshalZone(Packet):
    _fields_ = [
        ("zone_start", ctypes.c_float),  # Fraction (0..1) of way through the lap
        ("zone_flag", ctypes.c_int8),    # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
    ]


class WeatherForecastSample(Packet):
    _fields_ = [
        ("session_type", ctypes.c_uint8),           # 0 = unknown, see appendix
        ("time_offset", ctypes.c_uint8),            # Time in minutes the forecast is for
        ("weather", ctypes.c_uint8),                # 0 = clear, 1 = light cloud, 2 = overcast, 3 = light rain, 4 = heavy rain, 5 = storm
        ("track_temperature", ctypes.c_int8),       # Track temp. in degrees celsius
        ("track_temperature_change", ctypes.c_int8),# Track temp. change - 0 = up, 1 = down, 2 = no change
        ("air_temperature", ctypes.c_int8),         # Air temp. in degrees celsius
        ("air_temperature_change", ctypes.c_int8),  # Air temp. change - 0 = up, 1 = down, 2 = no change
        ("rain_percentage", ctypes.c_uint8),        # Rain percentage (0-100)
    ]


class PacketSessionData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("weather", ctypes.c_uint8),                        # 0 = clear .. 5 = storm
        ("track_temperature", ctypes.c_int8),               # Track temp. in degrees celsius
        ("air_temperature", ctypes.c_int8),                 # Air temp. in degrees celsius
        ("total_laps", ctypes.c_uint8),                     # Total number of laps in this race
        ("track_length", ctypes.c_uint16),                  # Track length in metres
        ("session_type", ctypes.c_uint8),                   # 0 = unknown, see appendix
        ("track_id", ctypes.c_int8),                        # -1 for unknown, see appendix
        ("formula", ctypes.c_uint8),                        # Formula type, see appendix
        ("session_time_left", ctypes.c_uint16),             # Time left in session in seconds
        ("session_duration", ctypes.c_uint16),              # Session duration in seconds
        ("pit_speed_limit", ctypes.c_uint8),                # Pit speed limit in km/h
        ("game_paused", ctypes.c_uint8),                    # Whether the game is paused - network game only
        ("is_spectating", ctypes.c_uint8),                  # Whether the player is spectating
        ("spectator_car_index", ctypes.c_uint8),            # Index of the car being spectated
        ("sli_pro_native_support", ctypes.c_uint8),         # SLI Pro support, 0 = inactive, 1 = active
        ("num_marshal_zones", ctypes.c_uint8),              # Number of marshal zones to follow
        ("marshal_zones", MarshalZone * 21),                # List of marshal zones - max 21
        ("safety_car_status", ctypes.c_uint8),              # 0 = no safety car, 1 = full, 2 = virtual, 3 = formation lap
        ("network_game", ctypes.c_uint8),                   # 0 = offline, 1 = online
        ("num_weather_forecast_samples", ctypes.c_uint8),   # Number of weather samples to follow
        ("weather_forecast_samples", WeatherForecastSample * 64),  # Array of weather forecast samples
        ("forecast_accuracy", ctypes.c_uint8),              # 0 = Perfect, 1 = Approximate
        ("ai_difficulty", ctypes.c_uint8),                  # AI difficulty - 0-110
        ("season_link_identifier", ctypes.c_uint32),        # Identifier for season
        ("weekend_link_identifier", ctypes.c_uint32),       # Identifier for weekend
        ("session_link_identifier", ctypes.c_uint32),       # Identifier for session
        ("pit_stop_window_ideal_lap", ctypes.c_uint8),      # Ideal lap to pit on for current strategy (player)
        ("pit_stop_window_latest_lap", ctypes.c_uint8),     # Latest lap to pit on for current strategy (player)
        ("pit_stop_rejoin_position", ctypes.c_uint8),       # Predicted position to rejoin at (player)
        ("steering_assist", ctypes.c_uint8),                # 0 = off, 1 = on
        ("braking_assist", ctypes.c_uint8),                 # 0 = off, 1 = low, 2 = medium, 3 = high
        ("gearbox_assist", ctypes.c_uint8),                 # 1 = manual, 2 = manual & suggested gear, 3 = auto
        ("pit_assist", ctypes.c_uint8),                     # 0 = off, 1 = on
        ("pit_release_assist", ctypes.c_uint8),             # 0 = off, 1 = on
        ("ers_assist", ctypes.c_uint8),                     # 0 = off, 1 = on
        ("drs_assist", ctypes.c_uint8),                     # 0 = off, 1 = on
        ("dynamic_racing_line", ctypes.c_uint8),            # 0 = off, 1 = corners only, 2 = full
        ("dynamic_racing_line_type", ctypes.c_uint8),       # 0 = 2D, 1 = 3D
        ("game_mode", ctypes.c_uint8),                      # Game mode id - see appendix
        ("rule_set", ctypes.c_uint8),                       # Ruleset - see appendix
        ("time_of_day", ctypes.c_uint32),                   # Local time of day - minutes since midnight
        ("session_length", ctypes.c_uint8),                 # 0 = None, 2 = Very Short ... 7 = Full
        ("speed_units_lead_player", ctypes.c_uint8),        # 0 = MPH, 1 = KPH
        ("temperature_units_lead_player", ctypes.c_uint8),  # 0 = Celsius, 1 = Fahrenheit
        ("speed_units_secondary_player", ctypes.c_uint8),   # 0 = MPH, 1 = KPH
        ("temperature_units_secondary_player", ctypes.c_uint8),
        ("num_safety_car_periods", ctypes.c_uint8),         # Number of safety cars called during session
        ("num_virtual_safety_car_periods", ctypes.c_uint8), # Number of virtual safety cars called
        ("num_red_flag_periods", ctypes.c_uint8),           # Number of red flags called
        ("equal_car_performance", ctypes.c_uint8),          # 0 = Off, 1 = On
        ("recovery_mode", ctypes.c_uint8),                  # 0 = None, 1 = Flashbacks, 2 = Auto-recovery
        ("flashback_limit", ctypes.c_uint8),                # 0 = Low, 1 = Medium, 2 = High, 3 = Unlimited
        ("surface_type", ctypes.c_uint8),                   # 0 = Simplified, 1 = Realistic
        ("low_fuel_mode", ctypes.c_uint8),                  # 0 = Easy, 1 = Hard
        ("race_starts", ctypes.c_uint8),                    # 0 = Manual, 1 = Assisted
        ("tyre_temperature", ctypes.c_uint8),               # 0 = Surface only, 1 = Surface & Carcass
        ("pit_lane_tyre_sim", ctypes.c_uint8),              # 0 = On, 1 = Off
        ("car_damage", ctypes.c_uint8),                     # 0 = Off, 1 = Reduced, 2 = Standard, 3 = Simulation
        ("car_damage_rate", ctypes.c_uint8),                # 0 = Reduced, 1 = Standard, 2 = Simulation
        ("collisions", ctypes.c_uint8),                     # 0 = Off, 1 = Player-to-Player Off, 2 = On
        ("collisions_off_for_first_lap_only", ctypes.c_uint8),
        ("mp_unsafe_pit_release", ctypes.c_uint8),          # 0 = On, 1 = Off (Multiplayer)
        ("mp_off_for_griefing", ctypes.c_uint8),            # 0 = Disabled, 1 = Enabled (Multiplayer)
        ("corner_cutting_stringency", ctypes.c_uint8),      # 0 = Regular, 1 = Strict
        ("parc_ferme_rules", ctypes.c_uint8),               # 0 = Off, 1 = On
        ("pit_stop_experience", ctypes.c_uint8),            # 0 = Automatic, 1 = Broadcast, 2 = Immersive
        ("safety_car", ctypes.c_uint8),                     # 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
        ("safety_car_experience", ctypes.c_uint8),          # 0 = Broadcast, 1 = Immersive
        ("formation_lap", ctypes.c_uint8),                  # 0 = Off, 1 = On
        ("formation_lap_experience", ctypes.c_uint8),       # 0 = Broadcast, 1 = Immersive
        ("red_flags", ctypes.c_uint8),                      # 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
        ("affects_licence_level_solo", ctypes.c_uint8),     # 0 = Off, 1 = On
        ("affects_licence_level_mp", ctypes.c_uint8),       # 0 = Off, 1 = On
        ("num_sessions_in_weekend", ctypes.c_uint8),        # Number of sessions in weekend structure
        ("weekend_structure", ctypes.c_uint8 * 12),         # List of session types in weekend
        ("sector2_lap_distance_start", ctypes.c_float),     # Distance in m around track where sector 2 starts
        ("sector3_lap_distance_start", ctypes.c_float),     # Distance in m around track where sector 3 starts
    ]


# -----------------------------------------------------------------------------
# Lap Data - 1285 bytes
# -----------------------------------------------------------------------------

class LapData(Packet):
    _fields_ = [
        ("last_lap_time_in_ms", ctypes.c_uint32),               # Last lap time in milliseconds
        ("current_lap_time_in_ms", ctypes.c_uint32),            # Current time around the lap in milliseconds
        ("sector1_time_ms_part", ctypes.c_uint16),              # Sector 1 time milliseconds part
        ("sector1_time_minutes_part", ctypes.c_uint8),          # Sector 1 whole minute part
        ("sector2_time_ms_part", ctypes.c_uint16),              # Sector 2 time milliseconds part
        ("sector2_time_minutes_part", ctypes.c_uint8),          # Sector 2 whole minute part
        ("delta_to_car_in_front_ms_part", ctypes.c_uint16),     # Time delta to car in front milliseconds part
        ("delta_to_car_in_front_minutes_part", ctypes.c_uint8), # Time delta to car in front whole minute part
        ("delta_to_race_leader_ms_part", ctypes.c_uint16),      # Time delta to race leader milliseconds part
        ("delta_to_race_leader_minutes_part", ctypes.c_uint8),  # Time delta to race leader whole minute part
        ("lap_distance", ctypes.c_float),                       # Distance vehicle is around current lap in metres
        ("total_distance", ctypes.c_float),                     # Total distance travelled in session in metres
        ("safety_car_delta", ctypes.c_float),                   # Delta in seconds for safety car
        ("car_position", ctypes.c_uint8),                       # Car race position
        ("current_lap_num", ctypes.c_uint8),                    # Current lap number
        ("pit_status", ctypes.c_uint8),                         # 0 = none, 1 = pitting, 2 = in pit area
        ("num_pit_stops", ctypes.c_uint8),                      # Number of pit stops taken in this race
        ("sector", ctypes.c_uint8),                             # 0 = sector1, 1 = sector2, 2 = sector3
        ("current_lap_invalid", ctypes.c_uint8),                # 0 = valid, 1 = invalid
        ("penalties", ctypes.c_uint8),                          # Accumulated time penalties in seconds
        ("total_warnings", ctypes.c_uint8),                     # Accumulated number of warnings issued
        ("corner_cutting_warnings", ctypes.c_uint8),            # Accumulated corner cutting warnings
        ("num_unserved_drive_through_pens", ctypes.c_uint8),    # Num drive through pens left to serve
        ("num_unserved_stop_go_pens", ctypes.c_uint8),          # Num stop go pens left to serve
        ("grid_position", ctypes.c_uint8),                      # Grid position the vehicle started in
        ("driver_status", ctypes.c_uint8),                      # 0 = in garage, 1 = flying lap, 2 = in lap, 3 = out lap, 4 = on track
        ("result_status", ctypes.c_uint8),                      # 0 = invalid, 1 = inactive, 2 = active, 3 = finished, 4 = dnf, 5 = dsq, 6 = not classified, 7 = retired
        ("pit_lane_timer_active", ctypes.c_uint8),              # Pit lane timing, 0 = inactive, 1 = active
        ("pit_lane_time_in_lane_in_ms", ctypes.c_uint16),       # Time spent in pit lane in ms
        ("pit_stop_timer_in_ms", ctypes.c_uint16),              # Time of the actual pit stop in ms
        ("pit_stop_should_serve_pen", ctypes.c_uint8),          # Whether car should serve a penalty at this stop
        ("speed_trap_fastest_speed", ctypes.c_float),           # Fastest speed through speed trap in kmph
        ("speed_trap_fastest_lap", ctypes.c_uint8),             # Lap no the fastest speed was achieved, 255 = not set
    ]


class PacketLapData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("lap_data", LapData * 22),
        ("time_trial_pb_car_idx", ctypes.c_uint8),     # Index of Personal Best car in time trial (255 if invalid)
        ("time_trial_rival_car_idx", ctypes.c_uint8),  # Index of Rival car in time trial (255 if invalid)
    ]


# -----------------------------------------------------------------------------
# Event - 45 bytes
# -----------------------------------------------------------------------------

class FastestLap(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of car achieving fastest lap
        ("lap_time", ctypes.c_float),     # Lap time is in seconds
    ]


class Retirement(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of car retiring
        ("reason", ctypes.c_uint8),       # 0 = invalid, 1 = retired, 2 = finished, 3 = terminal damage, etc.
    ]


class DRSDisabled(Packet):
    _fields_ = [
        ("reason", ctypes.c_uint8),  # 0 = Wet track, 1 = Safety car deployed, 2 = Red flag, 3 = Min lap not reached
    ]


class TeamMateInPits(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
    ]


class RaceWinner(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
    ]


class Penalty(Packet):
    _fields_ = [
        ("penalty_type", ctypes.c_uint8),       # Penalty type - see appendix
        ("infringement_type", ctypes.c_uint8),  # Infringement type - see appendix
        ("vehicle_idx", ctypes.c_uint8),        # Vehicle index of the car the penalty is applied to
        ("other_vehicle_idx", ctypes.c_uint8),  # Vehicle index of the other car involved
        ("time", ctypes.c_uint8),               # Time gained, or time spent doing action in seconds
        ("lap_num", ctypes.c_uint8),            # Lap the penalty occurred on
        ("places_gained", ctypes.c_uint8),      # Number of places gained by this
    ]


class SpeedTrap(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),                  # Vehicle index of the vehicle triggering speed trap
        ("speed", ctypes.c_float),                        # Top speed achieved in km/h
        ("is_overall_fastest_in_session", ctypes.c_uint8),# Overall fastest speed in session = 1, otherwise 0
        ("is_driver_fastest_in_session", ctypes.c_uint8), # Fastest speed for driver in session = 1, otherwise 0
        ("fastest_vehicle_idx_in_session", ctypes.c_uint8),
        ("fastest_speed_in_session", ctypes.c_float),
    ]


class StartLights(Packet):
    _fields_ = [
        ("num_lights", ctypes.c_uint8),
    ]


class DriveThroughPenaltyServed(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
    ]


class StopGoPenaltyServed(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
        ("stop_time", ctypes.c_float),  # Time spent serving stop go in seconds
    ]


class Flashback(Packet):
    _fields_ = [
        ("flashback_frame_identifier", ctypes.c_uint32),
        ("flashback_session_time", ctypes.c_float),
    ]


class Buttons(Packet):
    _fields_ = [
        ("button_status", ctypes.c_uint32),
    ]


class Overtake(Packet):
    _fields_ = [
        ("overtaking_vehicle_idx", ctypes.c_uint8),
        ("being_overtaken_vehicle_idx", ctypes.c_uint8),
    ]


class SafetyCar(Packet):
    _fields_ = [
        ("safety_car_type", ctypes.c_uint8),  # 0 = No Safety Car, 1 = Full, 2 = Virtual, 3 = Formation Lap
        ("event_type", ctypes.c_uint8),       # 0 = Deployed, 1 = Returning, 2 = Returned, 3 = Resume Race
    ]


class Collision(Packet):
    _fields_ = [
        ("vehicle1_idx", ctypes.c_uint8),
        ("vehicle2_idx", ctypes.c_uint8),
    ]


class EventDataDetails(ctypes.Union, PacketMixin):
    _fields_ = [
        ("fastest_lap", FastestLap),
        ("retirement", Retirement),
        ("drs_disabled", DRSDisabled),
        ("team_mate_in_pits", TeamMateInPits),
        ("race_winner", RaceWinner),
        ("penalty", Penalty),
        ("speed_trap", SpeedTrap),
        ("start_lights", StartLights),
        ("drive_through_penalty_served", DriveThroughPenaltyServed),
        ("stop_go_penalty_served", StopGoPenaltyServed),
        ("flashback", Flashback),
        ("buttons", Buttons),
        ("overtake", Overtake),
        ("safety_car", SafetyCar),
        ("collision", Collision),
    ]


class PacketEventData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("event_string_code", ctypes.c_uint8 * 4),
        ("event_details", EventDataDetails),
    ]


# -----------------------------------------------------------------------------
# Participants - 1284 bytes
# -----------------------------------------------------------------------------

class LiveryColour(Packet):
    _fields_ = [
        ("red", ctypes.c_uint8),
        ("green", ctypes.c_uint8),
        ("blue", ctypes.c_uint8),
    ]


class ParticipantData(Packet):
    _fields_ = [
        ("ai_controlled", ctypes.c_uint8),          # Whether the vehicle is AI (1) or Human (0) controlled
        ("driver_id", ctypes.c_uint8),              # Driver id - see appendix, 255 if network human
        ("network_id", ctypes.c_uint8),             # Network id - unique identifier for network players
        ("team_id", ctypes.c_uint8),                # Team id - see appendix
        ("my_team", ctypes.c_uint8),                # My team flag - 1 = My Team, 0 = otherwise
        ("race_number", ctypes.c_uint8),            # Race number of the car
        ("nationality", ctypes.c_uint8),            # Nationality of the driver
        ("name", ctypes.c_char * 32),               # Name of participant in UTF-8 format (null terminated)
        ("your_telemetry", ctypes.c_uint8),         # 0 = restricted, 1 = public
        ("show_online_names", ctypes.c_uint8),      # 0 = off, 1 = on
        ("tech_level", ctypes.c_uint16),            # F1 World tech level
        ("platform", ctypes.c_uint8),               # 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
        ("num_colours", ctypes.c_uint8),            # Number of colours valid for this car
        ("livery_colours", LiveryColour * 4),       # Colours for the car
    ]


class PacketParticipantsData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("num_active_cars", ctypes.c_uint8),
        ("participants", ParticipantData * 22),
    ]


# -----------------------------------------------------------------------------
# Car Setups - 1133 bytes
# -----------------------------------------------------------------------------

class CarSetupData(Packet):
    _fields_ = [
        ("front_wing", ctypes.c_uint8),             # Front wing aero
        ("rear_wing", ctypes.c_uint8),              # Rear wing aero
        ("on_throttle", ctypes.c_uint8),            # Differential adjustment on throttle (percentage)
        ("off_throttle", ctypes.c_uint8),           # Differential adjustment off throttle (percentage)
        ("front_camber", ctypes.c_float),           # Front camber angle (suspension geometry)
        ("rear_camber", ctypes.c_float),            # Rear camber angle (suspension geometry)
        ("front_toe", ctypes.c_float),              # Front toe angle (suspension geometry)
        ("rear_toe", ctypes.c_float),               # Rear toe angle (suspension geometry)
        ("front_suspension", ctypes.c_uint8),       # Front suspension
        ("rear_suspension", ctypes.c_uint8),        # Rear suspension
        ("front_anti_roll_bar", ctypes.c_uint8),    # Front anti-roll bar
        ("rear_anti_roll_bar", ctypes.c_uint8),     # Rear anti-roll bar
        ("front_suspension_height", ctypes.c_uint8),# Front ride height
        ("rear_suspension_height", ctypes.c_uint8), # Rear ride height
        ("brake_pressure", ctypes.c_uint8),         # Brake pressure (percentage)
        ("brake_bias", ctypes.c_uint8),             # Brake bias (percentage)
        ("engine_braking", ctypes.c_uint8),         # Engine braking (percentage)
        ("rear_left_tyre_pressure", ctypes.c_float),
        ("rear_right_tyre_pressure", ctypes.c_float),
        ("front_left_tyre_pressure", ctypes.c_float),
        ("front_right_tyre_pressure", ctypes.c_float),
        ("ballast", ctypes.c_uint8),
        ("fuel_load", ctypes.c_float),
    ]


class PacketCarSetupData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_setups", CarSetupData * 22),
        ("next_front_wing_value", ctypes.c_float),  # Value of front wing after next pit stop - player only
    ]


# -----------------------------------------------------------------------------
# Car Telemetry - 1352 bytes
# -----------------------------------------------------------------------------

class CarTelemetryData(Packet):
    _fields_ = [
        ("speed", ctypes.c_uint16),                         # Speed of car in km/h
        ("throttle", ctypes.c_float),                       # Amount of throttle applied (0.0 to 1.0)
        ("steer", ctypes.c_float),                          # Steering (-1.0 full lock left to 1.0 full lock right)
        ("brake", ctypes.c_float),                          # Amount of brake applied (0.0 to 1.0)
        ("clutch", ctypes.c_uint8),                         # Amount of clutch applied (0 to 100)
        ("gear", ctypes.c_int8),                            # Gear selected (1-8, N=0, R=-1)
        ("engine_rpm", ctypes.c_uint16),                    # Engine RPM
        ("drs", ctypes.c_uint8),                            # 0 = off, 1 = on
        ("rev_lights_percent", ctypes.c_uint8),             # Rev lights indicator (percentage)
        ("rev_lights_bit_value", ctypes.c_uint16),          # Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
        ("brakes_temperature", ctypes.c_uint16 * 4),        # Brakes temperature (celsius) RL RR FL FR
        ("tyres_surface_temperature", ctypes.c_uint8 * 4),  # Tyres surface temperature (celsius) RL RR FL FR
        ("tyres_inner_temperature", ctypes.c_uint8 * 4),    # Tyres inner temperature (celsius) RL RR FL FR
        ("engine_temperature", ctypes.c_uint16),            # Engine temperature (celsius)
        ("tyres_pressure", ctypes.c_float * 4),             # Tyre pressure (PSI) RL RR FL FR
        ("surface_type", ctypes.c_uint8 * 4),               # Driving surface, see appendices RL RR FL FR
    ]


class PacketCarTelemetryData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_telemetry_data", CarTelemetryData * 22),
        ("mfd_panel_index", ctypes.c_uint8),                     # Index of MFD panel open - 255 = MFD closed
        ("mfd_panel_index_secondary_player", ctypes.c_uint8),
        ("suggested_gear", ctypes.c_int8),                       # Suggested gear (1-8), 0 if no suggestion
    ]


# -----------------------------------------------------------------------------
# Car Status - 1239 bytes
# -----------------------------------------------------------------------------

class CarStatusData(Packet):
    _fields_ = [
        ("traction_control", ctypes.c_uint8),           # 0 = off, 1 = medium, 2 = full
        ("anti_lock_brakes", ctypes.c_uint8),           # 0 = off, 1 = on
        ("fuel_mix", ctypes.c_uint8),                   # 0 = lean, 1 = standard, 2 = rich, 3 = max
        ("front_brake_bias", ctypes.c_uint8),           # Front brake bias (percentage)
        ("pit_limiter_status", ctypes.c_uint8),         # 0 = off, 1 = on
        ("fuel_in_tank", ctypes.c_float),               # Current fuel mass
        ("fuel_capacity", ctypes.c_float),              # Fuel capacity
        ("fuel_remaining_laps", ctypes.c_float),        # Fuel remaining in terms of laps
        ("max_rpm", ctypes.c_uint16),                   # Cars max RPM, point of rev limiter
        ("idle_rpm", ctypes.c_uint16),                  # Cars idle RPM
        ("max_gears", ctypes.c_uint8),                  # Maximum number of gears
        ("drs_allowed", ctypes.c_uint8),                # 0 = not allowed, 1 = allowed
        ("drs_activation_distance", ctypes.c_uint16),   # 0 = DRS not available, otherwise distance in metres
        ("actual_tyre_compound", ctypes.c_uint8),       # F1 Modern: 16=C5, 17=C4, 18=C3, 19=C2, 20=C1, 21=C0, 22=C6, 7=inter, 8=wet
        ("visual_tyre_compound", ctypes.c_uint8),       # F1 visual: 16=soft, 17=medium, 18=hard, 7=inter, 8=wet
        ("tyres_age_laps", ctypes.c_uint8),             # Age in laps of the current set of tyres
        ("vehicle_fia_flags", ctypes.c_int8),           # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
        ("engine_power_ice", ctypes.c_float),           # Engine power output of ICE (W)
        ("engine_power_mguk", ctypes.c_float),          # Engine power output of MGU-K (W)
        ("ers_store_energy", ctypes.c_float),           # ERS energy store in Joules
        ("ers_deploy_mode", ctypes.c_uint8),            # 0 = none, 1 = medium, 2 = hotlap, 3 = overtake
        ("ers_harvested_this_lap_mguk", ctypes.c_float),
        ("ers_harvested_this_lap_mguh", ctypes.c_float),
        ("ers_deployed_this_lap", ctypes.c_float),
        ("network_paused", ctypes.c_uint8),             # Whether the car is paused in a network game
    ]


class PacketCarStatusData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_status_data", CarStatusData * 22),
    ]


# -----------------------------------------------------------------------------
# Final Classification - 1042 bytes
# -----------------------------------------------------------------------------

class FinalClassificationData(Packet):
    _fields_ = [
        ("position", ctypes.c_uint8),               # Finishing position
        ("num_laps", ctypes.c_uint8),               # Number of laps completed
        ("grid_position", ctypes.c_uint8),          # Grid position of the car
        ("points", ctypes.c_uint8),                 # Number of points scored
        ("num_pit_stops", ctypes.c_uint8),          # Number of pit stops made
        ("result_status", ctypes.c_uint8),          # 0=invalid, 1=inactive, 2=active, 3=finished, 4=dnf, 5=dsq, 6=not classified, 7=retired
        ("result_reason", ctypes.c_uint8),          # 0=invalid, 1=retired, 2=finished, 3=terminal damage, etc.
        ("best_lap_time_in_ms", ctypes.c_uint32),   # Best lap time of the session in milliseconds
        ("total_race_time", ctypes.c_double),       # Total race time in seconds without penalties
        ("penalties_time", ctypes.c_uint8),         # Total penalties accumulated in seconds
        ("num_penalties", ctypes.c_uint8),          # Number of penalties applied to this driver
        ("num_tyre_stints", ctypes.c_uint8),        # Number of tyre stints up to maximum
        ("tyre_stints_actual", ctypes.c_uint8 * 8),
        ("tyre_stints_visual", ctypes.c_uint8 * 8),
        ("tyre_stints_end_laps", ctypes.c_uint8 * 8),
    ]


class PacketFinalClassificationData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("num_cars", ctypes.c_uint8),
        ("classification_data", FinalClassificationData * 22),
    ]


# -----------------------------------------------------------------------------
# Lobby Info - 954 bytes
# -----------------------------------------------------------------------------

class LobbyInfoData(Packet):
    _fields_ = [
        ("ai_controlled", ctypes.c_uint8),      # Whether the vehicle is AI (1) or Human (0) controlled
        ("team_id", ctypes.c_uint8),            # Team id - see appendix (255 if no team currently selected)
        ("nationality", ctypes.c_uint8),        # Nationality of the driver
        ("platform", ctypes.c_uint8),           # 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
        ("name", ctypes.c_char * 32),           # Name of participant in UTF-8 format (null terminated)
        ("car_number", ctypes.c_uint8),         # Car number of the player
        ("your_telemetry", ctypes.c_uint8),     # 0 = restricted, 1 = public
        ("show_online_names", ctypes.c_uint8),  # 0 = off, 1 = on
        ("tech_level", ctypes.c_uint16),        # F1 World tech level
        ("ready_status", ctypes.c_uint8),       # 0 = not ready, 1 = ready, 2 = spectating
    ]


class PacketLobbyInfoData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("num_players", ctypes.c_uint8),
        ("lobby_players", LobbyInfoData * 22),
    ]


# -----------------------------------------------------------------------------
# Car Damage - 1041 bytes
# -----------------------------------------------------------------------------

class CarDamageData(Packet):
    _fields_ = [
        ("tyres_wear", ctypes.c_float * 4),                         # Tyre wear (percentage) RL RR FL FR
        ("tyres_damage", ctypes.c_uint8 * 4),                       # Tyre damage (percentage) RL RR FL FR
        ("brakes_damage", ctypes.c_uint8 * 4),                      # Brakes damage (percentage) RL RR FL FR
        ("tyre_blisters", ctypes.c_uint8 * 4),                      # Tyre blisters (percentage) RL RR FL FR
        ("front_left_wing_damage", ctypes.c_uint8),
        ("front_right_wing_damage", ctypes.c_uint8),
        ("rear_wing_damage", ctypes.c_uint8),
        ("floor_damage", ctypes.c_uint8),
        ("diffuser_damage", ctypes.c_uint8),
        ("sidepod_damage", ctypes.c_uint8),
        ("drs_fault", ctypes.c_uint8),          # 0 = OK, 1 = fault
        ("ers_fault", ctypes.c_uint8),          # 0 = OK, 1 = fault
        ("gearbox_damage", ctypes.c_uint8),
        ("engine_damage", ctypes.c_uint8),
        ("engine_mguh_wear", ctypes.c_uint8),
        ("engine_es_wear", ctypes.c_uint8),
        ("engine_ce_wear", ctypes.c_uint8),
        ("engine_ice_wear", ctypes.c_uint8),
        ("engine_mguk_wear", ctypes.c_uint8),
        ("engine_tc_wear", ctypes.c_uint8),
        ("engine_blown", ctypes.c_uint8),       # 0 = OK, 1 = fault
        ("engine_seized", ctypes.c_uint8),      # 0 = OK, 1 = fault
    ]


class PacketCarDamageData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_damage_data", CarDamageData * 22),
    ]


# -----------------------------------------------------------------------------
# Session History - 1460 bytes
# -----------------------------------------------------------------------------

class LapHistoryData(Packet):
    _fields_ = [
        ("lap_time_in_ms", ctypes.c_uint32),        # Lap time in milliseconds
        ("sector1_time_ms_part", ctypes.c_uint16),  # Sector 1 milliseconds part
        ("sector1_time_minutes_part", ctypes.c_uint8),
        ("sector2_time_ms_part", ctypes.c_uint16),  # Sector 2 time milliseconds part
        ("sector2_time_minutes_part", ctypes.c_uint8),
        ("sector3_time_ms_part", ctypes.c_uint16),  # Sector 3 time milliseconds part
        ("sector3_time_minutes_part", ctypes.c_uint8),
        ("lap_valid_bit_flags", ctypes.c_uint8),    # 0x01 = lap valid, 0x02 = s1 valid, 0x04 = s2 valid, 0x08 = s3 valid
    ]


class TyreStintHistoryData(Packet):
    _fields_ = [
        ("end_lap", ctypes.c_uint8),               # Lap the tyre usage ends on (255 if current tyre)
        ("tyre_actual_compound", ctypes.c_uint8),
        ("tyre_visual_compound", ctypes.c_uint8),
    ]


class PacketSessionHistoryData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_idx", ctypes.c_uint8),
        ("num_laps", ctypes.c_uint8),
        ("num_tyre_stints", ctypes.c_uint8),
        ("best_lap_time_lap_num", ctypes.c_uint8),
        ("best_sector1_lap_num", ctypes.c_uint8),
        ("best_sector2_lap_num", ctypes.c_uint8),
        ("best_sector3_lap_num", ctypes.c_uint8),
        ("lap_history_data", LapHistoryData * 100),
        ("tyre_stints_history_data", TyreStintHistoryData * 8),
    ]


# -----------------------------------------------------------------------------
# Tyre Sets - 231 bytes
# -----------------------------------------------------------------------------

class TyreSetData(Packet):
    _fields_ = [
        ("actual_tyre_compound", ctypes.c_uint8),
        ("visual_tyre_compound", ctypes.c_uint8),
        ("wear", ctypes.c_uint8),               # Tyre wear (percentage)
        ("available", ctypes.c_uint8),          # Whether this set is currently available
        ("recommended_session", ctypes.c_uint8),
        ("life_span", ctypes.c_uint8),          # Laps left in this tyre set
        ("usable_life", ctypes.c_uint8),        # Max number of laps recommended for this compound
        ("lap_delta_time", ctypes.c_int16),     # Lap delta time in milliseconds compared to fitted set
        ("fitted", ctypes.c_uint8),             # Whether the set is fitted or not
    ]


class PacketTyreSetsData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("car_idx", ctypes.c_uint8),
        ("tyre_set_data", TyreSetData * 20),  # 13 (dry) + 7 (wet)
        ("fitted_idx", ctypes.c_uint8),
    ]


# -----------------------------------------------------------------------------
# Motion Ex - 273 bytes
# -----------------------------------------------------------------------------

class PacketMotionExData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("suspension_position", ctypes.c_float * 4),      # RL, RR, FL, FR
        ("suspension_velocity", ctypes.c_float * 4),      # RL, RR, FL, FR
        ("suspension_acceleration", ctypes.c_float * 4),  # RL, RR, FL, FR
        ("wheel_speed", ctypes.c_float * 4),
        ("wheel_slip_ratio", ctypes.c_float * 4),
        ("wheel_slip_angle", ctypes.c_float * 4),
        ("wheel_lat_force", ctypes.c_float * 4),
        ("wheel_long_force", ctypes.c_float * 4),
        ("height_of_cog_above_ground", ctypes.c_float),
        ("local_velocity_x", ctypes.c_float),
        ("local_velocity_y", ctypes.c_float),
        ("local_velocity_z", ctypes.c_float),
        ("angular_velocity_x", ctypes.c_float),
        ("angular_velocity_y", ctypes.c_float),
        ("angular_velocity_z", ctypes.c_float),
        ("angular_acceleration_x", ctypes.c_float),
        ("angular_acceleration_y", ctypes.c_float),
        ("angular_acceleration_z", ctypes.c_float),
        ("front_wheels_angle", ctypes.c_float),
        ("wheel_vert_force", ctypes.c_float * 4),
        ("front_aero_height", ctypes.c_float),    # Front plank edge height above road surface
        ("rear_aero_height", ctypes.c_float),     # Rear plank edge height above road surface
        ("front_roll_angle", ctypes.c_float),     # Roll angle of the front suspension
        ("rear_roll_angle", ctypes.c_float),      # Roll angle of the rear suspension
        ("chassis_yaw", ctypes.c_float),          # Yaw angle of chassis relative to direction of motion
        ("chassis_pitch", ctypes.c_float),        # Pitch angle of chassis relative to direction of motion
        ("wheel_camber", ctypes.c_float * 4),     # Camber of each wheel in radians
        ("wheel_camber_gain", ctypes.c_float * 4),# Camber gain for each wheel in radians
    ]


# -----------------------------------------------------------------------------
# Time Trial - 101 bytes
# -----------------------------------------------------------------------------

class TimeTrialDataSet(Packet):
    _fields_ = [
        ("car_idx", ctypes.c_uint8),
        ("team_id", ctypes.c_uint8),
        ("lap_time_in_ms", ctypes.c_uint32),
        ("sector1_time_in_ms", ctypes.c_uint32),
        ("sector2_time_in_ms", ctypes.c_uint32),
        ("sector3_time_in_ms", ctypes.c_uint32),
        ("traction_control", ctypes.c_uint8),       # 0 = assist off, 1 = assist on
        ("gearbox_assist", ctypes.c_uint8),         # 0 = assist off, 1 = assist on
        ("anti_lock_brakes", ctypes.c_uint8),       # 0 = assist off, 1 = assist on
        ("equal_car_performance", ctypes.c_uint8),  # 0 = Realistic, 1 = Equal
        ("custom_setup", ctypes.c_uint8),           # 0 = No, 1 = Yes
        ("valid", ctypes.c_uint8),                  # 0 = invalid, 1 = valid
    ]


class PacketTimeTrialData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("player_session_best_data_set", TimeTrialDataSet),
        ("personal_best_data_set", TimeTrialDataSet),
        ("rival_data_set", TimeTrialDataSet),
    ]


# -----------------------------------------------------------------------------
# Lap Positions - 1131 bytes
# -----------------------------------------------------------------------------

class PacketLapPositionsData(Packet):
    _fields_ = [
        ("header", PacketHeader),
        ("num_laps", ctypes.c_uint8),
        ("lap_start", ctypes.c_uint8),
        ("position_for_vehicle_idx", (ctypes.c_uint8 * 22) * 50),
    ]


# -----------------------------------------------------------------------------
# Packet type lookup
# -----------------------------------------------------------------------------

HEADER_FIELD_TO_PACKET_TYPE = {
    (2025, 1, 0): PacketMotionData,
    (2025, 1, 1): PacketSessionData,
    (2025, 1, 2): PacketLapData,
    (2025, 1, 3): PacketEventData,
    (2025, 1, 4): PacketParticipantsData,
    (2025, 1, 5): PacketCarSetupData,
    (2025, 1, 6): PacketCarTelemetryData,
    (2025, 1, 7): PacketCarStatusData,
    (2025, 1, 8): PacketFinalClassificationData,
    (2025, 1, 9): PacketLobbyInfoData,
    (2025, 1, 10): PacketCarDamageData,
    (2025, 1, 11): PacketSessionHistoryData,
    (2025, 1, 12): PacketTyreSetsData,
    (2025, 1, 13): PacketMotionExData,
    (2025, 1, 14): PacketTimeTrialData,
    (2025, 1, 15): PacketLapPositionsData,
}
