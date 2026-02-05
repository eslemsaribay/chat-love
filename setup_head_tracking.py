# ============================================================================
# FACE TRACKING FINAL - MediaPipe to Luna FBX
# ============================================================================
# Single script to set up face point tracking for Luna model
#
# USAGE:
#   exec(open(project.folder + '/face_tracking_final.py').read())
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
HEAD_BONE_PATH = '/project1/luna_container/Luna/mixamorig_Head'  # Head bone
CONTAINER_PATH = '/project1'                        # Where to create operators

# ============================================================================
# TUNING PARAMETERS
# ============================================================================

PITCH_MULT = 200.0    # Up/down sensitivity
YAW_MULT = 150.0      # Left/right sensitivity
ROLL_MULT = 5.0       # Tilt sensitivity
SMOOTH = 0.85         # Smoothing (0-1, higher = smoother)

# Offset adjustment for neutral pose alignment
# Positive PITCH_OFFSET = model looks more UP at neutral
# Positive YAW_OFFSET = model looks more RIGHT at neutral
PITCH_OFFSET = 5.0
YAW_OFFSET = 3.0
ROLL_OFFSET = 0.0

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
# FACE TRACKING - Execute DAT
# ============================================================================

MEDIAPIPE = '{MEDIAPIPE_CHOP}'
HEAD_POSE = '{CONTAINER_PATH}/luna_head_pose'

# Landmarks (MediaPipe face mesh indices)
NOSE = 4
FOREHEAD = 10
CHIN = 152
LEFT_EYE = 33
RIGHT_EYE = 263
LEFT_CHEEK = 234
RIGHT_CHEEK = 454

# Tuning (edit these to adjust behavior)
PITCH_MULT = {PITCH_MULT}
YAW_MULT = {YAW_MULT}
ROLL_MULT = {ROLL_MULT}
SMOOTH = {SMOOTH}

# Offsets for neutral pose alignment
PITCH_OFFSET = {PITCH_OFFSET}
YAW_OFFSET = {YAW_OFFSET}
ROLL_OFFSET = {ROLL_OFFSET}

def getState():
    hp = op(HEAD_POSE)
    if hp is None:
        return None
    s = hp.storage.get('hpstate', None)
    if s is None:
        s = {{'prev': [0,0,0], 'neutral': None}}
        hp.storage['hpstate'] = s
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

    # Output to Constant CHOP
    hp.par.value0 = pitch
    hp.par.value1 = yaw
    hp.par.value2 = roll

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
    # Done
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("""
Operators created:
  - luna_head_pose: Constant CHOP holding rotation values
  - luna_face_exec: Execute DAT updating values each frame

Look straight at the camera to capture neutral position.

Helper commands:
  recalibrate()      - Reset neutral position (look at camera first)
  disable_tracking() - Stop tracking
  enable_tracking()  - Resume tracking
  reset_tracking()   - Full reset (removes expressions from bone)

To adjust sensitivity/offsets, edit the face_tracking DAT directly.
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
    """Full reset - removes expressions from bone, resets values."""
    # Reset bone
    hb = op(HEAD_BONE_PATH)
    if hb:
        hb.par.rx.mode = ParMode.CONSTANT
        hb.par.rx.val = 0
        hb.par.ry.mode = ParMode.CONSTANT
        hb.par.ry.val = 0
        hb.par.rz.mode = ParMode.CONSTANT
        hb.par.rz.val = 0
        print("Head bone reset to default")

    # Reset CHOP values
    hp = op(CONTAINER_PATH + '/luna_head_pose')
    if hp:
        hp.par.value0 = 0
        hp.par.value1 = 0
        hp.par.value2 = 0
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
