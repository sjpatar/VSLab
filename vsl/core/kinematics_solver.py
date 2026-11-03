import math
from pygame.math import Vector2

from vsl.components.kinematics import PhysicsBlock, Spring, Rope, PinJoint, SliderJoint
from vsl.core.kinematics_config import (
    DEFAULT_MAX_LINEAR_SPEED_MPS,
    DEFAULT_RESTITUTION_THRESHOLD_MPS,
    DEFAULT_SLEEP_LINEAR_THRESHOLD_MPS,
    GRAVITY_PXPS2,
    PIXELS_PER_METER,
)
def closest_point_on_segment(point: Vector2, start: Vector2, end: Vector2) -> Vector2:
    segment = end - start
    length_squared = segment.length_squared()
    if length_squared <= 1e-9:
        return Vector2(start)
    t = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    return start + segment * t


def perpendicular_velocity(angular_velocity: float, radius_vector: Vector2) -> Vector2:
    return Vector2(-angular_velocity * radius_vector.y, angular_velocity * radius_vector.x)


def cross_2d(vec_a: Vector2, vec_b: Vector2) -> float:
    return vec_a.x * vec_b.y - vec_a.y * vec_b.x

class KinematicsSolver:
    def __init__(self):
        self.pixels_per_meter = PIXELS_PER_METER
        self.gravity = Vector2(0, GRAVITY_PXPS2)
        self.accumulator = 0.0
        self.dt = 1.0 / 120.0
        self.linear_damping = 0.999
        self.angular_damping = 0.998
        self.max_linear_speed = DEFAULT_MAX_LINEAR_SPEED_MPS * self.pixels_per_meter
        self.max_angular_speed = 20.0
        self.constraint_iterations = 14
        self.restitution_threshold = DEFAULT_RESTITUTION_THRESHOLD_MPS * self.pixels_per_meter
        self.sleep_linear_threshold = DEFAULT_SLEEP_LINEAR_THRESHOLD_MPS * self.pixels_per_meter
        self.sleep_angular_threshold = 0.12
        self.sleep_time_threshold = 0.35
        self.floor_static_friction = 0.82
        self.floor_dynamic_friction = 0.58

    def effective_inv_mass(self, body):
        return 0.0 if getattr(body, "is_static", False) else body.inv_mass

    def effective_inv_inertia(self, body):
        return 0.0 if getattr(body, "is_static", False) else body.inv_inertia

    def solve(self, objects, links, frame_time, screen_width, floor_y):
        if frame_time <= 0:
            return
        frame_time = min(frame_time, 0.05)
        self.accumulator += frame_time
        while self.accumulator >= self.dt:
            self.physics_step(objects, links, self.dt, screen_width, floor_y)
            self.accumulator -= self.dt

    def physics_step(self, objects, links, dt, screen_width, floor_y):
        bodies = [obj for obj in objects if isinstance(obj, PhysicsBlock)]

        for body in bodies:
            if body.is_dragging:
                current_pos = Vector2(body.rect.x, body.rect.y)
                body.pos = Vector2(current_pos)
                body.vel = (current_pos - body.last_pos) / max(dt, 1e-6)
                body.last_pos = current_pos
                body.angular_vel = 0.0
                body.wake()
                continue

            if getattr(body, "is_static", False):
                body.acc = Vector2(0, 0)
                body.vel = Vector2(0, 0)
                body.angular_vel = 0.0
                continue

            body.acc = Vector2(self.gravity) * getattr(body, "gravity_scale", 1.0)
            body.torque = 0.0
            body.angular_acc = 0.0

        for obj in objects:
            if hasattr(obj, "pos") and hasattr(obj, "rect") and not isinstance(obj, PhysicsBlock):
                obj.rect.center = (int(obj.pos.x), int(obj.pos.y))

        for link in links:
            if isinstance(link, Spring):
                link.apply_force()

        for body in bodies:
            if body.is_dragging or getattr(body, "is_static", False):
                continue

            if getattr(body, "is_sleeping", False):
                if body.acc.length_squared() < 1e-4:
                    continue
                body.is_sleeping = False

            linear_drag = math.exp(-getattr(body, "air_drag", 0.0) * dt)
            angular_drag = math.exp(-getattr(body, "angular_drag", 0.0) * dt)

            # Fix framerate-dependent damping
            lin_damping_factor = math.pow(self.linear_damping, dt * 120.0)
            ang_damping_factor = math.pow(self.angular_damping, dt * 120.0)

            body.vel += body.acc * dt
            body.vel *= linear_drag * lin_damping_factor
            if body.vel.length_squared() > self.max_linear_speed * self.max_linear_speed:
                body.vel.scale_to_length(self.max_linear_speed)

            body.angular_acc = body.torque * body.inv_inertia
            body.angular_vel += body.angular_acc * dt
            body.angular_vel *= angular_drag * ang_damping_factor
            body.angular_vel = max(-self.max_angular_speed, min(self.max_angular_speed, body.angular_vel))

            body.pos += body.vel * dt
            body.angle += body.angular_vel * dt

        for _ in range(self.constraint_iterations):
            self.resolve_collisions(bodies)
            self.resolve_boundaries(bodies, screen_width, floor_y)

            for link in links:
                if isinstance(link, Rope):
                    link.solve_constraint()
                    self.apply_rope_velocity_clamp(link)

            self.solve_advanced_constraints(objects, links)

        for body in bodies:
            if not body.is_dragging:
                self.update_sleep_state(body, floor_y, dt)
                body.rect.x, body.rect.y = int(body.pos.x), int(body.pos.y)
                body.last_pos = Vector2(body.pos)

        for obj in objects:
            if hasattr(obj, "pos") and hasattr(obj, "rect") and not isinstance(obj, PhysicsBlock):
                obj.rect.center = (int(obj.pos.x), int(obj.pos.y))

    def update_sleep_state(self, body, floor_y, dt):
        if getattr(body, "is_static", False):
            return

        # Fixed sleep bug by removing the strict floor distance requirement
        if body.vel.length_squared() <= self.sleep_linear_threshold**2 and abs(body.angular_vel) <= self.sleep_angular_threshold:
            body.sleep_timer += dt
            if body.sleep_timer >= self.sleep_time_threshold:
                body.is_sleeping = True
                body.vel = Vector2(0, 0)
                body.angular_vel = 0.0
        else:
            body.sleep_timer = 0.0
            body.is_sleeping = False

    def apply_rope_velocity_clamp(self, link):
        p1, p2 = link.endpoints()
        diff = p2 - p1
        distance = diff.length()
        if distance <= link.length or distance <= 1e-6:
            return

        normal = diff.normalize()
        inv_mass_a = self.effective_inv_mass(link.obj_a)
        inv_mass_b = self.effective_inv_mass(link.obj_b)
        total_inv_mass = inv_mass_a + inv_mass_b
        if total_inv_mass <= 1e-9:
            return

        relative_velocity = link.obj_b.vel - link.obj_a.vel
        velocity_along_rope = relative_velocity.dot(normal)
        if velocity_along_rope <= 0:
            return

        impulse_magnitude = velocity_along_rope / total_inv_mass
        impulse = normal * impulse_magnitude
        if not getattr(link.obj_a, "is_static", False):
            link.obj_a.vel += impulse * inv_mass_a
            if hasattr(link.obj_a, "wake"):
                link.obj_a.wake()
        if not getattr(link.obj_b, "is_static", False):
            link.obj_b.vel -= impulse * inv_mass_b
            if hasattr(link.obj_b, "wake"):
                link.obj_b.wake()

    def solve_advanced_constraints(self, objects, links):
        for link in links:
            if isinstance(link, PinJoint):
                wa, wb = link.get_world_anchors()
                error = wb - wa
                correction = error * 0.2
                inv_mass_a = self.effective_inv_mass(link.obj_a)
                inv_mass_b = self.effective_inv_mass(link.obj_b)
                total_inv_mass = inv_mass_a + inv_mass_b
                if total_inv_mass > 0:
                    if not getattr(link.obj_a, "is_static", False):
                        link.obj_a.pos += correction * (inv_mass_a / total_inv_mass)
                    if not getattr(link.obj_b, "is_static", False):
                        link.obj_b.pos -= correction * (inv_mass_b / total_inv_mass)

                relative_velocity = link.obj_b.vel - link.obj_a.vel
                impulse = relative_velocity * 0.35
                if not getattr(link.obj_a, "is_static", False):
                    link.obj_a.vel += impulse * inv_mass_a
                if not getattr(link.obj_b, "is_static", False):
                    link.obj_b.vel -= impulse * inv_mass_b

            elif isinstance(link, SliderJoint):
                link.obj_a.angle = link.locked_angle
                link.obj_a.angular_vel = 0.0
                perpendicular_speed = link.obj_a.vel.dot(link.perp_axis)
                link.obj_a.vel += link.perp_axis * -perpendicular_speed

    def resolve_boundaries(self, bodies, screen_width, floor_y):
        for body in bodies:
            if getattr(body, "is_static", False) or body.is_dragging:
                continue

            left, top, right, bottom = self.get_world_bounds(body)

            if bottom > floor_y:
                penetration = bottom - floor_y
                contact_point = self.boundary_contact_point(body, Vector2(0, 1))
                self.apply_boundary_impulse(body, Vector2(0, -1), penetration, contact_point)

            if left < 0:
                penetration = -left
                contact_point = self.boundary_contact_point(body, Vector2(-1, 0))
                self.apply_boundary_impulse(body, Vector2(1, 0), penetration, contact_point)
            elif right > screen_width:
                penetration = right - screen_width
                contact_point = self.boundary_contact_point(body, Vector2(1, 0))
                self.apply_boundary_impulse(body, Vector2(-1, 0), penetration, contact_point)

    def resolve_collisions(self, bodies):
        for index_a in range(len(bodies)):
            for index_b in range(index_a + 1, len(bodies)):
                body_a = bodies[index_a]
                body_b = bodies[index_b]
                if self.aabb_separated(body_a, body_b):
                    continue
                self.sat_collision(body_a, body_b)

    def aabb_separated(self, body_a, body_b):
        min_ax, min_ay, max_ax, max_ay = self.get_world_bounds(body_a)
        min_bx, min_by, max_bx, max_by = self.get_world_bounds(body_b)
        return max_ax < min_bx or max_bx < min_ax or max_ay < min_by or max_by < min_ay

    def get_world_bounds(self, body):
        if hasattr(body, "radius"):
            center = body.get_center()
            return (
                center.x - body.radius,
                center.y - body.radius,
                center.x + body.radius,
                center.y + body.radius,
            )

        vertices = body.get_vertices()
        xs = [vertex.x for vertex in vertices]
        ys = [vertex.y for vertex in vertices]
        return min(xs), min(ys), max(xs), max(ys)

    def sat_collision(self, body_a, body_b):
        circle_a = hasattr(body_a, "radius")
        circle_b = hasattr(body_b, "radius")
        center_a = body_a.get_center()
        center_b = body_b.get_center()

        if circle_a and circle_b:
            distance = center_a.distance_to(center_b)
            min_distance = body_a.radius + body_b.radius
            if distance <= 1e-6 or distance >= min_distance:
                return
            normal = (center_b - center_a).normalize()
            contact_point = center_a + normal * body_a.radius
            self.apply_impulse(body_a, body_b, normal, min_distance - distance, contact_point)
            return

        vertices_a = [] if circle_a else body_a.get_vertices()
        vertices_b = [] if circle_b else body_b.get_vertices()
        axes = []
        if not circle_a:
            axes.extend(self.get_axes(vertices_a))
        if not circle_b:
            axes.extend(self.get_axes(vertices_b))

        if circle_a and not circle_b:
            closest_point = self.closest_point_on_polygon(center_a, vertices_b)
            axis = center_a - closest_point
            if axis.length_squared() > 1e-9:
                axes.append(axis.normalize())
        elif circle_b and not circle_a:
            closest_point = self.closest_point_on_polygon(center_b, vertices_a)
            axis = center_b - closest_point
            if axis.length_squared() > 1e-9:
                axes.append(axis.normalize())

        min_overlap = float("inf")
        smallest_axis = None
        for axis in axes:
            min_a, max_a = self.project_shape(body_a, axis, circle_a)
            min_b, max_b = self.project_shape(body_b, axis, circle_b)
            if max_a <= min_b or max_b <= min_a:
                return
            overlap = min(max_a, max_b) - max(min_a, min_b)
            if overlap < min_overlap:
                min_overlap = overlap
                smallest_axis = axis

        if smallest_axis is None:
            return

        direction = center_b - center_a
        if direction.dot(smallest_axis) < 0:
            smallest_axis = -smallest_axis
        contact_point = self.get_contact_point(
            body_a,
            body_b,
            smallest_axis,
            circle_a,
            circle_b,
            vertices_a,
            vertices_b,
            center_a,
            center_b,
        )
        self.apply_impulse(body_a, body_b, smallest_axis, min_overlap, contact_point)

    def closest_point_on_polygon(self, point, vertices):
        closest = None
        closest_distance = float("inf")
        for index, vertex in enumerate(vertices):
            next_vertex = vertices[(index + 1) % len(vertices)]
            candidate = closest_point_on_segment(point, vertex, next_vertex)
            distance = (point - candidate).length_squared()
            if distance < closest_distance:
                closest_distance = distance
                closest = candidate
        return closest if closest is not None else Vector2(point)

    def project_shape(self, body, axis, is_circle):
        if is_circle:
            center = body.get_center()
            projection = center.dot(axis)
            return projection - body.radius, projection + body.radius
        return self.project(body.get_vertices(), axis)

    def get_axes(self, vertices):
        axes = []
        for index, vertex in enumerate(vertices):
            edge = vertices[(index + 1) % len(vertices)] - vertex
            normal = Vector2(-edge.y, edge.x)
            if normal.length_squared() > 1e-9:
                axes.append(normal.normalize())
        return axes

    def project(self, vertices, axis):
        min_projection = float("inf")
        max_projection = float("-inf")
        for vertex in vertices:
            projection = vertex.dot(axis)
            min_projection = min(min_projection, projection)
            max_projection = max(max_projection, projection)
        return min_projection, max_projection

    def support_point(self, body, direction: Vector2) -> Vector2:
        if hasattr(body, "radius"):
            center = body.get_center()
            if direction.length_squared() <= 1e-9:
                return Vector2(center)
            return center + direction.normalize() * body.radius

        vertices = body.get_vertices()
        return max(vertices, key=lambda vertex: vertex.dot(direction))

    def support_points(self, body, direction: Vector2, tolerance: float = 1.5) -> list[Vector2]:
        if hasattr(body, "radius"):
            return [self.support_point(body, direction)]

        vertices = body.get_vertices()
        if not vertices:
            return [body.get_center()]

        best_projection = max(vertex.dot(direction) for vertex in vertices)
        return [vertex for vertex in vertices if best_projection - vertex.dot(direction) <= tolerance]

    def boundary_contact_point(self, body, direction: Vector2) -> Vector2:
        points = self.support_points(body, direction)
        if not points:
            return self.support_point(body, direction)

        accumulator = Vector2()
        for point in points:
            accumulator += point
        return accumulator / len(points)

    def get_contact_point(self, body_a, body_b, normal, circle_a, circle_b, vertices_a, vertices_b, center_a, center_b):
        if circle_a and circle_b:
            return center_a + normal * body_a.radius
        if circle_a and not circle_b:
            return self.closest_point_on_polygon(center_a, vertices_b)
        if circle_b and not circle_a:
            return self.closest_point_on_polygon(center_b, vertices_a)
        support_a = self.support_point(body_a, normal)
        support_b = self.support_point(body_b, -normal)
        return (support_a + support_b) * 0.5

    def apply_boundary_impulse(self, body, normal, penetration, contact_point):
        body.pos += normal * penetration
        body.wake()

        inv_mass = self.effective_inv_mass(body)
        inv_inertia = self.effective_inv_inertia(body)
        center = body.get_center()
        radius_vector = contact_point - center
        contact_velocity = body.vel + perpendicular_velocity(body.angular_vel, radius_vector)
        velocity_along_normal = contact_velocity.dot(normal)
        normal_impulse_mag = 0.0

        if velocity_along_normal < 0:
            restitution = getattr(body, "restitution", 0.2)
            if abs(velocity_along_normal) < self.restitution_threshold:
                restitution = 0.0

            radius_cross_normal = cross_2d(radius_vector, normal)
            normal_denom = inv_mass + (radius_cross_normal * radius_cross_normal) * inv_inertia
            if normal_denom > 1e-9:
                normal_impulse_mag = -(1.0 + restitution) * velocity_along_normal / normal_denom
                normal_impulse = normal * normal_impulse_mag
                body.vel += normal_impulse * inv_mass
                body.angular_vel += cross_2d(radius_vector, normal_impulse) * inv_inertia

        # Settle low-energy resting contacts instead of feeding endless micro-bounces.
        if abs(body.vel.y) < self.sleep_linear_threshold and abs(body.angular_vel) < self.sleep_angular_threshold:
            if abs(normal.y) > 0.5:
                body.vel.y = 0.0
            if abs(normal.x) > 0.5:
                body.vel.x = 0.0
            body.angular_vel = 0.0

        contact_velocity = body.vel + perpendicular_velocity(body.angular_vel, radius_vector)
        tangent = contact_velocity - normal * contact_velocity.dot(normal)
        if tangent.length_squared() > 1e-8:
            tangent = tangent.normalize()
            tangent_speed = contact_velocity.dot(tangent)
            radius_cross_tangent = cross_2d(radius_vector, tangent)
            tangent_denom = inv_mass + (radius_cross_tangent * radius_cross_tangent) * inv_inertia
            if tangent_denom > 1e-9:
                tangent_impulse_mag = -tangent_speed / tangent_denom
                static_friction = getattr(body, "static_friction", 0.5)
                dynamic_friction = getattr(body, "dynamic_friction", 0.4)
                if abs(normal.y) > 0.5:
                    contact_static = getattr(body, "surface_friction", static_friction)
                    static_friction = math.sqrt(max(static_friction, 0.0) * max(contact_static, 0.0) * self.floor_static_friction)
                    dynamic_friction = math.sqrt(max(dynamic_friction, 0.0) * max(contact_static, 0.0) * self.floor_dynamic_friction)
                    dynamic_friction = min(dynamic_friction, static_friction)

                if abs(tangent_impulse_mag) <= normal_impulse_mag * static_friction:
                    tangent_impulse = tangent * tangent_impulse_mag
                else:
                    tangent_impulse = tangent * (-normal_impulse_mag * dynamic_friction)

                body.vel += tangent_impulse * inv_mass
                body.angular_vel += cross_2d(radius_vector, tangent_impulse) * inv_inertia

    def apply_impulse(self, body_a, body_b, normal, penetration, contact_point):
        inv_mass_a = self.effective_inv_mass(body_a)
        inv_mass_b = self.effective_inv_mass(body_b)
        inv_inertia_a = self.effective_inv_inertia(body_a)
        inv_inertia_b = self.effective_inv_inertia(body_b)
        total_inv_mass = inv_mass_a + inv_mass_b
        if total_inv_mass <= 0:
            return

        slop = 0.4
        correction_percent = 0.72
        correction_amount = max(penetration - slop, 0.0) / total_inv_mass
        correction = correction_amount * correction_percent * normal

        if not getattr(body_a, "is_static", False):
            body_a.pos -= inv_mass_a * correction
            body_a.wake()
        if not getattr(body_b, "is_static", False):
            body_b.pos += inv_mass_b * correction
            body_b.wake()

        center_a = body_a.get_center()
        center_b = body_b.get_center()
        ra = contact_point - center_a
        rb = contact_point - center_b
        vel_a = body_a.vel + perpendicular_velocity(body_a.angular_vel, ra)
        vel_b = body_b.vel + perpendicular_velocity(body_b.angular_vel, rb)
        relative_velocity = vel_b - vel_a
        velocity_along_normal = relative_velocity.dot(normal)
        if velocity_along_normal > 0:
            return

        restitution = min(getattr(body_a, "restitution", 0.2), getattr(body_b, "restitution", 0.2))
        if abs(velocity_along_normal) < self.restitution_threshold:
            restitution = 0.0

        ra_cross_normal = cross_2d(ra, normal)
        rb_cross_normal = cross_2d(rb, normal)
        normal_denom = total_inv_mass
        normal_denom += (ra_cross_normal * ra_cross_normal) * inv_inertia_a
        normal_denom += (rb_cross_normal * rb_cross_normal) * inv_inertia_b
        if normal_denom <= 1e-9:
            return

        normal_impulse_magnitude = -(1 + restitution) * velocity_along_normal / normal_denom
        normal_impulse = normal_impulse_magnitude * normal

        if not getattr(body_a, "is_static", False):
            body_a.vel -= inv_mass_a * normal_impulse
            body_a.angular_vel -= cross_2d(ra, normal_impulse) * inv_inertia_a
        if not getattr(body_b, "is_static", False):
            body_b.vel += inv_mass_b * normal_impulse
            body_b.angular_vel += cross_2d(rb, normal_impulse) * inv_inertia_b

        vel_a = body_a.vel + perpendicular_velocity(body_a.angular_vel, ra)
        vel_b = body_b.vel + perpendicular_velocity(body_b.angular_vel, rb)
        relative_velocity = vel_b - vel_a
        velocity_along_normal = relative_velocity.dot(normal)
        tangent = relative_velocity - normal * velocity_along_normal
        if tangent.length_squared() > 1e-8:
            tangent = tangent.normalize()
            tangent_speed = relative_velocity.dot(tangent)
            ra_cross_tangent = cross_2d(ra, tangent)
            rb_cross_tangent = cross_2d(rb, tangent)
            tangent_denom = total_inv_mass
            tangent_denom += (ra_cross_tangent * ra_cross_tangent) * inv_inertia_a
            tangent_denom += (rb_cross_tangent * rb_cross_tangent) * inv_inertia_b
            if tangent_denom <= 1e-9:
                return

            tangent_impulse_magnitude = -tangent_speed / tangent_denom
            static_friction = math.sqrt(getattr(body_a, "static_friction", 0.7) * getattr(body_b, "static_friction", 0.7))
            dynamic_friction = math.sqrt(getattr(body_a, "dynamic_friction", 0.5) * getattr(body_b, "dynamic_friction", 0.5))

            if abs(tangent_impulse_magnitude) < normal_impulse_magnitude * static_friction:
                tangent_impulse = tangent * tangent_impulse_magnitude
            else:
                tangent_impulse = tangent * (-normal_impulse_magnitude * dynamic_friction)

            if not getattr(body_a, "is_static", False):
                body_a.vel -= inv_mass_a * tangent_impulse
                body_a.angular_vel -= cross_2d(ra, tangent_impulse) * inv_inertia_a
            if not getattr(body_b, "is_static", False):
                body_b.vel += inv_mass_b * tangent_impulse
                body_b.angular_vel += cross_2d(rb, tangent_impulse) * inv_inertia_b
