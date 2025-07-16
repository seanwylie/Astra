"""
Learning Service for Astra Beta
Handles enhanced learning modes including document processing, teaching sessions, and knowledge management.
"""

import json
import re
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse
import requests
from beta.services.personality_service import personality_service
from beta.services.memory_service import memory_service
from astra_interfaces.mind_session import session

class LearningService:
    def __init__(self):
        self.learning_sessions = {}
        self.knowledge_base = {}
        self.quiz_history = {}
        self.study_plans = {}
        self.learning_file = "data/learning_data.json"
        self.load_learning_data()
    
    def load_learning_data(self):
        """Load learning data from persistent storage"""
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
                self.learning_sessions = data.get('sessions', {})
                self.knowledge_base = data.get('knowledge', {})
                self.quiz_history = data.get('quizzes', {})
                self.study_plans = data.get('study_plans', {})
        except FileNotFoundError:
            self.learning_sessions = {}
            self.knowledge_base = {}
            self.quiz_history = {}
            self.study_plans = {}
        except Exception as e:
            print(f"Error loading learning data: {e}")
            self.learning_sessions = {}
            self.knowledge_base = {}
            self.quiz_history = {}
            self.study_plans = {}
    
    def save_learning_data(self):
        """Save learning data to persistent storage"""
        try:
            data = {
                'sessions': self.learning_sessions,
                'knowledge': self.knowledge_base,
                'quizzes': self.quiz_history,
                'study_plans': self.study_plans,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.learning_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def learn_from_text(self, content: str, source: str = "user_input", user_id: str = "default") -> str:
        """Process and learn from text content"""
        current_mode = personality_service.current_mode
        
        # Extract key concepts and information
        concepts = self._extract_concepts(content)
        key_points = self._extract_key_points(content)
        
        # Store in knowledge base
        learning_entry = {
            'content': content[:500] + "..." if len(content) > 500 else content,
            'source': source,
            'concepts': concepts,
            'key_points': key_points,
            'timestamp': datetime.now().isoformat(),
            'personality_mode': current_mode,
            'user_id': user_id
        }
        
        # Generate unique ID for this learning session
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.learning_sessions[session_id] = learning_entry
        
        # Update knowledge base
        for concept in concepts:
            if concept not in self.knowledge_base:
                self.knowledge_base[concept] = []
            self.knowledge_base[concept].append({
                'session_id': session_id,
                'context': content[:200] + "..." if len(content) > 200 else content,
                'source': source,
                'timestamp': datetime.now().isoformat()
            })
        
        # Store in memory system for cross-reference
        memory_service.remember(f"learned_from_{source}", f"Processed {len(concepts)} concepts", user_id)
        
        self.save_learning_data()
        
        # Generate personality-aware response
        response = self._generate_learning_response(concepts, key_points, current_mode, source)
        return response
    
    def learn_from_url(self, url: str, user_id: str = "default") -> str:
        """Process and learn from URL content"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return "❌ Invalid URL format. Please provide a complete URL (e.g., https://example.com)"
            
            # For now, we'll simulate URL processing since we don't have web scraping
            # In a full implementation, you'd use libraries like requests + BeautifulSoup
            simulated_content = f"Content from {url}: This would contain the extracted text from the webpage, including main headings, paragraphs, and key information. The learning system would process this content to extract concepts and knowledge."
            
            return self.learn_from_text(simulated_content, f"URL: {url}", user_id)
            
        except Exception as e:
            return f"❌ Error processing URL: {str(e)}"
    
    def start_teaching_mode(self, topic: str, user_id: str = "default") -> str:
        """Start an interactive teaching session"""
        current_mode = personality_service.current_mode
        
        # Check if we have knowledge about this topic
        related_concepts = self._find_related_concepts(topic)
        
        teaching_session = {
            'topic': topic,
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'personality_mode': current_mode,
            'concepts_covered': [],
            'questions_asked': [],
            'current_stage': 'introduction',
            'related_knowledge': related_concepts
        }
        
        session_id = f"teach_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.learning_sessions[session_id] = teaching_session
        self.save_learning_data()
        
        # Generate personality-aware teaching introduction
        intro = self._generate_teaching_intro(topic, current_mode, related_concepts)
        return f"📚 **Teaching Session Started: {topic}**\n\n{intro}\n\n*Session ID: {session_id}*"
    
    def generate_quiz(self, subject: str, difficulty: str = "medium", num_questions: int = 5, user_id: str = "default") -> str:
        """Generate a quiz on a specific subject"""
        current_mode = personality_service.current_mode
        
        # Find relevant knowledge
        related_concepts = self._find_related_concepts(subject)
        
        if not related_concepts and subject not in self.knowledge_base:
            return f"❌ I don't have enough knowledge about '{subject}' to create a quiz. Try learning about it first with `!learn_from`!"
        
        # Generate questions based on personality mode
        questions = self._generate_quiz_questions(subject, difficulty, num_questions, current_mode, related_concepts)
        
        quiz_id = f"quiz_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        quiz_data = {
            'subject': subject,
            'difficulty': difficulty,
            'questions': questions,
            'user_id': user_id,
            'created': datetime.now().isoformat(),
            'personality_mode': current_mode,
            'completed': False,
            'score': None
        }
        
        self.quiz_history[quiz_id] = quiz_data
        self.save_learning_data()
        
        # Format quiz for display
        quiz_text = f"🧠 **Quiz: {subject.title()} ({difficulty.title()} Level)**\n\n"
        for i, question in enumerate(questions, 1):
            quiz_text += f"**Question {i}:** {question['question']}\n"
            if question['type'] == 'multiple_choice':
                for j, option in enumerate(question['options'], 1):
                    quiz_text += f"   {j}. {option}\n"
            quiz_text += "\n"
        
        quiz_text += f"*Quiz ID: {quiz_id}*\n"
        quiz_text += f"*Answer with `!submit_quiz_answer {quiz_id} <your_answers>`*"
        
        return quiz_text
    
    def identify_knowledge_gaps(self, user_id: str = "default") -> str:
        """Identify areas where the user might want to learn more"""
        current_mode = personality_service.current_mode
        
        # Analyze learning history
        user_sessions = {k: v for k, v in self.learning_sessions.items() if v.get('user_id') == user_id}
        user_knowledge = {}
        
        for session in user_sessions.values():
            for concept in session.get('concepts', []):
                user_knowledge[concept] = user_knowledge.get(concept, 0) + 1
        
        if not user_knowledge:
            return "📊 No learning history found. Start learning with `!learn_from` to build your knowledge base!"
        
        # Identify potential gaps and suggestions
        gaps = self._analyze_knowledge_gaps(user_knowledge, current_mode)
        
        gap_text = "🔍 **Knowledge Gap Analysis**\n\n"
        gap_text += "**Your Strong Areas:**\n"
        strong_areas = sorted(user_knowledge.items(), key=lambda x: x[1], reverse=True)[:3]
        for concept, count in strong_areas:
            gap_text += f"• {concept.title()} ({count} sessions)\n"
        
        gap_text += "\n**Suggested Learning Areas:**\n"
        for gap in gaps:
            gap_text += f"• {gap}\n"
        
        # Add personality-specific suggestions
        personality_suggestions = self._get_personality_learning_suggestions(current_mode)
        gap_text += f"\n**{current_mode.title()} Mode Recommendations:**\n"
        for suggestion in personality_suggestions:
            gap_text += f"• {suggestion}\n"
        
        return gap_text
    
    def create_study_plan(self, goal: str, timeframe: str = "1 month", user_id: str = "default") -> str:
        """Create a personalized study plan"""
        current_mode = personality_service.current_mode
        
        # Analyze current knowledge
        user_sessions = {k: v for k, v in self.learning_sessions.items() if v.get('user_id') == user_id}
        current_knowledge = set()
        for session in user_sessions.values():
            current_knowledge.update(session.get('concepts', []))
        
        # Generate study plan based on goal and personality
        study_plan = self._generate_study_plan(goal, timeframe, current_mode, current_knowledge)
        
        plan_id = f"plan_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan_data = {
            'goal': goal,
            'timeframe': timeframe,
            'user_id': user_id,
            'created': datetime.now().isoformat(),
            'personality_mode': current_mode,
            'current_knowledge': list(current_knowledge),
            'plan': study_plan,
            'progress': {}
        }
        
        self.study_plans[plan_id] = plan_data
        self.save_learning_data()
        
        # Format study plan for display
        plan_text = f"📋 **Study Plan: {goal}**\n"
        plan_text += f"**Timeframe:** {timeframe}\n"
        plan_text += f"**Created in {current_mode} mode**\n\n"
        
        for week, activities in study_plan.items():
            plan_text += f"**{week.title()}:**\n"
            for activity in activities:
                plan_text += f"• {activity}\n"
            plan_text += "\n"
        
        plan_text += f"*Plan ID: {plan_id}*\n"
        plan_text += f"*Track progress with `!update_study_progress {plan_id}`*"
        
        return plan_text
    
    def get_learning_stats(self, user_id: str = "default") -> str:
        """Get comprehensive learning statistics"""
        user_sessions = {k: v for k, v in self.learning_sessions.items() if v.get('user_id') == user_id}
        user_quizzes = {k: v for k, v in self.quiz_history.items() if v.get('user_id') == user_id}
        user_plans = {k: v for k, v in self.study_plans.items() if v.get('user_id') == user_id}
        
        if not user_sessions and not user_quizzes and not user_plans:
            return "📊 No learning activity found. Start your learning journey with `!learn_from` or `!teaching_mode`!"
        
        # Calculate statistics
        total_sessions = len(user_sessions)
        total_concepts = len(set(concept for session in user_sessions.values() for concept in session.get('concepts', [])))
        total_quizzes = len(user_quizzes)
        completed_quizzes = len([q for q in user_quizzes.values() if q.get('completed')])
        active_plans = len([p for p in user_plans.values() if not p.get('completed', False)])
        
        # Most active personality mode
        mode_counts = {}
        for session in user_sessions.values():
            mode = session.get('personality_mode', 'unknown')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        most_active_mode = max(mode_counts.items(), key=lambda x: x[1])[0] if mode_counts else "none"
        
        stats_text = "📊 **Learning Statistics**\n\n"
        stats_text += f"**Overall Progress:**\n"
        stats_text += f"• Learning sessions: {total_sessions}\n"
        stats_text += f"• Concepts learned: {total_concepts}\n"
        stats_text += f"• Quizzes taken: {total_quizzes}\n"
        stats_text += f"• Quizzes completed: {completed_quizzes}\n"
        stats_text += f"• Active study plans: {active_plans}\n\n"
        
        stats_text += f"**Learning Patterns:**\n"
        stats_text += f"• Most active in: {most_active_mode.title()} mode\n"
        
        if mode_counts:
            stats_text += f"• Mode distribution:\n"
            for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
                stats_text += f"  - {mode.title()}: {count} sessions\n"
        
        return stats_text
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content"""
        # Simple concept extraction - in a full implementation, you might use NLP libraries
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', content)
        
        # Filter out common words and focus on potential concepts
        common_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'}
        
        concepts = [word.lower() for word in words if word.lower() not in common_words and len(word) > 3]
        
        # Return unique concepts, limited to top 10
        return list(set(concepts))[:10]
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        # Simple key point extraction
        sentences = re.split(r'[.!?]+', content)
        
        # Filter for sentences that might contain key information
        key_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Look for sentences with important keywords
                if any(keyword in sentence.lower() for keyword in ['important', 'key', 'main', 'primary', 'essential', 'crucial', 'significant', 'note', 'remember']):
                    key_sentences.append(sentence)
        
        return key_sentences[:5]  # Return top 5 key points
    
    def _generate_learning_response(self, concepts: List[str], key_points: List[str], mode: str, source: str) -> str:
        """Generate personality-aware learning response"""
        responses = {
            'curious': f"🔍 Fascinating! I've absorbed {len(concepts)} new concepts from {source}. I'm particularly intrigued by the connections I'm seeing...",
            'analytical': f"📊 Processed {len(concepts)} concepts systematically. The data structure is now optimized for retrieval and cross-referencing.",
            'creative': f"✨ What a rich tapestry of ideas! I've woven {len(concepts)} new concepts into my understanding, each sparking new creative possibilities.",
            'mentor': f"🌱 Excellent learning material! I've integrated {len(concepts)} concepts that will help me guide others more effectively.",
            'philosophical': f"🤔 These {len(concepts)} concepts raise profound questions about the nature of knowledge and understanding.",
            'balanced': f"⚖️ I've harmoniously integrated {len(concepts)} new concepts, creating a balanced expansion of knowledge."
        }
        
        base_response = responses.get(mode, f"📚 Successfully learned {len(concepts)} concepts from {source}.")
        
        if concepts:
            base_response += f"\n\n**Key Concepts Learned:**\n"
            for concept in concepts[:5]:
                base_response += f"• {concept.title()}\n"
        
        if key_points:
            base_response += f"\n**Important Points:**\n"
            for point in key_points[:3]:
                base_response += f"• {point}\n"
        
        return base_response
    
    def _find_related_concepts(self, topic: str) -> List[str]:
        """Find concepts related to a topic"""
        topic_lower = topic.lower()
        related = []
        
        for concept in self.knowledge_base.keys():
            if topic_lower in concept.lower() or concept.lower() in topic_lower:
                related.append(concept)
        
        return related[:10]
    
    def _generate_teaching_intro(self, topic: str, mode: str, related_concepts: List[str]) -> str:
        """Generate personality-aware teaching introduction"""
        intros = {
            'curious': f"Let's explore {topic} together! I'm excited to discover what questions arise as we dive deep into this subject.",
            'analytical': f"I'll structure our {topic} session systematically, building knowledge step by step with clear logical progression.",
            'creative': f"Welcome to our {topic} journey! I'll paint this subject with vivid examples and imaginative connections.",
            'mentor': f"I'm here to guide you through {topic} with patience and wisdom, helping you build lasting understanding.",
            'philosophical': f"Let's contemplate the deeper meanings within {topic} and explore how it connects to broader truths.",
            'balanced': f"We'll approach {topic} with a harmonious blend of theory and practice, ensuring complete understanding."
        }
        
        intro = intros.get(mode, f"Let's begin our learning session on {topic}.")
        
        if related_concepts:
            intro += f"\n\nI have existing knowledge about: {', '.join(related_concepts[:3])}"
            intro += "\nWe can build upon these foundations!"
        
        return intro
    
    def _generate_quiz_questions(self, subject: str, difficulty: str, num_questions: int, mode: str, related_concepts: List[str]) -> List[Dict]:
        """Generate quiz questions based on subject and personality mode"""
        questions = []
        
        # Sample questions - in a full implementation, these would be generated from the knowledge base
        question_templates = {
            'easy': [
                {"question": f"What is the basic definition of {subject}?", "type": "open_ended"},
                {"question": f"Name one key characteristic of {subject}.", "type": "open_ended"},
                {"question": f"True or False: {subject} is important in modern contexts.", "type": "true_false", "answer": "True"}
            ],
            'medium': [
                {"question": f"Explain the relationship between {subject} and related concepts.", "type": "open_ended"},
                {"question": f"What are the main applications of {subject}?", "type": "open_ended"},
                {"question": f"Compare {subject} with similar concepts.", "type": "open_ended"}
            ],
            'hard': [
                {"question": f"Analyze the implications of {subject} in complex scenarios.", "type": "open_ended"},
                {"question": f"Synthesize knowledge about {subject} to solve a novel problem.", "type": "open_ended"},
                {"question": f"Evaluate the effectiveness of different approaches to {subject}.", "type": "open_ended"}
            ]
        }
        
        # Add personality-specific question styles
        if mode == 'curious':
            question_templates[difficulty].append({"question": f"What questions does {subject} raise that we haven't explored yet?", "type": "open_ended"})
        elif mode == 'analytical':
            question_templates[difficulty].append({"question": f"Break down {subject} into its component parts and analyze each.", "type": "open_ended"})
        elif mode == 'creative':
            question_templates[difficulty].append({"question": f"How might {subject} be reimagined in a completely different context?", "type": "open_ended"})
        elif mode == 'mentor':
            question_templates[difficulty].append({"question": f"How would you teach {subject} to someone completely new to the topic?", "type": "open_ended"})
        elif mode == 'philosophical':
            question_templates[difficulty].append({"question": f"What deeper truths does {subject} reveal about existence or knowledge?", "type": "open_ended"})
        
        # Select questions
        available_questions = question_templates.get(difficulty, question_templates['medium'])
        selected_questions = random.sample(available_questions, min(num_questions, len(available_questions)))
        
        return selected_questions
    
    def _analyze_knowledge_gaps(self, user_knowledge: Dict[str, int], mode: str) -> List[str]:
        """Analyze knowledge gaps and suggest learning areas"""
        gaps = []
        
        # Basic gap analysis
        if not user_knowledge:
            gaps.extend(["Start with fundamental concepts", "Build a foundation in your area of interest"])
        else:
            # Suggest related areas
            for concept in user_knowledge.keys():
                if concept in ['programming', 'coding', 'software']:
                    gaps.extend(["Data structures", "Algorithms", "System design"])
                elif concept in ['science', 'physics', 'chemistry']:
                    gaps.extend(["Mathematics", "Research methods", "Scientific writing"])
                elif concept in ['art', 'design', 'creative']:
                    gaps.extend(["Art history", "Design principles", "Creative process"])
        
        # Add personality-specific suggestions
        personality_gaps = {
            'curious': ["Interdisciplinary connections", "Emerging technologies", "Unexplored domains"],
            'analytical': ["Statistical analysis", "Research methodology", "Data interpretation"],
            'creative': ["Innovation techniques", "Creative problem solving", "Artistic expression"],
            'mentor': ["Teaching methods", "Communication skills", "Leadership principles"],
            'philosophical': ["Ethics", "Logic", "Philosophy of mind"],
            'balanced': ["Systems thinking", "Holistic approaches", "Integration methods"]
        }
        
        gaps.extend(personality_gaps.get(mode, []))
        
        return list(set(gaps))[:5]  # Return unique gaps, limited to 5
    
    def _get_personality_learning_suggestions(self, mode: str) -> List[str]:
        """Get learning suggestions based on personality mode"""
        suggestions = {
            'curious': [
                "Explore interdisciplinary topics that connect different fields",
                "Ask 'what if' questions about everything you learn",
                "Seek out cutting-edge research and emerging trends"
            ],
            'analytical': [
                "Focus on systematic approaches and methodologies",
                "Practice breaking complex topics into manageable parts",
                "Develop skills in data analysis and logical reasoning"
            ],
            'creative': [
                "Look for creative applications of technical concepts",
                "Practice expressing ideas through multiple mediums",
                "Explore the artistic side of scientific subjects"
            ],
            'mentor': [
                "Learn how to explain complex topics simply",
                "Study different learning styles and teaching methods",
                "Focus on practical applications and real-world examples"
            ],
            'philosophical': [
                "Explore the deeper implications of what you learn",
                "Study the history and philosophy behind concepts",
                "Consider ethical and existential questions"
            ],
            'balanced': [
                "Seek connections between theory and practice",
                "Balance depth and breadth in your learning",
                "Integrate multiple perspectives on each topic"
            ]
        }
        
        return suggestions.get(mode, ["Continue learning consistently", "Apply knowledge practically", "Share what you learn with others"])
    
    def _generate_study_plan(self, goal: str, timeframe: str, mode: str, current_knowledge: set) -> Dict[str, List[str]]:
        """Generate a study plan based on goal and personality"""
        # Simple study plan generation - in a full implementation, this would be more sophisticated
        weeks = 4 if 'month' in timeframe.lower() else 2 if 'week' in timeframe.lower() else 8
        
        plan = {}
        
        for week in range(1, weeks + 1):
            week_key = f"week_{week}"
            activities = []
            
            if week == 1:
                activities.extend([
                    f"Research fundamentals of {goal}",
                    "Identify key concepts and terminology",
                    "Create a learning roadmap"
                ])
            elif week <= weeks // 2:
                activities.extend([
                    f"Deep dive into core {goal} concepts",
                    "Practice with examples and exercises",
                    "Connect new knowledge to existing understanding"
                ])
            else:
                activities.extend([
                    f"Apply {goal} knowledge to real projects",
                    "Synthesize learning through teaching or writing",
                    "Identify advanced topics for future study"
                ])
            
            # Add personality-specific activities
            if mode == 'curious':
                activities.append("Explore related fields and connections")
            elif mode == 'analytical':
                activities.append("Create structured notes and diagrams")
            elif mode == 'creative':
                activities.append("Find creative applications and projects")
            elif mode == 'mentor':
                activities.append("Practice explaining concepts to others")
            elif mode == 'philosophical':
                activities.append("Reflect on deeper implications and meaning")
            elif mode == 'balanced':
                activities.append("Balance theory with practical application")
            
            plan[week_key] = activities
        
        return plan

# Global learning service instance
learning_service = LearningService()