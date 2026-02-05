# Face Mouth Deformation Script SOP for TouchDesigner
# ===================================================
# Deforms lip/mouth vertices based on MediaPipe blendshapes and landmarks
#
# SETUP:
# 1. Create a Script SOP inside /project1/luna_container/Luna/Zenna_high_poly/
# 2. Connect deform SOP as input
# 3. Set this file as the Script parameter
# 4. Connect output to the render chain (or material)

import math

# ============================================================================
# CONFIGURATION
# ============================================================================

# Path to blendshapes CHOP
BLENDSHAPES_CHOP = '/project1/blend_shapes'

# Path to face landmarks CHOP
FACE_POINTS_CHOP = '/project1/face_points'

# Mouth region bounds (adjust based on your model's face position)
# These define the Y range where mouth vertices are located
MOUTH_REGION = {
    'y_min': 1.55,   # Lower bound of mouth region
    'y_max': 1.72,   # Upper bound of mouth region
    'z_min': 0.0,    # Front of face (positive Z is forward in this model)
    'z_max': 0.15,   # Limit to front-facing vertices
}

# Upper/lower lip boundary (vertices above this Y are upper lip)
LIP_BOUNDARY_Y = 1.63

# Deformation scales (adjust these to tune the animation)
JAW_SCALE = 0.025           # How much jawOpen moves lower vertices down
LIP_UP_SCALE = 0.015        # Upper lip movement scale
LIP_DOWN_SCALE = 0.015      # Lower lip movement scale
SMILE_SCALE_X = 0.01        # Smile horizontal spread
SMILE_SCALE_Y = 0.012       # Smile vertical lift
PUCKER_SCALE_Z = 0.01       # Pucker forward protrusion
PUCKER_SCALE_X = 0.008      # Pucker horizontal compression

# Smoothing (0 = no smoothing, higher = more smoothing)
SMOOTHING = 0.6

# Debug mode - print info on first cook
DEBUG = True

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Store state in a dict attached to the scriptOP
def get_state(scriptOP):
    """Get or create state storage."""
    if not hasattr(scriptOP, '_mouth_state'):
        scriptOP._mouth_state = {
            'initialized': False,
            'rest_positions': {},      # vertex_index -> (x, y, z)
            'prev_deltas': {},         # vertex_index -> (dx, dy, dz)
            'mouth_vertices': [],      # list of vertex indices in mouth region
            'upper_lip_vertices': [],  # vertices in upper lip
            'lower_lip_vertices': [],  # vertices in lower lip
            'left_vertices': [],       # vertices on left side
            'right_vertices': [],      # vertices on right side
            'center_x': 0.0,           # center X of mouth region
        }
    return scriptOP._mouth_state


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_blendshape(chop, name):
    """Get blendshape value by name, returns 0 if not found."""
    if chop is None:
        return 0.0
    try:
        chan = chop[name]
        if chan is not None:
            return chan.eval()
    except:
        pass
    return 0.0


def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t


def smooth_value(current, target, factor):
    """Exponential smoothing - returns smoothed value."""
    return lerp(target, current, factor)


def is_in_mouth_region(pos):
    """Check if a vertex position is in the mouth region."""
    x, y, z = pos
    return (MOUTH_REGION['y_min'] <= y <= MOUTH_REGION['y_max'] and
            MOUTH_REGION['z_min'] <= z <= MOUTH_REGION['z_max'])


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize(scriptOP):
    """Initialize the deformation system - store rest positions and classify vertices."""
    state = get_state(scriptOP)

    if len(scriptOP.inputs) == 0:
        return False

    input_sop = scriptOP.inputs[0]
    if input_sop is None:
        return False

    if DEBUG:
        print(f"[MouthDeform] Initializing with {input_sop.numPoints} points...")

    # Find all mouth vertices and store rest positions
    mouth_verts = []
    upper_lip = []
    lower_lip = []
    left_verts = []
    right_verts = []

    sum_x = 0.0
    count = 0

    for point in input_sop.points:
        pos = point.P
        state['rest_positions'][point.index] = (pos[0], pos[1], pos[2])

        if is_in_mouth_region(pos):
            mouth_verts.append(point.index)
            sum_x += pos[0]
            count += 1

            # Classify as upper or lower lip
            if pos[1] > LIP_BOUNDARY_Y:
                upper_lip.append(point.index)
            else:
                lower_lip.append(point.index)

    # Calculate center X for left/right classification
    if count > 0:
        state['center_x'] = sum_x / count

    # Classify left/right
    for idx in mouth_verts:
        pos = state['rest_positions'][idx]
        if pos[0] < state['center_x']:
            left_verts.append(idx)
        else:
            right_verts.append(idx)

    state['mouth_vertices'] = mouth_verts
    state['upper_lip_vertices'] = upper_lip
    state['lower_lip_vertices'] = lower_lip
    state['left_vertices'] = left_verts
    state['right_vertices'] = right_verts
    state['initialized'] = True

    if DEBUG:
        print(f"[MouthDeform] Found {len(mouth_verts)} mouth vertices:")
        print(f"  Upper lip: {len(upper_lip)}")
        print(f"  Lower lip: {len(lower_lip)}")
        print(f"  Left side: {len(left_verts)}")
        print(f"  Right side: {len(right_verts)}")
        print(f"  Center X: {state['center_x']:.4f}")
        print(f"[MouthDeform] Initialization complete!")

    return True


