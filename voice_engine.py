"""
voice_engine.py - TTS synthesis with dynamic vocal parameter modulation
"""

import os
import io
import tempfile

# ---------------------------------------------------
# FFmpeg configuration
# Works locally on Windows and in deployment platforms
# like Render / Railway
# ---------------------------------------------------

ffmpeg_path = os.getenv("FFMPEG_PATH")
ffprobe_path = os.getenv("FFPROBE_PATH")

# Local Windows fallback
if not ffmpeg_path:
    ffmpeg_path = (
        r"C:\Users\HP\Downloads\ffmpeg-2026-04-09-git-d3d0b7a5ee-essentials_build"
        r"\ffmpeg-2026-04-09-git-d3d0b7a5ee-essentials_build\bin\ffmpeg.exe"
    )

if not ffprobe_path:
    ffprobe_path = (
        r"C:\Users\HP\Downloads\ffmpeg-2026-04-09-git-d3d0b7a5ee-essentials_build"
        r"\ffmpeg-2026-04-09-git-d3d0b7a5ee-essentials_build\bin\ffprobe.exe"
    )

# Add FFmpeg folder to PATH if it exists
ffmpeg_dir = os.path.dirname(ffmpeg_path)
if os.path.exists(ffmpeg_dir):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir

from pydub import AudioSegment

AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# ---------------------------------------------------
# Optional TTS backends
# ---------------------------------------------------

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class VoiceEngine:
    def __init__(self, audio_dir="static/audio"):
        self.audio_dir = audio_dir
        os.makedirs(self.audio_dir, exist_ok=True)

    def synthesize(self, text, emotion, output_path):
        """
        Generate audio from text and apply emotion-based modulation.
        Returns: (success: bool, error_message: str)
        """
        try:
            params = emotion.get("voice_params", {})

            rate = params.get("rate", 1.0)
            pitch_str = params.get("pitch", "0st")
            volume = params.get("volume", 100)

            # Generate base speech
            base_audio = self._generate_base_tts(text)

            if base_audio is None:
                return False, "No TTS engine available"

            # Apply speaking speed
            audio = self._apply_speed(base_audio, rate)

            # Apply pitch shift
            semitones = self._parse_semitones(pitch_str)
            if semitones != 0:
                audio = self._apply_pitch(audio, semitones)

            # Apply volume
            audio = self._apply_volume(audio, volume)

            # Export audio
            audio.export(output_path, format="mp3", bitrate="128k")

            return True, ""

        except Exception as e:
            return False, str(e)

    def _generate_base_tts(self, text):
        """
        First try gTTS (online), fallback to pyttsx3 (offline)
        """
        # Try Google TTS
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=text, lang="en", slow=False)

                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)

                return AudioSegment.from_file(buffer, format="mp3")

            except Exception as e:
                print(f"gTTS failed: {e}")

        # Fallback to offline pyttsx3
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 175)

                with tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False
                ) as temp_file:
                    temp_path = temp_file.name

                engine.save_to_file(text, temp_path)
                engine.runAndWait()

                audio = AudioSegment.from_wav(temp_path)

                try:
                    os.remove(temp_path)
                except Exception:
                    pass

                return audio

            except Exception as e:
                print(f"pyttsx3 failed: {e}")

        return None

    def _apply_speed(self, audio, rate):
        """
        Change playback speed while preserving compatibility.
        """
        if abs(rate - 1.0) < 0.01:
            return audio

        new_frame_rate = int(audio.frame_rate * rate)

        modified = audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": new_frame_rate}
        )

        return modified.set_frame_rate(audio.frame_rate)

    def _apply_pitch(self, audio, semitones):
        """
        Shift pitch by semitones.
        """
        ratio = 2 ** (semitones / 12.0)

        shifted = audio._spawn(
            audio.raw_data,
            overrides={
                "frame_rate": int(audio.frame_rate * ratio)
            }
        ).set_frame_rate(audio.frame_rate)

        # Keep original speed after pitch shift
        return self._apply_speed(shifted, 1.0 / ratio)

    def _apply_volume(self, audio, volume):
        """
        Volume expected in range 0-100
        """
        if volume <= 0:
            return audio - 40

        target_dbfs = -30 + (volume / 100.0) * 27
        change = target_dbfs - audio.dBFS

        return audio + change

    def _parse_semitones(self, pitch_str):
        """
        Convert values like '+2st' or '-1.5st' into float semitones.
        """
        if not pitch_str:
            return 0.0

        try:
            return float(pitch_str.replace("st", "").strip())
        except Exception:
            return 0.0