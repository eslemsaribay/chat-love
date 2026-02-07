# ============================================================================
# EXPLORE MEDIAPIPE - DIRECT ACCESS
# ============================================================================
# Run in TD textport:
#   exec(open(project.folder + '/explore_mediapipe_direct.py').read())
# ============================================================================

print("=" * 70)
print("DIRECT EXPLORATION OF MEDIAPIPE")
print("=" * 70)

# List all direct children of MediaPipe
mp = op('/project1/MediaPipe')
print("\n[DIRECT CHILDREN OF /project1/MediaPipe]")
print("-" * 50)
for child in mp.children:
    print(f"  {child.name} ({child.type}) - {type(child).__name__}")

# Explore image_segmentation
print("\n[CHILDREN OF /project1/MediaPipe/image_segmentation]")
print("-" * 50)
seg = op('/project1/MediaPipe/image_segmentation')
if seg:
    for child in seg.children:
        print(f"  {child.name} ({child.type})")
else:
    print("  NOT FOUND")

# Explore face_tracking
print("\n[CHILDREN OF /project1/MediaPipe/face_tracking]")
print("-" * 50)
ft = op('/project1/MediaPipe/face_tracking')
if ft:
    for child in ft.children:
        print(f"  {child.name} ({child.type})")
else:
    print("  NOT FOUND")

# Check the 'video' OUT TOP - what feeds it?
print("\n[TRACING 'video' OUT TOP]")
print("-" * 50)
video_out = op('/project1/MediaPipe/video')
if video_out:
    print(f"  video OUT: {video_out.path}")
    # Check its inputs
    for i, conn in enumerate(video_out.inputConnectors):
        if conn.connections:
            for c in conn.connections:
                src = c.owner
                print(f"    <- Input {i}: {src.path} ({src.type})")
                # Go one level deeper
                if hasattr(src, 'inputConnectors'):
                    for j, conn2 in enumerate(src.inputConnectors):
                        if conn2.connections:
                            for c2 in conn2.connections:
                                print(f"       <- {c2.owner.path} ({c2.owner.type})")

# Check the switch1 - this might switch between video and mask
print("\n[CHECKING switch1]")
print("-" * 50)
sw = op('/project1/MediaPipe/switch1')
if sw:
    print(f"  switch1 index: {sw.par.index.eval()}")
    for i, conn in enumerate(sw.inputConnectors):
        if conn.connections:
            for c in conn.connections:
                print(f"    Input {i}: {c.owner.path} ({c.owner.type})")

# Check all Out TOPs at top level
print("\n[ALL OUT TOPs IN MEDIAPIPE (potential outputs)]")
print("-" * 50)
for child in mp.children:
    if child.type == 'out' and isinstance(child, TOP):
        print(f"  {child.name}")
        for i, conn in enumerate(child.inputConnectors):
            if conn.connections:
                for c in conn.connections:
                    print(f"    <- {c.owner.path}")

print("\n" + "=" * 70)
