# Debug Mouth Deformation Setup
# ==============================
# Run this to diagnose why mouth deformation isn't working
#
# exec(open(project.folder + '/debug_mouth_deform.py').read())

print("\n" + "=" * 70)
print("MOUTH DEFORMATION DIAGNOSTICS")
print("=" * 70)

# ============================================================================
# 1. CHECK PATHS AND OPERATORS
# ============================================================================

print("\n[1] CHECKING OPERATORS...")

FACE_MESH_PATH = '/project1/luna_container/Luna/Zenna_high_poly'
BLENDSHAPES_CHOP = '/project1/blend_shapes'

container = op(FACE_MESH_PATH)
if container:
    print(f"  Container: {container.path} [OK]")
else:
    print(f"  Container: {FACE_MESH_PATH} [NOT FOUND]")

mesh = op(FACE_MESH_PATH + '/mesh')
if mesh:
    try:
        num_pts = mesh.numPoints
    except:
        num_pts = "(not accessible)"
    print(f"  Mesh: {mesh.path} (type: {type(mesh).__name__}, points: {num_pts}) [OK]")
else:
    print(f"  Mesh: NOT FOUND")

deform = op(FACE_MESH_PATH + '/deform')
if deform:
    print(f"  Deform: {deform.path} (type: {type(deform).__name__}) [OK]")
    # Check what SOP the deform is reading from
    if hasattr(deform.par, 'sop'):
        print(f"    deform.par.sop = '{deform.par.sop.eval()}'")
    else:
        print(f"    No 'sop' parameter found on deform")
        print(f"    Available parameters:")
        for p in deform.pars()[:20]:
            print(f"      {p.name} = {p.eval()}")
else:
    print(f"  Deform: NOT FOUND")

script_sop = op(FACE_MESH_PATH + '/face_deform')
if script_sop:
    print(f"  Script SOP: {script_sop.path} [OK]")
    print(f"    Type: {type(script_sop).__name__}")
    print(f"    Callbacks DAT: '{script_sop.par.callbacks.eval()}'")
    print(f"    Has input: {len(script_sop.inputs) > 0 if hasattr(script_sop, 'inputs') else 'N/A'}")
    if hasattr(script_sop, 'inputs') and script_sop.inputs:
        print(f"    Input: {script_sop.inputs[0].path} (type: {type(script_sop.inputs[0]).__name__})")
    try:
        print(f"    Num points: {script_sop.numPoints}")
    except:
        print(f"    Num points: (cannot access)")

    # Check if it has our state
    if hasattr(script_sop, '_mouth_state'):
        state = script_sop._mouth_state
        print(f"    State initialized: {state.get('initialized', False)}")
        print(f"    Mouth vertices: {len(state.get('mouth_vertices', []))}")
        print(f"    Upper lip: {len(state.get('upper_lip_vertices', []))}")
        print(f"    Lower lip: {len(state.get('lower_lip_vertices', []))}")
    else:
        print(f"    State: NOT INITIALIZED (script hasn't run)")
else:
    print(f"  Script SOP: NOT FOUND - Run setup_mouth_deform.py first")

script_dat = op(FACE_MESH_PATH + '/mouth_deform_script')
if script_dat:
    print(f"  Script DAT: {script_dat.path} [OK]")
    print(f"    Text length: {len(script_dat.text)} chars")
else:
    print(f"  Script DAT: NOT FOUND")

blend_chop = op(BLENDSHAPES_CHOP)
if blend_chop:
    print(f"  Blendshapes CHOP: {blend_chop.path} ({blend_chop.numChans} channels) [OK]")
else:
    print(f"  Blendshapes CHOP: NOT FOUND at {BLENDSHAPES_CHOP}")

# ============================================================================
# 2. CHECK BLENDSHAPE VALUES
# ============================================================================

print("\n[2] CHECKING BLENDSHAPE VALUES...")

