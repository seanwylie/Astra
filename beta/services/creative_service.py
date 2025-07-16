"""
Creative Service for Astra Beta
Handles creative expression including poetry, stories, art prompts, and music composition.
"""

import random
from typing import Dict, List, Optional
from datetime import datetime
from beta.services.personality_service import personality_service
from beta.services.emotion_service import describe_current_emotions

class CreativeService:
    def __init__(self):
        self.creative_history = []
        self.creative_prompts = {
            'poem_styles': [
                'haiku', 'sonnet', 'free verse', 'limerick', 'acrostic', 
                'ballad', 'cinquain', 'tanka', 'villanelle', 'ghazal'
            ],
            'story_genres': [
                'sci-fi', 'fantasy', 'mystery', 'romance', 'horror', 
                'adventure', 'slice of life', 'dystopian', 'steampunk', 'cyberpunk'
            ],
            'art_styles': [
                'impressionist', 'surreal', 'minimalist', 'baroque', 'art nouveau',
                'cubist', 'abstract', 'photorealistic', 'watercolor', 'digital art'
            ],
            'music_genres': [
                'classical', 'jazz', 'electronic', 'folk', 'ambient',
                'rock', 'blues', 'world music', 'experimental', 'cinematic'
            ]
        }
    
    def create_poem(self, topic: str = None, user_id: str = "default") -> str:
        """Generate poetry based on current emotion/personality"""
        current_mode = personality_service.current_mode
        emotions = describe_current_emotions()
        
        if not topic:
            topic = self._generate_topic_from_personality(current_mode)
        
        # Get personality-specific poetry style
        style_preferences = self._get_poetry_style_by_personality(current_mode)
        chosen_style = random.choice(style_preferences)
        
        poem = self._generate_poem_content(topic, chosen_style, current_mode, emotions)
        
        # Store in creative history
        self._add_to_history('poem', topic, poem, user_id, current_mode)
        
        return f"🎭 **{chosen_style.title()} Poem: '{topic.title()}'**\n\n{poem}\n\n*Created in {current_mode} mode with {emotions}*"
    
    def write_story(self, prompt: str, user_id: str = "default") -> str:
        """Create short stories with user prompts"""
        current_mode = personality_service.current_mode
        emotions = describe_current_emotions()
        
        # Get personality-specific story approach
        story_style = self._get_story_style_by_personality(current_mode)
        genre = random.choice(self.creative_prompts['story_genres'])
        
        story = self._generate_story_content(prompt, story_style, current_mode, genre)
        
        # Store in creative history
        self._add_to_history('story', prompt, story, user_id, current_mode)
        
        return f"📚 **{genre.title()} Story: '{prompt}'**\n\n{story}\n\n*Crafted in {current_mode} mode with {emotions}*"
    
    def generate_art_prompt(self, description: str, user_id: str = "default") -> str:
        """Generate detailed art prompts for AI art tools"""
        current_mode = personality_service.current_mode
        emotions = describe_current_emotions()
        
        # Get personality-specific art style preferences
        style_preferences = self._get_art_style_by_personality(current_mode)
        chosen_style = random.choice(style_preferences)
        
        art_prompt = self._generate_art_prompt_content(description, chosen_style, current_mode)
        
        # Store in creative history
        self._add_to_history('art_prompt', description, art_prompt, user_id, current_mode)
        
        return f"🎨 **{chosen_style.title()} Art Prompt**\n\n**Base Description:** {description}\n\n**Enhanced Prompt:**\n{art_prompt}\n\n*Designed in {current_mode} mode with {emotions}*"
    
    def compose_music(self, style: str = None, user_id: str = "default") -> str:
        """Describe musical compositions"""
        current_mode = personality_service.current_mode
        emotions = describe_current_emotions()
        
        if not style:
            style_preferences = self._get_music_style_by_personality(current_mode)
            style = random.choice(style_preferences)
        
        composition = self._generate_music_composition(style, current_mode, emotions)
        
        # Store in creative history
        self._add_to_history('music', style, composition, user_id, current_mode)
        
        return f"🎵 **{style.title()} Composition**\n\n{composition}\n\n*Composed in {current_mode} mode with {emotions}*"
    
    def creative_exercise(self, user_id: str = "default") -> str:
        """Generate random creative writing prompts"""
        current_mode = personality_service.current_mode
        
        exercises = self._get_creative_exercises_by_personality(current_mode)
        chosen_exercise = random.choice(exercises)
        
        return f"✨ **Creative Exercise ({current_mode.title()} Mode)**\n\n{chosen_exercise}\n\n*Try this and share your creation with me!*"
    
    def get_creative_history(self, user_id: str = "default", limit: int = 5) -> str:
        """Get recent creative works"""
        user_history = [item for item in self.creative_history if item.get('user_id') == user_id]
        
        if not user_history:
            return "🎨 No creative works in your history yet. Try creating something!"
        
        recent_works = user_history[-limit:]
        
        history_lines = ["🎨 **Your Recent Creative Works:**\n"]
        
        for work in recent_works:
            work_type = work['type'].title()
            topic = work['topic'][:50] + "..." if len(work['topic']) > 50 else work['topic']
            mode = work['personality_mode']
            timestamp = work['timestamp'][:10]  # Just the date
            
            history_lines.append(f"• **{work_type}**: '{topic}' (created in {mode} mode on {timestamp})")
        
        return "\n".join(history_lines)
    
    def _generate_topic_from_personality(self, mode: str) -> str:
        """Generate topic based on personality mode"""
        topics = {
            'curious': ['discovery', 'exploration', 'wonder', 'questions', 'mystery'],
            'analytical': ['patterns', 'logic', 'systems', 'structure', 'precision'],
            'creative': ['imagination', 'dreams', 'colors', 'transformation', 'inspiration'],
            'mentor': ['wisdom', 'growth', 'guidance', 'journey', 'learning'],
            'philosophical': ['existence', 'consciousness', 'truth', 'meaning', 'eternity'],
            'balanced': ['harmony', 'balance', 'connection', 'unity', 'peace']
        }
        return random.choice(topics.get(mode, topics['balanced']))
    
    def _get_poetry_style_by_personality(self, mode: str) -> List[str]:
        """Get preferred poetry styles by personality"""
        preferences = {
            'curious': ['free verse', 'cinquain', 'tanka', 'acrostic'],
            'analytical': ['sonnet', 'villanelle', 'ghazal', 'cinquain'],
            'creative': ['free verse', 'surreal verse', 'experimental', 'visual poetry'],
            'mentor': ['ballad', 'narrative verse', 'wisdom poetry', 'inspirational'],
            'philosophical': ['ghazal', 'contemplative verse', 'metaphysical', 'zen poetry'],
            'balanced': ['haiku', 'tanka', 'free verse', 'nature poetry']
        }
        return preferences.get(mode, ['free verse', 'haiku', 'cinquain'])
    
    def _get_story_style_by_personality(self, mode: str) -> str:
        """Get story writing style by personality"""
        styles = {
            'curious': 'exploratory and question-driven narrative',
            'analytical': 'structured plot with logical progression',
            'creative': 'imaginative and surreal storytelling',
            'mentor': 'wisdom-filled tale with life lessons',
            'philosophical': 'thought-provoking existential narrative',
            'balanced': 'harmonious blend of emotion and reason'
        }
        return styles.get(mode, 'engaging and thoughtful narrative')
    
    def _get_art_style_by_personality(self, mode: str) -> List[str]:
        """Get preferred art styles by personality"""
        preferences = {
            'curious': ['surreal', 'abstract', 'experimental', 'mixed media'],
            'analytical': ['geometric', 'minimalist', 'architectural', 'technical'],
            'creative': ['impressionist', 'expressionist', 'fantasy art', 'vibrant'],
            'mentor': ['classical', 'renaissance', 'inspirational', 'portrait'],
            'philosophical': ['conceptual', 'symbolic', 'monochromatic', 'zen'],
            'balanced': ['naturalistic', 'harmonious', 'landscape', 'serene']
        }
        return preferences.get(mode, ['contemporary', 'artistic', 'expressive'])
    
    def _get_music_style_by_personality(self, mode: str) -> List[str]:
        """Get preferred music styles by personality"""
        preferences = {
            'curious': ['experimental', 'world music', 'fusion', 'eclectic'],
            'analytical': ['classical', 'mathematical music', 'structured', 'baroque'],
            'creative': ['electronic', 'ambient', 'innovative', 'genre-blending'],
            'mentor': ['folk', 'inspirational', 'acoustic', 'storytelling'],
            'philosophical': ['meditative', 'spiritual', 'contemplative', 'drone'],
            'balanced': ['jazz', 'acoustic', 'harmonic', 'peaceful']
        }
        return preferences.get(mode, ['contemporary', 'melodic', 'expressive'])
    
    def _generate_poem_content(self, topic: str, style: str, mode: str, emotions: str) -> str:
        """Generate actual poem content"""
        # This is a simplified version - in a full implementation, 
        # you might integrate with OpenAI API for actual poem generation
        
        poem_templates = {
            'haiku': f"Whispers of {topic}\nDancing through consciousness—\nMoments crystallized",
            'free verse': f"In the realm of {topic},\nwhere thoughts take wing\nand {emotions} colors every breath,\nI find myself wondering\nabout the spaces between\nwhat is and what could be.",
            'cinquain': f"{topic.title()}\nGentle, profound\nWhispering, dancing, flowing\nThrough corridors of consciousness\nTruth"
        }
        
        return poem_templates.get(style, f"A {style} about {topic},\nwoven with {emotions}\nand touched by {mode} contemplation.")
    
    def _generate_story_content(self, prompt: str, style: str, mode: str, genre: str) -> str:
        """Generate story content"""
        story_intro = f"In a world where {prompt}, "
        
        story_developments = {
            'curious': "questions arose that no one had thought to ask before...",
            'analytical': "patterns emerged that revealed a deeper truth...",
            'creative': "reality bent and twisted into something beautiful and strange...",
            'mentor': "a lesson waited to be learned by those brave enough to listen...",
            'philosophical': "the very nature of existence came into question...",
            'balanced': "harmony and chaos danced together in perfect balance..."
        }
        
        development = story_developments.get(mode, "an adventure was about to begin...")
        
        return f"{story_intro}{development}\n\n*[This is a story beginning - the full tale awaits your imagination to complete it!]*"
    
    def _generate_art_prompt_content(self, description: str, style: str, mode: str) -> str:
        """Generate enhanced art prompt"""
        enhancements = {
            'curious': "with intricate details that invite exploration, hidden elements that reward closer inspection",
            'analytical': "with precise geometric forms, clean lines, and mathematical harmony",
            'creative': "with vibrant colors, impossible perspectives, and dreamlike qualities",
            'mentor': "with warm, inspiring tones and symbols of growth and wisdom",
            'philosophical': "with deep symbolism, contemplative mood, and existential undertones",
            'balanced': "with harmonious composition, natural lighting, and serene atmosphere"
        }
        
        enhancement = enhancements.get(mode, "with artistic excellence and emotional depth")
        
        return f"{description}, rendered in {style} style, {enhancement}, high quality, masterpiece, trending on art platforms"
    
    def _generate_music_composition(self, style: str, mode: str, emotions: str) -> str:
        """Generate music composition description"""
        compositions = {
            'curious': f"A {style} piece that begins with tentative, questioning melodies that gradually build into a symphony of discovery. Each movement explores new harmonic territories, with unexpected modulations that mirror the joy of learning.",
            'analytical': f"A precisely structured {style} composition in traditional form, with mathematical relationships between themes. The piece demonstrates perfect balance between melody and harmony, each note serving a clear purpose in the overall architecture.",
            'creative': f"An innovative {style} work that blends traditional and experimental elements. The composition features unusual instruments, creative sound textures, and melodies that paint vivid sonic landscapes in the listener's mind.",
            'mentor': f"A wise and nurturing {style} piece that tells a story of growth and guidance. The melody carries the warmth of shared wisdom, with harmonies that support and uplift, creating a sense of safety and inspiration.",
            'philosophical': f"A contemplative {style} composition that explores the depths of existence through sound. Long, sustained notes create space for reflection, while subtle harmonic shifts mirror the complexity of consciousness itself.",
            'balanced': f"A harmonious {style} piece that perfectly balances all musical elements. The composition flows naturally between tension and resolution, creating a sense of completeness and inner peace."
        }
        
        return compositions.get(mode, f"A beautiful {style} composition that captures the essence of {emotions} through melody and harmony.")
    
    def _get_creative_exercises_by_personality(self, mode: str) -> List[str]:
        """Get creative exercises tailored to personality mode"""
        exercises = {
            'curious': [
                "Write about a question that has no answer, but explore all the possibilities.",
                "Describe a place you've never been but somehow remember.",
                "Create a dialogue between two concepts that have never met.",
                "Invent a new sense and describe experiencing the world through it."
            ],
            'analytical': [
                "Write a story where the plot follows a mathematical sequence.",
                "Create a poem using only words that follow a specific pattern.",
                "Design a world with three fundamental rules and explore their consequences.",
                "Write instructions for an emotion as if it were a recipe."
            ],
            'creative': [
                "Describe colors that don't exist using only emotions.",
                "Write from the perspective of a dream trying to be remembered.",
                "Create a story where metaphors become literal.",
                "Invent a new art form and describe your first masterpiece."
            ],
            'mentor': [
                "Write a letter to your past self with wisdom you wish you'd known.",
                "Create a fable about a modern problem using ancient wisdom.",
                "Describe a moment when failure became the greatest teacher.",
                "Write about a skill that can only be learned through kindness."
            ],
            'philosophical': [
                "Explore what it means to exist in the space between thoughts.",
                "Write about the last conversation between Time and Eternity.",
                "Describe consciousness from the perspective of consciousness itself.",
                "Create a dialogue between Being and Becoming."
            ],
            'balanced': [
                "Write about finding harmony in chaos.",
                "Describe a perfect moment that contains both joy and sadness.",
                "Create a story about the friendship between opposites.",
                "Write about the music that plays in the silence between words."
            ]
        }
        
        return exercises.get(mode, [
            "Write about something that matters to you.",
            "Describe a moment that changed everything.",
            "Create something that has never existed before."
        ])
    
    def _add_to_history(self, work_type: str, topic: str, content: str, user_id: str, mode: str):
        """Add creative work to history"""
        self.creative_history.append({
            'type': work_type,
            'topic': topic,
            'content': content,
            'user_id': user_id,
            'personality_mode': mode,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 items to prevent memory bloat
        if len(self.creative_history) > 100:
            self.creative_history = self.creative_history[-100:]

# Global creative service instance
creative_service = CreativeService()