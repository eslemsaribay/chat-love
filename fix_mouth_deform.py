# Fix Mouth Deformation - Convert FBX from POPs to SOPs
# =====================================================
# The FBX COMP uses POPs by default. We need to switch to SOPs for Script SOP to work.
#
# exec(open(project.folder + '/fix_mouth_deform.py').read())

print("\n" + "=" * 60)
print("FIXING MOUTH DEFORMATION SETUP")
print("=" * 60)

FBX_COMP_PATH = '/project1/luna_container/Luna'
FACE_MESH_PATH = '/project1/luna_container/Luna/Zenna_high_poly'
BLENDSHAPES_CHOP = '/project1/blend_shapes'

# ============================================================================
# STEP 1: Check FBX COMP Import POPs setting
# ============================================================================

print("\n[Step 1] Checking FBX COMP settings...")

fbx_comp = op(FBX_COMP_PATH)
if fbx_comp is None:
    print(f"ERROR: FBX COMP not found at {FBX_COMP_PATH}")
    raise SystemExit

# Check if Import POPs is enabled
import_pops = None
if hasattr(fbx_comp.par, 'importpops'):
    import_pops = fbx_comp.par.importpops.eval()
    print(f"  Import POPs setting: {import_pops}")
elif hasattr(fbx_comp.par, 'Importpops'):
    import_pops = fbx_comp.par.Importpops.eval()
    print(f"  Import POPs setting: {import_pops}")
else:
    # List FBX-related parameters
    print("  Looking for Import POPs parameter...")
    for p in fbx_comp.pars():
        if 'import' in p.name.lower() or 'pop' in p.name.lower():
            print(f"    {p.name} = {p.eval()}")

container = op(FACE_MESH_PATH)
if container is None:
    print(f"ERROR: Container not found at {FACE_MESH_PATH}")
    raise SystemExit

# ============================================================================
# STEP 2: Clean up existing setup
# ============================================================================

print("\n[Step 2] Cleaning up existing setup...")

# Delete old disconnected operators
for name in ['face_deform', 'sopto1', 'face_out', 'in1']:
    old_op = container.op(name)
    if old_op:
        old_op.destroy()
        print(f"  Deleted old {name}")

# Keep the script DAT if it exists
script_dat = container.op('mouth_deform_script')
if script_dat:
    print(f"  Keeping script DAT: {script_dat.path}")

deform = container.op('deform')
mesh = container.op('mesh')

print(f"\n  Current operators:")
print(f"    mesh type: {type(mesh).__name__}")
print(f"    deform type: {type(deform).__name__}")

# ============================================================================
# STEP 3: Create In SOP to access geo COMP's processed geometry
# ============================================================================

print("\n[Step 3] Creating In SOP to bridge POP->SOP...")

# In SOP grabs the geo COMP's processed geometry (after POPs) as a SOP
in_sop = container.op('in1')
if in_sop is None:
    in_sop = container.create(inSOP, 'in1')
    print(f"  Created: {in_sop.path}")
else:
    print(f"  Already exists: {in_sop.path}")

# Position after deform
in_sop.nodeX = deform.nodeX + 150
in_sop.nodeY = deform.nodeY

# Check if In SOP has geometry
try:
    in_pts = in_sop.numPoints
    print(f"  In SOP has {in_pts} points")
except Exception as e:
    print(f"  In SOP point check: {e}")

# ============================================================================
# STEP 4: Create Script SOP connected to In SOP
# ============================================================================

print("\n[Step 4] Creating Script SOP...")

script_sop = container.op('face_deform')
if script_sop is None:
    script_sop = container.create(scriptSOP, 'face_deform')
    print(f"  Created: {script_sop.path}")
else:
    print(f"  Already exists: {script_sop.path}")

# Connect Script SOP to In SOP output
script_sop.inputConnectors[0].connect(in_sop)
print(f"  Connected: {in_sop.name} -> {script_sop.name}")

# Position in network
script_sop.nodeX = in_sop.nodeX + 150
script_sop.nodeY = in_sop.nodeY

# ============================================================================
# STEP 5: Create/update script DAT with deformation code
# ============================================================================

