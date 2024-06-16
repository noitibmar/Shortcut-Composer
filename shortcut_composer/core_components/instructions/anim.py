from api_krita import Krita
from ..instruction_base import Instruction

class RollPlayAnim(Instruction):
    """
    Play/Pause animation on a short release
    Jump to current keyframe on long release
    ### Example usage:
    ```python
    instructions.RollPlayAnim()
    ```
    """

    def on_short_key_release(self) -> None:
        """Play or Pause animation on a short press"""
        Krita.trigger_action("toggle_playback")

    def on_long_key_release(self) -> None:
        """Jump to current key frame"""
        self.active_document = Krita.get_active_document()
        self.active_node = self.active_document.active_node
        if not self.active_node.is_animated:
            return
        curtime = self.active_document.current_time
        if not self.active_node.node.hasKeyframeAtTime(curtime):
            Krita.trigger_action("previous_keyframe")


__all__ = ["RollPlayAnim"]
