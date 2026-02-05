# Explore Zenna_body Mesh for Mouth Vertices
# ============================================
# Properly analyze the body mesh to find mouth region
#
# exec(open(project.folder + '/explore_body_mesh.py').read())

print("\n" + "=" * 70)
print("EXPLORING ZENNA_BODY MESH FOR MOUTH VERTICES")
print("=" * 70)

BODY_PATH = '/project1/luna_container/Luna/Zenna_body'

# ============================================================================
# 1. Check the geometry COMP structure
# ============================================================================

print("\n[1] CHECKING ZENNA_BODY STRUCTURE...")

container = op(BODY_PATH)
if container is None:
    print(f"ERROR: Container not found at {BODY_PATH}")
    raise SystemExit

print(f"  Container: {container.path}")
print(f"  Type: {type(container).__name__}")

# List all children
print(f"\n  Children:")
for child in container.children:
    inp_str = ""
    if hasattr(child, 'inputs') and child.inputs:
        inp_str = f" <- {[i.name for i in child.inputs]}"
    print(f"    {child.name} ({type(child).__name__}){inp_str}")

mesh = container.op('mesh')
deform = container.op('deform')
bonegroup = container.op('bonegroup')
null_out = container.op('null')

print(f"\n  mesh type: {type(mesh).__name__} (family: {mesh.family})" if mesh else "  mesh: NOT FOUND")
if deform:
    print(f"  deform type: {type(deform).__name__} (family: {deform.family})")
if bonegroup:
    print(f"  bonegroup type: {type(bonegroup).__name__} (family: {bonegroup.family})")
if null_out:
    print(f"  null type: {type(null_out).__name__} (family: {null_out.family})")

# Use bonegroup or deform as the deformation operator
deform_op = deform if deform else bonegroup
if deform_op:
    print(f"\n  Using '{deform_op.name}' as deformation operator")

# ============================================================================
# 2. Try to access geometry via In SOP
# ============================================================================

print("\n[2] TESTING IN SOP FOR GEOMETRY ACCESS...")

# Since mesh is already a SOP (importselectSOP), we can analyze it directly
# or use the final output (null) which has the fully deformed geometry
geo_source = null_out if null_out else (bonegroup if bonegroup else mesh)

print(f"  Using geometry source: {geo_source.path if geo_source else 'NONE'}")

if geo_source:
    geo_source.cook(force=True)
    try:
        num_points = geo_source.numPoints
        print(f"  Geometry has {num_points} points")
        if num_points > 0:
            print(f"  SUCCESS: Can access geometry directly (already SOPs)!")
    except Exception as e:
        print(f"  ERROR accessing points: {e}")
        geo_source = None

# ============================================================================
# 3. Analyze geometry bounds to find mouth region
# ============================================================================

print("\n[3] ANALYZING GEOMETRY BOUNDS...")

