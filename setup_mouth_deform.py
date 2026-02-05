# Setup Mouth Deformation Script SOP for TouchDesigner
# =====================================================
# Creates Text DAT with deform script and links to Script SOP
#
# USAGE:
# exec(open(project.folder + '/setup_mouth_deform.py').read())

# ============================================================================
# CONFIGURATION
# ============================================================================

FACE_MESH_PATH = '/project1/luna_container/Luna/Zenna_high_poly'
BLENDSHAPES_CHOP = '/project1/blend_shapes'

# Mouth region bounds (adjust based on your model)
MOUTH_Y_MIN = 1.0
MOUTH_Y_MAX = 2.0
MOUTH_Z_MIN = 0.0
MOUTH_Z_MAX = 0.15
LIP_BOUNDARY_Y = 1.63

# Deformation scales
JAW_SCALE = 0.025
LIP_UP_SCALE = 0.015
LIP_DOWN_SCALE = 0.015
SMILE_SCALE_X = 0.01
SMILE_SCALE_Y = 0.012
PUCKER_SCALE_Z = 0.01
PUCKER_SCALE_X = 0.008
SMOOTHING = 0.6

# ============================================================================
# SCRIPT CONTENT FOR TEXT DAT
# ============================================================================

SCRIPT_CONTENT = '''
import math

# Configuration - injected from setup script
BLENDSHAPES_CHOP = '{blendshapes_chop}'
MOUTH_REGION = {{'y_min': {y_min}, 'y_max': {y_max}, 'z_min': {z_min}, 'z_max': {z_max}}}
LIP_BOUNDARY_Y = {lip_boundary}
JAW_SCALE = {jaw_scale}
LIP_UP_SCALE = {lip_up_scale}
LIP_DOWN_SCALE = {lip_down_scale}
SMILE_SCALE_X = {smile_x}
SMILE_SCALE_Y = {smile_y}
PUCKER_SCALE_Z = {pucker_z}
PUCKER_SCALE_X = {pucker_x}
SMOOTHING = {smoothing}

def get_state(scriptOP):
    if not hasattr(scriptOP, '_mouth_state'):
        scriptOP._mouth_state = {{
            'initialized': False,
            'rest_positions': {{}},
            'prev_deltas': {{}},
            'mouth_vertices': [],
            'upper_lip_vertices': [],
            'lower_lip_vertices': [],
            'center_x': 0.0,
        }}
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
        return False

    input_sop = scriptOP.inputs[0]
    mouth_verts, upper_lip, lower_lip = [], [], []
    sum_x, count = 0.0, 0

    for point in input_sop.points:
        pos = point.P
        state['rest_positions'][point.index] = (pos[0], pos[1], pos[2])
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

    state['mouth_vertices'] = mouth_verts
    state['upper_lip_vertices'] = upper_lip
    state['lower_lip_vertices'] = lower_lip
    state['initialized'] = True
    print(f"[MouthDeform] Found {{len(mouth_verts)}} mouth vertices (upper: {{len(upper_lip)}}, lower: {{len(lower_lip)}})")
    return True

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
    if not state['initialized']:
        if not initialize(scriptOP):
            return

    blend_chop = op(BLENDSHAPES_CHOP)
    if blend_chop is None:
        return

    # Read blendshapes
    bs = {{
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
    }}

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

# ============================================================================
# SETUP FUNCTIONS
# ============================================================================

def create_script_dat():
    """Create Text DAT with the mouth deform script."""
    container = op(FACE_MESH_PATH)
    if container is None:
        print(f"[Setup] ERROR: Face mesh not found at {FACE_MESH_PATH}")
        return None

    # Create or get Text DAT
    script_dat = container.op('mouth_deform_script')
    if script_dat is None:
        script_dat = container.create(textDAT, 'mouth_deform_script')

    # Format script with configuration values
    formatted_script = SCRIPT_CONTENT.format(
        blendshapes_chop=BLENDSHAPES_CHOP,
        y_min=MOUTH_Y_MIN,
        y_max=MOUTH_Y_MAX,
        z_min=MOUTH_Z_MIN,
        z_max=MOUTH_Z_MAX,
        lip_boundary=LIP_BOUNDARY_Y,
        jaw_scale=JAW_SCALE,
        lip_up_scale=LIP_UP_SCALE,
        lip_down_scale=LIP_DOWN_SCALE,
        smile_x=SMILE_SCALE_X,
        smile_y=SMILE_SCALE_Y,
        pucker_z=PUCKER_SCALE_Z,
        pucker_x=PUCKER_SCALE_X,
        smoothing=SMOOTHING,
    )

    script_dat.text = formatted_script
    print(f"[Setup] Created script DAT: {script_dat.path}")
    return script_dat


def create_script_sop():
    """Create Script SOP and insert between mesh and deform."""
    container = op(FACE_MESH_PATH)
    if container is None:
        print(f"[Setup] ERROR: Face mesh not found at {FACE_MESH_PATH}")
        return None

    # Find mesh SOP (the base geometry before skinning)
    mesh = container.op('mesh')
    if mesh is None:
        print(f"[Setup] ERROR: mesh SOP not found in {FACE_MESH_PATH}")
        return None

    # Find deform POP (skindeformPOP)
    deform = container.op('deform')
    if deform is None:
        print(f"[Setup] ERROR: deform not found in {FACE_MESH_PATH}")
        return None

    # Check for existing Script SOP
    script_sop = container.op('face_deform')
    if script_sop is not None:
        print(f"[Setup] Script SOP already exists: {script_sop.path}")
        return script_sop

    # Create Script SOP
    script_sop = container.create(scriptSOP, 'face_deform')

    # Connect Script SOP input to mesh
    script_sop.inputConnectors[0].connect(mesh)

    # Position in network
    script_sop.nodeX = mesh.nodeX + 100
    script_sop.nodeY = mesh.nodeY

    print(f"[Setup] Created Script SOP: {script_sop.path}")

    # Update skindeformPOP to read from our Script SOP instead of mesh
    # Try different parameter names that skindeformPOP might use
    try:
        # Check what the current SOP input is
        current_sop = None
        if hasattr(deform.par, 'sop'):
            current_sop = deform.par.sop.eval()
            deform.par.sop = script_sop.name
            print(f"[Setup] Updated deform.par.sop: {current_sop} -> {script_sop.name}")
        elif hasattr(deform.par, 'Sop'):
            current_sop = deform.par.Sop.eval()
            deform.par.Sop = script_sop.name
            print(f"[Setup] Updated deform.par.Sop: {current_sop} -> {script_sop.name}")
        else:
            # List available parameters for debugging
            print(f"[Setup] WARNING: Could not find SOP parameter on deform")
            print(f"[Setup] Available parameters starting with 's':")
            for p in deform.pars():
                if p.name.lower().startswith('s'):
                    print(f"    {p.name} = {p.eval()}")
    except Exception as e:
        print(f"[Setup] WARNING: Could not update deform input: {e}")
        print(f"[Setup] You may need to manually set deform's SOP parameter to: {script_sop.name}")

    return script_sop


def link_script_to_sop(script_dat, script_sop):
    """Link Text DAT to Script SOP callbacks."""
    if script_dat is None or script_sop is None:
        return False

    script_sop.par.callbacks = script_dat.path
    print(f"[Setup] Linked callbacks: {script_sop.path} -> {script_dat.path}")
    return True


def run_setup():
    """Main setup function."""
    print("\n" + "=" * 60)
    print("MOUTH DEFORMATION SETUP")
    print("=" * 60)

    # Step 1: Create Text DAT with script
    print("\n[Step 1] Creating script DAT...")
    script_dat = create_script_dat()
    if script_dat is None:
        return False

    # Step 2: Create Script SOP
    print("\n[Step 2] Creating Script SOP...")
    script_sop = create_script_sop()
    if script_sop is None:
        return False

    # Step 3: Link them
    print("\n[Step 3] Linking script to SOP...")
    if not link_script_to_sop(script_dat, script_sop):
        return False

    # Verify blendshapes
    print("\n[Step 4] Verifying blendshapes...")
    blend_chop = op(BLENDSHAPES_CHOP)
    if blend_chop:
        print(f"  Blendshapes CHOP: {blend_chop.path} ({blend_chop.numChans} channels)")
    else:
        print(f"  WARNING: Blendshapes not found at {BLENDSHAPES_CHOP}")

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"\nScript DAT: {script_dat.path}")
    print(f"Script SOP: {script_sop.path}")
    print("\nOpen your mouth or smile to test!")
    print("\nIf no movement, adjust MOUTH_Y_MIN/MAX in this script")
    print("to match your model's mouth vertex positions.")

    return True


# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__' or True:
    run_setup()
