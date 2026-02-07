# ============================================================================
# EXPLORE ALL MEDIAPIPE OUTPUTS
# ============================================================================
# Run in TD textport:
#   exec(open(project.folder + '/explore_outputs.py').read())
# ============================================================================

print("=" * 70)
print("MEDIAPIPE OUTPUTS - DETAILED")
print("=" * 70)

mp = op('/project1/MediaPipe')

# Check each output connector
print("\n[ALL 9 OUTPUTS]")
print("-" * 50)
for i in range(9):
    conn = mp.outputConnectors[i]
    # Find what internal operator feeds this output
    print(f"\nOutput {i}:")

    # Get connected external operators
    if conn.connections:
        for c in conn.connections:
            print(f"  -> External: {c.owner.path}")
    else:
        print(f"  -> External: (not connected)")

# Trace the webBrowser1 - this is where video comes from
print("\n" + "=" * 70)
print("EXPLORING webBrowser1")
print("=" * 70)

wb = op('/project1/MediaPipe/webBrowser1')
if wb:
    print(f"\nType: {wb.type}")
    print(f"\n[Children of webBrowser1]:")
    for child in wb.children:
        print(f"  {child.name} ({child.type})")

    print(f"\n[Output connectors]:")
    for i, conn in enumerate(wb.outputConnectors):
        if conn.connections:
            for c in conn.connections:
                print(f"  Output {i} -> {c.owner.path}")

# Check what feeds into switch1 (this switches between video sources)
print("\n" + "=" * 70)
print("SWITCH1 INPUTS (video source selector)")
print("=" * 70)
sw = op('/project1/MediaPipe/switch1')
if sw:
    print(f"Current index: {sw.par.index.eval()}")
    for i, conn in enumerate(sw.inputConnectors):
        if conn.connections:
            for c in conn.connections:
                src = c.owner
                print(f"  Input {i}: {src.path} ({src.type})")
                # Check size
                if hasattr(src, 'width'):
                    print(f"           Size: {src.width}x{src.height}")

# Explore what's inside webBrowser1 deeper
print("\n" + "=" * 70)
print("INSIDE webBrowser1")
print("=" * 70)
if wb:
    for child in wb.children:
        if isinstance(child, TOP):
            size = f"{child.width}x{child.height}" if child.width else "?"
            print(f"  TOP: {child.name} ({child.type}) {size}")
        elif isinstance(child, COMP):
            print(f"  COMP: {child.name} ({child.type})")
            # Look inside
            for subchild in child.children:
                if isinstance(subchild, TOP):
                    print(f"    -> {subchild.name} ({subchild.type})")
