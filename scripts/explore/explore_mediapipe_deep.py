# ============================================================================
# EXPLORE MEDIAPIPE - DEEP SEARCH
# ============================================================================
# Find the raw video feed INSIDE MediaPipe before segmentation
#
# Run in TD textport:
#   exec(open(project.folder + '/explore_mediapipe_deep.py').read())
# ============================================================================

MEDIAPIPE = '/project1/MediaPipe'

print("=" * 70)
print("DEEP SEARCH INSIDE MEDIAPIPE")
print("=" * 70)

mp = op(MEDIAPIPE)
if not mp:
    print("ERROR: MediaPipe not found")
else:
    # Find ALL TOPs inside MediaPipe (any depth)
    print("\n[ALL TOPs INSIDE MEDIAPIPE]")
    print("-" * 50)
    all_tops = mp.findChildren(type=TOP, depth=10)
    for t in all_tops:
        size = f"{t.width}x{t.height}" if hasattr(t, 'width') and t.width else "?"
        print(f"  {t.path} ({t.type}) {size}")

    # Find Video Device In TOPs inside
    print("\n[VIDEO DEVICE IN TOPs INSIDE]")
    print("-" * 50)
    found = False
    for t in all_tops:
        if t.type == 'videodevicein':
            print(f"  {t.path}")
            found = True
    if not found:
        print("  None found")

    # Find In TOPs (inputs from outside or internal feeds)
    print("\n[IN TOPs (potential video sources)]")
    print("-" * 50)
    for t in all_tops:
        if t.type == 'in':
            print(f"  {t.path}")

    # Find Null TOPs (often used as pass-through)
    print("\n[NULL TOPs (pass-through candidates)]")
    print("-" * 50)
    for t in all_tops:
        if t.type == 'null':
            print(f"  {t.path}")

    # Find what feeds into image_segmentation
    print("\n[INPUTS TO image_segmentation]")
    print("-" * 50)
    seg = op(MEDIAPIPE + '/image_segmentation')
    if seg:
        for i, conn in enumerate(seg.inputConnectors):
            if conn.connections:
                for c in conn.connections:
                    print(f"  Input {i}: {c.owner.path} ({c.owner.type})")
    else:
        print("  image_segmentation comp not found")

    # Look for websocket/webserver related TOPs (might stream video)
    print("\n[LOOKING FOR VIDEO STREAM SOURCE]")
    print("-" * 50)
    for t in all_tops:
        name = t.name.lower()
        if 'stream' in name or 'source' in name or 'input' in name or 'webcam' in name or 'capture' in name:
            print(f"  {t.path} ({t.type})")

    # Check face_tracking for video
    print("\n[TOPs IN face_tracking]")
    print("-" * 50)
    ft = op(MEDIAPIPE + '/face_tracking')
    if ft:
        for t in ft.findChildren(type=TOP, depth=3):
            size = f"{t.width}x{t.height}" if hasattr(t, 'width') and t.width else "?"
            print(f"  {t.path} ({t.type}) {size}")

print("\n" + "=" * 70)
print("Look for a TOP that has color video BEFORE it becomes the mask")
print("=" * 70)
