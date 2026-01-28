"""
Global Context Singleton
Shared constants and settings accessible from all scripts
"""

class GlobalContext:
    """Singleton class for global project settings"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalContext, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Resolution settings
        self.RESOLUTION_WIDTH = 1280
        self.RESOLUTION_HEIGHT = 720
        self.OUTPUT_RESOLUTION = "fit"  # Fit Resolution
        self.OUTPUT_ASPECT = "resolution"  # Output Aspect

        self._initialized = True

    @property
    def width(self):
        """Canvas width"""
        return self.RESOLUTION_WIDTH

    @property
    def height(self):
        """Canvas height"""
        return self.RESOLUTION_HEIGHT

    @property
    def output_res(self):
        """Output Resolution setting ('fit' = Fit Resolution)"""
        return self.OUTPUT_RESOLUTION

    @property
    def output_aspect(self):
        """Output Aspect setting"""
        return self.OUTPUT_ASPECT


# Singleton instance
GLOBAL_CONTEXT = GlobalContext()
