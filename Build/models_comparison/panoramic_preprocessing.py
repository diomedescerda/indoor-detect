"""
Panoramic Image Preprocessing Module

Implements algorithms to improve object detection on equirectangular panoramic images:
1. Lens distortion correction (Brown-Conrady model)
2. Perspective cropping from equirectangular projection with annotation transform
3. Vignetting correction
4. Multi-strip detection pipeline
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict
import math


class PanoramicPreprocessor:
    """Preprocessing pipeline for equirectangular panoramic images."""

    def __init__(self, image_width: int = 1520, image_height: int = 760):
        """
        Initialize preprocessor with image dimensions.

        Args:
            image_width: Width of the equirectangular image
            image_height: Height of the equirectangular image
        """
        self.width = image_width
        self.height = image_height

        # Default camera matrix (will be calibrated if needed)
        self.camera_matrix = np.array([
            [image_width, 0, image_width / 2],
            [0, image_width, image_height / 2],
            [0, 0, 1]
        ], dtype=np.float32)

        # Default distortion coefficients (Brown-Conrady model)
        # [k1, k2, p1, p2, k3]
        self.dist_coeffs = np.array([-0.2, 0.05, 0.0, 0.0, -0.01], dtype=np.float32)

    def correct_lens_distortion(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Brown-Conrady lens distortion correction.

        Corrects radial distortion (barrel/pincushion) and tangential distortion.
        Preserves original image dimensions to maintain annotation compatibility.

        Args:
            image: Input image (BGR format)

        Returns:
            Corrected image (same dimensions as input)
        """
        h, w = image.shape[:2]

        # Apply distortion correction WITHOUT cropping
        # This preserves the coordinate system for annotations
        corrected = cv2.undistort(
            image,
            self.camera_matrix,
            self.dist_coeffs,
            None,
            self.camera_matrix  # Use same camera matrix to preserve dimensions
        )

        return corrected

    def correct_vignetting(self, image: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """
        Apply vignetting correction by normalizing brightness across the image.

        Uses a radial gradient mask to compensate for light falloff at edges.

        Args:
            image: Input image (BGR format)
            strength: Correction strength (0.0 = no correction, 1.0 = full correction)

        Returns:
            Vignetting-corrected image
        """
        h, w = image.shape[:2]

        # Create radial gradient mask
        Y, X = np.ogrid[:h, :w]
        center_x, center_y = w / 2, h / 2

        # Normalized distance from center (0 at center, 1 at corners)
        dist_from_center = np.sqrt(
            ((X - center_x) / (w / 2)) ** 2 +
            ((Y - center_y) / (h / 2)) ** 2
        )

        # Vignetting model: light falls off with distance
        vignette_mask = 1.0 - strength * (dist_from_center ** 2) / 2.0

        # Normalize to [0, 1] range
        vignette_mask = np.clip(vignette_mask, 0.1, 1.0)

        # Apply correction: divide by vignette pattern
        corrected = image.astype(np.float32)
        for c in range(3):
            corrected[:, :, c] /= vignette_mask

        # Clip and convert back
        corrected = np.clip(corrected, 0, 255).astype(np.uint8)

        return corrected

    def normalize_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Improves local contrast which helps detection on varying exposures.

        Args:
            image: Input image (BGR format)

        Returns:
            Contrast-normalized image
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def equirectangular_to_perspective(
        self,
        image: np.ndarray,
        fov: float = 90.0,
        yaw: float = 0.0,
        pitch: float = 0.0,
        output_size: Tuple[int, int] = (640, 640)
    ) -> np.ndarray:
        """
        Extract a perspective view from an equirectangular panorama.

        Args:
            image: Equirectangular image (BGR format)
            fov: Field of view in degrees
            yaw: Horizontal angle in degrees (-180 to 180)
            pitch: Vertical angle in degrees (-90 to 90)
            output_size: (width, height) of output perspective image

        Returns:
            Perspective-corrected image
        """
        h, w = image.shape[:2]
        out_w, out_h = output_size

        fov_rad = np.radians(fov)
        yaw_rad = np.radians(yaw)
        pitch_rad = np.radians(pitch)

        f = out_w / (2 * np.tan(fov_rad / 2))

        x_out = np.arange(out_w) - out_w / 2
        y_out = np.arange(out_h) - out_h / 2
        x_grid, y_grid = np.meshgrid(x_out, y_out)

        z_cam = np.full_like(x_grid, f)
        x_cam = x_grid
        y_cam = y_grid

        norm = np.sqrt(x_cam**2 + y_cam**2 + z_cam**2)
        x_cam = x_cam / norm
        y_cam = y_cam / norm
        z_cam = z_cam / norm

        cos_yaw, sin_yaw = np.cos(yaw_rad), np.sin(yaw_rad)
        x_rot = x_cam * cos_yaw + z_cam * sin_yaw
        y_rot = y_cam
        z_rot = -x_cam * sin_yaw + z_cam * cos_yaw

        cos_pitch, sin_pitch = np.cos(pitch_rad), np.sin(pitch_rad)
        x_final = x_rot
        y_final = y_rot * cos_pitch - z_rot * sin_pitch
        z_final = y_rot * sin_pitch + z_rot * cos_pitch

        theta = np.arctan2(x_final, z_final)
        phi = np.arcsin(np.clip(y_final, -1, 1))

        x_eq = (theta / np.pi + 1) * w / 2
        y_eq = (phi / (np.pi / 2) + 1) * h / 2

        x_eq = x_eq % w

        map_x = x_eq.astype(np.float32)
        map_y = y_eq.astype(np.float32)

        perspective_view = cv2.remap(
            image, map_x, map_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP
        )

        return perspective_view

    def transform_bbox_equirect_to_perspective(
        self,
        bbox: List[float],
        img_width: int,
        img_height: int,
        fov: float,
        yaw: float,
        pitch: float,
        out_width: int,
        out_height: int
    ) -> Optional[List[float]]:
        """
        Transform a bounding box from equirectangular to perspective coordinates.

        Args:
            bbox: [x, y, w, h] in equirectangular coordinates
            img_width, img_height: Equirectangular image dimensions
            fov, yaw, pitch: Perspective view parameters
            out_width, out_height: Perspective output dimensions

        Returns:
            [x, y, w, h] in perspective coordinates, or None if box is outside view
        """
        x, y, w, h = bbox

        # Convert bbox corners to spherical coordinates
        # Equirectangular: x -> longitude, y -> latitude
        corners_eq = [
            (x, y),              # top-left
            (x + w, y),          # top-right
            (x, y + h),          # bottom-left
            (x + w, y + h),      # bottom-right
        ]

        # Convert equirectangular pixel to spherical (lon, lat) in degrees
        def eq_to_spherical(px, py):
            lon = (px / img_width - 0.5) * 360  # -180 to 180
            lat = (0.5 - py / img_height) * 180  # 90 to -90
            return lon, lat

        spherical_corners = [eq_to_spherical(px, py) for px, py in corners_eq]

        # Convert spherical to 3D points on unit sphere
        def spherical_to_3d(lon_deg, lat_deg):
            lon = np.radians(lon_deg)
            lat = np.radians(lat_deg)
            x = np.cos(lat) * np.sin(lon)
            y = np.sin(lat)
            z = np.cos(lat) * np.cos(lon)
            return np.array([x, y, z])

        points_3d = [spherical_to_3d(lon, lat) for lon, lat in spherical_corners]

        # Apply inverse rotation (undo yaw and pitch)
        yaw_rad = np.radians(-yaw)
        pitch_rad = np.radians(-pitch)

        rotated_points = []
        for p in points_3d:
            # Undo pitch (rotate around X)
            y_r = p[1] * np.cos(pitch_rad) - p[2] * np.sin(pitch_rad)
            z_r = p[1] * np.sin(pitch_rad) + p[2] * np.cos(pitch_rad)
            p = np.array([p[0], y_r, z_r])

            # Undo yaw (rotate around Y)
            x_r = p[0] * np.cos(yaw_rad) + p[2] * np.sin(yaw_rad)
            z_r = -p[0] * np.sin(yaw_rad) + p[2] * np.cos(yaw_rad)
            p = np.array([x_r, p[1], z_r])

            rotated_points.append(p)

        # Project to perspective image plane
        fov_rad = np.radians(fov)
        f = out_width / (2 * np.tan(fov_rad / 2))

        persp_corners = []
        for p in rotated_points:
            if p[2] <= 0:  # Behind camera
                return None

            px = (p[0] / p[2]) * f + out_width / 2
            py = (p[1] / p[2]) * f + out_height / 2
            persp_corners.append((px, py))

        # Get bounding box of projected corners
        xs = [c[0] for c in persp_corners]
        ys = [c[1] for c in persp_corners]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Clip to output image bounds
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(out_width, x_max)
        y_max = min(out_height, y_max)

        new_w = x_max - x_min
        new_h = y_max - y_min

        if new_w <= 0 or new_h <= 0:
            return None

        return [float(x_min), float(y_min), float(new_w), float(new_h)]

    def create_perspective_strips(
        self,
        image: np.ndarray,
        num_strips: int = 4,
        fov: float = 90.0,
        output_size: Tuple[int, int] = (640, 640)
    ) -> List[Tuple[np.ndarray, float]]:
        """
        Split equirectangular panorama into perspective strips.

        Args:
            image: Equirectangular image
            num_strips: Number of strips
            fov: Field of view for each strip
            output_size: Size of each strip

        Returns:
            List of (image, yaw_angle) tuples
        """
        strip_width_deg = 360 / num_strips

        strips = []
        for i in range(num_strips):
            yaw = -180 + (i + 0.5) * strip_width_deg
            strip = self.equirectangular_to_perspective(
                image, fov=fov, yaw=yaw, pitch=0, output_size=output_size
            )
            strips.append((strip, yaw))

        return strips

    def preprocess_pipeline(
        self,
        image: np.ndarray,
        method: str = "perspective",
        **kwargs
    ) -> np.ndarray:
        """
        Apply the full preprocessing pipeline.

        Args:
            image: Input equirectangular image (BGR format)
            method: Preprocessing method to apply
            **kwargs: Additional arguments

        Returns:
            Preprocessed image
        """
        if method == "distortion":
            return self.correct_lens_distortion(image)

        elif method == "vignetting":
            strength = kwargs.get("strength", 0.5)
            return self.correct_vignetting(image, strength)

        elif method == "contrast":
            return self.normalize_contrast(image)

        elif method == "distortion_vignetting":
            corrected = self.correct_lens_distortion(image)
            return self.correct_vignetting(corrected)

        elif method == "full":
            corrected = self.correct_lens_distortion(image)
            corrected = self.correct_vignetting(corrected)
            corrected = self.normalize_contrast(corrected)
            return corrected

        elif method == "perspective":
            fov = kwargs.get("fov", 90.0)
            yaw = kwargs.get("yaw", 0.0)
            pitch = kwargs.get("pitch", 0.0)
            output_size = kwargs.get("output_size", (640, 640))
            return self.equirectangular_to_perspective(
                image, fov, yaw, pitch, output_size
            )

        else:
            raise ValueError(f"Unknown preprocessing method: {method}")


def preprocess_image(
    image_path: str,
    output_path: str,
    method: str = "perspective",
    **kwargs
) -> str:
    """
    Convenience function to preprocess a single image.

    Args:
        image_path: Path to input equirectangular image
        output_path: Path to save preprocessed image
        method: Preprocessing method
        **kwargs: Additional arguments

    Returns:
        Path to the saved preprocessed image
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    preprocessor = PanoramicPreprocessor(image.shape[1], image.shape[0])
    processed = preprocessor.preprocess_pipeline(image, method, **kwargs)

    cv2.imwrite(output_path, processed)
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python panoramic_preprocessing.py <input_image> <output_image> [method]")
        print("Methods: distortion, vignetting, contrast, distortion_vignetting, full, perspective")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else "perspective"

    result = preprocess_image(input_path, output_path, method)
    print(f"Saved preprocessed image to {result}")