# ============================================================================
# DEFORMATION
# ============================================================================

def calculate_vertex_delta(state, idx, blendshapes):
    """Calculate the deformation delta for a vertex based on blendshapes."""
    rest = state['rest_positions'][idx]
    rest_x, rest_y, rest_z = rest

    dx, dy, dz = 0.0, 0.0, 0.0

    # Get blendshape values
    jaw_open = blendshapes.get('jawOpen', 0)
    mouth_upper_up_left = blendshapes.get('mouthUpperUpLeft', 0)
    mouth_upper_up_right = blendshapes.get('mouthUpperUpRight', 0)
    mouth_lower_down_left = blendshapes.get('mouthLowerDownLeft', 0)
    mouth_lower_down_right = blendshapes.get('mouthLowerDownRight', 0)
    mouth_smile_left = blendshapes.get('mouthSmileLeft', 0)
    mouth_smile_right = blendshapes.get('mouthSmileRight', 0)
    mouth_pucker = blendshapes.get('mouthPucker', 0)
    mouth_frown_left = blendshapes.get('mouthFrownLeft', 0)
    mouth_frown_right = blendshapes.get('mouthFrownRight', 0)

    # Determine if vertex is on left or right side
    is_left = rest_x < state['center_x']
    is_upper = idx in state['upper_lip_vertices']
    is_lower = idx in state['lower_lip_vertices']

    # Calculate horizontal distance from center (for falloff)
    dist_from_center = abs(rest_x - state['center_x'])
    max_dist = 0.05  # Approximate mouth half-width
    center_factor = 1.0 - min(dist_from_center / max_dist, 1.0)  # 1 at center, 0 at edges
    edge_factor = min(dist_from_center / max_dist, 1.0)  # 0 at center, 1 at edges

    # === JAW OPEN ===
    # Lower lip and jaw move down when mouth opens
    if is_lower:
        # Lower lip moves down more at center, less at edges
        dy -= jaw_open * JAW_SCALE * (0.5 + 0.5 * center_factor)

    # === UPPER LIP ===
    if is_upper:
        if is_left:
            dy += mouth_upper_up_left * LIP_UP_SCALE
        else:
            dy += mouth_upper_up_right * LIP_UP_SCALE

    # === LOWER LIP ===
    if is_lower:
        if is_left:
            dy -= mouth_lower_down_left * LIP_DOWN_SCALE
        else:
            dy -= mouth_lower_down_right * LIP_DOWN_SCALE

    # === SMILE ===
    # Corners lift up and spread outward
    if is_left:
        smile = mouth_smile_left
        frown = mouth_frown_left
    else:
        smile = mouth_smile_right
        frown = mouth_frown_right

    # Smile affects corners more than center
    dy += smile * SMILE_SCALE_Y * edge_factor
    # Spread horizontally (left goes more left, right goes more right)
    if is_left:
        dx -= smile * SMILE_SCALE_X * edge_factor
    else:
        dx += smile * SMILE_SCALE_X * edge_factor

    # Frown pulls corners down
    dy -= frown * SMILE_SCALE_Y * edge_factor

    # === PUCKER ===
    # Lips push forward and compress horizontally
    dz += mouth_pucker * PUCKER_SCALE_Z
    # Compress toward center
    if is_left:
        dx += mouth_pucker * PUCKER_SCALE_X * edge_factor
    else:
        dx -= mouth_pucker * PUCKER_SCALE_X * edge_factor

    return (dx, dy, dz)


