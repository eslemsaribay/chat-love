# ============================================================================
# FIND RAW CAMERA FEED
# ============================================================================
# Run in TD textport:
#   exec(open(project.folder + '/explore_mediapipe.py').read())
# ============================================================================

print("=" * 70)
print("SEARCHING FOR RAW CAMERA / VIDEO INPUTS")
print("=" * 70)

# Find all Video Device In TOPs
print("\n[VIDEO DEVICE IN TOPs]")
print("-" * 50)
for t in root.findChildren(type=TOP, depth=5):
    if t.type == 'videodevicein':
        print(f"  {t.path}")

# Find all NDI In TOPs
print("\n[NDI IN TOPs]")
print("-" * 50)
for t in root.findChildren(type=TOP, depth=5):
    if t.type == 'ndiin':
        print(f"  {t.path}")

# Find what feeds INTO MediaPipe
print("\n[INPUTS TO MEDIAPIPE]")
print("-" * 50)
mp = op('/project1/MediaPipe')
if mp:
    for i, conn in enumerate(mp.inputConnectors):
        if conn.connections:
            for c in conn.connections:
                print(f"  Input {i}: {c.owner.path} ({c.owner.type})")
        else:
            print(f"  Input {i}: (not connected)")

# Find all TOPs with "cam" or "video" or "webcam" in name
print("\n[TOPs WITH 'cam/video/webcam' IN NAME]")
print("-" * 50)
for t in root.findChildren(type=TOP, depth=5):
    name = t.name.lower()
    if 'cam' in name or 'video' in name or 'webcam' in name:
        print(f"  {t.path} ({t.type})")

print("\n" + "=" * 70)
print("USE THE RAW CAMERA TOP (before MediaPipe) FOR COLOR VIDEO")
print("=" * 70)

# Old explore function (keep for reference)
MEDIAPIPE_PATH = '/project1/MediaPipe'

def explore_comp(path):
    comp = op(path)
    if comp is None:
        print(f"ERROR: Component not found at {path}")
        print("\nSearching for MediaPipe components...")
        for c in root.findChildren(type=COMP, depth=3):
            name = c.name.lower()
            if 'media' in name or 'pipe' in name or 'face' in name or 'landmark' in name:
                print(f"  Found: {c.path}")
        return

    print("=" * 70)
    print(f"COMPONENT: {comp.path}")
    print(f"Type: {comp.type}")
    print("=" * 70)

    # List all outputs (connectors)
    print(f"\n[OUTPUTS] ({len(comp.outputConnectors)} total)")
    print("-" * 50)
    for i, conn in enumerate(comp.outputConnectors):
        out_op = conn.connections[0] if conn.connections else None
        connected = f" -> {out_op.owner.path}" if out_op else ""
        print(f"  Output {i}: {conn.owner.name}{connected}")

    # List all TOPs inside
    print(f"\n[TOPs INSIDE]")
    print("-" * 50)
    for t in comp.findChildren(type=TOP, depth=1):
        info = f"{t.width}x{t.height}" if hasattr(t, 'width') else ""
        print(f"  {t.name} ({t.type}) {info}")

    # List all CHOPs inside
    print(f"\n[CHOPs INSIDE]")
    print("-" * 50)
    for c in comp.findChildren(type=CHOP, depth=1):
        chans = c.numChans if hasattr(c, 'numChans') else '?'
        print(f"  {c.name} ({c.type}) - {chans} channels")

    # List all DATs inside
    print(f"\n[DATs INSIDE]")
    print("-" * 50)
    for d in comp.findChildren(type=DAT, depth=1):
        print(f"  {d.name} ({d.type})")

    # List key parameters
    print(f"\n[CUSTOM PARAMETERS]")
    print("-" * 50)
    for page in comp.customPages:
        print(f"  Page: {page.name}")
        for par in page.pars:
            val = par.eval() if hasattr(par, 'eval') else par.val
            print(f"    {par.name} = {val}")

    # Look for segmentation-related ops
    print(f"\n[SEGMENTATION RELATED]")
    print("-" * 50)
    found = False
    for child in comp.findChildren(depth=2):
        name = child.name.lower()
        if 'seg' in name or 'mask' in name or 'alpha' in name:
            print(f"  {child.path} ({child.type})")
            found = True
    if not found:
        print("  None found")

    print("\n" + "=" * 70)
    print("TIP: Check the TOPs list above for segmentation/mask outputs")
    print("=" * 70)

# Run exploration
explore_comp(MEDIAPIPE_PATH)
