"""
Edit History Manager for undo/redo operations.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from copy import deepcopy


class EditOperation:
    """Represents a single edit operation that can be undone/redone"""
    
    def __init__(self, op_type: str, data: Dict[str, Any]):
        self.op_type = op_type  # 'add', 'delete', 'edit', 'split', 'move'
        self.data = data  # Operation-specific data
        
    def __repr__(self):
        return f"EditOperation({self.op_type}, {self.data})"


class EditHistory(QObject):
    """
    Manages edit history for undo/redo functionality.
    """
    
    # Signals
    history_changed = Signal()  # Emitted when undo/redo state changes
    
    def __init__(self, max_history: int = 50):
        super().__init__()
        self.max_history = max_history
        self.undo_stack: List[EditOperation] = []
        self.redo_stack: List[EditOperation] = []
        
    def add_operation(self, op_type: str, data: Dict[str, Any]):
        """
        Add a new operation to history.
        Clears redo stack since branching from current state.
        """
        operation = EditOperation(op_type, deepcopy(data))
        self.undo_stack.append(operation)
        
        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
            
        # Clear redo stack (can't redo after new operation)
        self.redo_stack.clear()
        
        self.history_changed.emit()
        
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0
        
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0
        
    def undo(self) -> Optional[EditOperation]:
        """
        Undo the last operation.
        Returns the operation to be undone, or None if nothing to undo.
        """
        if not self.can_undo():
            return None
            
        operation = self.undo_stack.pop()
        self.redo_stack.append(operation)
        self.history_changed.emit()
        
        return operation
        
    def redo(self) -> Optional[EditOperation]:
        """
        Redo the last undone operation.
        Returns the operation to be redone, or None if nothing to redo.
        """
        if not self.can_redo():
            return None
            
        operation = self.redo_stack.pop()
        self.undo_stack.append(operation)
        self.history_changed.emit()
        
        return operation
        
    def clear(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.history_changed.emit()
