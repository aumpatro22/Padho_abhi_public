"""
Gemini AI Service for generating educational content
"""
import google.generativeai as genai
import logging
import json
import re
from django.conf import settings


class GeminiService:
    """Service class for all Gemini AI interactions"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _configure_client(self, api_key=None):
        """Configure the client with the appropriate API key"""
        # If a custom key is provided, use it. Otherwise use the system key.
        key = api_key if api_key else settings.GEMINI_API_KEY
        genai.configure(api_key=key)
        # Re-initialize model to ensure it picks up the new config
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _clean_json_response(self, text):
        """Extract JSON from response text"""
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return None

    def _extract_usage(self, response):
        """Extract token usage metadata from response"""
        try:
            if hasattr(response, 'usage_metadata'):
                return {
                    'input': response.usage_metadata.prompt_token_count,
                    'output': response.usage_metadata.candidates_token_count
                }
        except Exception:
            pass
        return {'input': 0, 'output': 0}

    def _error_dict(self, e):
        logging.getLogger(__name__).exception('GeminiService error')
        msg = str(e)
        lower = msg.lower()
        if 'quota' in lower or 'rate limit' in lower or 'too many requests' in lower or '429' in lower:
            return {'error': msg, 'error_code': 'quota_exceeded'}
        return {'error': msg}
    
    def generate_notes(self, topic_name, subject_name="Computer Networks", api_key=None):
        """
        Generate notes for a topic
        Returns: dict with content and usage
        """
        self._configure_client(api_key)
        prompt = f"""You are a professor teaching {subject_name} to 3rd semester B.Tech students.
Topic: "{topic_name}"

Explain this topic in simple language. Return your response as JSON with this exact structure:
{{
    "summary": "A 150-word summary explaining the topic clearly",
    "detailed_content": "A detailed 300-word explanation with key points",
    "analogies": ["analogy 1", "analogy 2", "analogy 3"],
    "diagram_description": "A text description of a diagram that would help understand this topic"
}}

Make the content easy to understand for students. Use simple language and practical examples.
Return ONLY the JSON, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result = self._clean_json_response(response.text)
            if not result:
                # Fallback
                result = {
                    "summary": response.text[:500],
                    "detailed_content": response.text,
                    "analogies": [],
                    "diagram_description": ""
                }
            result['usage'] = self._extract_usage(response)
            return result
        except Exception as e:
            return self._error_dict(e)
    
    def generate_mindmap(self, topic_name, subject_name="Computer Networks", api_key=None):
        """
        Generate mindmap structure for a topic
        Returns: dict with content and usage
        """
        self._configure_client(api_key)
        prompt = f"""Create a mindmap structure IN ENGLISH ONLY for the topic "{topic_name}" in {subject_name} for B.Tech level students.

IMPORTANT: All text must be in English language only. Do not use any other language.

Return ONLY a JSON object in this exact format:
{{
    "central_idea": "{topic_name}",
    "branches": [
        {{
            "title": "Main Branch 1",
            "subpoints": ["subpoint 1", "subpoint 2", "subpoint 3"]
        }},
        {{
            "title": "Main Branch 2",
            "subpoints": ["subpoint 1", "subpoint 2"]
        }}
    ]
}}

Include 4-6 main branches with 2-4 subpoints each. Make it comprehensive but organized.
Return ONLY the JSON, no other text. Write everything in English."""

        try:
            response = self.model.generate_content(prompt)
            result = self._clean_json_response(response.text)
            if not result:
                result = {
                    "central_idea": topic_name,
                    "branches": [{"title": "Error parsing response", "subpoints": []}]
                }
            result['usage'] = self._extract_usage(response)
            return result
        except Exception as e:
            return self._error_dict(e)
    
    def generate_flashcards(self, topic_name, notes_content="", count=10, api_key=None):
        """
        Generate flashcards for a topic
        Returns: dict with list 'flashcards' and 'usage'
        """
        self._configure_client(api_key)
        context = f"\nContext from notes:\n{notes_content}" if notes_content else ""
        
        prompt = f"""Create {count} flashcards IN ENGLISH for B.Tech level students for the topic "{topic_name}".{context}

IMPORTANT: All text must be in English language only.

Return ONLY a JSON array in this exact format:
[
    {{"front": "Question or term", "back": "Answer or definition"}},
    {{"front": "Question or term", "back": "Answer or definition"}}
]

Make flashcards that:
- Cover key concepts, definitions, and important facts
- Use clear, concise English language
- Help students memorize and understand the topic

Return ONLY the JSON array, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result = self._clean_json_response(response.text)
            if not result or not isinstance(result, list):
                result = []
            return {
                'flashcards': result,
                'usage': self._extract_usage(response)
            }
        except Exception as e:
            return self._error_dict(e)
    
    def generate_mcqs(self, topic_name, notes_content="", count=10, api_key=None):
        """
        Generate MCQs for a topic
        Returns: dict with list 'mcqs' and 'usage'
        """
        self._configure_client(api_key)
        context = f"\nBased on these notes:\n{notes_content}" if notes_content else ""
        
        prompt = f"""Generate {count} B.Tech level MCQs IN ENGLISH for the topic "{topic_name}".{context}

