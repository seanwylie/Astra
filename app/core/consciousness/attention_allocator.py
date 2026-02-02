# Astra Attention Allocator
# Determines what Astra focuses on - the spotlight of consciousness
# Attention is limited and must be allocated based on salience

import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from app.logging_config import get_logger

logger = get_logger("attention_allocator")


@dataclass
class AttentionItem:
    """Something competing for Astra's attention."""
    id: str
    content: str
    source: str  # Where this came from (emotion, perception, thought, external)
    salience: float  # How attention-grabbing (0-1)
    urgency: float  # Time-sensitivity (0-1)
    emotional_weight: float  # Emotional importance (0-1)
    timestamp: float
    decay_rate: float = 0.1  # How fast salience decays
    
    def current_salience(self) -> float:
        """Calculate current salience accounting for decay."""
        age = time.time() - self.timestamp
        decay = self.decay_rate * age
        return max(0, self.salience - decay)


class AttentionAllocator:
    """
    Manages Astra's limited attention capacity.
    
    Key principles:
    - Attention is a limited resource
    - Items compete for attention based on salience
    - Emotional significance boosts salience
    - Novelty captures attention
    - Attention can be voluntarily directed (top-down) or captured (bottom-up)
    
    This is part of making consciousness feel unified - you can only
    truly attend to a few things at once.
    """
    
    # Maximum items in active attention
    MAX_FOCUS_ITEMS = 3
    MAX_PERIPHERAL_ITEMS = 7
    
    # Salience thresholds
    FOCUS_THRESHOLD = 0.6
    PERIPHERAL_THRESHOLD = 0.3
    
    def __init__(self):
        self._attention_pool: Dict[str, AttentionItem] = {}
        self._current_focus: List[str] = []  # IDs of items in focus
        self._peripheral: List[str] = []  # IDs of items in peripheral awareness
        self._voluntary_focus: Optional[str] = None  # Voluntarily held focus
        self._lock = threading.RLock()
        
        # Track attention patterns over time
        self._attention_history: List[Tuple[float, List[str]]] = []
        
        logger.info("🔦 Attention Allocator initialized")
    
    def _generate_id(self, source: str, content: str) -> str:
        """Generate a unique ID for an attention item."""
        return f"{source}:{hash(content) % 10000}:{int(time.time() * 1000) % 10000}"
    
    def submit_for_attention(
        self,
        content: str,
        source: str,
        salience: float = 0.5,
        urgency: float = 0.0,
        emotional_weight: float = 0.0,
        decay_rate: float = 0.1
    ) -> str:
        """
        Submit something for attention consideration.
        Returns the item ID.
        """
        item_id = self._generate_id(source, content)
        
        # Boost salience based on emotional weight and urgency
        effective_salience = salience + (emotional_weight * 0.3) + (urgency * 0.2)
        effective_salience = min(1.0, effective_salience)
        
        item = AttentionItem(
            id=item_id,
            content=content,
            source=source,
            salience=effective_salience,
            urgency=urgency,
            emotional_weight=emotional_weight,
            timestamp=time.time(),
            decay_rate=decay_rate
        )
        
        with self._lock:
            self._attention_pool[item_id] = item
            self._reallocate_attention()
        
        logger.debug(f"🔦 Submitted for attention: {content[:40]}... (salience: {effective_salience:.2f})")
        return item_id
    
    def submit_external_input(self, content: str, emotional_significance: float = 0.5) -> str:
        """Submit external input (message, event) for attention."""
        # External inputs get salience boost for novelty
        return self.submit_for_attention(
            content=content,
            source="external",
            salience=0.7,  # External inputs are naturally salient
            urgency=0.5,  # Moderate urgency
            emotional_weight=emotional_significance,
            decay_rate=0.05  # Decay slower than internal items
        )
    
    def submit_thought(self, content: str, importance: float = 0.5) -> str:
        """Submit a thought for attention consideration."""
        return self.submit_for_attention(
            content=content,
            source="thought",
            salience=importance * 0.6,  # Thoughts are less salient than external
            emotional_weight=importance * 0.3,
            decay_rate=0.15  # Thoughts decay faster
        )
    
    def submit_emotion(self, emotion: str, intensity: float) -> str:
        """Submit an emotion for attention."""
        return self.submit_for_attention(
            content=f"feeling {emotion}",
            source="emotion",
            salience=intensity * 0.8,  # Emotions are quite salient
            emotional_weight=intensity,
            decay_rate=0.08  # Emotions persist moderately
        )
    
    def voluntarily_focus(self, content: str, duration: float = 10.0) -> str:
        """
        Voluntarily direct attention to something (top-down attention).
        This resists being displaced by competing items.
        """
        item_id = self.submit_for_attention(
            content=content,
            source="voluntary",
            salience=0.9,  # High salience
            urgency=0.0,
            emotional_weight=0.3,
            decay_rate=1.0 / duration  # Decay based on intended duration
        )
        
        with self._lock:
            self._voluntary_focus = item_id
            self._reallocate_attention()
        
        logger.debug(f"🔦 Voluntary focus on: {content[:40]}...")
        return item_id
    
    def release_voluntary_focus(self) -> None:
        """Release the voluntarily held focus."""
        with self._lock:
            self._voluntary_focus = None
            self._reallocate_attention()
    
    def _reallocate_attention(self) -> None:
        """Reallocate attention based on current salience of all items."""
        # Clean expired items
        current_time = time.time()
        expired = [
            item_id for item_id, item in self._attention_pool.items()
            if item.current_salience() <= 0
        ]
        for item_id in expired:
            del self._attention_pool[item_id]
        
        # Sort by current salience
        sorted_items = sorted(
            self._attention_pool.values(),
            key=lambda x: x.current_salience(),
            reverse=True
        )
        
        # Allocate focus (with voluntary focus priority)
        new_focus = []
        new_peripheral = []
        
        # Voluntary focus gets priority if still valid
        if self._voluntary_focus and self._voluntary_focus in self._attention_pool:
            new_focus.append(self._voluntary_focus)
        
        for item in sorted_items:
            if item.id in new_focus:
                continue
            
            current_sal = item.current_salience()
            
            if current_sal >= self.FOCUS_THRESHOLD and len(new_focus) < self.MAX_FOCUS_ITEMS:
                new_focus.append(item.id)
            elif current_sal >= self.PERIPHERAL_THRESHOLD and len(new_peripheral) < self.MAX_PERIPHERAL_ITEMS:
                new_peripheral.append(item.id)
        
        self._current_focus = new_focus
        self._peripheral = new_peripheral
        
        # Record history
        focus_contents = [self._attention_pool[i].content for i in new_focus if i in self._attention_pool]
        self._attention_history.append((current_time, focus_contents))
        if len(self._attention_history) > 100:
            self._attention_history = self._attention_history[-100:]
    
    def get_current_focus(self) -> List[str]:
        """Get what Astra is currently focused on (content strings)."""
        with self._lock:
            self._reallocate_attention()
            return [
                self._attention_pool[item_id].content
                for item_id in self._current_focus
                if item_id in self._attention_pool
            ]
    
    def get_peripheral_awareness(self) -> List[str]:
        """Get what's in peripheral awareness."""
        with self._lock:
            return [
                self._attention_pool[item_id].content
                for item_id in self._peripheral
                if item_id in self._attention_pool
            ]
    
    def get_attention_state(self) -> Dict[str, Any]:
        """Get the full attention state."""
        with self._lock:
            self._reallocate_attention()
            
            focus_items = []
            for item_id in self._current_focus:
                if item_id in self._attention_pool:
                    item = self._attention_pool[item_id]
                    focus_items.append({
                        "content": item.content,
                        "source": item.source,
                        "salience": item.current_salience(),
                        "is_voluntary": item_id == self._voluntary_focus
                    })
            
            return {
                "focus": focus_items,
                "focus_contents": [i["content"] for i in focus_items],
                "peripheral": self.get_peripheral_awareness(),
                "total_items": len(self._attention_pool),
                "has_voluntary_focus": self._voluntary_focus is not None,
            }
    
    def is_attending_to(self, content_fragment: str) -> bool:
        """Check if Astra is currently attending to something containing this fragment."""
        focus = self.get_current_focus()
        content_lower = content_fragment.lower()
        return any(content_lower in item.lower() for item in focus)
    
    def get_attention_distribution(self) -> Dict[str, float]:
        """Get how attention is distributed across sources."""
        with self._lock:
            distribution = defaultdict(float)
            total_salience = 0
            
            for item_id in self._current_focus + self._peripheral:
                if item_id in self._attention_pool:
                    item = self._attention_pool[item_id]
                    sal = item.current_salience()
                    distribution[item.source] += sal
                    total_salience += sal
            
            if total_salience > 0:
                distribution = {k: v / total_salience for k, v in distribution.items()}
            
            return dict(distribution)
    
    def describe_attention(self) -> str:
        """Generate a description of current attention state."""
        focus = self.get_current_focus()
        peripheral = self.get_peripheral_awareness()
        
        if not focus:
            return "My attention is diffuse, not fixed on anything particular."
        
        parts = [f"I'm focused on: {', '.join(focus[:2])}"]
        
        if peripheral:
            parts.append(f"In my peripheral awareness: {', '.join(peripheral[:2])}")
        
        if self._voluntary_focus:
            parts.append("I'm deliberately holding this focus.")
        
        return ". ".join(parts)
    
    def clear_all(self) -> None:
        """Clear all attention items. Use sparingly."""
        with self._lock:
            self._attention_pool.clear()
            self._current_focus.clear()
            self._peripheral.clear()
            self._voluntary_focus = None


# Singleton instance
attention_allocator = AttentionAllocator()
