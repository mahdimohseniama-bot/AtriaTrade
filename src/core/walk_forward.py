from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence

@dataclass
class WindowSplit:
    train_start: int
    train_end: int
    test_start: int
    test_end: int

class WalkForwardValidator:
    """
    Splits historical datasets into rolling In-Sample (Train) 
    and Out-of-Sample (Test) windows to prevent overfitting (Pure Python).
    """
    def __init__(self, train_size: int, test_size: int, step_size: int = None):
        if train_size <= 0 or test_size <= 0:
            raise ValueError("train_size and test_size must be positive integers")
        
        self.train_size = int(train_size)
        self.test_size = int(test_size)
        self.step_size = int(step_size) if step_size is not None else self.test_size
        
        if self.step_size <= 0:
            raise ValueError("step_size must be a positive integer")

    def generate_splits(self, total_records: int) -> List[WindowSplit]:
        if total_records < (self.train_size + self.test_size):
            return []
        
        splits = []
        start = 0
        while start + self.train_size + self.test_size <= total_records:
            train_start = start
            train_end = start + self.train_size
            test_start = train_end
            test_end = test_start + self.test_size
            
            splits.append(WindowSplit(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            ))
            start += self.step_size
            
        return splits

    def split_data(self, data: Sequence[Any]) -> List[Tuple[Sequence[Any], Sequence[Any]]]:
        """
        Returns pairs of (train_slice, test_slice) for any sequence (list, tuple, etc.).
        """
        splits = self.generate_splits(len(data))
        slices = []
        for s in splits:
            train_slice = data[s.train_start:s.train_end]
            test_slice = data[s.test_start:s.test_end]
            slices.append((train_slice, test_slice))
        return slices

    def calculate_walk_forward_efficiency(self, in_sample_returns: float, out_of_sample_returns: float) -> float:
        """
        Walk-Forward Efficiency (WFE) = OOS_Return / IS_Return
        WFE >= 0.50 (50%) indicates a robust, non-overfitted strategy.
        """
        if in_sample_returns == 0:
            return 0.0 if out_of_sample_returns <= 0 else 1.0
        return float(out_of_sample_returns / in_sample_returns)
