#!/usr/bin/env python3
"""
HCV PRO - Lanceur Package Autonome
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire bin au path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir / "bin"))

try:
    from harmonic_autonomous_package import main
    
    # Rediriger vers le package principal
    main()
    
except ImportError as e:
    print(f"❌ Erreur importation package : {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur exécution : {e}")
    sys.exit(1)
