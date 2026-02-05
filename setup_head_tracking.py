# ============================================================================
# FACE TRACKING - MediaPipe to Luna FBX
# ============================================================================
# Sets up head pose tracking and eyebrow movement for Luna model
#
# USAGE:
#   exec(open(project.folder + '/setup_head_tracking.py').read())
#
# AFTER SETUP:
#   - Look straight at camera to calibrate neutral position
#   - Recalibrate: recalibrate()
#   - Disable:     disable_tracking()
#   - Enable:      enable_tracking()
#   - Reset:       reset_tracking()
# ============================================================================

# ============================================================================
# CONFIGURATION - Adjust these paths to match your setup
# ============================================================================

MEDIAPIPE_CHOP = '/project1/face_points'           # MediaPipe face points output
BLENDSHAPES_CHOP = '/project1/blend_shapes'        # MediaPipe blendshapes output
HEAD_BONE_PATH = '/project1/luna_container/Luna/mixamorig_Head'  # Head bone
EYEBROW_PATH = '/project1/luna_container/Luna/Zenna_eyebrow006'  # Eyebrow geometry
CONTAINER_PATH = '/project1'                        # Where to create operators

# ============================================================================
# TUNING PARAMETERS - HEAD
# ============================================================================

PITCH_MULT = 200.0    # Up/down sensitivity
YAW_MULT = 150.0      # Left/right sensitivity
ROLL_MULT = 5.0       # Tilt sensitivity
SMOOTH = 0.85         # Smoothing (0-1, higher = smoother)

# Offset adjustment for neutral pose alignment
PITCH_OFFSET = 5.0
YAW_OFFSET = 3.0 
ROLL_OFFSET = 0.0

# ============================================================================
# TUNING PARAMETERS - EYEBROWS
# ============================================================================

EYEBROW_SCALE = 0.01    # How much eyebrows move (in scene units)
EYEBROW_SMOOTH = 0.6    # Smoothing for eyebrow movement (lower = more responsive)

# ============================================================================
# SETUP SCRIPT
# ============================================================================

