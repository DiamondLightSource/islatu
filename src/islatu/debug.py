class Debug:
    def __init__(self, logging_level):
        self.logging_level = logging_level

    def log(self, log_string, unimportance: int = 1, **kwargs):
        """
        Prints to stdout if self.logging_level >= unimportance.

        Args:
            log_string:
                The string to be printed.
            unimportance:
                A measure of unimportance assigned to the printing of this
                string. Very unimportant messages require a larger logging
                level to be printed. Defaults to 1.
        """
        if self.logging_level >= unimportance:
            print(log_string, **kwargs)
