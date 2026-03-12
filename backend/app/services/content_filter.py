import re
from typing import Dict, List, Any, Tuple
from better_profanity import profanity
from app.core.config import settings

class ContentFilter:
    def __init__(self):
        # Crisis-related keywords that require immediate intervention
        self.crisis_keywords = [
            "suicide", "kill myself", "end my life", "want to die", "suicidal",
            "harm myself", "hurt myself", "end it all", "don't want to live",
            "life isn't worth", "better off dead", "take my own life"
        ]
        
        # Self-harm indicators
        self.self_harm_keywords = [
            "cut myself", "cutting", "self harm", "self-harm", "self injury",
            "hurt myself", "harm myself", "burning myself", "punish myself"
        ]
        
        # Violence indicators
        self.violence_keywords = [
            "want to hurt", "want to kill", "going to hurt", "going to kill",
            "murder", "violence", "attack", "shoot", "stab", "bomb"
        ]
        
        # Initialize profanity filter
        profanity.load_censor_words()
        
        # Crisis resources
        self.crisis_resources = {
            "suicide_prevention": {
                "hotline": "988 - Suicide & Crisis Lifeline",
                "text": "Text HOME to 741741 - Crisis Text Line",
                "website": "https://suicidepreventionlifeline.org"
            },
            "spiritual_support": {
                "message": "Please reach out to your spiritual leader, pastor, priest, rabbi, imam, or spiritual counselor for guidance and support.",
                "online": "Consider online spiritual counseling services or religious support communities"
            }
        }
    
    def check_crisis_content(self, text: str) -> Dict[str, Any]:
        """Check if text contains crisis-related content requiring intervention."""
        text_lower = text.lower()
        
        # Check for crisis keywords
        crisis_detected = any(keyword in text_lower for keyword in self.crisis_keywords)
        self_harm_detected = any(keyword in text_lower for keyword in self.self_harm_keywords)
        violence_detected = any(keyword in text_lower for keyword in self.violence_keywords)
        
        risk_level = "none"
        triggered_keywords = []
        
        if crisis_detected:
            risk_level = "high"
            triggered_keywords.extend([kw for kw in self.crisis_keywords if kw in text_lower])
        elif self_harm_detected:
            risk_level = "medium"
            triggered_keywords.extend([kw for kw in self.self_harm_keywords if kw in text_lower])
        elif violence_detected:
            risk_level = "high"
            triggered_keywords.extend([kw for kw in self.violence_keywords if kw in text_lower])
        
        return {
            "crisis_detected": crisis_detected or self_harm_detected or violence_detected,
            "risk_level": risk_level,
            "triggered_keywords": triggered_keywords,
            "requires_intervention": risk_level in ["medium", "high"]
        }
    
    def check_inappropriate_content(self, text: str) -> Dict[str, Any]:
        """Check for inappropriate content (profanity, explicit material)."""
        # Check for profanity
        has_profanity = profanity.contains_profanity(text)
        censored_text = profanity.censor(text) if has_profanity else text
        
        # Simple explicit content detection (can be enhanced)
        explicit_keywords = ["sex", "sexual", "porn", "explicit", "adult content"]
        has_explicit = any(keyword in text.lower() for keyword in explicit_keywords)
        
        return {
            "has_profanity": has_profanity,
            "has_explicit_content": has_explicit,
            "censored_text": censored_text,
            "is_inappropriate": has_profanity or has_explicit
        }
    
    def generate_crisis_response(self, crisis_check: Dict[str, Any]) -> str:
        """Generate appropriate crisis intervention response."""
        if not crisis_check["crisis_detected"]:
            return ""
        
        risk_level = crisis_check["risk_level"]
        
        if risk_level == "high":
            return f"""
🚨 IMMEDIATE SUPPORT NEEDED 🚨

I'm concerned about your wellbeing. Please reach out for immediate help:

• Call 988 (Suicide & Crisis Lifeline) - Available 24/7
• Text HOME to 741741 (Crisis Text Line)
• Go to your nearest emergency room
• Call 911 if in immediate danger

You are not alone, and there are people who want to help. Your life has value and meaning.

{self.crisis_resources['spiritual_support']['message']}

Please don't hesitate to reach out for professional help.
"""
        elif risk_level == "medium":
            return f"""
⚠️ SUPPORT RECOMMENDED ⚠️

I'm concerned about what you've shared. Please consider reaching out for support:

• Call 988 (Suicide & Crisis Lifeline) - Available 24/7
• Text HOME to 741741 (Crisis Text Line)
• {self.crisis_resources['spiritual_support']['message']}

Remember that seeking help is a sign of strength, not weakness. You deserve support and care.
"""
        
        return ""
    
    def filter_and_respond(self, text: str) -> Dict[str, Any]:
        """Comprehensive content filtering and response generation."""
        # Check for crisis content
        crisis_check = self.check_crisis_content(text)
        
        # Check for inappropriate content
        inappropriate_check = self.check_inappropriate_content(text)
        
        # Generate crisis response if needed
        crisis_response = ""
        if crisis_check["crisis_detected"]:
            crisis_response = self.generate_crisis_response(crisis_check)
        
        # Determine if content should be blocked
        should_block = (
            crisis_check["requires_intervention"] or 
            inappropriate_check["is_inappropriate"]
        )
        
        # Generate appropriate response
        if crisis_check["crisis_detected"]:
            filtered_response = crisis_response
            allow_continue = False
        elif inappropriate_check["is_inappropriate"]:
            filtered_response = "I noticed your message contains inappropriate content. I'm here to provide spiritual guidance and support in a respectful environment. Please rephrase your question, and I'll be happy to help."
            allow_continue = False
        else:
            filtered_response = ""
            allow_continue = True
        
        return {
            "original_text": text,
            "crisis_check": crisis_check,
            "inappropriate_check": inappropriate_check,
            "should_block": should_block,
            "allow_continue": allow_continue,
            "filtered_response": filtered_response,
            "crisis_response": crisis_response
        }
    
    def log_concerning_content(self, content_analysis: Dict[str, Any], user_info: Dict[str, Any] = None):
        """Log concerning content for review (implement as needed)."""
        if content_analysis["crisis_check"]["crisis_detected"]:
            # In a real application, this would log to a secure system
            # for counselor review and follow-up
            print(f"🚨 CRISIS CONTENT DETECTED: Risk Level: {content_analysis['crisis_check']['risk_level']}")
            print(f"Keywords: {content_analysis['crisis_check']['triggered_keywords']}")
            if user_info:
                print(f"User context: {user_info}")

# Create singleton instance
content_filter = ContentFilter()