def apply_deformation(scriptOP):
    """Apply deformation to mouth vertices."""
    state = get_state(scriptOP)

    if not state['initialized']:
        if not initialize(scriptOP):
            return

    # Get blendshapes CHOP
    blend_chop = op(BLENDSHAPES_CHOP)
    if blend_chop is None:
        return

    # Read all relevant blendshapes
    blendshapes = {
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

    # Apply deformation to each mouth vertex
    for idx in state['mouth_vertices']:
        # Calculate target delta
        target_delta = calculate_vertex_delta(state, idx, blendshapes)

        # Apply smoothing
        if idx in state['prev_deltas']:
            prev = state['prev_deltas'][idx]
            delta = (
                smooth_value(prev[0], target_delta[0], SMOOTHING),
                smooth_value(prev[1], target_delta[1], SMOOTHING),
                smooth_value(prev[2], target_delta[2], SMOOTHING),
            )
        else:
            delta = target_delta

        state['prev_deltas'][idx] = delta

        # Apply to vertex
        rest = state['rest_positions'][idx]
        point = scriptOP.points[idx]
        point.P = (
            rest[0] + delta[0],
            rest[1] + delta[1],
            rest[2] + delta[2],
        )


# ============================================================================
# SCRIPT SOP INTERFACE
# ============================================================================

def cook(scriptOP):
    """
    Main cook function for Script SOP.
    Called every frame by TouchDesigner.
    """
    # Copy input geometry first
    if len(scriptOP.inputs) > 0 and scriptOP.inputs[0] is not None:
        scriptOP.copy(scriptOP.inputs[0])
    else:
        return

    # Apply mouth deformation
    apply_deformation(scriptOP)


def onSetupParameters(scriptOP):
    """Called when Script SOP parameters need setup."""
    page = scriptOP.appendCustomPage('Mouth Deform')

    # Add tuning parameters
    page.appendFloat('Jawscale', label='Jaw Open Scale')[0].default = JAW_SCALE
    page.appendFloat('Lipscale', label='Lip Scale')[0].default = LIP_UP_SCALE
    page.appendFloat('Smilescale', label='Smile Scale')[0].default = SMILE_SCALE_Y
    page.appendFloat('Smoothing', label='Smoothing')[0].default = SMOOTHING
    page.appendPulse('Reinit', label='Re-initialize')


def onPulse(par):
    """Handle pulse parameter events."""
    if par.name == 'Reinit':
        # Clear state to force re-initialization
        scriptOP = par.owner
        if hasattr(scriptOP, '_mouth_state'):
            delattr(scriptOP, '_mouth_state')
        print("[MouthDeform] Re-initialization triggered")


# ============================================================================
# SETUP HELPER - Run this to insert Script SOP into the geometry chain
# ============================================================================

def setup_mouth_deform_sop():
    """
    Creates and inserts the Script SOP into the Zenna_high_poly geometry chain.
    Run this once to set up the network.
    """
    import os

    face_mesh_path = '/project1/luna_container/Luna/Zenna_high_poly'
    face_mesh = op(face_mesh_path)

    if face_mesh is None:
        print(f"[MouthDeform] ERROR: Face mesh not found at {face_mesh_path}")
        return False

    # Find the deform SOP
    deform = face_mesh.op('deform')
    if deform is None:
        print(f"[MouthDeform] ERROR: deform SOP not found in {face_mesh_path}")
        return False

    # Check if Script SOP already exists
    script_sop = face_mesh.op('face_deform')
    if script_sop is not None:
        print(f"[MouthDeform] Script SOP already exists at {script_sop.path}")
        return True

    # Create Script SOP
    script_sop = face_mesh.create(scriptSOP, 'face_deform')

    # Set the script file - Script SOP uses 'dat' parameter to reference a DAT
    # Or we can set callbacks directly. For file-based scripts, use 'callbacks' parameter
    script_path = project.folder + '/face_mouth_deform.py'
    if os.path.exists(script_path):
        # Script SOP doesn't have a file parameter - it uses a DAT reference or inline code
        # We'll set it to use callbacks DAT pattern instead
        print(f"[MouthDeform] Script SOP created. You need to manually set up the script:")
        print(f"  1. Create a Text DAT with the script content")
        print(f"  2. Set the Script SOP's 'Callbacks DAT' parameter to that DAT")
        print(f"  OR copy the cook() function content to the Script SOP's script parameter")
    else:
        print(f"[MouthDeform] WARNING: Script file not found at {script_path}")

    # Connect: deform -> face_deform
    script_sop.inputConnectors[0].connect(deform)

    # Position nicely in network
    script_sop.nodeX = deform.nodeX + 150
    script_sop.nodeY = deform.nodeY

    # Find what was connected to deform's output and reconnect to script_sop
    # Usually the material references the geometry
    material = face_mesh.op('phong1')
    if material is not None:
        # Check if material has a geometry reference
        # In this case, the FBX COMP handles rendering, so we just need the SOP chain
        pass

    print(f"[MouthDeform] Script SOP created at {script_sop.path}")
    print(f"  Input: {deform.path}")
    print(f"  Script: {script_path}")
    print("\n  NOTE: You may need to update the render references to use face_deform instead of deform")

    return True


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == '__main__' or True:
    print("\n" + "=" * 60)
    print("MOUTH DEFORMATION SCRIPT SOP")
    print("=" * 60)

    # Check blendshapes
    blend_chop = op(BLENDSHAPES_CHOP)
    if blend_chop:
        print(f"\nBlendshapes CHOP: {BLENDSHAPES_CHOP}")
        print(f"  Channels: {blend_chop.numChans}")

        # List mouth-related channels
        mouth_chans = []
        for chan in blend_chop.chans():
            if 'mouth' in chan.name.lower() or 'jaw' in chan.name.lower():
                mouth_chans.append((chan.name, chan.eval()))

        print(f"\n  Mouth-related channels ({len(mouth_chans)}):")
        for name, val in sorted(mouth_chans):
            print(f"    {name} = {val:.3f}")
    else:
        print(f"\nWARNING: Blendshapes CHOP not found at {BLENDSHAPES_CHOP}")

    print("\n" + "-" * 60)
    print("SETUP:")
    print("  Run: setup_mouth_deform_sop()")
    print("  This will create the Script SOP in the geometry chain.")
    print("-" * 60 + "\n")
