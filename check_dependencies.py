#!/usr/bin/env python3
"""
Check which dependencies are installed and which are missing.
"""

import sys

def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def main():
    print("=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    print(f"Python: {sys.version}\n")
    
    # List of packages to check
    packages = [
        ('torch', 'torch'),
        ('opencv-python', 'cv2'),
        ('numpy', 'numpy'),
        ('joblib', 'joblib'),
        ('Pillow', 'PIL'),
        ('transformers', 'transformers'),
        ('ultralytics', 'ultralytics'),
        ('scikit-learn', 'sklearn'),
        ('protobuf', 'google.protobuf'),
        ('hypothesis', 'hypothesis'),
        ('pytest', 'pytest'),
        ('pytest-cov', 'pytest_cov'),
        ('pyyaml', 'yaml'),
        ('matplotlib', 'matplotlib'),
    ]
    
    installed = []
    missing = []
    
    print("Checking packages...\n")
    
    for package_name, import_name in packages:
        if check_package(package_name, import_name):
            print(f"✓ {package_name}")
            installed.append(package_name)
        else:
            print(f"✗ {package_name} (MISSING)")
            missing.append(package_name)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Installed: {len(installed)}/{len(packages)}")
    print(f"Missing: {len(missing)}/{len(packages)}")
    
    if missing:
        print("\n" + "=" * 60)
        print("MISSING PACKAGES")
        print("=" * 60)
        for pkg in missing:
            print(f"  - {pkg}")
        
        print("\n" + "=" * 60)
        print("INSTALLATION COMMAND")
        print("=" * 60)
        print("\nTo install all missing packages, run:")
        print(f"\npip install {' '.join(missing)}")
        
        print("\nOr install all requirements:")
        print("\npip install -r requirements.txt")
        
        print("\n" + "=" * 60)
        print("NOTE: PyTorch Installation")
        print("=" * 60)
        print("\nFor GPU support (CUDA), install PyTorch separately:")
        print("\nCUDA 11.8:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print("\nCUDA 12.1:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        print("\nCPU only:")
        print("pip install torch torchvision torchaudio")
        
        return 1
    else:
        print("\n✅ All dependencies are installed!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