if blend_chop:
    mouth_channels = ['jawOpen', 'mouthSmileLeft', 'mouthSmileRight',
                      'mouthUpperUpLeft', 'mouthUpperUpRight',
                      'mouthLowerDownLeft', 'mouthLowerDownRight',
                      'mouthPucker', 'mouthFrownLeft', 'mouthFrownRight']

    print("  Current values (move your face to see changes):")
    for name in mouth_channels:
        try:
            chan = blend_chop[name]
            if chan:
                val = chan.eval()
                bar = '#' * int(val * 20)
                print(f"    {name:25s} = {val:.3f} |{bar}")
            else:
                print(f"    {name:25s} = CHANNEL NOT FOUND")
        except:
            print(f"    {name:25s} = ERROR")
else:
    print("  Cannot check - blendshapes CHOP not found")

# ============================================================================
# 3. CHECK MESH GEOMETRY BOUNDS
# ============================================================================

print("\n[3] ANALYZING MESH GEOMETRY...")

# Try to get geometry from script_sop (which should have copied from mesh)
geo_source = script_sop if script_sop else mesh
geo_name = "Script SOP" if script_sop else "mesh"

if geo_source and hasattr(geo_source, 'points'):
    print(f"  Reading geometry from: {geo_source.path}")
    # Find actual Y and Z bounds
    y_vals = []
    z_vals = []
    try:
        for pt in geo_source.points:
            y_vals.append(pt.P[1])
            z_vals.append(pt.P[2])
    except Exception as e:
        print(f"  ERROR accessing points: {e}")

    if y_vals:
        print(f"  Total vertices: {len(y_vals)}")
        print(f"  Y range: {min(y_vals):.3f} to {max(y_vals):.3f}")
        print(f"  Z range: {min(z_vals):.3f} to {max(z_vals):.3f}")

        # Count vertices in different Y ranges
        print("\n  Vertex distribution by Y:")
        for y_start in [0.0, 0.5, 1.0, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0]:
            y_end = y_start + 0.1
            count = sum(1 for y in y_vals if y_start <= y < y_end)
            if count > 0:
                print(f"    Y [{y_start:.1f} - {y_end:.1f}]: {count} vertices")

        # Find likely mouth region (middle third of face height, front of face)
        y_mid = (min(y_vals) + max(y_vals)) / 2
        z_front = max(z_vals) - (max(z_vals) - min(z_vals)) * 0.3

        print(f"\n  Estimated face center Y: {y_mid:.3f}")
        print(f"  Estimated front Z threshold: {z_front:.3f}")

        # Sample some front-facing vertices around mouth area
        print("\n  Sample vertices in potential mouth region (front, middle height):")
        count = 0
        try:
            for pt in geo_source.points:
                y, z = pt.P[1], pt.P[2]
                if abs(y - y_mid) < 0.2 and z > z_front:
                    if count < 10:
                        print(f"    Vertex {pt.index}: Y={y:.3f}, Z={z:.3f}")
                    count += 1
            print(f"    (Found {count} vertices in this region)")
        except Exception as e:
            print(f"    Error sampling vertices: {e}")
    else:
        print("  No vertex data collected")
else:
    print("  Cannot analyze - no geometry source available")

# ============================================================================
# 4. TEST SCRIPT SOP EXECUTION
# ============================================================================

print("\n[4] TESTING SCRIPT SOP EXECUTION...")

if script_sop and script_dat:
    # Force a cook
    script_sop.cook(force=True)

    # Check if state was created
    if hasattr(script_sop, '_mouth_state'):
        state = script_sop._mouth_state
        print(f"  Script executed successfully!")
        print(f"  Found {len(state.get('mouth_vertices', []))} mouth vertices")

        if state.get('mouth_vertices'):
            # Show some sample vertices
            print(f"  Sample mouth vertex indices: {state['mouth_vertices'][:10]}")

            # Check if vertices are actually being modified
            if state.get('prev_deltas'):
                print(f"  Deltas stored for {len(state['prev_deltas'])} vertices")
                # Show sample delta
                for idx, delta in list(state['prev_deltas'].items())[:3]:
                    print(f"    Vertex {idx}: delta = ({delta[0]:.4f}, {delta[1]:.4f}, {delta[2]:.4f})")
            else:
                print(f"  No deltas stored yet (blendshapes might be zero)")
        else:
            print(f"  WARNING: No mouth vertices found!")
            print(f"  Check MOUTH_REGION bounds in the script")
    else:
        print(f"  Script did NOT execute - check callbacks DAT connection")
        print(f"  Expected callbacks: {script_dat.path}")
        print(f"  Actual callbacks: {script_sop.par.callbacks.eval()}")
