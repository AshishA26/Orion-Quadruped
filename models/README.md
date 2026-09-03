# CAD Models
SolidWorks parts and assemblies for Orion's chassis and legs.

## Structure

```
models/
├── Main_Assembly.SLDASM         # Full robot assembly
├── Leg_Assembly_Left.SLDASM     # Left leg sub-assembly
├── Leg_Assembly_Right.SLDASM    # Right leg sub-assembly
├── Foot_Assembly.SLDASM         # Foot + mold assembly
├── *.SLDPRT                     # Individual parts (body panels, femur, tibia, bellcrank, linkages, etc.)
├── STL/                         # 3D print-ready STL exports (32 files)
├── 3mf_Files/                   # 3MF print files
├── linear_rail/                 # Single-leg linear-rail test jig (IK/gait validation)
├── Bearing-tests/               # Bearing fit test prints
└── Electronics/                 # Electronic component models (for assembly reference)
```

## Key Parts

| Part | Description |
|:-----|:------------|
| `Body_Bottom`, `Body_Top_Front/Rear`, `Body_Front/Rear`, `Body_side` | Main chassis panels |
| `Femur_Inside`, `Femur_Outside` | Upper leg links |
| `Tibia` | Lower leg link |
| `Bellcrank`, `Linkage_Long`, `Linkage_Short` | 4-bar linkage mechanism for tibia actuation |
| `Leg_servo_holder` | Hip servo mounting bracket |
| `Foot`, `Foot_mold_*` | Foot geometry and 2-part silicone mold |
| `Rear_Shelf`, `Rear_Shelf_Leg` | Internal magnetic shelf components |
| `Camera_Holder`, `Lidar_Camera_Holder`, `Lidar_Holder_Leg` | Sensor mounting hardware |

## Notes

- The `linear_rail/` test jig (`LinearRail.SLDASM`, `WeightTestJig.SLDASM`) was built to validate motor calibration, lifting capacity, IK, and gait before full robot integration.
- Silicone feet use a 2-part mold (`Foot_mold_top_side`, `Foot_mold_bottom_side`) with 2-part silicone injection.