print("\n[Step 5] Setting up script DAT...")

if script_dat is None:
    script_dat = container.create(textDAT, 'mouth_deform_script')
    print(f"  Created: {script_dat.path}")

# Update the script content with proper configuration
SCRIPT_CONTENT = '''
import math

# Configuration
BLENDSHAPES_CHOP = '/project1/blend_shapes'
MOUTH_REGION = {'y_min': 1.0, 'y_max': 2.0, 'z_min': -0.5, 'z_max': 0.5}
LIP_BOUNDARY_Y = 1.5
JAW_SCALE = 0.05
LIP_UP_SCALE = 0.03
LIP_DOWN_SCALE = 0.03
SMILE_SCALE_X = 0.02
SMILE_SCALE_Y = 0.025
PUCKER_SCALE_Z = 0.02
PUCKER_SCALE_X = 0.015
SMOOTHING = 0.5

# Debug - print once on init
DEBUG_INIT = True

def get_state(scriptOP):
    if not hasattr(scriptOP, '_mouth_state'):
        scriptOP._mouth_state = {
            'initialized': False,
            'rest_positions': {},
            'prev_deltas': {},
            'mouth_vertices': [],
            'upper_lip_vertices': [],
            'lower_lip_vertices': [],
            'center_x': 0.0,
            'frame_count': 0,
        }
    return scriptOP._mouth_state

def get_blendshape(chop, name):
    if chop is None:
        return 0.0
    try:
        chan = chop[name]
        if chan is not None:
            return chan.eval()
    except:
        pass
    return 0.0

def is_in_mouth_region(pos):
    x, y, z = pos
    return (MOUTH_REGION['y_min'] <= y <= MOUTH_REGION['y_max'] and
            MOUTH_REGION['z_min'] <= z <= MOUTH_REGION['z_max'])

def initialize(scriptOP):
    state = get_state(scriptOP)
    if len(scriptOP.inputs) == 0 or scriptOP.inputs[0] is None:
        print("[MouthDeform] ERROR: No input connected")
        return False

    input_geo = scriptOP.inputs[0]

    try:
        num_points = input_geo.numPoints
    except:
        print("[MouthDeform] ERROR: Cannot access input geometry points")
        return False

    if num_points == 0:
        print("[MouthDeform] ERROR: Input has 0 points")
        return False

    print(f"[MouthDeform] Initializing with {num_points} points...")

    mouth_verts, upper_lip, lower_lip = [], [], []
    sum_x, count = 0.0, 0

    # Analyze geometry bounds first
    y_min, y_max = float('inf'), float('-inf')
    z_min, z_max = float('inf'), float('-inf')

    for point in input_geo.points:
        pos = point.P
        y_min = min(y_min, pos[1])
        y_max = max(y_max, pos[1])
        z_min = min(z_min, pos[2])
        z_max = max(z_max, pos[2])
        state['rest_positions'][point.index] = (pos[0], pos[1], pos[2])

    print(f"[MouthDeform] Geometry bounds: Y=[{y_min:.3f}, {y_max:.3f}], Z=[{z_min:.3f}, {z_max:.3f}]")

    # Find mouth vertices
    for point in input_geo.points:
        pos = point.P
        if is_in_mouth_region(pos):
            mouth_verts.append(point.index)
            sum_x += pos[0]
            count += 1
            if pos[1] > LIP_BOUNDARY_Y:
                upper_lip.append(point.index)
            else:
                lower_lip.append(point.index)

    if count > 0:
        state['center_x'] = sum_x / count
    else:
        print(f"[MouthDeform] WARNING: No mouth vertices found in region Y=[{MOUTH_REGION['y_min']}, {MOUTH_REGION['y_max']}]")
        # Use middle third of geometry as fallback
        y_mid = (y_min + y_max) / 2
        y_range = (y_max - y_min) / 6
        print(f"[MouthDeform] Trying fallback region Y=[{y_mid - y_range:.3f}, {y_mid + y_range:.3f}]")

        for point in input_geo.points:
            pos = point.P
            if abs(pos[1] - y_mid) < y_range and pos[2] > (z_max - (z_max - z_min) * 0.3):
                mouth_verts.append(point.index)
                sum_x += pos[0]
                count += 1
                if pos[1] > y_mid:
                    upper_lip.append(point.index)
                else:
                    lower_lip.append(point.index)

        if count > 0:
            state['center_x'] = sum_x / count

    state['mouth_vertices'] = mouth_verts
    state['upper_lip_vertices'] = upper_lip
    state['lower_lip_vertices'] = lower_lip
    state['initialized'] = True

    print(f"[MouthDeform] Found {len(mouth_verts)} mouth vertices")
    print(f"[MouthDeform]   Upper lip: {len(upper_lip)}, Lower lip: {len(lower_lip)}")
    print(f"[MouthDeform]   Center X: {state['center_x']:.3f}")

    return len(mouth_verts) > 0

def calculate_vertex_delta(state, idx, bs):
    rest = state['rest_positions'][idx]
    rest_x, rest_y, rest_z = rest
    dx, dy, dz = 0.0, 0.0, 0.0

    is_left = rest_x < state['center_x']
    is_upper = idx in state['upper_lip_vertices']
    is_lower = idx in state['lower_lip_vertices']

    dist_from_center = abs(rest_x - state['center_x'])
    max_dist = 0.05
    center_factor = 1.0 - min(dist_from_center / max_dist, 1.0)
    edge_factor = min(dist_from_center / max_dist, 1.0)

    # Jaw open - lower lip moves down
    if is_lower:
        dy -= bs['jawOpen'] * JAW_SCALE * (0.5 + 0.5 * center_factor)
        if is_left:
            dy -= bs['mouthLowerDownLeft'] * LIP_DOWN_SCALE
        else:
            dy -= bs['mouthLowerDownRight'] * LIP_DOWN_SCALE

    # Upper lip moves up
    if is_upper:
        if is_left:
            dy += bs['mouthUpperUpLeft'] * LIP_UP_SCALE
        else:
            dy += bs['mouthUpperUpRight'] * LIP_UP_SCALE

    # Smile - corners lift and spread
    smile = bs['mouthSmileLeft'] if is_left else bs['mouthSmileRight']
    frown = bs['mouthFrownLeft'] if is_left else bs['mouthFrownRight']

    dy += smile * SMILE_SCALE_Y * edge_factor
    if is_left:
        dx -= smile * SMILE_SCALE_X * edge_factor
    else:
        dx += smile * SMILE_SCALE_X * edge_factor
    dy -= frown * SMILE_SCALE_Y * edge_factor

    # Pucker - lips push forward and compress
    dz += bs['mouthPucker'] * PUCKER_SCALE_Z
    if is_left:
        dx += bs['mouthPucker'] * PUCKER_SCALE_X * edge_factor
    else:
        dx -= bs['mouthPucker'] * PUCKER_SCALE_X * edge_factor

    return (dx, dy, dz)

def cook(scriptOP):
    # Copy input geometry
    if len(scriptOP.inputs) > 0 and scriptOP.inputs[0] is not None:
        scriptOP.copy(scriptOP.inputs[0])
    else:
        return

    state = get_state(scriptOP)

    # Initialize on first run or if no mouth vertices found
    if not state['initialized'] or not state['mouth_vertices']:
        if not initialize(scriptOP):
            return

    # Debug output every 100 frames
    state['frame_count'] += 1

    blend_chop = op(BLENDSHAPES_CHOP)
    if blend_chop is None:
        if state['frame_count'] % 100 == 1:
            print(f"[MouthDeform] WARNING: Blendshapes not found at {BLENDSHAPES_CHOP}")
        return

    # Read blendshapes
    bs = {
        'jawOpen': get_blendshape(blend_chop, 'jawOpen'),
        'mouthUpperUpLeft': get_blendshape(blend_chop, 'mouthUpperUpLeft'),
        'mouthUpperUpRight': get_blendshape(blend_chop, 'mouthUpperUpRight'),
        'mouthLowerDownLeft': get_blendshape(blend_chop, 'mouthLowerDownLeft'),
        'mouthLowerDownRight': get_blendshape(blend_chop, 'mouthLowerDownRight'),
        'mouthSmileLeft': get_blendshape(blend_chop, 'mouthSmileLeft'),
        'mouthSmileRight': get_blendshape(blend_chop, 'mouthSmileRight'),
        'mouthPucker': get_blendshape(blend_chop, 'mouthPucker'),
        'mouthFrownLeft': get_blendshape(blend_chop, 'mouthFrownLeft'),
        'mouthFrownRight': get_blendshape(blend_chop, 'mouthFrownRight'),
    }

    # Debug: print blendshape values occasionally
    if state['frame_count'] % 300 == 1:
        print(f"[MouthDeform] jawOpen={bs['jawOpen']:.3f}, smile={bs['mouthSmileLeft']:.3f}/{bs['mouthSmileRight']:.3f}")

    # Apply deformation to mouth vertices
    for idx in state['mouth_vertices']:
        target_delta = calculate_vertex_delta(state, idx, bs)

        # Smoothing
        if idx in state['prev_deltas']:
            prev = state['prev_deltas'][idx]
            delta = (
                prev[0] * SMOOTHING + target_delta[0] * (1 - SMOOTHING),
                prev[1] * SMOOTHING + target_delta[1] * (1 - SMOOTHING),
                prev[2] * SMOOTHING + target_delta[2] * (1 - SMOOTHING),
            )
        else:
            delta = target_delta

        state['prev_deltas'][idx] = delta
        rest = state['rest_positions'][idx]
        scriptOP.points[idx].P = (rest[0] + delta[0], rest[1] + delta[1], rest[2] + delta[2])
'''