def setup_face_tracking():
    """Main setup function - creates all necessary operators."""

    print("\n" + "=" * 70)
    print("FACE TRACKING SETUP")
    print("=" * 70)

    container = op(CONTAINER_PATH)
    if container is None:
        print(f"ERROR: Container not found at {CONTAINER_PATH}")
        return False

    # Verify MediaPipe CHOP exists
    mp = op(MEDIAPIPE_CHOP)
    if mp is None:
        print(f"ERROR: MediaPipe CHOP not found at {MEDIAPIPE_CHOP}")
        return False
    print(f"[OK] MediaPipe CHOP: {mp.path} ({mp.numSamples} samples)")

    # Verify head bone exists
    hb = op(HEAD_BONE_PATH)
    if hb is None:
        print(f"ERROR: Head bone not found at {HEAD_BONE_PATH}")
        return False
    print(f"[OK] Head bone: {hb.path}")

    # Verify eyebrow geometry exists
    eyebrow = op(EYEBROW_PATH)
    if eyebrow is None:
        print(f"WARNING: Eyebrow geometry not found at {EYEBROW_PATH}")
        print(f"         Eyebrow tracking will be skipped")
    else:
        print(f"[OK] Eyebrow geometry: {eyebrow.path}")

    # Verify blendshapes CHOP exists (needed for eyebrows)
    blend = op(BLENDSHAPES_CHOP)
    if blend is None:
        print(f"WARNING: Blendshapes CHOP not found at {BLENDSHAPES_CHOP}")
        print(f"         Eyebrow tracking will be skipped")
    else:
        print(f"[OK] Blendshapes CHOP: {blend.path} ({blend.numChans} channels)")

    # -------------------------------------------------------------------------
    # Create Constant CHOP for head pose values
    # -------------------------------------------------------------------------
    print("\n[1] Creating luna_head_pose Constant CHOP...")

    # Use unique names to avoid conflicts with existing operators
    head_pose = op(CONTAINER_PATH + '/luna_head_pose')
    if head_pose is None:
        head_pose = container.create(constantCHOP, 'luna_head_pose')
    else:
        print("    Using existing luna_head_pose")
    head_pose.par.name0 = 'mixamorig_Head:rx'
    head_pose.par.value0 = 0
    head_pose.par.name1 = 'mixamorig_Head:ry'
    head_pose.par.value1 = 0
    head_pose.par.name2 = 'mixamorig_Head:rz'
    head_pose.par.value2 = 0
    head_pose.par.name3 = 'eyebrow_ty'
    head_pose.par.value3 = 0
    head_pose.nodeX = 0
    head_pose.nodeY = -300
    print(f"    Created: {head_pose.path}")

    # -------------------------------------------------------------------------
    # Create Execute DAT with tracking logic
    # -------------------------------------------------------------------------
    print("\n[2] Creating luna_face_exec Execute DAT...")

    exec_dat = op(CONTAINER_PATH + '/luna_face_exec')
    if exec_dat is None:
        exec_dat = container.create(executeDAT, 'luna_face_exec')
    else:
        print("    Using existing luna_face_exec")
    exec_dat.nodeX = -200
    exec_dat.nodeY = -300

    # The tracking code
    tracking_code = f'''import math

# ============================================================================
# FACE TRACKING - Execute DAT (Head + Eyebrows)
# ============================================================================

MEDIAPIPE = '{MEDIAPIPE_CHOP}'
BLENDSHAPES = '{BLENDSHAPES_CHOP}'
HEAD_POSE = '{CONTAINER_PATH}/luna_head_pose'

# Landmarks (MediaPipe face mesh indices)
NOSE = 4
FOREHEAD = 10
CHIN = 152
LEFT_EYE = 33
RIGHT_EYE = 263
LEFT_CHEEK = 234
RIGHT_CHEEK = 454

# Head tuning
PITCH_MULT = {PITCH_MULT}
YAW_MULT = {YAW_MULT}
ROLL_MULT = {ROLL_MULT}
SMOOTH = {SMOOTH}

# Offsets for neutral pose alignment
PITCH_OFFSET = {PITCH_OFFSET}
YAW_OFFSET = {YAW_OFFSET}
ROLL_OFFSET = {ROLL_OFFSET}

# Eyebrow tuning
EYEBROW_SCALE = {EYEBROW_SCALE}
EYEBROW_SMOOTH = {EYEBROW_SMOOTH}

def getState():
    hp = op(HEAD_POSE)
    if hp is None:
        return None
    s = hp.storage.get('hpstate', None)
    if s is None:
        s = {{'prev': [0,0,0], 'neutral': None, 'prev_eyebrow': 0.0}}
        hp.storage['hpstate'] = s
    # Ensure prev_eyebrow exists (for upgrades)
    if 'prev_eyebrow' not in s:
        s['prev_eyebrow'] = 0.0
    return s

def angle_difference(a, b):
    diff = a - b
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return diff

def onFrameStart(frame):
    mp = op(MEDIAPIPE)
    hp = op(HEAD_POSE)

    if mp is None or hp is None:
        return
    if mp.numSamples < 468:
        return

    state = getState()
    if state is None:
        return

    def lm(idx):
        try:
            return (mp.chan('x')[idx], mp.chan('y')[idx], mp.chan('z')[idx])
        except:
            return None

    nose = lm(NOSE)
    forehead = lm(FOREHEAD)
    chin = lm(CHIN)
    left_eye = lm(LEFT_EYE)
    right_eye = lm(RIGHT_EYE)
    left_cheek = lm(LEFT_CHEEK)
    right_cheek = lm(RIGHT_CHEEK)

    if None in [nose, forehead, chin, left_eye, right_eye, left_cheek, right_cheek]:
        return

    # PITCH (up/down): Forehead Z - Chin Z
    pitch_value = forehead[2] - chin[2]

    # YAW (left/right): Left Cheek Z - Right Cheek Z
    yaw_value = left_cheek[2] - right_cheek[2]

    # ROLL (tilt): Eye line angle
    eye_dx = left_eye[0] - right_eye[0]
    eye_dy = left_eye[1] - right_eye[1]
    roll_angle = math.atan2(eye_dy, eye_dx) * 180 / math.pi

    # Capture neutral on first frame
    if state['neutral'] is None:
        state['neutral'] = {{
            'pitch_value': pitch_value,
            'yaw_value': yaw_value,
            'roll_angle': roll_angle
        }}
        print("Face tracking: Neutral position captured")

    n = state['neutral']

    # Calculate rotation with offsets (negated for correct direction)
    pitch = -((pitch_value - n['pitch_value']) * PITCH_MULT) + PITCH_OFFSET
    yaw = -((yaw_value - n['yaw_value']) * YAW_MULT) + YAW_OFFSET
    roll = angle_difference(roll_angle, n['roll_angle']) * ROLL_MULT + ROLL_OFFSET

    # Clamp to reasonable values
    pitch = max(-40, min(40, pitch))
    yaw = max(-50, min(50, yaw))
    roll = max(-25, min(25, roll))

    # Smoothing
    p = state['prev']
    pitch = p[0] * SMOOTH + pitch * (1 - SMOOTH)
    yaw = p[1] * SMOOTH + yaw * (1 - SMOOTH)
    roll = p[2] * SMOOTH + roll * (1 - SMOOTH)
    state['prev'] = [pitch, yaw, roll]

    # Output head pose to Constant CHOP
    hp.par.value0 = pitch
    hp.par.value1 = yaw
    hp.par.value2 = roll

    # -------------------------------------------------------------------------
    # EYEBROW TRACKING
    # -------------------------------------------------------------------------
    blend = op(BLENDSHAPES)
    if blend is not None:
        # Read eyebrow blendshapes (safe get)
        def get_blend(name):
            try:
                c = blend[name]
                return c.eval() if c else 0.0
            except:
                return 0.0

        # MediaPipe eyebrow blendshapes
        brow_inner_up = get_blend('browInnerUp')
        brow_down_l = get_blend('browDownLeft')
        brow_down_r = get_blend('browDownRight')
        brow_outer_up_l = get_blend('browOuterUpLeft')
        brow_outer_up_r = get_blend('browOuterUpRight')

        # Combine: up values raise, down values lower
        brow_up = brow_inner_up + (brow_outer_up_l + brow_outer_up_r) / 2
        brow_down = (brow_down_l + brow_down_r) / 2

        # Net eyebrow movement
        eyebrow_raw = (brow_up - brow_down) * EYEBROW_SCALE

        # Smooth
        eyebrow_val = state['prev_eyebrow'] * EYEBROW_SMOOTH + eyebrow_raw * (1 - EYEBROW_SMOOTH)
        state['prev_eyebrow'] = eyebrow_val

        # Output
        hp.par.value3 = eyebrow_val

# Required callback stubs
def onFrameEnd(frame):
    return

def onPlayStateChange(state):
    return

def onDeviceChange():
    return

def onProjectPreSave():
    return

def onProjectPostSave():
    return

def onCreate():
    return

def onExit():
    return

def onStart():
    return
'''

    exec_dat.text = tracking_code
    exec_dat.par.active = True
    exec_dat.par.framestart = True
    exec_dat.par.frameend = False
    print(f"    Created: {exec_dat.path}")

    # -------------------------------------------------------------------------
    # Connect head_pose to head bone via expressions
    # -------------------------------------------------------------------------
    print("\n[3] Connecting to head bone...")

    HEAD_POSE_PATH = CONTAINER_PATH + '/luna_head_pose'

    hb.par.rx.mode = ParMode.EXPRESSION
    hb.par.rx.expr = f"op('{HEAD_POSE_PATH}')['mixamorig_Head:rx']"

    hb.par.ry.mode = ParMode.EXPRESSION
    hb.par.ry.expr = f"op('{HEAD_POSE_PATH}')['mixamorig_Head:ry']"

    hb.par.rz.mode = ParMode.EXPRESSION
    hb.par.rz.expr = f"op('{HEAD_POSE_PATH}')['mixamorig_Head:rz']"

    print(f"    rx -> head_pose[mixamorig_Head:rx]")
    print(f"    ry -> head_pose[mixamorig_Head:ry]")
    print(f"    rz -> head_pose[mixamorig_Head:rz]")

    # -------------------------------------------------------------------------
    # Connect eyebrow to blendshape tracking via Transform POP
    # -------------------------------------------------------------------------
    print("\n[4] Setting up eyebrow vertical tracking...")

    eyebrow = op(EYEBROW_PATH)
    HEAD_POSE_PATH = CONTAINER_PATH + '/luna_head_pose'

    if eyebrow is None:
        print(f"    Eyebrow not found at {EYEBROW_PATH} - skipped")
    else:
        # First, clean up any old expressions from COMP transform
        for p in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'px', 'py', 'pz']:
            par = getattr(eyebrow.par, p, None)
            if par and par.mode == ParMode.EXPRESSION:
                par.mode = ParMode.CONSTANT
                par.val = 0
                print(f"    Cleaned old expression from COMP {p}")

        # Find the deform POP (skindeformPOP) inside the eyebrow COMP
        deform_pop = eyebrow.op('deform')
        if deform_pop is None:
            print(f"    ERROR: No 'deform' POP found inside eyebrow COMP")
        else:
            print(f"    Found deform POP: {deform_pop.path}")

            # Check if we already have a transform POP
            transform_pop = eyebrow.op('eyebrow_offset')
            if transform_pop is None:
                # Create Transform POP after the deform
                transform_pop = eyebrow.create(transformPOP, 'eyebrow_offset')
                print(f"    Created: {transform_pop.path}")
            else:
                print(f"    Using existing: {transform_pop.path}")

            # Connect: deform -> transform
            transform_pop.inputConnectors[0].connect(deform_pop)

            # Position in network
            transform_pop.nodeX = deform_pop.nodeX + 150
            transform_pop.nodeY = deform_pop.nodeY

            # Link transform POP's ty to eyebrow tracking
            transform_pop.par.ty.mode = ParMode.EXPRESSION
            transform_pop.par.ty.expr = f"op('{HEAD_POSE_PATH}')['eyebrow_ty']"
            print(f"    Transform POP ty -> luna_head_pose['eyebrow_ty']")

            # Set this POP as the display/render node for the geometryCOMP
            # POPs use the .display property (not par.display)
            # First, turn OFF the deform POP's display/render
            deform_pop.display = False
            deform_pop.render = False
            # Then set our transform POP as the output
            transform_pop.display = True
            transform_pop.render = True
            print(f"    Set transform POP as sole render output")

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("""
Operators created:
  - luna_head_pose: Constant CHOP holding head rotation + eyebrow values
  - luna_face_exec: Execute DAT updating values each frame

Tracking:
  - Head pose: pitch (rx), yaw (ry), roll (rz)
  - Eyebrows: raise/lower (ty)

Look straight at the camera to capture neutral position.

Helper commands:
  recalibrate()      - Reset neutral position (look at camera first)
  disable_tracking() - Stop tracking
  enable_tracking()  - Resume tracking
  reset_tracking()   - Full reset (removes expressions from bone/eyebrow)

To adjust sensitivity, edit the DAT directly or change values at top of this script.
""")
    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def recalibrate():
    """Reset neutral position - look straight at camera before calling."""
    hp = op(CONTAINER_PATH + '/luna_head_pose')
    if hp and 'hpstate' in hp.storage:
        hp.storage['hpstate']['neutral'] = None
        print("Neutral position cleared - will recalibrate on next frame")
    else:
        print("luna_head_pose not found or no state stored")


