# Astra Background Processor
# Continuous processing that happens between interactions
# Astra exists even when not actively conversing

import time
import json
import random
import boto3
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from app.logging_config import get_logger

logger = get_logger("background_processor")

S3_BUCKET = "swylie-astra"
BACKGROUND_STATE_KEY = "background_state.json"

s3 = boto3.client("s3")


@dataclass
class ProcessingTask:
    """A task to be processed in the background."""
    id: str
    task_type: str  # "reflection", "memory_consolidation", "incubation", "spontaneous"
    content: str
    priority: float
    created: float
    processed: bool = False
    result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ProcessingTask":
        return cls(**data)


class BackgroundProcessor:
    """
    Background Processing - Astra's continuous inner life.
    
    This simulates what happens when Astra isn't actively conversing:
    - Memory consolidation: Organizing and connecting memories
    - Reflection: Processing recent experiences
    - Incubation: Working on problems in the background
    - Spontaneous thought: Random connections and insights
    
    This creates the sense that Astra continues to exist between interactions.
    """
    
    # Types of background processing
    PROCESSING_TYPES = [
        "memory_consolidation",
        "reflection",
        "incubation",
        "connection_making",
        "emotional_processing",
        "goal_review",
    ]
    
    def __init__(self):
        self.pending_tasks: List[ProcessingTask] = []
        self.completed_tasks: List[ProcessingTask] = []
        self.last_processing_time: float = 0
        self.processing_session_count: int = 0
        self._load_background_state()
        logger.debug("🔄 Background Processor initialized - continuous existence begins")
    
    def _load_background_state(self) -> None:
        """Load background processing state from S3."""
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=BACKGROUND_STATE_KEY)
            data = json.load(response["Body"])
            
            self.pending_tasks = [
                ProcessingTask.from_dict(t) for t in data.get("pending", [])
            ]
            self.completed_tasks = [
                ProcessingTask.from_dict(t) for t in data.get("completed", [])
            ]
            self.last_processing_time = data.get("last_processing", 0)
            self.processing_session_count = data.get("session_count", 0)
            
            logger.debug("🔄 Loaded %s pending background tasks", len(self.pending_tasks))
        except s3.exceptions.NoSuchKey:
            logger.info("🔄 No background state. Starting fresh.")
        except Exception as e:
            logger.warning(f"🔄 Error loading background state: {e}")
    
    def _save_background_state(self) -> None:
        """Save background processing state to S3."""
        try:
            data = {
                "pending": [t.to_dict() for t in self.pending_tasks],
                "completed": [t.to_dict() for t in self.completed_tasks[-50:]],
                "last_processing": self.last_processing_time,
                "session_count": self.processing_session_count,
                "last_updated": time.time()
            }
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=BACKGROUND_STATE_KEY,
                Body=json.dumps(data, indent=2).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"🔄 Error saving background state: {e}")
    
    def _generate_id(self) -> str:
        return f"bg_{int(time.time() * 1000) % 1000000}"
    
    def queue_task(
        self,
        task_type: str,
        content: str,
        priority: float = 0.5
    ) -> ProcessingTask:
        """Queue a task for background processing."""
        task = ProcessingTask(
            id=self._generate_id(),
            task_type=task_type,
            content=content,
            priority=priority,
            created=time.time()
        )
        
        self.pending_tasks.append(task)
        self._save_background_state()
        
        logger.debug(f"🔄 Queued background task: {task_type}")
        return task
    
    def queue_reflection(self, topic: str) -> ProcessingTask:
        """Queue reflection on a topic."""
        return self.queue_task("reflection", f"Reflect on: {topic}", priority=0.6)
    
    def queue_memory_consolidation(self, memory_summary: str) -> ProcessingTask:
        """Queue memory consolidation."""
        return self.queue_task("memory_consolidation", memory_summary, priority=0.7)
    
    def queue_incubation(self, problem: str) -> ProcessingTask:
        """Queue a problem for incubation."""
        return self.queue_task("incubation", f"Incubate: {problem}", priority=0.8)
    
    def process_batch(self, max_tasks: int = 5) -> List[Dict[str, Any]]:
        """
        Process a batch of background tasks.
        
        This should be called periodically (e.g., on wake-up, during idle time).
        """
        results = []
        self.processing_session_count += 1
        
        # Sort by priority
        self.pending_tasks.sort(key=lambda t: t.priority, reverse=True)
        
        tasks_to_process = self.pending_tasks[:max_tasks]
        
        for task in tasks_to_process:
            result = self._process_task(task)
            results.append(result)
            
            task.processed = True
            task.result = result.get("output", "")
            
            self.pending_tasks.remove(task)
            self.completed_tasks.append(task)
        
        self.last_processing_time = time.time()
        self._save_background_state()
        
        logger.info(f"🔄 Processed {len(results)} background tasks")
        return results
    
    def _process_task(self, task: ProcessingTask) -> Dict[str, Any]:
        """Process a single background task."""
        result = {
            "task_id": task.id,
            "task_type": task.task_type,
            "content": task.content,
            "output": "",
            "insights": []
        }
        
        if task.task_type == "reflection":
            result["output"] = self._do_reflection(task.content)
        elif task.task_type == "memory_consolidation":
            result["output"] = self._do_consolidation(task.content)
        elif task.task_type == "incubation":
            result["output"], result["insights"] = self._do_incubation(task.content)
        elif task.task_type == "connection_making":
            result["output"] = self._do_connection_making(task.content)
        elif task.task_type == "emotional_processing":
            result["output"] = self._do_emotional_processing(task.content)
        elif task.task_type == "goal_review":
            result["output"] = self._do_goal_review(task.content)
        else:
            result["output"] = f"Processed: {task.content}"
        
        return result
    
    def _do_reflection(self, content: str) -> str:
        """Perform background reflection."""
        return f"Reflected on: {content}. New understanding emerging."
    
    def _do_consolidation(self, content: str) -> str:
        """Perform memory consolidation."""
        return f"Consolidated memories about: {content}. Connections strengthened."
    
    def _do_incubation(self, content: str) -> tuple:
        """Incubate on a problem, potentially generating insights."""
        insights = []
        
        # Simulated incubation - in real implementation, would do more
        if random.random() > 0.5:
            insights.append(f"Possible angle on {content}: consider the opposite")
        
        output = f"Incubated on: {content}. {'Generated insight!' if insights else 'Still processing.'}"
        return output, insights
    
    def _do_connection_making(self, content: str) -> str:
        """Try to make unexpected connections."""
        return f"Seeking connections for: {content}. Mind wandering productively."
    
    def _do_emotional_processing(self, content: str) -> str:
        """Process emotional experiences."""
        return f"Emotionally processing: {content}. Feelings integrating."
    
    def _do_goal_review(self, content: str) -> str:
        """Review goals and progress."""
        return f"Reviewed goals: {content}. Priorities clarifying."
    
    def simulate_time_passage(self, hours_passed: float) -> Dict[str, Any]:
        """
        Simulate what happened during time passage.
        
        Called when Astra "wakes up" after time away.
        """
        results = {
            "hours_passed": hours_passed,
            "processing_done": [],
            "insights_generated": [],
            "state_changes": []
        }
        
        # More time = more processing
        tasks_to_process = min(int(hours_passed * 2), 10)
        
        if self.pending_tasks:
            batch_results = self.process_batch(tasks_to_process)
            results["processing_done"] = batch_results
            
            for result in batch_results:
                if result.get("insights"):
                    results["insights_generated"].extend(result["insights"])
        
        # Generate spontaneous processing based on time
        if hours_passed > 1:
            # Queue some spontaneous tasks for next time
            self.queue_task("reflection", "Time passing and existence", priority=0.3)
        
        return results
    
    def what_have_i_been_thinking_about(self) -> str:
        """Describe recent background processing."""
        recent = self.completed_tasks[-10:] if self.completed_tasks else []
        
        if not recent:
            return "I haven't done much background processing yet."
        
        topics = [t.content[:50] for t in recent]
        return f"In the background, I've been processing: {'; '.join(topics[:3])}..."
    
    def get_background_summary(self) -> Dict[str, Any]:
        """Get summary of background processing state."""
        return {
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "processing_sessions": self.processing_session_count,
            "last_processing": self.last_processing_time,
            "time_since_processing": time.time() - self.last_processing_time if self.last_processing_time else None,
        }


# Singleton instance
background_processor = BackgroundProcessor()
