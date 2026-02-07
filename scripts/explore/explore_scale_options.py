# Explore Scale Options
# =====================
# Find what we can scale to resize the Luna model
#
# exec(open(project.folder + '/explore_scale_options.py').read())

print("\n" + "=" * 70)
print("EXPLORE SCALE OPTIONS")
print("=" * 70)

LUNA_CONTAINER = '/project1/luna_container'
LUNA_PATH = '/project1/luna_container/Luna'

# =============================================================================
# 1. Check luna_container type and parameters
# =============================================================================

print("\n[1] LUNA_CONTAINER")
print("-" * 50)

container = op(LUNA_CONTAINER)
if container:
    print(f"  Path: {container.path}")
    print(f"  Type: {type(container).__name__}")
    print(f"  Family: {container.family}")

    # Check for transform parameters
    has_transform = hasattr(container.par, 'tx')
    print(f"  Has transform params (tx): {has_transform}")

    if has_transform:
        print(f"  tx: {container.par.tx.eval()}")
        print(f"  ty: {container.par.ty.eval()}")
        print(f"  tz: {container.par.tz.eval()}")
        print(f"  sx: {container.par.sx.eval()}")
        print(f"  sy: {container.par.sy.eval()}")
        print(f"  sz: {container.par.sz.eval()}")

# =============================================================================
# 2. Check Luna FBX COMP
# =============================================================================

print("\n[2] LUNA FBX COMP")
print("-" * 50)

luna = op(LUNA_PATH)
if luna:
    print(f"  Path: {luna.path}")
    print(f"  Type: {type(luna).__name__}")
    print(f"  Family: {luna.family}")

    # Check for transform parameters
    has_transform = hasattr(luna.par, 'tx')
    print(f"  Has transform params (tx): {has_transform}")

    if has_transform:
        print(f"\n  Current transform:")
        print(f"    tx: {luna.par.tx.eval()}")
        print(f"    ty: {luna.par.ty.eval()}")
        print(f"    tz: {luna.par.tz.eval()}")
        print(f"    sx: {luna.par.sx.eval()}")
        print(f"    sy: {luna.par.sy.eval()}")
        print(f"    sz: {luna.par.sz.eval()}")

        print(f"\n  To scale Luna model:")
        print(f"    op('{LUNA_PATH}').par.sx = 1.5")
        print(f"    op('{LUNA_PATH}').par.sy = 1.5")
        print(f"    op('{LUNA_PATH}').par.sz = 1.5")

# =============================================================================
# 3. Check for camera
# =============================================================================

print("\n[3] CAMERA OPTIONS")
print("-" * 50)

# Search for cameras
cameras = []
def find_cameras(parent_path):
    parent = op(parent_path)
    if parent:
        for child in parent.children:
            if 'Camera' in type(child).__name__ or 'cam' in child.name.lower():
                cameras.append(child)
            # Check children of COMPs
            if hasattr(child, 'children'):
                for grandchild in child.children:
                    if 'Camera' in type(grandchild).__name__ or 'cam' in grandchild.name.lower():
                        cameras.append(grandchild)

find_cameras('/project1')
find_cameras(LUNA_CONTAINER)

if cameras:
    print(f"  Found {len(cameras)} camera(s):")
    for cam in cameras:
        print(f"\n    {cam.path} ({type(cam).__name__})")
        if hasattr(cam.par, 'tz'):
            print(f"      Position: tx={cam.par.tx.eval():.3f}, ty={cam.par.ty.eval():.3f}, tz={cam.par.tz.eval():.3f}")
        if hasattr(cam.par, 'fov'):
            print(f"      FOV: {cam.par.fov.eval()}")
else:
    print(f"  No cameras found in /project1 or luna_container")

# =============================================================================
# 4. Check render setup
# =============================================================================

print("\n[4] RENDER SETUP")
print("-" * 50)

# Look for render TOPs
render_tops = []
project = op('/project1')
if project:
    for child in project.children:
        if 'Render' in type(child).__name__ or 'render' in child.name.lower():
            render_tops.append(child)

if render_tops:
    print(f"  Found {len(render_tops)} render TOP(s):")
    for r in render_tops:
        print(f"    {r.path} ({type(r).__name__})")
        if hasattr(r.par, 'camera'):
            print(f"      Camera param: {r.par.camera.eval()}")
        if hasattr(r, 'width'):
            print(f"      Resolution: {r.width} x {r.height}")
else:
    print(f"  No render TOPs found")

# =============================================================================
# 5. Summary
# =============================================================================

print("\n" + "=" * 70)
print("SCALE OPTIONS")
print("=" * 70)

if luna and hasattr(luna.par, 'sx'):
    print(f"""
OPTION 1: Scale the Luna FBX COMP directly
  luna = op('{LUNA_PATH}')
  luna.par.sx = 1.5  # Adjust this value
  luna.par.sy = 1.5
  luna.par.sz = 1.5
""")

if cameras:
    cam = cameras[0]
    print(f"""
OPTION 2: Adjust camera distance
  cam = op('{cam.path}')
  cam.par.tz = 5.0  # Move camera back (larger) or forward (smaller)
""")

print("""
OPTION 3: Create a Transform TOP to scale the rendered output
  (Scale the 2D image after rendering)
""")

print("=" * 70 + "\n")