IMPORTANT: All text must be in English language only.

Return ONLY a JSON array in this exact format:
[
    {{
        "question": "The question text here?",
        "options": {{
            "a": "Option A text",
            "b": "Option B text",
            "c": "Option C text",
            "d": "Option D text"
        }},
        "correct": "a",
        "explanation": "Brief explanation of why this answer is correct",
        "difficulty": "medium"
    }}
]

Requirements:
- Mix of easy, medium, and hard questions
- Clear, unambiguous English questions
- Plausible distractors for wrong options
- Helpful explanations in English

Return ONLY the JSON array, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result = self._clean_json_response(response.text)
            if not result or not isinstance(result, list):
                result = []
            return {
                'mcqs': result,
                'usage': self._extract_usage(response)
            }
        except Exception as e:
            return self._error_dict(e)
    
    def tag_pyq_to_topic(self, question_text, topic_list, api_key=None):
        """
        Tag a PYQ to the most relevant topic
        Returns: dict with 'topic' and 'usage'
        """
        self._configure_client(api_key)
        topics_str = "\n".join([f"- {t}" for t in topic_list])
        
        prompt = f"""Given the following topics:
{topics_str}

Question: "{question_text}"

Which ONE topic does this question best belong to?
Reply with EXACTLY the topic text only, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            return {
                'topic': response.text.strip(),
                'usage': self._extract_usage(response)
            }
        except Exception as e:
            return self._error_dict(e)
    
    def answer_doubt(self, user_question, topic_name, notes_content, api_key=None):
        """
        Answer a student's doubt using provided material or general knowledge
        Returns: dict with 'answer' and 'usage'
        """
        self._configure_client(api_key)
        prompt = f"""You are a helpful tutor for B.Tech students studying Computer Networks.
The student is asking about the topic: "{topic_name}"

Here are the notes for this topic:
\"\"\"
{notes_content}
\"\"\"

Student's question: "{user_question}"

Instructions:
- Answer the question clearly and concisely.
- You may use the provided notes as context, but if the information is missing, use your general knowledge to explain the concept.
- Keep the explanation brief and easy to understand.

Your answer:"""

        try:
            response = self.model.generate_content(prompt)
            return {
                'answer': response.text,
                'usage': self._extract_usage(response)
            }
        except Exception as e:
            return self._error_dict(e)
    
    def generate_all_content(self, topic_name, subject_name="Computer Networks", api_key=None):
        """
        Generate all content (notes, mindmap, flashcards, MCQs) for a topic
        Returns: dict with all content and aggregated usage
        """
        notes = self.generate_notes(topic_name, subject_name, api_key)
        mindmap = self.generate_mindmap(topic_name, subject_name, api_key)
        
        notes_content = notes.get('detailed_content', notes.get('summary', ''))
        flashcards = self.generate_flashcards(topic_name, notes_content, count=10, api_key=api_key)
        mcqs = self.generate_mcqs(topic_name, notes_content, count=10, api_key=api_key)
        
        # Aggregate usage
        total_usage = {'input': 0, 'output': 0}
        for item in [notes, mindmap, flashcards, mcqs]:
            if 'usage' in item:
                total_usage['input'] += item['usage']['input']
                total_usage['output'] += item['usage']['output']

        return {
            'notes': notes,
            'mindmap': mindmap,
            'flashcards': flashcards.get('flashcards', []),
            'mcqs': mcqs.get('mcqs', []),
            'usage': total_usage
        }

    def parse_syllabus(self, syllabus_text, subject_name, api_key=None):
        """
        Parse uploaded syllabus text and extract units and topics
        Returns: dict with content and usage
        """
        self._configure_client(api_key)
        prompt = f"""You are an expert at parsing academic syllabi. 
Given the following syllabus for the subject "{subject_name}", extract and organize all units and topics.

Syllabus:
\"\"\"
{syllabus_text}
\"\"\"

Return ONLY a JSON object in this exact format:
{{
    "subject_name": "{subject_name}",
    "subject_code": "extracted code if present or empty string",
    "description": "brief 1-2 sentence description of the subject",
    "units": [
        {{
            "unit_number": 1,
            "name": "Unit Name",
            "description": "brief description of what this unit covers",
            "topics": [
                "Topic 1 name",
                "Topic 2 name",
                "Topic 3 name"
            ]
        }},
        {{
            "unit_number": 2,
            "name": "Unit Name",
            "topics": ["Topic 1", "Topic 2"]
        }}
    ]
}}

IMPORTANT RULES:
- Each topic in the "topics" array should be a SIMPLE STRING, not an object or dictionary
- Extract ALL units and topics from the syllabus
- Keep topic names concise but descriptive
- Maintain the order of units and topics as they appear
- If unit numbers are not explicit, number them sequentially
- Each unit should have its list of topics as an array of strings

Return ONLY the JSON, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result = self._clean_json_response(response.text)
            if not result:
                result = {"error": "Failed to parse syllabus"}
            if 'error' not in result:
                result['usage'] = self._extract_usage(response)
            return result
        except Exception as e:
            return self._error_dict(e)


# Singleton instance
gemini_service = GeminiService()
