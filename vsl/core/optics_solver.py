import math
from dataclasses import dataclass
from pygame.math import Vector2

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def cross_2d(vec_a: Vector2, vec_b: Vector2) -> float:
    return vec_a.x * vec_b.y - vec_a.y * vec_b.x

def reflect(direction: Vector2, normal: Vector2) -> Vector2:
    return (direction - 2 * direction.dot(normal) * normal).normalize()

def refract(direction: Vector2, normal: Vector2, n1: float, n2: float):
    eta = n1 / n2
    cos_i = clamp(-normal.dot(direction), -1.0, 1.0)
    k = 1.0 - eta * eta * (1.0 - cos_i * cos_i)
    if k < 0.0:
        return None
    return (eta * direction + (eta * cos_i - math.sqrt(k)) * normal).normalize()

def fresnel_reflectance(direction: Vector2, normal: Vector2, n1: float, n2: float) -> float:
    cos_i = abs(clamp(-normal.dot(direction), -1.0, 1.0))
    if n1 <= 0.0 or n2 <= 0.0:
        return 1.0
    r0 = ((n1 - n2) / (n1 + n2)) ** 2
    return clamp(r0 + (1.0 - r0) * ((1.0 - cos_i) ** 5), 0.0, 1.0)

@dataclass
class Intersection:
    distance: float
    point: Vector2
    normal: Vector2
    surface: dict

SPECTRUM_BANDS = [
    {"name": "violet", "color": (148, 92, 255), "ior_offset": 0.030},
    {"name": "indigo", "color": (112, 110, 255), "ior_offset": 0.022},
    {"name": "blue", "color": (76, 156, 255), "ior_offset": 0.015},
    {"name": "green", "color": (88, 220, 132), "ior_offset": 0.008},
    {"name": "yellow", "color": (255, 226, 92), "ior_offset": 0.002},
    {"name": "orange", "color": (255, 166, 82), "ior_offset": -0.004},
    {"name": "red", "color": (255, 86, 86), "ior_offset": -0.010},
]

