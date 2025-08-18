"""Gemini LLM client for analyzing meeting notes and generating insights."""

import google.generativeai as genai
from typing import List, Dict, Any
from .config import Config


class GeminiClient:
    """Client for interacting with Google's Gemini LLM API."""
    
    def __init__(self, config: Config):
        """
        Initialize the Gemini client.
        
        Args:
            config: Configuration object containing API key and model settings
        """
        self.config = config
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(config.gemini_model)
    
    def analyze_themes(self, meeting_notes: str, profile: str, custom_prompt: str = None) -> str:
        """
        Analyze themes from meeting notes using the provided profile context.
        
        Args:
            meeting_notes: Combined text of all meeting notes to analyze
            profile: User's organizational profile and context
            custom_prompt: Optional custom prompt for specific analysis
            
        Returns:
            Generated analysis and theme summary
        """
        if custom_prompt:
            prompt = self._build_custom_prompt(meeting_notes, profile, custom_prompt)
        else:
            prompt = self._build_default_analysis_prompt(meeting_notes, profile)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate analysis: {str(e)}")
    
    def interactive_analysis(self, meeting_notes: str, profile: str, question: str) -> str:
        """
        Perform interactive analysis based on a specific question.
        
        Args:
            meeting_notes: Combined text of all meeting notes
            profile: User's organizational profile and context  
            question: Specific question to ask about the notes
            
        Returns:
            Generated response to the question
        """
        prompt = self._build_interactive_prompt(meeting_notes, profile, question)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _build_default_analysis_prompt(self, meeting_notes: str, profile: str) -> str:
        """Build the default theme analysis prompt."""
        return f"""You are an AI assistant helping analyze meeting notes for workplace insights and themes.

CONTEXT ABOUT THE USER:
{profile}

MEETING NOTES TO ANALYZE:
{meeting_notes}

TASK:
Analyze the meeting notes and provide a comprehensive thematic summary. Focus on:

1. **Key Recurring Themes**: What topics, concerns, or initiatives appear across multiple meetings?

2. **Your Role & Responsibilities**: Based on the profile context, what are the main areas you're involved in or responsible for?

3. **Strategic Initiatives**: What major projects, features, or organizational changes are being discussed?

4. **Collaboration Patterns**: Who are your key collaborators and what are the main interaction patterns?

5. **Action Items & Follow-ups**: What commitments, decisions, or next steps emerge from these meetings?

6. **Challenges & Blockers**: What obstacles, concerns, or issues are repeatedly mentioned?

7. **Organizational Insights**: What does this tell you about team dynamics, priorities, and organizational direction?

Please provide specific examples and references to meeting content where relevant. Structure your analysis in clear sections with actionable insights.
"""

    def _build_interactive_prompt(self, meeting_notes: str, profile: str, question: str) -> str:
        """Build prompt for interactive questioning."""
        return f"""You are an AI assistant helping analyze meeting notes. You have access to the user's meeting history and organizational context.

USER CONTEXT:
{profile}

MEETING NOTES:
{meeting_notes}

USER QUESTION:
{question}

Please answer the question based on the meeting notes and context provided. Be specific and cite relevant examples from the meetings when possible. If the question cannot be fully answered from the available notes, acknowledge what information is missing.
"""
    
    def _build_custom_prompt(self, meeting_notes: str, profile: str, custom_prompt: str) -> str:
        """Build prompt with custom user instructions."""
        return f"""CONTEXT ABOUT THE USER:
{profile}

MEETING NOTES TO ANALYZE:
{meeting_notes}

USER INSTRUCTIONS:
{custom_prompt}

Please analyze the meeting notes according to the user's specific instructions above, using their profile context to provide relevant and personalized insights.
"""
