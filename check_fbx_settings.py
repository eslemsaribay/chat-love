# Check FBX COMP Settings for POP/SOP Switch
# ============================================
# Explore if we can switch from POPs to SOPs
#
# exec(open(project.folder + '/check_fbx_settings.py').read())

print("\n" + "=" * 70)
print("CHECKING FBX COMP SETTINGS")
print("=" * 70)

# The Luna FBX COMP path
FBX_PATH = '/project1/luna_container/Luna'

fbx = op(FBX_PATH)
if fbx is None:
    print(f"ERROR: FBX COMP not found at {FBX_PATH}")
    raise SystemExit

print(f"\nFBX COMP: {fbx.path}")
print(f"Type: {type(fbx).__name__}")

# ============================================================================
# Check all parameters related to import/POPs
# ============================================================================

print("\n[1] SEARCHING FOR IMPORT/POP RELATED PARAMETERS...")

relevant_pars = []
for p in fbx.pars():
    name_lower = p.name.lower()
    if any(keyword in name_lower for keyword in ['import', 'pop', 'sop', 'geo', 'mesh', 'build', 'update']):
        relevant_pars.append((p.name, p.eval(), p.mode, p.page.name if p.page else 'N/A'))

if relevant_pars:
    print(f"\n  Found {len(relevant_pars)} relevant parameters:")
    for name, val, mode, page in sorted(relevant_pars, key=lambda x: x[3]):
        print(f"    [{page}] {name} = {val}")
else:
    print("  No obvious import/POP parameters found")

# ============================================================================
# Check specific known FBX parameters
# ============================================================================

print("\n[2] CHECKING SPECIFIC FBX PARAMETERS...")

# Try different possible parameter names
param_checks = [
    'importpops', 'Importpops', 'importPops', 'ImportPops',
    'usepops', 'usePops', 'pops', 'Pops',
    'straighttogpu', 'Straighttogpu', 'directtogpu',
    'import', 'Import', 'rebuild', 'Rebuild', 'update', 'Update'
]

for pname in param_checks:
    if hasattr(fbx.par, pname):
        val = getattr(fbx.par, pname).eval()
        print(f"  fbx.par.{pname} = {val}")

# ============================================================================
# List ALL parameters on FBX page
# ============================================================================

print("\n[3] ALL PARAMETERS BY PAGE...")

pages = {}
for p in fbx.pars():
    page_name = p.page.name if p.page else 'Unknown'
    if page_name not in pages:
        pages[page_name] = []
    pages[page_name].append((p.name, p.eval()))

for page_name in sorted(pages.keys()):
    if page_name.lower() in ['fbx', 'import', 'geo', 'geometry', 'common']:
        print(f"\n  Page: {page_name}")
        for name, val in pages[page_name][:20]:  # First 20 params
            val_str = str(val)[:50]  # Truncate long values
            print(f"    {name} = {val_str}")

# ============================================================================
# Check the parent container (luna_container)
# ============================================================================

print("\n[4] CHECKING PARENT CONTAINER...")

parent = op('/project1/luna_container')
if parent:
    print(f"  Parent: {parent.path} ({type(parent).__name__})")

    # Check if it's an FBX COMP
    for p in parent.pars():
        name_lower = p.name.lower()
        if 'import' in name_lower or 'pop' in name_lower or 'fbx' in name_lower:
            print(f"    {p.name} = {p.eval()}")

# ============================================================================
# Summary and recommendations
# ============================================================================

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
The FBX COMP uses POPs internally for geometry. The 'Import POPs' setting
controls this behavior.

OPTIONS TO ENABLE SOP-BASED DEFORMATION:

1. DISABLE IMPORT POPs (if available):
   - Find the 'Import POPs' or similar parameter
   - Set it to False/Off
   - Click 'Rebuild' or 'Import' to regenerate the network
   - This will convert internal operators from POPs to SOPs

2. MANUAL APPROACH:
   - Create an Object Merge SOP outside the FBX structure
   - Reference the geometry COMP directly
   - Apply deformation in the external SOP chain
   - Use this for rendering instead

3. CHOP-BASED APPROACH:
   - Use SOP to CHOP to extract point positions
   - Modify positions based on blendshapes
   - Use CHOP to SOP to output modified geometry

To try option 1, look for 'Import POPs' in the FBX COMP parameters
and set it to OFF, then rebuild.
""")

print("=" * 70 + "\n")
