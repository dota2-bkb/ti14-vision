import cv2
import numpy as np

def draw_arrow_fixed_tip(img, pt1, pt2, color, thickness=2, tip_length=20):
    """
    Draw an arrow from pt1 -> pt2 with a constant arrowhead size.
    tip_length: the length of each side of the arrow tip in pixels (constant).
    """

    # Convert to numpy float arrays
    p1 = np.array(pt1, dtype=float)
    p2 = np.array(pt2, dtype=float)

    # Draw the main line (shaft)
    cv2.line(img, pt1, pt2, color, thickness, cv2.LINE_AA)

    # Direction vector
    direction = p1 - p2
    length = np.linalg.norm(direction)

    if length == 0:
        return

    # Unit direction
    direction /= length

    # Perpendicular vector for arrowhead width
    # (rotate by 90 degrees)
    perp = np.array([-direction[1], direction[0]])

    # Compute arrowhead triangle points
    tip = p2
    left = p2 + direction * tip_length + perp * (tip_length * 0.5)
    right = p2 + direction * tip_length - perp * (tip_length * 0.5)

    # Draw arrowhead
    pts = np.array([tip, left, right], dtype=np.int32)
    cv2.fillConvexPoly(img, pts, color)
