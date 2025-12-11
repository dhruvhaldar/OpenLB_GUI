import os
import tarfile
import shutil
from pathlib import Path

def setup_olb(project_root: Path):
    olb_dir = project_root / "olb-release"
    tar_path = project_root / "release-1.8.1.tar.gz"

    if olb_dir.exists():
        print(f"OpenLB directory found at {olb_dir}")
        return

    if not tar_path.exists():
        print(f"OpenLB tarball not found at {tar_path}. Cannot set up OpenLB.")
        return

    print(f"Extracting OpenLB from {tar_path}...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=project_root)

        # The tarball extracts to "release-1.8.1"
        extracted_dir = project_root / "release-1.8.1"
        if extracted_dir.exists():
            print(f"Renaming {extracted_dir} to {olb_dir}...")
            extracted_dir.rename(olb_dir)
        else:
            # Check if it extracted directly to olb-release (unlikely unless I repacked it)
            # Or maybe the tarball structure is different?
            # Based on my experience, it extracts to release-1.8.1
            print(f"Warning: Expected extraction directory {extracted_dir} not found.")

        print("OpenLB setup complete.")
    except Exception as e:
        print(f"Error setting up OpenLB: {e}")

if __name__ == "__main__":
    # For testing
    root = Path(__file__).resolve().parent.parent.parent
    setup_olb(root)
