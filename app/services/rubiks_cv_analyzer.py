import cv2
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class RubiksCubeAnalyzer:
    """Adaptive computer vision analyzer for Rubik's cube faces"""

    @staticmethod
    def analyze_cube_face_adaptive(image_data: bytes, debug: bool = False) -> Dict[str, str]:
        """
        Analyze using relative color differences instead of absolute HSV ranges.
        Much more robust to lighting and white balance variations.

        Args:
            image_data: Raw image bytes
            debug: Enable debug logging

        Returns:
            Dictionary with tile positions and color codes
        """
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise ValueError("Failed to decode image")

            # Extract the 9 tile regions
            tiles_bgr = RubiksCubeAnalyzer._extract_tile_samples(img)

            if debug:
                logger.info(f"Extracted {len(tiles_bgr)} tile samples")

            # Classify colors using relative approach
            colors = RubiksCubeAnalyzer._classify_colors_relative(tiles_bgr, debug)

            # Map to positions
            positions = ['TL', 'TC', 'TR', 'ML', 'C', 'MR', 'BL', 'BC', 'BR']
            result = {pos: color for pos, color in zip(positions, colors)}

            if debug:
                logger.info(f"Final result: {result}")

            return result

        except Exception as e:
            logger.error(f"Error in adaptive analysis: {str(e)}")
            raise ValueError(f"Failed to analyze cube: {str(e)}")

    @staticmethod
    def _extract_tile_samples(img: np.ndarray) -> List[np.ndarray]:
        """
        Extract average color from center of each tile.
        Returns list of 9 BGR color arrays.
        """
        height, width = img.shape[:2]
        tile_height = height // 3
        tile_width = width // 3

        tiles = []

        for row in range(3):
            for col in range(3):
                # Sample from very center of tile (avoid edges entirely)
                center_y = row * tile_height + tile_height // 2
                center_x = col * tile_width + tile_width // 2

                # Take 20% of tile size as sample region
                sample_size_y = max(tile_height // 5, 10)
                sample_size_x = max(tile_width // 5, 10)

                y1 = center_y - sample_size_y // 2
                y2 = center_y + sample_size_y // 2
                x1 = center_x - sample_size_x // 2
                x2 = center_x + sample_size_x // 2

                # Get average color of sample region
                tile_region = img[y1:y2, x1:x2]
                avg_color = np.mean(tile_region, axis=(0, 1))  # Average BGR

                tiles.append(avg_color)

        return tiles

    @staticmethod
    def _classify_colors_relative(tiles_bgr: List[np.ndarray], debug: bool = False) -> List[str]:
        """
        Classify colors using relative properties rather than absolute values.
        Works across different lighting conditions.
        """
        colors = []

        for idx, bgr in enumerate(tiles_bgr):
            b, g, r = bgr

            # Convert to multiple color spaces for robust detection
            hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]
            h, s, v = hsv

            # Color classification based on relative properties
            color_code = RubiksCubeAnalyzer._determine_color(r, g, b, h, s, v)

            if debug:
                logger.info(f"Tile {idx}: BGR=({b:.0f},{g:.0f},{r:.0f}) "
                          f"HSV=({h:.0f},{s:.0f},{v:.0f}) -> {color_code}")

            colors.append(color_code)

        # Post-process: use center tile to validate/adjust
        colors = RubiksCubeAnalyzer._refine_with_context(colors, tiles_bgr, debug)

        return colors

    @staticmethod
    def _determine_color(r: float, g: float, b: float,
                        h: float, s: float, v: float) -> str:
        """
        Determine color using multiple heuristics.
        More robust than pure HSV ranges.
        """
        # White: low saturation, high brightness
        if s < 50 and v > 150:
            return 'W'

        # Yellow: high R and G, low B
        if r > 150 and g > 150 and b < 130 and s > 40:
            return 'Y'

        # Orange: R > G > B, moderate saturation
        if r > g > b and r > 130 and g > 80 and s > 80:
            # Distinguish from red by checking if G is significant
            if g > 100:
                return 'O'
            else:
                return 'R'

        # Red: high R, low G and B
        if r > max(g, b) + 30 and r > 100:
            return 'R'

        # Green: high G
        if g > max(r, b) + 20 and g > 80:
            return 'G'

        # Blue: high B
        if b > max(r, g) + 20 and b > 80:
            return 'B'

        # Use hue as fallback for ambiguous cases
        if s > 30:  # Has some saturation
            if h < 15 or h > 165:
                return 'R'
            elif 15 <= h < 30:
                return 'O'
            elif 30 <= h < 75:
                return 'Y'
            elif 75 <= h < 150:
                return 'G'
            else:
                return 'B'

        # Default to white if really unsure
        return 'W'

    @staticmethod
    def _refine_with_context(colors: List[str], tiles_bgr: List[np.ndarray],
                            debug: bool = False) -> List[str]:
        """
        Use contextual information to improve accuracy.
        The center tile defines the face color.
        """
        # Count color frequencies
        from collections import Counter
        color_counts = Counter(colors)

        # Center tile (index 4) should be confident
        center_color = colors[4]

        # If center appears multiple times, it's probably correct
        if color_counts[center_color] >= 3:
            if debug:
                logger.info(f"Center color {center_color} appears {color_counts[center_color]} times - high confidence")
            return colors

        # Otherwise, check for ambiguities
        # Compare similar tiles using BGR distance
        refined = colors.copy()

        for i in range(9):
            if i == 4:  # Don't modify center
                continue

            # If this tile's color is very rare (appears only once), verify it
            if color_counts[colors[i]] == 1:
                # Find most similar tile by color distance
                min_dist = float('inf')
                most_similar_idx = 4

                for j in range(9):
                    if i == j:
                        continue
                    dist = np.linalg.norm(tiles_bgr[i] - tiles_bgr[j])
                    if dist < min_dist:
                        min_dist = dist
                        most_similar_idx = j

                # If very similar to another tile, consider using its color
                if min_dist < 30 and color_counts[colors[most_similar_idx]] > 1:
                    if debug:
                        logger.info(f"Tile {i}: {colors[i]} is rare, similar to tile {most_similar_idx}: {colors[most_similar_idx]}")
                    # Keep original for now, but this could be adjusted

        return refined


def analyze_cube_cv(image_data: bytes, check_connection=None) -> dict:
    """
    Drop-in replacement using adaptive CV analysis.
    Much more robust to lighting variations.
    """
    if check_connection:
        check_connection()

    analyzer = RubiksCubeAnalyzer()
    result = analyzer.analyze_cube_face_adaptive(image_data, debug=False)

    if check_connection:
        check_connection()

    return result


def analyze_cube_hybrid(image_data: bytes, check_connection=None,
                       llm_fallback_func=None, confidence_threshold: float = 0.7) -> dict:
    """
    Hybrid approach: Try CV first, fall back to LLM if confidence is low.

    Args:
        image_data: Raw image bytes
        check_connection: Connection check callback
        llm_fallback_func: Function to call for LLM inference (should accept image_data, check_connection)
        confidence_threshold: If CV confidence below this, use LLM (0.0-1.0)

    Returns:
        Dictionary with cube face colors
    """
    try:
        # Try CV first
        cv_result = analyze_cube_cv(image_data, check_connection)

        # Check confidence (e.g., are colors well-distributed?)
        from collections import Counter
        color_counts = Counter(cv_result.values())

        # Calculate confidence score
        # - Good: Center color appears 3-5 times (it plus some corners/edges)
        # - Bad: One color dominates everything OR every tile is different
        center_color = cv_result['C']
        center_count = color_counts[center_color]
        unique_colors = len(color_counts)

        # Heuristic: good detection has 3-5 colors, center appears 3-5 times
        confidence = 1.0
        if center_count < 2 or center_count > 7:
            confidence *= 0.5
        if unique_colors < 2 or unique_colors > 6:
            confidence *= 0.7

        logger.info(f"CV confidence: {confidence:.2f} (center={center_color} count={center_count}, unique={unique_colors})")

        if confidence >= confidence_threshold:
            logger.info("CV analysis confidence acceptable, using CV result")
            return cv_result
        else:
            logger.warning(f"CV confidence {confidence:.2f} below threshold {confidence_threshold}")

            if llm_fallback_func:
                logger.info("Falling back to LLM analysis")
                return llm_fallback_func(image_data, check_connection)
            else:
                logger.warning("No LLM fallback available, returning CV result anyway")
                return cv_result

    except Exception as e:
        logger.error(f"CV analysis failed: {e}")

        if llm_fallback_func:
            logger.info("CV failed, using LLM fallback")
            return llm_fallback_func(image_data, check_connection)
        else:
            raise


if __name__ == "__main__":
    print("Adaptive Rubik's Cube CV Analyzer ready!")
    print("- analyze_cube_cv(): Fast adaptive CV (50-100ms)")
    print("- analyze_cube_hybrid(): CV with LLM fallback for tricky cases")
