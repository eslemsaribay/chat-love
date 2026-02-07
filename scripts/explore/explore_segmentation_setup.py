# ============================================================================
# EXPLORE NEW IMAGE_SEGMENTATION COMP + MEDIAPIPE OUTPUTS
# ============================================================================
# Run in TD textport:
#   exec(open(project.folder + '/explore_segmentation_setup.py').read())
# ============================================================================

print("=" * 70)
print("NEW IMAGE_SEGMENTATION COMPONENT")
print("=" * 70)

seg = op('/project1/image_segmentation')
if seg:
    print(f"\nPath: {seg.path}")
    print(f"Type: {seg.type}")

    print("\n[INPUT CONNECTORS]")
    print("-" * 50)
    for i, conn in enumerate(seg.inputConnectors):
        # Try to find the IN TOP name
        print(f"  Input {i}:")
        if conn.connections:
            for c in conn.connections:
                print(f"    Connected from: {c.owner.path}")
        else:
            print(f"    (not connected)")

    print("\n[IN TOPs INSIDE (input names)]")
    print("-" * 50)
    for child in seg.children:
        if child.type == 'in':
            print(f"  {child.name} (index: {child.par.index if hasattr(child.par, 'index') else '?'})")

    print("\n[OUTPUT CONNECTORS]")
    print("-" * 50)
    for i, conn in enumerate(seg.outputConnectors):
        print(f"  Output {i}")

    print("\n[OUT TOPs INSIDE (output names)]")
    print("-" * 50)
    for child in seg.children:
        if child.type == 'out' and isinstance(child, TOP):
            print(f"  {child.name}")

    print("\n[ALL CHILDREN]")
    print("-" * 50)
    for child in seg.children:
        print(f"  {child.name} ({child.type})")
else:
    print("ERROR: /project1/image_segmentation not found")

# Now explore MediaPipe outputs in detail
print("\n" + "=" * 70)
print("MEDIAPIPE OUTPUTS - WHAT EACH ONE PROVIDES")
print("=" * 70)

mp = op('/project1/MediaPipe')
if mp:
    # List all OUT operators inside MediaPipe (these become the outputs)
    print("\n[OUT TOPs in MediaPipe (become external outputs)]")
    print("-" * 50)
    out_tops = []
    for child in mp.children:
        if child.type == 'out' and isinstance(child, TOP):
            out_tops.append(child)
            # Check what feeds into this OUT
            print(f"\n  {child.name}:")
            for conn in child.inputConnectors:
                if conn.connections:
                    for c in conn.connections:
                        print(f"    <- {c.owner.path} ({c.owner.type})")

    print("\n[OUT DATs in MediaPipe]")
    print("-" * 50)
    for child in mp.children:
        if child.type == 'out' and isinstance(child, DAT):
            print(f"  {child.name}")

    print("\n[OUT CHOPs in MediaPipe]")
    print("-" * 50)
    for child in mp.children:
        if child.type == 'out' and isinstance(child, CHOP):
            print(f"  {child.name}")

# Check what the face_tracking outputs
print("\n" + "=" * 70)
print("FACE_TRACKING OUTPUTS (might have video)")
print("=" * 70)
ft = op('/project1/MediaPipe/face_tracking')
if ft:
    print("\n[OUT TOPs in face_tracking]")
    for child in ft.children:
        if child.type == 'out' and isinstance(child, TOP):
            print(f"  {child.name}")
            for conn in child.inputConnectors:
                if conn.connections:
                    for c in conn.connections:
                        print(f"    <- {c.owner.path}")

# Check webBrowser1 outputs
print("\n" + "=" * 70)
print("webBrowser1 OUTPUTS")
print("=" * 70)
wb = op('/project1/MediaPipe/webBrowser1')
if wb:
    print(f"\n[Output connectors from webBrowser1]")
    for i, conn in enumerate(wb.outputConnectors):
        print(f"  Output {i}:")
        if conn.connections:
            for c in conn.connections:
                print(f"    -> {c.owner.path}")

    # Check for OUT TOPs inside
    print(f"\n[OUT TOPs inside webBrowser1]")
    for child in wb.children:
        if child.type == 'out' and isinstance(child, TOP):
            print(f"  {child.name}")

print("\n" + "=" * 70)
print("SUMMARY: What you likely need to connect:")
print("-" * 50)
print("  original_video  <- MediaPipe video output (with segmentation OFF)")
print("  segmentation_mask <- MediaPipe video output (with segmentation ON)")
print("  background <- optional custom background")
print("=" * 70)