class OpticsSolver:
    def __init__(self):
        self.max_bounces = 12
        self.max_segments_per_ray = 18
        self.min_intensity = 0.02
        self.epsilon = 0.0015

    def solve(self, scene_objects, viewport_rect):
        surfaces = []
        for obj in scene_objects:
            if hasattr(obj, "reset_solver_state"):
                obj.reset_solver_state()
            if hasattr(obj, "get_optical_surfaces"):
                surfaces.extend(obj.get_optical_surfaces())

        segments = []
        emitters = [obj for obj in scene_objects if hasattr(obj, "get_emitters")]
        for emitter in emitters:
            for emitter_ray in emitter.get_emitters():
                direction = Vector2(emitter_ray["direction"])
                if direction.length_squared() <= 1e-9:
                    continue
                self.trace_ray(
                    origin=Vector2(emitter_ray["origin"]),
                    direction=direction.normalize(),
                    color=emitter_ray["color"],
                    intensity=emitter_ray.get("intensity", 1.0),
                    medium_stack=[], 
                    spectrum_enabled=emitter_ray.get("spectrum_enabled", False),
                    spectral_band=emitter_ray.get("spectral_band"),
                    surfaces=surfaces,
                    viewport_rect=viewport_rect,
                    segments=segments,
                    depth=0,
                )
        return segments

    def trace_ray(self, origin, direction, color, intensity, medium_stack, spectrum_enabled, spectral_band, surfaces, viewport_rect, segments, depth):
        if intensity < self.min_intensity or depth >= self.max_bounces or len(segments) >= 4000:
            return

        intersection = self.find_nearest_hit(origin, direction, surfaces)
        boundary_distance = self.distance_to_bounds(origin, direction, viewport_rect)

        distance_traveled = intersection.distance if intersection else boundary_distance
        if medium_stack:
            attenuation_coeff = getattr(medium_stack[-1], "attenuation", 0.002)
            intensity *= math.exp(-attenuation_coeff * distance_traveled)

        if intersection is None or boundary_distance < intersection.distance:
            end_point = origin + direction * boundary_distance
            segments.append({"start": Vector2(origin), "end": end_point, "color": color, "intensity": intensity})
            return

        segments.append({"start": Vector2(origin), "end": intersection.point, "color": color, "intensity": intensity})
        surface = intersection.surface
        material = surface["material"]
        owner = surface["owner"]

        if material == "absorber":
            if hasattr(owner, "register_hit"):
                owner.register_hit(intersection.point, intensity, color)
            return

        if material == "mirror":
            next_direction = reflect(direction, intersection.normal)
            self.trace_ray(
                origin=intersection.point + next_direction * self.epsilon,
                direction=next_direction,
                color=color,
                intensity=intensity * surface.get("reflectivity", 0.92),
                medium_stack=list(medium_stack),
                spectrum_enabled=spectrum_enabled,
                spectral_band=spectral_band,
                surfaces=surfaces,
                viewport_rect=viewport_rect,
                segments=segments,
                depth=depth + 1,
            )
            return

        if material == "refractive":
            if spectrum_enabled and spectral_band is None:
                for band in SPECTRUM_BANDS:
                    self.trace_refractive_ray(
                        intersection=intersection,
                        direction=direction,
                        color=band["color"],
                        intensity=intensity / len(SPECTRUM_BANDS),
                        medium_stack=list(medium_stack),
                        spectral_band=band,
                        surfaces=surfaces,
                        viewport_rect=viewport_rect,
                        segments=segments,
                        depth=depth,
                    )
                return

            self.trace_refractive_ray(
                intersection=intersection,
                direction=direction,
                color=color,
                intensity=intensity,
                medium_stack=list(medium_stack),
                spectral_band=spectral_band,
                surfaces=surfaces,
                viewport_rect=viewport_rect,
                segments=segments,
                depth=depth,
            )

    def trace_refractive_ray(self, intersection, direction, color, intensity, medium_stack, spectral_band, surfaces, viewport_rect, segments, depth):
        surface = intersection.surface
        owner = surface["owner"]
        outward_normal = intersection.normal

        currently_inside_owner = owner in medium_stack
        entering = direction.dot(outward_normal) < 0

        band_offset = 0.0 if spectral_band is None else spectral_band.get("ior_offset", 0.0)
        next_medium_stack = list(medium_stack)

        if entering:
            n1 = 1.0 if not medium_stack else getattr(medium_stack[-1], "refractive_index", 1.0)
            n2 = surface.get("refractive_index", getattr(owner, "refractive_index", 1.0)) + band_offset
            normal = outward_normal
            if not currently_inside_owner:
                next_medium_stack.append(owner)
        else:
            n1 = getattr(owner, "refractive_index", 1.0) + band_offset
            if currently_inside_owner:
                next_medium_stack.remove(owner)
            n2 = 1.0 if not next_medium_stack else getattr(next_medium_stack[-1], "refractive_index", 1.0)
            normal = -outward_normal

        refracted_direction = refract(direction, normal, n1, n2)
        if refracted_direction is None:
            reflected_direction = reflect(direction, outward_normal)
            self.trace_ray(
                origin=intersection.point + reflected_direction * self.epsilon,
                direction=reflected_direction,
                color=color,
                intensity=intensity,
                medium_stack=medium_stack,
                spectrum_enabled=False,
                spectral_band=spectral_band,
                surfaces=surfaces,
                viewport_rect=viewport_rect,
                segments=segments,
                depth=depth + 1,
            )
            return

        reflectance = fresnel_reflectance(direction, normal, n1, n2)
        transmittance = max(0.0, 1.0 - reflectance)

        reflected_direction = reflect(direction, outward_normal)
        reflected_intensity = intensity * reflectance
        if reflected_intensity >= self.min_intensity:
            self.trace_ray(
                origin=intersection.point + reflected_direction * self.epsilon,
                direction=reflected_direction,
                color=color,
                intensity=reflected_intensity,
                medium_stack=list(medium_stack),
                spectrum_enabled=False,
                spectral_band=spectral_band,
                surfaces=surfaces,
                viewport_rect=viewport_rect,
                segments=segments,
                depth=depth + 1,
            )

        self.trace_ray(
            origin=intersection.point + refracted_direction * self.epsilon,
            direction=refracted_direction,
            color=color,
            intensity=intensity * transmittance,
            medium_stack=next_medium_stack,
            spectrum_enabled=False,
            spectral_band=spectral_band,
            surfaces=surfaces,
            viewport_rect=viewport_rect,
            segments=segments,
            depth=depth + 1,
        )

    def find_nearest_hit(self, origin, direction, surfaces):
        nearest = None
        for surface in surfaces:
            if surface.get("material") == "mirror" and direction.dot(surface["normal"]) >= 0:
                continue
            intersection = self.intersect_surface(origin, direction, surface)
            if intersection is None:
                continue
            if nearest is None or intersection.distance < nearest.distance:
                nearest = intersection
        return nearest

    def intersect_surface(self, origin, direction, surface):
        if surface["kind"] == "segment":
            return self.intersect_segment(origin, direction, surface)
        if surface["kind"] == "circle":
            return self.intersect_circle(origin, direction, surface)
        return None

    def intersect_segment(self, origin, direction, surface):
        segment_start = surface["p1"]
        segment_end = surface["p2"]
        segment = segment_end - segment_start
        denominator = cross_2d(direction, segment)
        if abs(denominator) <= 1e-9:
            return None

        diff = segment_start - origin
        ray_distance = cross_2d(diff, segment) / denominator
        segment_ratio = cross_2d(diff, direction) / denominator
        if ray_distance <= self.epsilon or segment_ratio < 0.0 or segment_ratio > 1.0:
            return None

        point = origin + direction * ray_distance
        normal = Vector2(surface["normal"])
        if normal.length_squared() > 1e-9:
            normal = normal.normalize()
        return Intersection(ray_distance, point, normal, surface)

    def intersect_circle(self, origin, direction, surface):
        center = surface["center"]
        radius = surface["radius"]
        oc = origin - center
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - radius * radius
        discriminant = b * b - 4 * a * c
        if discriminant < 0.0:
            return None

        sqrt_discriminant = math.sqrt(discriminant)
        distances = [(-b - sqrt_discriminant) / (2 * a), (-b + sqrt_discriminant) / (2 * a)]
        valid_distances = [distance for distance in distances if distance > self.epsilon]
        if not valid_distances:
            return None

        ray_distance = min(valid_distances)
        point = origin + direction * ray_distance
        normal = point - center
        if normal.length_squared() > 1e-9:
            normal = normal.normalize()
        return Intersection(ray_distance, point, normal, surface)

    def distance_to_bounds(self, origin, direction, rect):
        distances = []
        if abs(direction.x) > 1e-9:
            distances.append((rect.left - origin.x) / direction.x)
            distances.append((rect.right - origin.x) / direction.x)
        if abs(direction.y) > 1e-9:
            distances.append((rect.top - origin.y) / direction.y)
            distances.append((rect.bottom - origin.y) / direction.y)

        valid = []
        for distance in distances:
            if distance <= self.epsilon:
                continue
            point = origin + direction * distance
            if rect.left - 1 <= point.x <= rect.right + 1 and rect.top - 1 <= point.y <= rect.bottom + 1:
                valid.append(distance)
        return min(valid) if valid else 2000.0