if geo_source and geo_source.numPoints > 0:
    # Collect all vertex positions
    x_vals, y_vals, z_vals = [], [], []

    print(f"  Scanning {geo_source.numPoints} vertices...")

    for pt in geo_source.points:
        pos = pt.P
        x_vals.append(pos[0])
        y_vals.append(pos[1])
        z_vals.append(pos[2])

    print(f"\n  Full body bounds:")
    print(f"    X: {min(x_vals):.3f} to {max(x_vals):.3f} (width: {max(x_vals)-min(x_vals):.3f})")
    print(f"    Y: {min(y_vals):.3f} to {max(y_vals):.3f} (height: {max(y_vals)-min(y_vals):.3f})")
    print(f"    Z: {min(z_vals):.3f} to {max(z_vals):.3f} (depth: {max(z_vals)-min(z_vals):.3f})")

    # The head/face should be at the top of the model (high Y)
    # Mouth is typically in the upper portion
    body_height = max(y_vals) - min(y_vals)
    head_y_min = max(y_vals) - body_height * 0.15  # Top 15% is likely head

    print(f"\n  Estimated head region: Y > {head_y_min:.3f}")

    # Count vertices in head region
    head_verts = []
    for pt in geo_source.points:
        if pt.P[1] > head_y_min:
            head_verts.append(pt.index)

    print(f"  Vertices in head region: {len(head_verts)}")

    # Analyze head region more specifically
    if head_verts:
        head_y = [geo_source.points[i].P[1] for i in head_verts]
        head_z = [geo_source.points[i].P[2] for i in head_verts]

        # Mouth is typically:
        # - In the middle-lower part of the head (not the very top)
        # - At the front of the face (high Z typically, or depends on model orientation)

        head_mid_y = (min(head_y) + max(head_y)) / 2

        print(f"\n  Head Y range: {min(head_y):.3f} to {max(head_y):.3f}")
        print(f"  Head Z range: {min(head_z):.3f} to {max(head_z):.3f}")
        print(f"  Head center Y: {head_mid_y:.3f}")

        # Sample vertices around mouth area (middle of head height, front)
        z_front = max(head_z) - (max(head_z) - min(head_z)) * 0.3

        mouth_candidates = []
        for i in head_verts:
            pt = geo_source.points[i]
            y, z = pt.P[1], pt.P[2]
            # Mouth region: roughly middle third of head height, front of face
            if abs(y - head_mid_y) < (max(head_y) - min(head_y)) * 0.2 and z > z_front:
                mouth_candidates.append(i)

        print(f"\n  Potential mouth vertices: {len(mouth_candidates)}")

        if mouth_candidates:
            # Show sample vertices
            print(f"  Sample mouth vertex positions:")
            for i in mouth_candidates[:10]:
                pt = geo_source.points[i]
                print(f"    Vertex {i}: ({pt.P[0]:.3f}, {pt.P[1]:.3f}, {pt.P[2]:.3f})")

            # Get Y bounds of mouth candidates
            mouth_y = [geo_source.points[i].P[1] for i in mouth_candidates]
            mouth_z = [geo_source.points[i].P[2] for i in mouth_candidates]

            print(f"\n  Mouth region bounds:")
            print(f"    Y: {min(mouth_y):.3f} to {max(mouth_y):.3f}")
            print(f"    Z: {min(mouth_z):.3f} to {max(mouth_z):.3f}")

            # Calculate suggested MOUTH_REGION values
            mouth_y_margin = (max(mouth_y) - min(mouth_y)) * 0.1
            print(f"\n  SUGGESTED CONFIGURATION:")
            print(f"    MOUTH_Y_MIN = {min(mouth_y) - mouth_y_margin:.3f}")
            print(f"    MOUTH_Y_MAX = {max(mouth_y) + mouth_y_margin:.3f}")
            print(f"    MOUTH_Z_MIN = {min(mouth_z):.3f}")
            print(f"    MOUTH_Z_MAX = {max(mouth_z):.3f}")
            print(f"    LIP_BOUNDARY_Y = {(min(mouth_y) + max(mouth_y)) / 2:.3f}")
else:
    print("  Cannot analyze - no geometry available")

# ============================================================================
# 4. Summary
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if geo_source and geo_source.numPoints > 0:
    print(f"""
GOOD NEWS: Zenna_body uses SOPs, not POPs!
This means we CAN apply Script SOP deformation directly.

Current chain:
  mesh (importselectSOP) -> bonegroup (bonegroupSOP) -> null (nullSOP)

To add mouth deformation, insert Script SOP after bonegroup:
  mesh -> bonegroup -> face_deform (Script SOP) -> null

Next steps:
1. Create setup_body_mouth.py with correct path: '{BODY_PATH}'
2. Use the suggested MOUTH_REGION values above
3. Insert Script SOP between bonegroup and null
""")
else:
    print(f"""
ISSUE: Could not access geometry.
Check that the mesh and bonegroup operators exist and are cooking.
""")

print("\n" + "=" * 70 + "\n")
