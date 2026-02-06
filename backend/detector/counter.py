from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PeopleCounter:
    def __init__(self, room_id: str, alpha: float = 0.3):
        """
        People counter with EMA smoothing.

        Args:
            room_id: Room identifier
            alpha: EMA smoothing factor (0-1, higher = more responsive)
        """
        self.room_id = room_id
        self.alpha = alpha
        self._smoothed_count: Optional[float] = None
        self._raw_count: int = 0

    def update(self, raw_count: int) -> int:
        """
        Update count with new detection.

        Returns:
            Smoothed count (rounded)
        """
        self._raw_count = raw_count

        if self._smoothed_count is None:
            self._smoothed_count = float(raw_count)
        else:
            # EMA: smoothed = alpha * current + (1 - alpha) * previous
            self._smoothed_count = (
                self.alpha * raw_count +
                (1 - self.alpha) * self._smoothed_count
            )

        return self.smoothed_count

    @property
    def smoothed_count(self) -> int:
        if self._smoothed_count is None:
            return 0
        return round(self._smoothed_count)

    @property
    def raw_count(self) -> int:
        return self._raw_count

    def set_alpha(self, alpha: float) -> None:
        self.alpha = max(0.0, min(1.0, alpha))
        logger.debug(f"Counter {self.room_id} alpha set to {self.alpha}")

    def reset(self) -> None:
        self._smoothed_count = None
        self._raw_count = 0
