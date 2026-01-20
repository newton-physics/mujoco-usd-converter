# MuJoCo Menagerie Benchmark Report

**Generated on:** 2026-01-19 16:57:20

**Repository:** [https://github.com/google-deepmind/mujoco_menagerie.git](https://github.com/google-deepmind/mujoco_menagerie.git)

## Summary Statistics

| Total Models | Successful | Failed | Total Warnings | Total Errors | Average Time | Total Time | Total File Size |
|:------------:|:----------:|:------:|:--------------:|:------------:|:------------:|:----------:|:---------------:|
| 85 | 85 (100.0%) | 0 (0.0%) | 265 | 0 | 2.29s | 3m 14.52s | 398.06 MB |

## Detailed Results

| Asset | Variant | Success | [Verified (Manual)](#manual-annotation-instructions) | Errors | Warnings | Time (s) | Size (MB) | Notes | Error Messages | Warning Messages |
|-------|---------|---------|----------|-------:|--------:|---------:|---------:|----------------------|----------------|------------------|
| **[agilex_piper](https://github.com/google-deepmind/mujoco_menagerie/tree/main/agilex_piper/)** | piper | ✅ | ❌ | 0 | 4 | 4.93 | 8.30 | Most actuation in MuJoCo looks good, but the gripper is broken without equality constraints |  | lights are not supported<br>keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[agility_cassie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/agility_cassie/)** | cassie | ✅ | ❓ | 0 | 6 | 1.16 | 1.39 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'Ellipsoid'<br>cameras are not supported<br>lights are not supported<br>keys are not supported<br>equalities are not supported<br>sensors are not supported |
| **[aloha](https://github.com/google-deepmind/mujoco_menagerie/tree/main/aloha/)** | aloha | ✅ | ❓ | 0 | 5 | 2.03 | 3.00 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[anybotics_anymal_b](https://github.com/google-deepmind/mujoco_menagerie/tree/main/anybotics_anymal_b/)** | anymal_b | ✅ | ❓ | 0 | 2 | 2.97 | 9.86 |  |  | lights are not supported<br>excludes are not supported |
| **[anybotics_anymal_c](https://github.com/google-deepmind/mujoco_menagerie/tree/main/anybotics_anymal_c/)** | anymal_c | ✅ | ✅ | 0 | 2 | 0.96 | 12.90 | Manual actuation in MuJoCo looks good |  | lights are not supported<br>excludes are not supported |
|  | anymal_c_mjx | ✅ | ❓ | 0 | 3 | 0.97 | 12.85 |  |  | cameras are not supported<br>keys are not supported<br>excludes are not supported |
| **[apptronik_apollo](https://github.com/google-deepmind/mujoco_menagerie/tree/main/apptronik_apollo/)** | apptronik_apollo | ✅ | ❌ | 0 | 4 | 11.27 | 28.54 | USD View looks good, and manual articulation in MuJoCo looks good, but without exclude pairs we cannot test actuation in MuJoCo as it falls through the ground plane |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[arx_l5](https://github.com/google-deepmind/mujoco_menagerie/tree/main/arx_l5/)** | arx_l5 | ✅ | ❓ | 0 | 5 | 1.48 | 2.00 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[berkeley_humanoid](https://github.com/google-deepmind/mujoco_menagerie/tree/main/berkeley_humanoid/)** | berkeley_humanoid | ✅ | ❓ | 0 | 4 | 4.72 | 7.64 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[bitcraze_crazyflie_2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/bitcraze_crazyflie_2/)** | cf2 | ✅ | ❓ | 0 | 3 | 0.75 | 0.24 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[booster_t1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/booster_t1/)** | t1 | ✅ | ❓ | 0 | 3 | 1.92 | 3.13 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[boston_dynamics_spot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/boston_dynamics_spot/)** | spot | ✅ | ❓ | 0 | 3 | 2.75 | 6.42 |  |  | lights are not supported<br>keys are not supported<br>excludes are not supported |
|  | spot_arm | ✅ | ❓ | 0 | 3 | 2.83 | 8.69 |  |  | lights are not supported<br>keys are not supported<br>excludes are not supported |
| **[dynamixel_2r](https://github.com/google-deepmind/mujoco_menagerie/tree/main/dynamixel_2r/)** | dynamixel_2r | ✅ | ❓ | 0 | 0 | 1.41 | 1.51 |  |  |  |
| **[flybody](https://github.com/google-deepmind/mujoco_menagerie/tree/main/flybody/)** | fruitfly | ✅ | ❓ | 0 | 24 | 5.95 | 13.24 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'thorax_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'thorax_collision2'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'head_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rostrum_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'labrum_left_lower_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'labrum_right_lower_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_brown_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_membrane_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_left_fluid'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_brown_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_membrane_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'wing_right_fluid'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T1_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T1_right_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T2_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T2_right_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T3_left_collision'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'coxa_T3_right_collision'<br>Target 'abduct_abdomen' not found for actuator 'abdomen_abduct'<br>cameras are not supported<br>lights are not supported<br>tendons are not supported<br>excludes are not supported<br>sensors are not supported |
| **[fourier_n1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/fourier_n1/)** | n1 | ✅ | ❓ | 0 | 2 | 10.79 | 19.57 |  |  | lights are not supported<br>sensors are not supported |
| **[franka_emika_panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda/)** | hand | ✅ | ❓ | 0 | 4 | 0.74 | 0.42 |  |  | Target 'split' not found for actuator 'actuator8'<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
|  | mjx_panda | ✅ | ❓ | 0 | 3 | 2.02 | 6.88 |  |  | lights are not supported<br>equalities are not supported<br>excludes are not supported |
|  | mjx_panda_nohand | ✅ | ❓ | 0 | 2 | 2.05 | 6.46 |  |  | lights are not supported<br>excludes are not supported |
|  | panda | ✅ | ❓ | 0 | 6 | 2.17 | 6.89 |  |  | Target 'split' not found for actuator 'actuator8'<br>lights are not supported<br>keys are not supported<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
|  | panda_nohand | ✅ | ❓ | 0 | 3 | 1.97 | 6.47 |  |  | lights are not supported<br>keys are not supported<br>excludes are not supported |
| **[franka_fr3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_fr3/)** | fr3 | ✅ | ✅ | 0 | 2 | 2.15 | 7.35 | Manual actuation in MuJoCo looks good |  | keys are not supported<br>excludes are not supported |
| **[google_barkour_v0](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_barkour_v0/)** | barkour_v0 | ✅ | ✅ | 0 | 3 | 2.28 | 3.47 | Manual actuation in MuJoCo looks good |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
|  | barkour_v0_mjx | ✅ | ❓ | 0 | 3 | 2.32 | 3.49 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[google_barkour_vb](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_barkour_vb/)** | barkour_vb | ✅ | ❓ | 0 | 2 | 1.34 | 1.64 |  |  | cameras are not supported<br>sensors are not supported |
|  | barkour_vb_mjx | ✅ | ❓ | 0 | 2 | 1.38 | 1.64 |  |  | cameras are not supported<br>sensors are not supported |
| **[google_robot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/google_robot/)** | robot | ✅ | ❓ | 0 | 1 | 0.91 | 2.81 |  |  | lights are not supported |
| **[hello_robot_stretch](https://github.com/google-deepmind/mujoco_menagerie/tree/main/hello_robot_stretch/)** | stretch | ✅ | ❓ | 0 | 7 | 4.41 | 11.86 |  |  | Target 'forward' not found for actuator 'forward'<br>Target 'turn' not found for actuator 'turn'<br>Target 'extend' not found for actuator 'arm_extend'<br>cameras are not supported<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
| **[hello_robot_stretch_3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/hello_robot_stretch_3/)** | stretch | ✅ | ❓ | 0 | 7 | 4.83 | 12.72 |  |  | Target 'extend' not found for actuator 'arm'<br>cameras are not supported<br>keys are not supported<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported<br>sensors are not supported |
| **[i2rt_yam](https://github.com/google-deepmind/mujoco_menagerie/tree/main/i2rt_yam/)** | yam | ✅ | ❓ | 0 | 3 | 1.43 | 1.76 |  |  | lights are not supported<br>keys are not supported<br>equalities are not supported |
| **[iit_softfoot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/iit_softfoot/)** | softfoot | ✅ | ❓ | 0 | 2 | 1.67 | 1.88 |  |  | tendons are not supported<br>equalities are not supported |
| **[kinova_gen3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/kinova_gen3/)** | gen3 | ✅ | ❓ | 0 | 2 | 1.18 | 1.59 |  |  | cameras are not supported<br>keys are not supported |
| **[kuka_iiwa_14](https://github.com/google-deepmind/mujoco_menagerie/tree/main/kuka_iiwa_14/)** | iiwa14 | ✅ | ❓ | 0 | 3 | 0.81 | 1.39 |  |  | lights are not supported<br>keys are not supported<br>excludes are not supported |
| **[leap_hand](https://github.com/google-deepmind/mujoco_menagerie/tree/main/leap_hand/)** | left_hand | ✅ | ❓ | 0 | 4 | 1.18 | 2.54 |  |  | "distal.obj" contains multiple meshes, only the first one will be converted<br>"thumb_distal.obj" contains multiple meshes, only the first one will be converted<br>excludes are not supported<br>sensors are not supported |
|  | right_hand | ✅ | ❓ | 0 | 4 | 1.11 | 2.12 |  |  | "distal.obj" contains multiple meshes, only the first one will be converted<br>"thumb_distal.obj" contains multiple meshes, only the first one will be converted<br>excludes are not supported<br>sensors are not supported |
| **[low_cost_robot_arm](https://github.com/google-deepmind/mujoco_menagerie/tree/main/low_cost_robot_arm/)** | low_cost_robot_arm | ✅ | ❓ | 0 | 2 | 1.60 | 2.32 |  |  | keys are not supported<br>excludes are not supported |
| **[pal_talos](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_talos/)** | talos | ✅ | ❓ | 0 | 2 | 2.63 | 3.37 |  |  | equalities are not supported<br>excludes are not supported |
|  | talos_motor | ✅ | ❓ | 0 | 3 | 2.76 | 3.38 |  |  | keys are not supported<br>equalities are not supported<br>excludes are not supported |
|  | talos_position | ✅ | ❓ | 0 | 3 | 2.74 | 3.39 |  |  | keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[pal_tiago](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_tiago/)** | tiago | ✅ | ❓ | 0 | 2 | 1.52 | 2.12 |  |  | cameras are not supported<br>excludes are not supported |
|  | tiago_motor | ✅ | ❓ | 0 | 2 | 1.48 | 2.12 |  |  | cameras are not supported<br>excludes are not supported |
|  | tiago_position | ✅ | ❓ | 0 | 3 | 1.48 | 2.13 |  |  | cameras are not supported<br>keys are not supported<br>excludes are not supported |
|  | tiago_velocity | ✅ | ❓ | 0 | 3 | 1.50 | 2.13 |  |  | cameras are not supported<br>keys are not supported<br>excludes are not supported |
| **[pal_tiago_dual](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_tiago_dual/)** | tiago_dual | ✅ | ❓ | 0 | 1 | 2.05 | 2.68 |  |  | excludes are not supported |
|  | tiago_dual_motor | ✅ | ❓ | 0 | 1 | 2.17 | 2.69 |  |  | excludes are not supported |
|  | tiago_dual_position | ✅ | ❓ | 0 | 1 | 2.13 | 2.69 |  |  | excludes are not supported |
|  | tiago_dual_velocity | ✅ | ❓ | 0 | 1 | 2.09 | 2.69 |  |  | excludes are not supported |
| **[pndbotics_adam_lite](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pndbotics_adam_lite/)** | adam_lite | ✅ | ❓ | 0 | 0 | 7.54 | 22.13 |  |  |  |
| **[realsense_d435i](https://github.com/google-deepmind/mujoco_menagerie/tree/main/realsense_d435i/)** | d435i | ✅ | ❓ | 0 | 1 | 4.65 | 7.72 |  |  | lights are not supported |
| **[rethink_robotics_sawyer](https://github.com/google-deepmind/mujoco_menagerie/tree/main/rethink_robotics_sawyer/)** | sawyer | ✅ | ❓ | 0 | 3 | 1.78 | 6.65 |  |  | lights are not supported<br>keys are not supported<br>excludes are not supported |
| **[robot_soccer_kit](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robot_soccer_kit/)** | robot_soccer_kit | ✅ | ❓ | 0 | 0 | 2.08 | 2.33 |  |  |  |
| **[robotiq_2f85](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotiq_2f85/)** | 2f85 | ✅ | ❓ | 0 | 4 | 1.28 | 1.01 |  |  | Target 'split' not found for actuator 'fingers_actuator'<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
| **[robotiq_2f85_v4](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotiq_2f85_v4/)** | 2f85 | ✅ | ❓ | 0 | 4 | 1.55 | 1.92 |  |  | Target 'split' not found for actuator 'fingers_actuator'<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
|  | mjx_2f85 | ✅ | ❓ | 0 | 2 | 1.55 | 1.91 |  |  | equalities are not supported<br>excludes are not supported |
| **[robotis_op3](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotis_op3/)** | op3 | ✅ | ❓ | 0 | 3 | 7.88 | 11.23 |  |  | cameras are not supported<br>lights are not supported<br>excludes are not supported |
| **[shadow_dexee](https://github.com/google-deepmind/mujoco_menagerie/tree/main/shadow_dexee/)** | shadow_dexee | ✅ | ❓ | 0 | 3 | 1.95 | 2.26 |  |  | lights are not supported<br>excludes are not supported<br>sensors are not supported |
| **[shadow_hand](https://github.com/google-deepmind/mujoco_menagerie/tree/main/shadow_hand/)** | left_hand | ✅ | ❓ | 0 | 6 | 0.89 | 0.89 |  |  | Target 'lh_FFJ0' not found for actuator 'lh_A_FFJ0'<br>Target 'lh_MFJ0' not found for actuator 'lh_A_MFJ0'<br>Target 'lh_RFJ0' not found for actuator 'lh_A_RFJ0'<br>Target 'lh_LFJ0' not found for actuator 'lh_A_LFJ0'<br>tendons are not supported<br>excludes are not supported |
|  | right_hand | ✅ | ❓ | 0 | 6 | 0.88 | 0.89 |  |  | Target 'rh_FFJ0' not found for actuator 'rh_A_FFJ0'<br>Target 'rh_MFJ0' not found for actuator 'rh_A_MFJ0'<br>Target 'rh_RFJ0' not found for actuator 'rh_A_RFJ0'<br>Target 'rh_LFJ0' not found for actuator 'rh_A_LFJ0'<br>tendons are not supported<br>excludes are not supported |
| **[skydio_x2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/skydio_x2/)** | x2 | ✅ | ❓ | 0 | 9 | 0.63 | 0.38 |  |  | Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor1'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor2'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor3'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'rotor4'<br>Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'Ellipsoid'<br>cameras are not supported<br>lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[stanford_tidybot](https://github.com/google-deepmind/mujoco_menagerie/tree/main/stanford_tidybot/)** | base | ✅ | ❓ | 0 | 0 | 0.67 | 0.08 |  |  |  |
|  | tidybot | ✅ | ❓ | 0 | 6 | 1.65 | 2.41 |  |  | Target 'split' not found for actuator 'fingers_actuator'<br>cameras are not supported<br>keys are not supported<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
| **[trossen_vx300s](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trossen_vx300s/)** | vx300s | ✅ | ❓ | 0 | 4 | 0.83 | 0.48 |  |  | lights are not supported<br>keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[trossen_wx250s](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trossen_wx250s/)** | wx250s | ✅ | ❓ | 0 | 4 | 0.73 | 0.25 |  |  | lights are not supported<br>keys are not supported<br>equalities are not supported<br>excludes are not supported |
| **[trs_so_arm100](https://github.com/google-deepmind/mujoco_menagerie/tree/main/trs_so_arm100/)** | so_arm100 | ✅ | ❓ | 0 | 2 | 1.12 | 1.01 |  |  | keys are not supported<br>excludes are not supported |
| **[ufactory_lite6](https://github.com/google-deepmind/mujoco_menagerie/tree/main/ufactory_lite6/)** | lite6 | ✅ | ❓ | 0 | 1 | 1.14 | 1.21 |  |  | keys are not supported |
|  | lite6_gripper_narrow | ✅ | ❓ | 0 | 2 | 1.21 | 1.37 |  |  | keys are not supported<br>equalities are not supported |
|  | lite6_gripper_wide | ✅ | ❓ | 0 | 2 | 1.32 | 1.39 |  |  | keys are not supported<br>equalities are not supported |
| **[ufactory_xarm7](https://github.com/google-deepmind/mujoco_menagerie/tree/main/ufactory_xarm7/)** | hand | ✅ | ❓ | 0 | 4 | 1.00 | 0.71 |  |  | Target 'split' not found for actuator 'fingers_actuator'<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
|  | xarm7 | ✅ | ❓ | 0 | 5 | 1.35 | 1.50 |  |  | Target 'split' not found for actuator 'gripper'<br>keys are not supported<br>tendons are not supported<br>equalities are not supported<br>excludes are not supported |
|  | xarm7_nohand | ✅ | ❓ | 0 | 1 | 0.97 | 0.78 |  |  | keys are not supported |
| **[umi_gripper](https://github.com/google-deepmind/mujoco_menagerie/tree/main/umi_gripper/)** | umi_gripper | ✅ | ❓ | 0 | 5 | 0.84 | 0.74 |  |  | Binding a textured Material '/umi_gripper/Materials/Left_Aruco_Base_Sticker' to a Cube Prim ('/umi_gripper/Geometry/tn__/left_finger_holder/left_marker') will discard textures at render time.<br>Binding a textured Material '/umi_gripper/Materials/Right_Aruco_Base_Sticker' to a Cube Prim ('/umi_gripper/Geometry/tn__/right_finger_holder/right_marker') will discard textures at render time.<br>Target 'split' not found for actuator 'fingers_actuator'<br>cameras are not supported<br>tendons are not supported |
| **[unitree_a1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_a1/)** | a1 | ✅ | ❓ | 0 | 2 | 1.43 | 3.97 |  |  | lights are not supported<br>keys are not supported |
| **[unitree_g1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_g1/)** | g1 | ✅ | ❓ | 0 | 3 | 3.63 | 7.83 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
|  | g1_mjx | ✅ | ❓ | 0 | 3 | 3.67 | 7.83 |  |  | cameras are not supported<br>lights are not supported<br>sensors are not supported |
|  | g1_with_hands | ✅ | ❓ | 0 | 3 | 5.31 | 10.49 |  |  | lights are not supported<br>keys are not supported<br>sensors are not supported |
| **[unitree_go1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_go1/)** | go1 | ✅ | ❓ | 0 | 3 | 2.00 | 2.70 |  |  | cameras are not supported<br>lights are not supported<br>keys are not supported |
| **[unitree_go2](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_go2/)** | go2 | ✅ | ❓ | 0 | 1 | 1.80 | 6.30 |  |  | keys are not supported |
|  | go2_mjx | ✅ | ❓ | 0 | 3 | 1.77 | 6.31 |  |  | cameras are not supported<br>keys are not supported<br>sensors are not supported |
| **[unitree_h1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_h1/)** | h1 | ✅ | ❓ | 0 | 2 | 2.83 | 5.42 |  |  | lights are not supported<br>excludes are not supported |
| **[unitree_z1](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_z1/)** | z1 | ✅ | ❓ | 0 | 1 | 1.92 | 3.40 |  |  | keys are not supported |
|  | z1_gripper | ✅ | ❓ | 0 | 1 | 2.46 | 4.70 |  |  | keys are not supported |
| **[universal_robots_ur10e](https://github.com/google-deepmind/mujoco_menagerie/tree/main/universal_robots_ur10e/)** | ur10e | ✅ | ❓ | 0 | 2 | 1.78 | 6.53 |  |  | lights are not supported<br>keys are not supported |
| **[universal_robots_ur5e](https://github.com/google-deepmind/mujoco_menagerie/tree/main/universal_robots_ur5e/)** | ur5e | ✅ | ❓ | 0 | 2 | 1.75 | 6.09 |  |  | lights are not supported<br>keys are not supported |
| **[wonik_allegro](https://github.com/google-deepmind/mujoco_menagerie/tree/main/wonik_allegro/)** | left_hand | ✅ | ❓ | 0 | 1 | 0.88 | 0.47 |  |  | excludes are not supported |
|  | right_hand | ✅ | ❓ | 0 | 1 | 0.83 | 0.37 |  |  | excludes are not supported |


## Manual Annotation Instructions

### Verified Status
Each model variant can be individually annotated with "Yes", "No", or "Unknown" based on manual
inspection of the converted USD files. Update the annotations in the `tools/menagerie_annotations.yaml`
file under each variant's `verified` field.

**Consider these factors:**
- Visual correctness when loaded in USD viewer
- Proper hierarchy and naming
- Material and texture fidelity
- Physics properties preservation
- Simulation correctness in MuJoCo Simulate compared to the original MJCF file

### Notes
Document any known issues, limitations, or special considerations for each model variant in the
`notes` field under each variant in the annotations file.

### Annotation Structure
Annotations are per-variant rather than per-asset. Each XML file listed under an asset's
`xml_files` array has its own `verified`, `notes`, `evaluation_date`, `evaluator`, and `notes` fields.

### File Size Information
**Total Size:** Overall size of all files in the output directory, including USD files, textures,
and any other generated assets.

---

*Report generated by mujoco-usd-converter benchmark tool*
