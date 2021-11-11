"""
This module defines the Region object, whose instances define regions of
interest in images.
"""


class Region:
    """
    Instances of this class define regions of interest.
    """

    def __init__(self, x_start, x_end, y_start, y_end):
        self.x_start = x_start
        self.x_end = x_end
        self.y_start = y_start
        self.y_end = y_end

    @property
    def x_length(self):
        """
        Returns the length of the region in the x-direction.
        """
        return self.x_start - self.x_end

    @property
    def y_length(self):
        """
        Returns the length of the region in the y-direction.
        """
        return self.y_start - self.y_end