def disable_tracking():
    """Disable face tracking (pause)."""
    exec_dat = op(CONTAINER_PATH + '/luna_face_exec')
    if exec_dat:
        exec_dat.par.active = False
        print("Face tracking disabled")
    else:
        print("luna_face_exec DAT not found")


def enable_tracking():
    """Enable face tracking (resume)."""
    exec_dat = op(CONTAINER_PATH + '/luna_face_exec')
    if exec_dat:
        exec_dat.par.active = True
        print("Face tracking enabled")
    else:
        print("luna_face_exec DAT not found")


def reset_tracking():
    """Full reset - removes expressions from bone and eyebrow, resets values."""
    # Reset head bone
    hb = op(HEAD_BONE_PATH)
    if hb:
        hb.par.rx.mode = ParMode.CONSTANT
        hb.par.rx.val = 0
        hb.par.ry.mode = ParMode.CONSTANT
        hb.par.ry.val = 0
        hb.par.rz.mode = ParMode.CONSTANT
        hb.par.rz.val = 0
        print("Head bone reset to default")

    # Reset eyebrow ty
    eyebrow = op(EYEBROW_PATH)
    if eyebrow:
        eyebrow.par.ty.mode = ParMode.CONSTANT
        eyebrow.par.ty.val = 0
        print("Eyebrow ty reset to default")

    # Reset CHOP values
    hp = op(CONTAINER_PATH + '/luna_head_pose')
    if hp:
        hp.par.value0 = 0
        hp.par.value1 = 0
        hp.par.value2 = 0
        hp.par.value3 = 0
        if 'hpstate' in hp.storage:
            del hp.storage['hpstate']
        print("luna_head_pose values and state cleared")

    # Disable execute
    disable_tracking()
    print("\nTracking fully reset. Run setup_face_tracking() to restart.")


# ============================================================================
# RUN SETUP
# ============================================================================

setup_face_tracking()