else:
    print("  Cannot test - Script SOP or DAT not found")

# ============================================================================
# 5. CHECK RENDER CHAIN AND OPERATOR TYPES
# ============================================================================

print("\n[5] CHECKING GEOMETRY CHAIN...")

# The FBX uses POPs not SOPs - this is important!
if mesh:
    print(f"  mesh operator type: {type(mesh).__name__}")
    print(f"  mesh family: {mesh.family}")
    if hasattr(mesh, 'inputs') and mesh.inputs:
        print(f"  mesh input: {mesh.inputs[0].path}")

if deform:
    print(f"  deform operator type: {type(deform).__name__}")
    print(f"  deform family: {deform.family}")
    if hasattr(deform, 'inputs') and deform.inputs:
        for i, inp in enumerate(deform.inputs):
            print(f"  deform input {i}: {inp.path} ({type(inp).__name__})")

# Check the geo COMP's render output
print(f"\n  Geo COMP render settings:")
if container:
    print(f"    Container type: {type(container).__name__}")
    print(f"    Container family: {container.family}")

    # Check what the geo COMP uses for display/render
    if hasattr(container.par, 'displayop'):
        print(f"    Display OP: {container.par.displayop.eval()}")
    if hasattr(container.par, 'renderop'):
        print(f"    Render OP: {container.par.renderop.eval()}")

    # List all children to understand structure
    print(f"\n  All operators in {container.name}:")
    for child in container.children:
        inp_str = ""
        if hasattr(child, 'inputs') and child.inputs:
            inp_str = f" <- {[i.name for i in child.inputs]}"
        print(f"    {child.name} ({type(child).__name__}){inp_str}")

# ============================================================================
# 6. CRITICAL ISSUE: POP vs SOP
# ============================================================================

print("\n[6] ARCHITECTURE ANALYSIS...")

print("""
  ISSUE IDENTIFIED: The FBX geometry chain uses POPs, not SOPs!

  Current chain:
    mesh (importselectPOP) -> deform (skindeformPOP) -> [rendered]

  Our Script SOP is disconnected from this chain because:
    - POPs and SOPs don't directly connect
    - The skindeformPOP doesn't read from our Script SOP
    - Our Script SOP output isn't being rendered

  SOLUTION OPTIONS:

  1. RECOMMENDED: Use geo COMP's render/display parameter
     - Set the geo COMP to render from our Script SOP instead
     - This requires the Script SOP to receive the deformed geometry

  2. ALTERNATIVE: Work outside the FBX structure
     - Create a separate geo COMP with our deformation
     - Hide the original face mesh
""")

# ============================================================================
# 7. RECOMMENDATIONS
# ============================================================================

print("\n[7] NEXT STEPS...")

issues = []

# Check the core issue
if mesh and 'POP' in type(mesh).__name__:
    issues.append("CRITICAL: mesh is a POP, not a SOP. Script SOP cannot connect directly.")
    issues.append("  -> Need to convert POP output to SOP, or use different approach.")

if not script_sop:
    issues.append("- Script SOP not created. Run: exec(open(project.folder + '/setup_mouth_deform.py').read())")

if script_sop and not script_dat:
    issues.append("- Script DAT not found. The script content is missing.")

if script_sop and script_dat:
    if script_sop.par.callbacks.eval() != script_dat.path:
        issues.append(f"- Callbacks not linked. Set script_sop.par.callbacks to '{script_dat.path}'")

if script_sop:
    # Check if script_sop has geometry
    try:
        pts = script_sop.numPoints
        if pts == 0:
            issues.append(f"- Script SOP has 0 points - not receiving geometry from POP input")
        else:
            issues.append(f"- Script SOP has {pts} points (geometry received OK)")
    except:
        issues.append("- Cannot check Script SOP point count")

if blend_chop:
    jaw_open = blend_chop['jawOpen']
    if jaw_open and jaw_open.eval() < 0.01:
        issues.append("- jawOpen is ~0. Open your mouth to test, or check MediaPipe is running")

for issue in issues:
    print(f"  {issue}")

print("\n" + "=" * 70)
print("END DIAGNOSTICS")
print("=" * 70 + "\n")
