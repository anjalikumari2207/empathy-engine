"""
emotion_engine.py - Multi-class emotion detection with intensity scaling

Uses VADER for base sentiment + rule-based emotion classification to detect:
Happy, Excited, Sad, Angry, Fearful, Surprised, Neutral, Concerned
"""

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class EmotionAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

        # Emotion keyword lexicons
        self.emotion_lexicon = {
            "excited": {
                "keywords": [
                    "amazing", "incredible", "fantastic", "awesome", "brilliant",
                    "won", "winning", "best ever", "unbelievable", "thrilled",
                    "ecstatic", "outstanding", "phenomenal", "extraordinary",
                    "can't believe", "this is great", "so excited", "love this",
                    "perfect", "wonderful", "celebrate", "victory"
                ],
                "weight": 1.4
            },
            "happy": {
                "keywords": [
                    "happy", "glad", "good", "great", "nice", "pleased",
                    "delighted", "joyful", "cheerful", "smile", "laugh",
                    "fun", "enjoy", "like", "thanks", "thank you",
                    "appreciate", "blessed", "grateful", "lucky", "fortunate"
                ],
                "weight": 1.0
            },
            "angry": {
                "keywords": [
                    "angry", "furious", "outraged", "infuriated", "disgusted",
                    "terrible", "awful", "horrible", "hate", "worst",
                    "unacceptable", "ridiculous", "useless", "broken",
                    "pathetic", "disaster", "disaster", "fed up", "livid",
                    "absurd", "stupid", "incompetent", "failed again"
                ],
                "weight": 1.3
            },
            "sad": {
                "keywords": [
                    "sad", "unhappy", "depressed", "miserable", "devastated",
                    "heartbroken", "lonely", "miss", "lost", "failed",
                    "disappointed", "unfortunate", "sorry", "regret", "wish",
                    "hurt", "pain", "crying", "tears", "hopeless", "terrible news"
                ],
                "weight": 1.0
            },
            "fearful": {
                "keywords": [
                    "scared", "afraid", "terrified", "worried", "anxious",
                    "nervous", "panic", "fear", "dread", "frightened",
                    "concerned about", "what if", "not sure", "uncertain",
                    "dangerous", "risk", "threat", "emergency"
                ],
                "weight": 1.1
            },
            "surprised": {
                "keywords": [
                    "wow", "whoa", "omg", "oh my", "really?", "seriously",
                    "can't believe", "unexpected", "shocking", "sudden",
                    "just heard", "wait what", "no way", "unreal",
                    "didn't expect", "out of nowhere", "just found out"
                ],
                "weight": 1.2
            },
            "concerned": {
                "keywords": [
                    "concern", "issue", "problem", "trouble", "difficulty",
                    "challenge", "struggle", "need help", "not working",
                    "please help", "urgent", "serious", "critical",
                    "something wrong", "not right", "delay", "stuck"
                ],
                "weight": 0.9
            }
        }

        # Voice parameter configurations per emotion + intensity
        self.voice_map = {
            "excited": {
                "base": {"rate": 1.35, "pitch": "+8st", "volume": 95},
                "high": {"rate": 1.5,  "pitch": "+12st", "volume": 100},
                "low":  {"rate": 1.2,  "pitch": "+4st",  "volume": 88}
            },
            "happy": {
                "base": {"rate": 1.1, "pitch": "+4st", "volume": 88},
                "high": {"rate": 1.2, "pitch": "+6st", "volume": 92},
                "low":  {"rate": 1.0, "pitch": "+2st", "volume": 85}
            },
            "angry": {
                "base": {"rate": 1.2, "pitch": "-2st", "volume": 100},
                "high": {"rate": 1.3, "pitch": "-4st", "volume": 100},
                "low":  {"rate": 1.1, "pitch": "-1st", "volume": 92}
            },
            "sad": {
                "base": {"rate": 0.82, "pitch": "-5st", "volume": 72},
                "high": {"rate": 0.75, "pitch": "-7st", "volume": 65},
                "low":  {"rate": 0.88, "pitch": "-3st", "volume": 78}
            },
            "fearful": {
                "base": {"rate": 1.0,  "pitch": "+3st", "volume": 75},
                "high": {"rate": 1.15, "pitch": "+5st", "volume": 70},
                "low":  {"rate": 0.95, "pitch": "+1st", "volume": 80}
            },
            "surprised": {
                "base": {"rate": 1.15, "pitch": "+6st", "volume": 90},
                "high": {"rate": 1.25, "pitch": "+9st", "volume": 95},
                "low":  {"rate": 1.05, "pitch": "+3st", "volume": 85}
            },
            "concerned": {
                "base": {"rate": 0.90, "pitch": "-2st", "volume": 80},
                "high": {"rate": 0.85, "pitch": "-3st", "volume": 78},
                "low":  {"rate": 0.95, "pitch": "-1st", "volume": 82}
            },
            "neutral": {
                "base": {"rate": 1.0,  "pitch": "0st",  "volume": 85},
                "high": {"rate": 1.0,  "pitch": "0st",  "volume": 85},
                "low":  {"rate": 1.0,  "pitch": "0st",  "volume": 85}
            }
        }

        # UI metadata (emoji, color, description)
        self.emotion_metadata = {
            "excited":   {"emoji": "🤩", "color": "#FF6B35", "desc": "High-energy enthusiasm"},
            "happy":     {"emoji": "😊", "color": "#4CAF50", "desc": "Warm positivity"},
            "angry":     {"emoji": "😠", "color": "#F44336", "desc": "Intense frustration"},
            "sad":       {"emoji": "😢", "color": "#5C6BC0", "desc": "Low & downcast"},
            "fearful":   {"emoji": "😨", "color": "#9C27B0", "desc": "Anxious & nervous"},
            "surprised": {"emoji": "😲", "color": "#FF9800", "desc": "Sudden shock"},
            "concerned": {"emoji": "😟", "color": "#607D8B", "desc": "Worried & cautious"},
            "neutral":   {"emoji": "😐", "color": "#78909C", "desc": "Calm & measured"}
        }

    def analyze(self, text: str) -> dict:
        text_lower = text.lower()

        # VADER scores
        vader_scores = self.vader.polarity_scores(text)
        compound = vader_scores["compound"]

        # Score each emotion
        emotion_scores = {}
        for emotion, config in self.emotion_lexicon.items():
            score = 0.0
            for kw in config["keywords"]:
                if kw in text_lower:
                    score += config["weight"]
            # Bonus for exclamation / question marks
            if emotion in ("excited", "surprised", "angry"):
                score += text.count("!") * 0.3
            if emotion == "surprised":
                score += text.count("?") * 0.2
            emotion_scores[emotion] = round(score, 3)

        # Normalize
        total = sum(emotion_scores.values()) or 1
        norm_scores = {e: round(s / total, 3) for e, s in emotion_scores.items()}

        # Pick winner with fallback to VADER
        best_emotion = max(norm_scores, key=norm_scores.get)
        best_score = norm_scores[best_emotion]

        # If no keyword matched strongly, fall back to VADER sentiment
        if best_score < 0.15:
            if compound >= 0.35:
                best_emotion = "happy"
                best_score = abs(compound)
            elif compound <= -0.35:
                best_emotion = "sad"
                best_score = abs(compound)
            else:
                best_emotion = "neutral"
                best_score = 1 - abs(compound)

        # Intensity: high if score > 0.45 or many exclamations
        exclamations = text.count("!")
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

        if best_score > 0.45 or exclamations >= 2 or caps_ratio > 0.3:
            intensity = "high"
        elif best_score < 0.2 and exclamations == 0:
            intensity = "low"
        else:
            intensity = "base"

        voice_params = self.voice_map[best_emotion][intensity]

        return {
            "label": best_emotion,
            "confidence": round(min(best_score + 0.3, 0.99), 2),
            "intensity": intensity,
            "scores": norm_scores,
            "voice_params": voice_params,
            "vader": vader_scores
        }

    def get_emotion_metadata(self) -> dict:
        return self.emotion_metadata
