"""
SalesBud - Allow running as python -m salesbud
"""

# Suppress urllib3/requests version mismatch warnings before any imports
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings("ignore", message=".*charset_normalizer.*", category=UserWarning)

from salesbud.cli.main import main

if __name__ == "__main__":
    main()
