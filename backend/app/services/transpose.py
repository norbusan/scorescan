import logging
from typing import Optional, Tuple
from music21 import converter, interval, pitch, key

from app.utils.storage import get_file_path

logger = logging.getLogger(__name__)

# Mapping of key names to music21 key objects
KEY_MAP = {
    "C": "C",
    "Cmaj": "C",
    "CM": "C",
    "Cm": "c",
    "Cmin": "c",
    "C#": "C#",
    "C#maj": "C#",
    "C#m": "c#",
    "Db": "D-",
    "Dbmaj": "D-",
    "Dbm": "d-",
    "D": "D",
    "Dmaj": "D",
    "DM": "D",
    "Dm": "d",
    "Dmin": "d",
    "D#": "D#",
    "D#m": "d#",
    "Eb": "E-",
    "Ebmaj": "E-",
    "Ebm": "e-",
    "E": "E",
    "Emaj": "E",
    "EM": "E",
    "Em": "e",
    "Emin": "e",
    "F": "F",
    "Fmaj": "F",
    "FM": "F",
    "Fm": "f",
    "Fmin": "f",
    "F#": "F#",
    "F#maj": "F#",
    "F#m": "f#",
    "Gb": "G-",
    "Gbmaj": "G-",
    "Gbm": "g-",
    "G": "G",
    "Gmaj": "G",
    "GM": "G",
    "Gm": "g",
    "Gmin": "g",
    "G#": "G#",
    "G#m": "g#",
    "Ab": "A-",
    "Abmaj": "A-",
    "Abm": "a-",
    "A": "A",
    "Amaj": "A",
    "AM": "A",
    "Am": "a",
    "Amin": "a",
    "A#": "A#",
    "A#m": "a#",
    "Bb": "B-",
    "Bbmaj": "B-",
    "Bbm": "b-",
    "B": "B",
    "Bmaj": "B",
    "BM": "B",
    "Bm": "b",
    "Bmin": "b",
}


class TransposeService:
    """
    Service for transposing MusicXML files using music21.
    Supports both semitone-based and key-based transposition.
    """

    def transpose_by_semitones(
        self, input_path: str, semitones: int, output_path: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Transpose a MusicXML file by a number of semitones.

        Args:
            input_path: Relative path to input MusicXML file
            semitones: Number of semitones to transpose (-12 to +12)
            output_path: Optional output path (defaults to overwriting input)

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            abs_input = get_file_path(input_path)
            abs_output = get_file_path(output_path) if output_path else abs_input

            logger.info(f"Transposing {input_path} by {semitones} semitones")

            # Parse the MusicXML file
            score = converter.parse(abs_input)

            # Create interval for transposition
            transpose_interval = interval.Interval(semitones)

            # Transpose the score
            transposed_score = score.transpose(transpose_interval)

            # Write the transposed score
            transposed_score.write("musicxml", fp=abs_output)

            logger.info(f"Transposition complete: {output_path or input_path}")
            return True, output_path or input_path, None

        except Exception as e:
            error_msg = f"Transposition error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def transpose_by_key(
        self,
        input_path: str,
        from_key: str,
        to_key: str,
        output_path: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Transpose a MusicXML file from one key to another.

        Args:
            input_path: Relative path to input MusicXML file
            from_key: Source key (e.g., "C", "Bb", "Em")
            to_key: Target key (e.g., "F", "Eb", "Am")
            output_path: Optional output path (defaults to overwriting input)

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            abs_input = get_file_path(input_path)
            abs_output = get_file_path(output_path) if output_path else abs_input

            # Convert key names to music21 format
            m21_from_key = KEY_MAP.get(from_key, from_key)
            m21_to_key = KEY_MAP.get(to_key, to_key)

            logger.info(f"Transposing {input_path} from {from_key} to {to_key}")

            # Parse the MusicXML file
            score = converter.parse(abs_input)

            # Create key objects
            source_key = key.Key(m21_from_key)
            target_key = key.Key(m21_to_key)

            # Calculate the interval between keys
            transpose_interval = interval.Interval(source_key.tonic, target_key.tonic)

            # Transpose the score
            transposed_score = score.transpose(transpose_interval)

            # Write the transposed score
            transposed_score.write("musicxml", fp=abs_output)

            logger.info(f"Transposition complete: {output_path or input_path}")
            return True, output_path or input_path, None

        except Exception as e:
            error_msg = f"Transposition error: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def detect_key(self, input_path: str) -> Optional[str]:
        """
        Attempt to detect the key of a MusicXML file.

        Args:
            input_path: Relative path to MusicXML file

        Returns:
            Detected key name or None
        """
        try:
            abs_input = get_file_path(input_path)
            score = converter.parse(abs_input)

            # Try to get key from score analysis
            detected_key = score.analyze("key")
            if detected_key:
                return str(detected_key)

            return None
        except Exception as e:
            logger.warning(f"Could not detect key: {e}")
            return None