script_dat.text = SCRIPT_CONTENT
print(f"  Updated script content ({len(SCRIPT_CONTENT)} chars)")

# ============================================================================
# STEP 6: Link Script DAT to Script SOP
# ============================================================================

print("\n[Step 6] Linking script to SOP...")

script_sop.par.callbacks = script_dat.path
print(f"  Set callbacks: {script_sop.par.callbacks.eval()}")

# ============================================================================
# STEP 7: Create output and update render
# ============================================================================

print("\n[Step 7] Setting up render output...")

# Create a Null SOP for clean output
null_sop = container.op('face_out')
if null_sop is None:
    null_sop = container.create(nullSOP, 'face_out')
    print(f"  Created: {null_sop.path}")

null_sop.inputConnectors[0].connect(script_sop)
null_sop.nodeX = script_sop.nodeX + 150
null_sop.nodeY = script_sop.nodeY

# Set the geo COMP to render from our output
# The geo COMP should display our deformed output instead of the POP chain
try:
    # In geo COMPs, you can set the display/render SOP
    container.par.soppath = null_sop.name
    print(f"  Set geo COMP soppath to: {null_sop.name}")
except:
    print("  Note: Could not set soppath parameter")

# Also try setting display flags
try:
    null_sop.display = True
    null_sop.render = True
    print(f"  Set display/render flags on {null_sop.name}")
except:
    pass

# ============================================================================
# STEP 8: Force cook and verify
# ============================================================================

print("\n[Step 8] Verifying setup...")

# Force cook
script_sop.cook(force=True)

# Check results
try:
    num_points = script_sop.numPoints
    print(f"  Script SOP now has {num_points} points")

    if hasattr(script_sop, '_mouth_state'):
        state = script_sop._mouth_state
        print(f"  Mouth vertices found: {len(state.get('mouth_vertices', []))}")
    else:
        print("  State not yet initialized (will init on next cook)")
except Exception as e:
    print(f"  Error checking: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 60)
print("SETUP COMPLETE")
print("=" * 60)
print(f"""
Network chain:
  mesh (importselectPOP) -> deform (skindeformPOP)
                                     |
                                     v
  in1 (In SOP - bridges POP output to SOP)
    -> face_deform (Script SOP with mouth deformation)
    -> face_out (Null SOP for clean output)

The In SOP captures the processed geometry after skeletal deformation.
The geo COMP should now render from face_out.

Open your mouth to test!

If still not working:
  1. Check if in1 has geometry: op('{container.path}/in1').numPoints
  2. Manually set display/render flags on face_out
  3. Check geo COMP render settings
""")
